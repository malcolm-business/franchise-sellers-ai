"""Multi-channel orchestrator.

Runs an audience through a multi-channel Sequence: applies cross-channel
suppression ONCE (so one unsubscribe/CRM-hit kills the prospect across every
channel), enrolls bulk channels (ads, LinkedIn), and walks each prospect's
touches — dispatching every touch to the right channel.

This is the multi-channel equivalent of pipeline.run_campaign. Dry-run-gated:
in dry-run it simulates the entire run + logs every intended touch, sends nothing.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from collections import Counter

from . import config, data_layer, scoring, suppression, verification, audiences
from .models import Contact
from .sequences import Sequence, get_sequence, Channel
from .channels.base import CHANNEL_REGISTRY
from . import channels as _channels  # ensure channels register


@dataclass
class ChannelPlan:
    channel: str
    available: bool
    reachable: int          # contacts this channel can actually touch
    touches_planned: int


@dataclass
class OrchestrationSummary:
    campaign: str
    brand: str
    sequence: str
    dry_run: bool
    audience_size: int = 0
    suppressed: int = 0
    suppression_reasons: dict = field(default_factory=dict)
    verified_deliverable: int = 0
    enrolled: int = 0
    channel_plans: list = field(default_factory=list)
    total_touches: int = 0
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def run_multichannel_campaign(
    campaign_name: str,
    audience: list[Contact] | str,     # a contact list, or a saved segment name
    sequence_name: str,
    brand: str | None = None,
    do_verify: bool = True,
    heyreach_campaign_id: str | None = None,
    test_offer: str | None = None,
    extra_vars: dict | None = None,
) -> OrchestrationSummary:
    """Plan + (dry-run) execute a multi-channel campaign. Analysis-safe by default.

    In DRY_RUN nothing is sent — every channel logs intent. Flip CEO_DRY_RUN=false
    + wire each channel's keys to go live per channel.
    """
    seq = get_sequence(sequence_name)
    if not seq:
        raise ValueError(f"Unknown sequence: {sequence_name}")
    brand = brand or seq.brand

    summary = OrchestrationSummary(campaign=campaign_name, brand=brand,
                                   sequence=sequence_name, dry_run=config.DRY_RUN)

    # 1. Resolve audience
    if isinstance(audience, str):
        spec = audiences.load_segment(audience)
        if not spec:
            summary.notes.append(f"Segment '{audience}' not found.")
            return summary
        contacts = audiences.build_segment(spec)
    else:
        contacts = list(audience)
    summary.audience_size = len(contacts)
    if not contacts:
        summary.notes.append("Empty audience.")
        return summary

    # 2. Cross-channel suppression — ONE gate for ALL channels
    scoring.apply_scores(contacts)
    filt = suppression.SuppressionFilter(require_verified=False)
    clean, suppressed = filt.filter_batch(contacts)
    summary.suppressed = len(suppressed)
    summary.suppression_reasons = filt.summary(suppressed)

    # 3. Verify (gates the email + ads channels which are email-based)
    if do_verify:
        verification.verify_contacts(clean)
        deliverable, _dead = verification.split_deliverable(clean)
        summary.verified_deliverable = len(deliverable)
    else:
        deliverable = clean

    # 4. Build the campaign context passed to every channel
    campaign_ctx = {
        "name": campaign_name, "brand": brand, "sequence": sequence_name,
        "heyreach_campaign_id": heyreach_campaign_id,
        "test_offer": test_offer, "extra_vars": extra_vars,
    }

    # 5. Bulk-enroll channels that support it (ads audience, LinkedIn campaign)
    enrolled_any = 0
    for ch_name in seq.channels_used():
        ch = CHANNEL_REGISTRY.get(ch_name)
        if ch and ch_name in ("ads", "linkedin"):
            audience_param = next((t.params.get("audience") for t in seq.touches
                                   if t.channel == "ads"), "default_retargeting")
            res = ch.enroll(deliverable, {**campaign_ctx, "audience": audience_param})
            enrolled_any = max(enrolled_any, res.get("enrolled", 0))
    summary.enrolled = enrolled_any

    # 6. Per-channel plan + dispatch touches (dry-run logs each)
    by_channel = Counter()
    reach_by_channel: dict[str, int] = {}
    for t in seq.touches:
        ch = CHANNEL_REGISTRY.get(t.channel)
        if not ch:
            continue
        reachable = [c for c in deliverable if ch.can_reach(c)]
        reach_by_channel[t.channel] = len(reachable)
        for c in reachable:
            ch.execute_touch(c, t, campaign_ctx)
            by_channel[t.channel] += 1
            summary.total_touches += 1

    for ch_name in sorted(seq.channels_used()):
        ch = CHANNEL_REGISTRY.get(ch_name)
        summary.channel_plans.append(asdict(ChannelPlan(
            channel=ch_name,
            available=ch.is_available() if ch else False,
            reachable=reach_by_channel.get(ch_name, 0),
            touches_planned=by_channel.get(ch_name, 0),
        )))

    # 7. Notes on channels not yet live
    for ch_name in sorted(seq.channels_used()):
        ch = CHANNEL_REGISTRY.get(ch_name)
        if ch and not ch.is_available():
            summary.notes.append(f"Channel '{ch_name}' not live yet (no API key) — touches were dry-run only.")

    return summary
