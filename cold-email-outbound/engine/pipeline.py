"""Cold Email Engine — end-to-end campaign orchestrator.

Wires all layers into a single campaign run:

  load pool -> ICP score -> suppression filter -> verify -> render copy ->
  push to Instantly -> activate

Every step is dry-run aware. A CampaignRun produces a structured summary you can
review before anything goes live. This is the function a Claude Code skill (or a
cron job) calls to run one stream.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path

from . import (config, data_layer, scoring, suppression, copy_gen,
               verification, sending)
from .models import Contact, CampaignStream, STREAM_BRAND


# Stream -> (template filename, default tier source loader)
STREAM_TEMPLATE = {
    CampaignStream.SELLER_COLD_FS_NICHE: "seller_cold_fs_niche.md",
    CampaignStream.SELLER_COLD_FS_BROAD: "seller_cold_fs_broad.md",
    CampaignStream.SELLER_COLD_CS: "seller_cold_cs.md",
    CampaignStream.BUYER_REACTIVATION: "buyer_reactivation.md",
    CampaignStream.REFERRAL_PARTNER_ADVISOR: "referral_partner_advisor.md",
    CampaignStream.REFERRAL_PARTNER_ZOR: "referral_partner_zor.md",
    CampaignStream.EVENT_PRE: "event_pre.md",
    CampaignStream.EVENT_POST: "event_post.md",
}


@dataclass
class RunSummary:
    stream: str
    brand: str
    dry_run: bool
    loaded: int = 0
    icp_eligible: int = 0
    icp_below: int = 0
    suppressed: int = 0
    suppression_reasons: dict = field(default_factory=dict)
    verified_deliverable: int = 0
    verified_dead: int = 0
    rendered: int = 0
    content_variation_pct: float = 0.0
    avg_word_count: float = 0.0
    pushed: int = 0
    campaign_id: str = ""
    activated: bool = False
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def run_campaign(
    stream: CampaignStream,
    contacts: list[Contact] | None = None,
    source_brand: str | None = None,
    limit: int = 500,
    do_verify: bool = True,
    do_push: bool = False,
    activate: bool = False,
    test_offer: str | None = None,
    extra_vars: dict | None = None,
    require_verified: bool = True,
) -> RunSummary:
    """Run one campaign stream end-to-end.

    do_push/activate default False so a run is analysis-only unless explicitly told
    to push. In DRY_RUN, even do_push=True only logs intent (no real send).
    """
    brand = STREAM_BRAND[stream]
    summary = RunSummary(stream=stream.value, brand=brand, dry_run=config.DRY_RUN)

    # 1. Load pool — source depends on stream
    if contacts is None:
        if stream in (CampaignStream.REFERRAL_PARTNER_ADVISOR, CampaignStream.REFERRAL_PARTNER_ZOR):
            # Referral partners live in Tier C
            contacts = data_layer.load_contacts(config.TIER_C, limit=limit)
        else:
            # Seller cold + buyer reactivation + events draw from Tier A by brand.
            # NOTE (go-live): buyer_reactivation needs a buyer-FLAGGED source; the
            # current dedup doesn't separate buyers from sellers. Until that's built,
            # this loads the brand's Tier A as a placeholder for dry-run wiring.
            load_brand = source_brand or brand
            if load_brand not in ("FS", "CS", "AMBIGUOUS"):
                load_brand = brand
            contacts = data_layer.load_tier_a(load_brand, limit=limit)
            if stream == CampaignStream.BUYER_REACTIVATION:
                summary.notes.append("Buyer source = Tier A placeholder; build buyer-flag source before go-live.")
    summary.loaded = len(contacts)
    if not contacts:
        summary.notes.append("No contacts loaded — check tier files / source_brand.")
        return summary

    # 2. ICP score + threshold
    # Seller-ICP scoring only applies to seller cold streams. Referral partners
    # (CPAs, advisors, franchisors) and buyer reactivation are pre-qualified by
    # being on a curated list — they'd score ~0 on the seller scorer, which is
    # correct but not a reason to exclude them.
    seller_streams = {
        CampaignStream.SELLER_COLD_FS_NICHE,
        CampaignStream.SELLER_COLD_FS_BROAD,
        CampaignStream.SELLER_COLD_CS,
    }
    if stream in seller_streams:
        scoring.apply_scores(contacts)
        eligible, below = scoring.filter_by_threshold(contacts)
    else:
        scoring.apply_scores(contacts)  # still compute scores for visibility
        eligible, below = contacts, []
        summary.notes.append("ICP threshold bypassed (curated/pre-qualified list).")
    summary.icp_eligible = len(eligible)
    summary.icp_below = len(below)

    # 3. Suppression (pre-verification: don't require verified yet)
    filt = suppression.SuppressionFilter(require_verified=False)
    clean, suppressed = filt.filter_batch(eligible)
    summary.suppressed = len(suppressed)
    summary.suppression_reasons = filt.summary(suppressed)

    # 4. Verify (LeadMagic -> ZeroBounce; dry-run simulates)
    if do_verify:
        verification.verify_contacts(clean)
        deliverable, dead = verification.split_deliverable(clean)
        summary.verified_deliverable = len(deliverable)
        summary.verified_dead = len(dead)
        sendable = deliverable
    else:
        sendable = clean
        summary.notes.append("Skipped verification (do_verify=False).")

    # Optional post-verification suppression (require verified)
    if require_verified and do_verify:
        filt2 = suppression.SuppressionFilter(require_verified=True)
        sendable, supp2 = filt2.filter_batch(sendable)
        if supp2:
            summary.notes.append(f"{len(supp2)} dropped by post-verify suppression.")

    # 5. Render copy
    tpl = copy_gen.parse_template(config.TEMPLATES_DIR / STREAM_TEMPLATE[stream])
    subjects = tpl["meta"].get("subjects", ["Quick question {{firstName}}"])
    leads = []
    step1_texts = []
    word_counts = []
    for c in sendable:
        c.campaign_stream = stream.value
        rendered = {}
        for st in tpl["steps"]:
            body, meta = copy_gen.render(st["body"], c, brand=brand, test_offer=test_offer,
                                         extra_vars=extra_vars)
            rendered[st["n"]] = body
            if st["n"] == 1:
                step1_texts.append(body)
                word_counts.append(meta["word_count"])
        leads.append((c, rendered))
    summary.rendered = len(leads)
    summary.content_variation_pct = round(copy_gen.variation_ratio(step1_texts), 1)
    summary.avg_word_count = round(sum(word_counts) / len(word_counts), 1) if word_counts else 0.0

    if summary.content_variation_pct < config.SENDING["min_spintax_variation_pct"]:
        summary.notes.append(
            f"⚠ Content variation {summary.content_variation_pct}% below "
            f"{config.SENDING['min_spintax_variation_pct']}% floor — add spintax."
        )

    # 6. Push + activate (gated; dry-run logs intent)
    if do_push and leads:
        camp = sending.create_campaign(stream, f"{stream.value} probe", subjects, tpl["steps"])
        summary.campaign_id = camp["campaign_id"]
        push = sending.push_leads(camp["campaign_id"], stream, leads)
        summary.pushed = push["added"]
        if activate:
            act = sending.activate_campaign(camp["campaign_id"])
            summary.activated = act["activated"]
    else:
        summary.notes.append("Analysis-only run (do_push=False). No campaign created.")

    return summary


def run_all_phase1_probes(limit: int = 500) -> dict[str, RunSummary]:
    """Run a dry-run probe across the active Phase 1 streams. Analysis-only by default.

    buyer_reactivation is excluded — Theodore 2026-06-07: buyers always lived in the
    GHL CRM, never in the cold archive, so there's no cold source for it. Run buyer
    re-engagement later via a GHL dormant-buyer pull (warm), not the cold engine.
    """
    streams = [
        CampaignStream.SELLER_COLD_FS_NICHE,
        CampaignStream.SELLER_COLD_FS_BROAD,
        CampaignStream.SELLER_COLD_CS,
        CampaignStream.REFERRAL_PARTNER_ADVISOR,
    ]
    out = {}
    for s in streams:
        out[s.value] = run_campaign(s, limit=limit, do_verify=True, do_push=False)
    return out
