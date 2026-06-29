#!/usr/bin/env python3
"""LeadMagic company-lookup coverage test (Stage 1).

Modes:
  --probe N    look up N real leads and DUMP the raw LeadMagic response (to confirm the
               endpoint URL + field names) before spending on a big run. Tries a few
               candidate endpoint paths and reports which one works.
  --test N     look up N real leads and tally per-field coverage; persists to the DB.
  --brand CS|FS   which tier-A pool to sample (default CS).

Runs LIVE LeadMagic calls (paid reads) even when CEO_DRY_RUN=true — enrichment spends
credits but SENDS NOTHING. Honors the test-then-evaluate rule: the coverage output tells
us whether LeadMagic gives us enough of the fields we need, or we escalate to a better tool.

    python3 scripts/enrich/test_enrichment.py --probe 3 --brand CS
    python3 scripts/enrich/test_enrichment.py --test 1000 --brand CS
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine import config, db, enrichment   # noqa: E402

CANDIDATE_URLS = [
    "https://api.leadmagic.io/company-search",
    "https://api.leadmagic.io/companies/company-search",
    "https://api.leadmagic.io/v1/companies/company-search",
    "https://api.leadmagic.io/company",
]


def _raw_call(url: str, body: dict, key: str) -> tuple[int, dict | str]:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"X-API-Key": key, "Content-Type": "application/json",
                 "User-Agent": config.USER_AGENT}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", "replace")[:600]
        return e.code, body_txt
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def _pull_pool(brand: str, n: int):
    leads = db.load_tier(brand, "A", limit=n * 3)
    pool = []
    for c in leads:
        if enrichment.domain_from_website(c.website) or (c.company or "").strip():
            pool.append(c)
        if len(pool) >= n:
            break
    return pool, len(leads)


def do_probe(n: int, brand: str, throttle_ms: int) -> int:
    key = config.require_key(config.VERIFICATION["leadmagic_key_env"])
    pool, scanned = _pull_pool(brand, max(n, 1))
    if not pool:
        print("no leads with a domain/name found"); return 2
    print(f"probing endpoint with {len(pool)} {brand}-A leads (scanned {scanned})\n")

    working_url = None
    for c in pool:
        domain = enrichment.domain_from_website(c.website)
        name = (c.company or "").strip()
        urls = [working_url] if working_url else CANDIDATE_URLS
        for url in urls:
            for body in ([{"company_domain": domain}] if domain else []) + ([{"company_name": name}] if name else []):
                status, data = _raw_call(url, body, key)
                tag = f"{url}  body={list(body.keys())}"
                if status == 200 and isinstance(data, dict):
                    working_url = url
                    print(f"OK  {tag}")
                    print(f"  company={c.company!r} domain={domain!r}")
                    print(f"  RAW KEYS: {sorted(data.keys())}")
                    print(f"  RAW (trunc):\n{json.dumps(data, indent=2)[:2200]}")
                    print(f"  NORMALIZED: {json.dumps(enrichment.normalize_company(data))}\n")
                    break
                else:
                    print(f"--  {status}  {tag}  -> {str(data)[:160]}")
            if working_url:
                break
        time.sleep(throttle_ms / 1000.0)
        if working_url and n <= 1:
            break
    if working_url:
        print(f"\n>>> WORKING ENDPOINT: {working_url}")
        if working_url != enrichment.LEADMAGIC_COMPANY_URL:
            print(f">>> NOTE: differs from engine default {enrichment.LEADMAGIC_COMPANY_URL} — update it.")
    else:
        print("\n>>> NO endpoint returned 200 — see errors above.")
    return 0


def do_test(n: int, brand: str, throttle_ms: int, persist: bool, workers: int) -> int:
    db.ensure_enrichment_columns()
    pool, scanned = _pull_pool(brand, n)
    print(f"pulled {len(pool)} {brand}-A leads with a domain/name (scanned {scanned})")
    print(f"running {'CONCURRENT x' + str(workers) if workers > 1 else 'serial'} ...")
    t0 = time.time()
    if workers > 1:
        stats = enrichment.enrich_batch_concurrent(pool, workers=workers, persist=persist)
    else:
        stats = enrichment.enrich_batch(pool, live=True, persist=persist, throttle_ms=throttle_ms)
    dt = time.time() - t0
    a = stats["attempted"] or 1

    def pct(x):
        return f"{100 * x / a:.1f}%"

    print("\n==================== COVERAGE ====================")
    print(f"attempted:           {stats['attempted']}")
    print(f"had a domain:        {stats['had_domain']:>5}  ({pct(stats['had_domain'])})")
    print(f"matched a company:   {stats['matched']:>5}  ({pct(stats['matched'])})")
    print(f"  -> has employees:  {stats['has_employees']:>5}  ({pct(stats['has_employees'])})")
    print(f"  -> has founded:    {stats['has_founded']:>5}  ({pct(stats['has_founded'])})")
    print(f"  -> has revenue:    {stats['has_revenue']:>5}  ({pct(stats['has_revenue'])})")
    print(f"  -> has office locs:{stats['has_office_locs']:>5}  ({pct(stats['has_office_locs'])})")
    print(f"no domain/name:      {stats['no_domain_or_name']}")
    print(f"errors:              {stats['errors']}  samples={stats['error_samples'][:5]}")
    print(f"sample raw keys:     {stats['sample_raw_keys']}")
    print("sample records:")
    for r in stats["sample_records"]:
        print("   ", r)
    print(f"\nelapsed {dt:.0f}s  (~{1000 * dt / a:.0f} ms/lead incl. throttle)")
    if persist and db.available():
        print("DB enrichment_stats (whole table):", json.dumps(db.enrichment_stats()))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", type=int, default=0)
    ap.add_argument("--test", type=int, default=0)
    ap.add_argument("--brand", default="CS", choices=["CS", "FS"])
    ap.add_argument("--throttle-ms", type=int, default=120)
    ap.add_argument("--workers", type=int, default=1, help="concurrent lookups for --test")
    ap.add_argument("--no-persist", action="store_true")
    args = ap.parse_args()

    print(config.status_banner())
    if not enrichment.available():
        print("LEADMAGIC_API_KEY not set — cannot run live test."); return 2
    if args.probe:
        return do_probe(args.probe, args.brand, args.throttle_ms)
    if args.test:
        return do_test(args.test, args.brand, args.throttle_ms,
                       persist=not args.no_persist, workers=args.workers)
    print("pass --probe N or --test N")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
