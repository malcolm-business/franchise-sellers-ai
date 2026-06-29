"""Small live test of the qualification funnel (Stage 0 + Stage 2 AI judge).

Picks a few real FS + CS contacts, runs Perplexity research + Claude judgment
(force_ai), saves results to the DB, and prints the verdicts. Costs a few cents.

    .venv/bin/python scripts/db/test_qualification.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine import data_layer, qualification, db  # noqa: E402


def main() -> int:
    fs = [c for c in data_layer.load_tier_a("FS", limit=60) if c.company and c.email_norm][:2]
    cs = [c for c in data_layer.load_tier_a("CS", limit=60) if c.company and c.email_norm][:2]
    sample = fs + cs
    print(f"Qualifying {len(sample)} contacts (force_ai)...\n")
    results = qualification.qualify_batch(sample, force_ai=True, save=True)
    for c, q in zip(sample, results):
        print(f"{c.display_name} | {c.company} | {c.industry or '-'} | {c.state or '-'} | tag={c.brand_tag}")
        print(f"  => qualified={q.qualified} brand={q.brand} product={q.product} "
              f"method={q.method} conf={q.confidence} failed={q.failed_rule or '-'}")
        for k in ("current_owner", "owner_us_based", "business_type", "ownership"):
            v = q.checks.get(k) or {}
            if v.get("verdict"):
                print(f"     {k}: {v['verdict']} — {v.get('reason', '')}")
        print()
    with db.connect() as cx:
        n = cx.execute("SELECT count(*) FROM contacts WHERE qualified_at IS NOT NULL").fetchone()[0]
        print(f"rows with qualification saved: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
