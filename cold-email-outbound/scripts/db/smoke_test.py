"""Smoke test for the Postgres-backed data layer.

Verifies the engine reads the pool from Neon with parity vs the known tier counts,
plus the suppression set, a random sample, and a send-event round-trip (cleaned up
after). Run from the project root with the venv that has psycopg.

    .venv/bin/python scripts/db/smoke_test.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # project root

from engine import data_layer, db
from engine.models import SendEvent


def main() -> int:
    assert db.available(), "DATABASE_URL not configured in .env"
    print("db.available:", True)

    fs = data_layer.load_tier_a("FS", limit=5)
    print("load_tier_a('FS', limit=5):", len(fs), "| first email:", fs[0].email_norm if fs else None)

    ok = True
    for brand, exp in [("FS", 10206), ("CS", 160699)]:
        n = db.count_tier(brand, "A")
        good = n == exp
        ok &= good
        print(f"count {brand} A: {n:,} ({'OK' if good else 'MISMATCH exp ' + format(exp, ',')})")

    print("sample CS A (50):", len(db.sample_tier("CS", "A", 50)))

    supp = data_layer.load_suppression_emails()
    print("suppression emails:", f"{len(supp):,}")

    ev = SendEvent(canonical_id="__SMOKE__", campaign_stream="__smoke__",
                   event_type="sent", timestamp=datetime.now(timezone.utc).isoformat(), step=1)
    data_layer.append_send_event(ev)
    back = data_layer.read_send_events("__smoke__")
    rt = len(back) >= 1 and back[-1].event_type == "sent"
    print("event round-trip:", len(back), "| type:", back[-1].event_type if back else None, "->", "OK" if rt else "FAIL")
    ok &= rt
    with db.connect() as c:
        c.execute("DELETE FROM send_events WHERE campaign_stream = '__smoke__'")
    print("cleaned smoke events")

    print("\n" + ("✅ DB data-layer smoke test passed" if ok else "❌ smoke test had failures"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
