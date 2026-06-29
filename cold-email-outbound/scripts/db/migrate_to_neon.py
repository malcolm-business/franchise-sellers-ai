#!/usr/bin/env python3
"""Migrate the flat-file contact pool into the Neon Postgres database.

Reads DATABASE_URL from cold-email-outbound/.env (gitignored — no secret here).
Creates the schema (contacts + send_events), bulk-loads the 6 tier CSVs via COPY,
runs a parity check against the files, then adds the primary key + indexes.

Both brands live in ONE table; the brand is the `brand_tag` column. Tier files are
just views (WHERE tier=.. AND brand_tag=..). This is the first-load migration:
it DROPs + recreates `contacts`. Safe to re-run (re-loads from the CSVs).

    .venv/bin/python scripts/db/migrate_to_neon.py
"""
from __future__ import annotations
import csv
from pathlib import Path

import psycopg

csv.field_size_limit(10_000_000)  # raw_notes can be large

ROOT = Path(__file__).resolve().parents[2]          # cold-email-outbound/
DEDUP = ROOT / "data" / "dedup-output"

# (file, expected tier, label) — the 6 tier files together are the whole pool.
TIER_FILES = [
    ("tier-a-fs.csv", "A"),
    ("tier-a-cs.csv", "A"),
    ("tier-a-ambiguous.csv", "A"),
    ("tier-b.csv", "B"),
    ("tier-c.csv", "C"),
    ("tier-d-suppression.csv", "D"),
]

# parity: file -> WHERE clause that should reproduce its row count
PARITY = [
    ("tier-a-fs.csv", "tier='A' AND brand_tag='FS'"),
    ("tier-a-cs.csv", "tier='A' AND brand_tag='CS'"),
    ("tier-a-ambiguous.csv", "tier='A' AND brand_tag IN ('AMBIGUOUS','UNKNOWN')"),
    ("tier-b.csv", "tier='B'"),
    ("tier-c.csv", "tier='C'"),
    ("tier-d-suppression.csv", "tier='D'"),
]


def db_url() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("DATABASE_URL not found in .env")


def file_rows(path: Path) -> int:
    # logical CSV records (csv.reader, like COPY, treats a quoted embedded
    # newline as one record) — NOT physical lines.
    with open(path, "r", encoding="utf-8", newline="") as f:
        return max(sum(1 for _ in csv.reader(f)) - 1, 0)


def header_cols(path: Path) -> list[str]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


def main() -> int:
    cols = header_cols(DEDUP / "tier-a-fs.csv")
    print(f"CSV columns ({len(cols)}): {cols}")
    coldefs = ",\n  ".join(f'"{c}" text' for c in cols)
    collist = ",".join(f'"{c}"' for c in cols)

    with psycopg.connect(db_url(), autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS contacts")
        cur.execute(f"""CREATE TABLE contacts (
  {coldefs},
  icp_score integer,
  qualification jsonb,
  company_size text,
  company_founded text,
  company_employees integer,
  revenue_band text,
  location_count integer,
  enriched_by text,
  enriched_at timestamptz,
  last_verified_at timestamptz,
  last_sent_at timestamptz,
  created_at timestamptz DEFAULT now()
)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS send_events (
  id bigserial PRIMARY KEY,
  canonical_id text,
  campaign_stream text,
  event_type text,
  brand text,
  ts timestamptz DEFAULT now(),
  detail jsonb
)""")

        total_file = 0
        for fname, _tier in TIER_FILES:
            path = DEDUP / fname
            if not path.exists():
                print(f"  MISSING: {fname}"); continue
            assert header_cols(path) == cols, f"{fname} header differs from sample"
            fr = file_rows(path); total_file += fr
            copy_sql = f"COPY contacts ({collist}) FROM STDIN WITH (FORMAT csv, HEADER true)"
            with cur.copy(copy_sql) as cp, open(path, "rb") as fobj:
                while True:
                    chunk = fobj.read(1 << 20)
                    if not chunk:
                        break
                    cp.write(chunk)
            now = cur.execute("SELECT count(*) FROM contacts").fetchone()[0]
            print(f"  loaded {fname}: file_rows={fr:,}  db_total={now:,}")

        print("\n=== PARITY CHECK ===")
        db_total = cur.execute("SELECT count(*) FROM contacts").fetchone()[0]
        ok = db_total == total_file
        print(f"TOTAL  file={total_file:,}  db={db_total:,}  {'OK' if ok else 'MISMATCH'}")
        all_ok = ok
        for fname, where in PARITY:
            fr = file_rows(DEDUP / fname)
            dn = cur.execute(f"SELECT count(*) FROM contacts WHERE {where}").fetchone()[0]
            good = fr == dn
            all_ok &= good
            print(f"  {fname:26s} file={fr:>8,}  db={dn:>8,}  {'OK' if good else 'MISMATCH'}")

        dup = cur.execute(
            "SELECT count(*) FROM (SELECT canonical_id FROM contacts "
            "GROUP BY canonical_id HAVING count(*)>1) t").fetchone()[0]
        print(f"\nduplicate canonical_ids: {dup}")
        if dup == 0:
            cur.execute("ALTER TABLE contacts ADD PRIMARY KEY (canonical_id)")
            print("added PRIMARY KEY (canonical_id)")
        else:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_cid ON contacts(canonical_id)")
            print("WARNING: duplicate canonical_ids — added non-unique index instead of PK")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email_norm)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_brand_tier ON contacts(brand_tag, tier)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_se_stream ON send_events(campaign_stream)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_se_canonical ON send_events(canonical_id)")
        print("indexes created")

        sz = cur.execute("SELECT pg_size_pretty(pg_total_relation_size('contacts'))").fetchone()[0]
        print(f"contacts table size: {sz}")
        print("\n" + ("✅ MIGRATION OK — parity verified" if all_ok else "❌ PARITY MISMATCH — investigate"))
        return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
