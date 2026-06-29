#!/usr/bin/env python3
"""Run a real (paid) qualification batch and save results to the DB.

Funnel per lead: Stage 0 (free US/geo) -> Stage 1 (LeadMagic company lookup) ->
Stage 2 (Perplexity research + Claude judge) -> derive (brand/product/caps). Runs
CONCURRENTLY (the AI step is the slow part). SENDS NOTHING — CEO_DRY_RUN stays true;
this only qualifies + spends on enrichment/AI.

MUST run with the venv python (has the anthropic SDK):
    ./.venv/bin/python scripts/qualify/run_batch.py --cs 1000 --fs 1000 --workers 6
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine import config, db, qualification   # noqa: E402


def run_brand(brand: str, n: int, workers: int, save: bool) -> dict:
    leads = db.load_tier(brand, "A", limit=n)
    total = len(leads)
    print(f"[{brand}] loaded {total} leads; qualifying with {workers} workers...", flush=True)
    qualified, done = 0, 0
    fails: dict[str, int] = {}
    brands: dict[str, int] = {}
    t0 = time.time()

    def work(c):
        try:
            q = qualification.qualify_contact(c, use_ai=True, enrich=True, live_enrich=True)
            if save and q.method == "ai" and db.available():
                db.save_qualification(c.canonical_id, q.to_dict(), q.qualified, q.brand)
            return q
        except Exception as e:   # never let one lead kill the batch
            return f"error:{type(e).__name__}"

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for q in ex.map(work, leads):
            done += 1
            if isinstance(q, str):
                fails[q] = fails.get(q, 0) + 1
            elif q.qualified:
                qualified += 1
                brands[q.brand] = brands.get(q.brand, 0) + 1
            else:
                fr = q.failed_rule or "?"
                fails[fr] = fails.get(fr, 0) + 1
            if done % 50 == 0 or done == total:
                el = time.time() - t0
                print(f"[{brand}] {done}/{total}  qualified={qualified}  "
                      f"({el:.0f}s, ~{el/max(done,1):.1f}s/lead)", flush=True)

    top = dict(sorted(fails.items(), key=lambda x: -x[1])[:8])
    print(f"[{brand}] DONE: {qualified}/{total} qualified  brands={brands}", flush=True)
    print(f"[{brand}] top non-qualify reasons: {top}", flush=True)
    return {"brand": brand, "total": total, "qualified": qualified, "brands": brands, "fails": fails}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cs", type=int, default=0)
    ap.add_argument("--fs", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    print(config.status_banner(), flush=True)
    if db.available():
        db.ensure_qualification_columns()
        db.ensure_enrichment_columns()
    save = not args.no_save

    out = []
    if args.cs:
        out.append(run_brand("CS", args.cs, args.workers, save))
    if args.fs:
        out.append(run_brand("FS", args.fs, args.workers, save))

    print("\n==================== SUMMARY ====================", flush=True)
    tq = sum(o["qualified"] for o in out)
    tt = sum(o["total"] for o in out)
    for o in out:
        print(f"  {o['brand']}: {o['qualified']}/{o['total']} qualified  {o['brands']}", flush=True)
    print(f"  TOTAL: {tq}/{tt} qualified", flush=True)
    if db.available():
        print("  DB qualification_stats:", db.qualification_stats(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
