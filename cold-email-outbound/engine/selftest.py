"""Cold Email Engine — selftest.

Runs every module in dry-run against the real Tier A data and prints a readiness
report. This is the "is the system wired correctly?" check to run any time, and
the first thing to run before go-live (it must be all-green in dry-run first).

    python3 -m engine.selftest
    (from cold-email-outbound/)  or  python3 engine/selftest.py

Spends nothing, sends nothing — asserts DRY_RUN is on and refuses to run live.
"""
from __future__ import annotations

import sys

from . import config, data_layer, pipeline
from .models import CampaignStream


def _check(label: str, ok: bool, detail: str = "") -> bool:
    mark = "✅" if ok else "❌"
    print(f"  {mark} {label}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    print("=" * 70)
    print(config.status_banner())
    print("=" * 70)

    if not config.DRY_RUN:
        print("\n❌ selftest refuses to run with CEO_DRY_RUN=false. Set dry-run and retry.")
        return 2

    all_ok = True

    # ── 1. Data source present (Neon DB or flat files) ───────────────────
    print("\n[1] Data source")
    from . import db
    if db.available():
        try:
            total = db.count_tier(None, None)
            fs, cs = db.count_tier("FS", "A"), db.count_tier("CS", "A")
            all_ok &= _check("neon contacts", total > 0, f"{total:,} rows (FS-A {fs:,} / CS-A {cs:,})")
        except Exception as e:
            all_ok &= _check("neon contacts", False, f"DB error: {type(e).__name__}: {e}")
    else:
        for label, path in [
            ("canonical-master", config.CANONICAL_MASTER),
            ("tier-a-fs", config.TIER_A_FS),
            ("tier-a-cs", config.TIER_A_CS),
            ("tier-c", config.TIER_C),
            ("tier-d-suppression", config.TIER_D_SUPPRESSION),
        ]:
            all_ok &= _check(f"{label}", path.exists(), str(path.name) if path.exists() else f"MISSING: {path}")

    # ── 2. Suppression + CRM sets load ───────────────────────────────────
    print("\n[2] Suppression sets")
    supp = data_layer.load_suppression_emails()
    all_ok &= _check("suppression emails loaded", len(supp) > 0, f"{len(supp):,} emails")
    crm = data_layer.load_crm_emails()
    _check("crm-snapshot emails", True, f"{len(crm):,} (0 expected off-droplet)")

    # ── 3. Templates parse ───────────────────────────────────────────────
    print("\n[3] Templates")
    from . import copy_gen
    for stream, fname in pipeline.STREAM_TEMPLATE.items():
        try:
            tpl = copy_gen.parse_template(config.TEMPLATES_DIR / fname)
            ok = bool(tpl["meta"].get("subjects")) and len(tpl["steps"]) >= 1
            all_ok &= _check(f"{stream.value}", ok,
                             f"{len(tpl['meta'].get('subjects', []))} subjects, {len(tpl['steps'])} steps")
        except Exception as e:
            all_ok &= _check(f"{stream.value}", False, f"parse error: {e}")

    # ── 4. End-to-end dry-run probes across the active Phase 1 streams ────
    # buyer_reactivation excluded — no cold source (buyers live in GHL CRM).
    print("\n[4] End-to-end dry-run probes (limit 300 each)")
    results = {}
    for s in [CampaignStream.SELLER_COLD_FS_NICHE, CampaignStream.SELLER_COLD_FS_BROAD,
              CampaignStream.SELLER_COLD_CS, CampaignStream.REFERRAL_PARTNER_ADVISOR]:
        try:
            r = pipeline.run_campaign(s, limit=300, do_verify=True, do_push=True)
            results[s.value] = r
            ok = r.rendered > 0
            all_ok &= _check(
                s.value, ok,
                f"loaded={r.loaded} icp_ok={r.icp_eligible} clean={r.icp_eligible - r.suppressed} "
                f"deliverable={r.verified_deliverable} rendered={r.rendered} "
                f"var={r.content_variation_pct}% words~{r.avg_word_count} pushed={r.pushed}"
            )
        except Exception as e:
            all_ok &= _check(s.value, False, f"run error: {e}")

    # ── 5. Reply classification + routing chain ──────────────────────────
    print("\n[5] Reply classify + route chain")
    from . import classify, routing, data_layer as dl
    sample = dl.load_tier_a("FS", limit=1)[0]
    cases = [
        ("Re: Quick question", "Yes I'd be interested, please send info", "ghl_fs"),
        ("Unsubscribe", "remove me from your list", "suppression"),
        ("Re: thoughts", "I'm interested in resales, looking to buy", "buyer_manager"),
        ("OOO", "out of office returning monday", "cooldown"),
    ]
    for subj, body, expected in cases:
        res = classify.classify_reply(subj, body)
        act = routing.route_reply(sample, res["category"], res.get("re_engage_date", ""))
        ok = act["destination"] == expected
        all_ok &= _check(f"{res['category']} -> {act['destination']}", ok,
                         "" if ok else f"expected {expected}")

    # ── 6. Dry-run audit trail ───────────────────────────────────────────
    print("\n[6] Dry-run audit trail")
    log = data_layer.read_dry_run_log()
    all_ok &= _check("dry-run log written", len(log) > 0, f"{len(log):,} would-be external calls logged")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ SELFTEST PASSED — engine is wired correctly in dry-run.")
        print("   Next: wire API keys in .env, re-run, then flip CEO_DRY_RUN=false on a probe.")
    else:
        print("❌ SELFTEST had failures — see above.")
    print("=" * 70)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
