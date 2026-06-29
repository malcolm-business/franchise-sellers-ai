#!/usr/bin/env python3
"""End-to-end qualification funnel smoke test (final-product validation).

Runs the FULL funnel on N Tier-A leads: Stage 0 (free) -> Stage 1 (LeadMagic enrich,
LIVE) -> Stage 2 (Perplexity + Claude AI judge, LIVE) -> derive. Prints each lead's
qualification so we can eyeball brand / product / caps / review flags.

Spends LeadMagic (~1 credit) + Perplexity (~$0.005) + Claude (~$0.006) per lead. Sends
NOTHING. Keep N small.

    python3 scripts/enrich/funnel_smoke.py --n 6 --brand CS
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine import config, db, qualification   # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--brand", default="CS", choices=["CS", "FS"])
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--no-enforce", action="store_true", help="don't hard-drop on CS caps")
    args = ap.parse_args()

    print(config.status_banner())
    leads = db.load_tier(args.brand, "A", limit=args.n * 2)
    pool = [c for c in leads if (c.company or c.website)][:args.n]
    print(f"running FULL funnel on {len(pool)} {args.brand}-A leads (force_ai + live_enrich)\n")

    quals = qualification.qualify_batch(
        pool, force_ai=True, live_enrich=True, save=args.save,
        enforce_caps=(False if args.no_enforce else None))

    for c, q in zip(pool, quals):
        bt = (q.checks.get("business_type") or {}).get("verdict", "?")
        rev = (q.checks.get("revenue_band") or {}).get("verdict", "?")
        co = (q.checks.get("current_owner") or {}).get("verdict", "?")
        own = (q.checks.get("ownership") or {}).get("verdict", "?")
        print(f"--- {c.display_name}  |  {c.company}")
        print(f"    stage1: emp={c.company_employees} size={c.company_size or '-'} "
              f"founded={c.company_founded or '-'} ownhint={c.company_ownership_status or '-'}")
        print(f"    RESULT: qualified={q.qualified} brand={q.brand or '-'} product={q.product or '-'} "
              f"conf={q.confidence} method={q.method} failed={q.failed_rule or '-'}")
        print(f"    ai: owner={co} type={bt} ownership={own} revenue={rev}"
              + (f"  flags={q.review_flags}" if q.review_flags else ""))

    n_q = sum(1 for q in quals if q.qualified)
    n_cs = sum(1 for q in quals if q.brand == "CS")
    n_fs = sum(1 for q in quals if q.brand == "FS")
    print(f"\n{n_q}/{len(quals)} qualified  (CS={n_cs} FS={n_fs})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
