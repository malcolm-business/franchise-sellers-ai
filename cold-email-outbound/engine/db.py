"""Postgres (Neon) data access — the single place that talks to the database.

`psycopg` is imported lazily inside connect() so the rest of the engine stays
import-clean when DB mode is off (DATABASE_URL unset → CSV fallback in data_layer).

Both brands live in ONE `contacts` table (brand_tag column); `send_events` holds
campaign activity. Schema created by scripts/db/migrate_to_neon.py.
"""
from __future__ import annotations

import json
from contextlib import contextmanager

from . import config
from .models import Contact, SendEvent, CANONICAL_COLUMNS

_COLS = CANONICAL_COLUMNS
_COLLIST = ", ".join(f'"{c}"' for c in _COLS)

# Stage-1 enrichment columns (added to the live table by ensure_enrichment_columns;
# baked into a fresh schema by migrate_to_neon.py). Read alongside the canonical
# columns so a loaded Contact carries its firmographics. Names == Contact fields.
_ENRICH_COLS = [
    "company_size", "company_founded", "company_employees",
    "revenue_band", "location_count", "enriched_by",
]
_READ_COLS = _COLS + _ENRICH_COLS
_READ_COLLIST = ", ".join(f'"{c}"' for c in _READ_COLS)

_enrich_ready = False  # process-level guard so we ALTER at most once per process


def available() -> bool:
    """True when a DATABASE_URL is configured (engine should use Postgres)."""
    return bool(config.get_key("DATABASE_URL"))


@contextmanager
def connect():
    import psycopg  # lazy — only when DB mode is actually used
    conn = psycopg.connect(config.require_key("DATABASE_URL"), autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def _rows_to_contacts(rows) -> list[Contact]:
    return [Contact.from_row(dict(zip(_READ_COLS, r))) for r in rows]


def ensure_enrichment_columns(conn=None) -> None:
    """Idempotent — add the Stage-1 company-lookup columns. Safe to call every run."""
    stmts = [
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS company_size text",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS company_founded text",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS company_employees integer",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS revenue_band text",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS location_count integer",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS enriched_by text",
        "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS enriched_at timestamptz",
    ]
    if conn is not None:
        for s in stmts:
            conn.execute(s)
        return
    with connect() as c:
        for s in stmts:
            c.execute(s)


def _ensure_enrich(conn) -> None:
    """Guarded once-per-process: make sure enrichment columns exist before a read
    SELECTs them, so reads are self-healing even before the first enrich/migrate."""
    global _enrich_ready
    if _enrich_ready:
        return
    ensure_enrichment_columns(conn)
    _enrich_ready = True


def _brand_cond(brand: str | None) -> tuple[str, list]:
    if brand in ("FS", "CS"):
        return "brand_tag = %s", [brand]
    if brand in ("AMBIGUOUS", "AMB"):
        return "brand_tag IN ('AMBIGUOUS','UNKNOWN')", []
    return "", []


def _tier_where(brand: str | None, tier: str | None) -> tuple[str, list]:
    conds, params = [], []
    if tier:
        conds.append("tier = %s"); params.append(tier)
    bc, bp = _brand_cond(brand)
    if bc:
        conds.append(bc); params += bp
    where = (" WHERE " + " AND ".join(conds)) if conds else ""
    return where, params


# ── reads ────────────────────────────────────────────────────────────────────

def load_tier(brand: str | None = None, tier: str | None = "A", limit: int | None = None) -> list[Contact]:
    where, params = _tier_where(brand, tier)
    sql = f"SELECT {_READ_COLLIST} FROM contacts{where}"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with connect() as c:
        _ensure_enrich(c)
        return _rows_to_contacts(c.execute(sql, params).fetchall())


def count_tier(brand: str | None = None, tier: str | None = "A") -> int:
    where, params = _tier_where(brand, tier)
    with connect() as c:
        return c.execute(f"SELECT count(*) FROM contacts{where}", params).fetchone()[0]


def sample_tier(brand: str | None = None, tier: str | None = "A", n: int = 4000) -> list[Contact]:
    """Representative random sample (replaces the CSV reservoir sampler)."""
    where, params = _tier_where(brand, tier)
    sql = f"SELECT {_READ_COLLIST} FROM contacts{where} ORDER BY random() LIMIT {int(n)}"
    with connect() as c:
        _ensure_enrich(c)
        return _rows_to_contacts(c.execute(sql, params).fetchall())


def suppression_emails() -> set[str]:
    with connect() as c:
        rows = c.execute(
            "SELECT email_norm FROM contacts WHERE tier='D' AND email_norm <> ''").fetchall()
    return {(r[0] or "").strip().lower() for r in rows if r[0]}


# ── send-event log ───────────────────────────────────────────────────────────

def append_event(event: SendEvent) -> None:
    from .models import STREAM_BRAND, CampaignStream
    brand = None
    try:
        brand = STREAM_BRAND.get(CampaignStream(event.campaign_stream))
    except Exception:
        pass
    with connect() as c:
        c.execute(
            "INSERT INTO send_events (canonical_id, campaign_stream, event_type, brand, ts, detail) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [event.canonical_id, event.campaign_stream, event.event_type, brand,
             event.timestamp or None, json.dumps(event.to_row())])


def read_events(campaign_stream: str) -> list[SendEvent]:
    with connect() as c:
        rows = c.execute(
            "SELECT detail FROM send_events WHERE campaign_stream = %s ORDER BY ts",
            [campaign_stream]).fetchall()
    fields = set(SendEvent.__dataclass_fields__)
    out = []
    for (d,) in rows:
        data = d if isinstance(d, dict) else json.loads(d)
        out.append(SendEvent(**{k: v for k, v in data.items() if k in fields}))
    return out


# ── qualification results ────────────────────────────────────────────────────

def ensure_qualification_columns() -> None:
    """Idempotent — adds the fast-filter columns for qualified leads."""
    with connect() as c:
        c.execute("ALTER TABLE contacts ADD COLUMN IF NOT EXISTS qualified boolean")
        c.execute("ALTER TABLE contacts ADD COLUMN IF NOT EXISTS qual_brand text")
        c.execute("ALTER TABLE contacts ADD COLUMN IF NOT EXISTS qualified_at timestamptz")
        c.execute("CREATE INDEX IF NOT EXISTS idx_contacts_qualified "
                  "ON contacts(qualified) WHERE qualified")


def save_qualification(canonical_id: str, qual: dict, qualified: bool, brand: str) -> None:
    with connect() as c:
        c.execute(
            "UPDATE contacts SET qualification=%s, qualified=%s, qual_brand=%s, qualified_at=now() "
            "WHERE canonical_id=%s",
            [json.dumps(qual), qualified, brand or None, canonical_id])


def save_enrichment(canonical_id: str, fields: dict) -> None:
    """Persist Stage-1 firmographics. `fields` keys are a subset of _ENRICH_COLS."""
    cols = [k for k in _ENRICH_COLS if k in fields]
    if not cols:
        return
    sets = ", ".join(f"{c}=%s" for c in cols) + ", enriched_at=now()"
    params = [fields[c] for c in cols] + [canonical_id]
    with connect() as c:
        _ensure_enrich(c)
        c.execute(f"UPDATE contacts SET {sets} WHERE canonical_id=%s", params)


def enrichment_stats() -> dict:
    """Dashboard counts: how much of the pool has firmographics + coverage per field."""
    with connect() as c:
        _ensure_enrich(c)
        row = c.execute(
            "SELECT count(*) FILTER (WHERE enriched_at IS NOT NULL), "
            "       count(*) FILTER (WHERE company_employees IS NOT NULL), "
            "       count(*) FILTER (WHERE company_founded IS NOT NULL AND company_founded <> ''), "
            "       count(*) FILTER (WHERE revenue_band IS NOT NULL AND revenue_band <> ''), "
            "       count(*) FILTER (WHERE location_count IS NOT NULL) "
            "FROM contacts").fetchone()
    return {"enriched": row[0], "has_employees": row[1], "has_founded": row[2],
            "has_revenue_band": row[3], "has_location_count": row[4]}


def pull_qualified(brand: str | None = None, limit: int | None = None,
                   min_confidence: float = 0.0) -> list[Contact]:
    """Qualified contacts ready for a campaign — qualified=true, correct brand, not in
    suppression (tier D), with an optional confidence floor. The operator lead-pull."""
    conds, params = ["qualified IS TRUE", "tier <> 'D'"], []
    if brand in ("FS", "CS"):
        conds.append("qual_brand = %s"); params.append(brand)
    if min_confidence and min_confidence > 0:
        conds.append("(qualification->>'confidence')::float >= %s"); params.append(min_confidence)
    sql = f"SELECT {_READ_COLLIST} FROM contacts WHERE {' AND '.join(conds)}"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with connect() as c:
        _ensure_enrich(c)
        return _rows_to_contacts(c.execute(sql, params).fetchall())


def qualification_stats() -> dict:
    """Dashboard counts: total judged, qualified, qualified-by-brand, top failure reasons."""
    with connect() as c:
        total_judged = c.execute(
            "SELECT count(*) FROM contacts WHERE qualified_at IS NOT NULL").fetchone()[0]
        qualified = c.execute(
            "SELECT count(*) FROM contacts WHERE qualified IS TRUE").fetchone()[0]
        by_brand = dict(c.execute(
            "SELECT qual_brand, count(*) FROM contacts WHERE qualified IS TRUE "
            "GROUP BY qual_brand").fetchall())
        failed = dict(c.execute(
            "SELECT qualification->>'failed_rule' AS r, count(*) FROM contacts "
            "WHERE qualified_at IS NOT NULL AND qualified IS NOT TRUE "
            "GROUP BY r ORDER BY 2 DESC LIMIT 8").fetchall())
    return {"total_judged": total_judged, "qualified": qualified,
            "qualified_by_brand": {k: v for k, v in by_brand.items() if k},
            "top_failures": {k: v for k, v in failed.items() if k}}


def weekly_activity() -> dict:
    """Send-event counts for the last 7 days, grouped by event_type then brand."""
    with connect() as c:
        rows = c.execute(
            "SELECT event_type, brand, count(*) FROM send_events "
            "WHERE ts >= now() - interval '7 days' GROUP BY 1, 2").fetchall()
    out: dict = {}
    for et, brand, n in rows:
        out.setdefault(et or "?", {})[brand or "?"] = n
    return out
