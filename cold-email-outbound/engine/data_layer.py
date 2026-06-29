"""Cold Email Engine — flat-file data layer (Phase 1).

Per the 2026-06-07 decision (05-decisions-log.md), Phase 1 runs on flat files,
NOT Airtable or RevyOps. The dedup output (canonical-master.csv + tier files)
is the source of truth for the contact pool. Runtime state (per-campaign send
logs, verified pools, suppression updates) is written under data/runtime/.

This module is the ONLY place that reads/writes those files, so the storage
backend can later be swapped (e.g. to RevyOps) by reimplementing this module
without touching the rest of the engine.

No network calls.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterator

from . import config, db
from .models import Contact, SendEvent, CANONICAL_COLUMNS

csv.field_size_limit(10_000_000)


# ────────────────────────────────────────────────────────────────────────────
# Reading the contact pool
# ────────────────────────────────────────────────────────────────────────────

def _read_csv(path: Path) -> Iterator[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Expected data file not found: {path}\n"
            f"Run the dedup first: python3 cold-email-outbound/scripts/dedup/run_dedup.py"
        )
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def _tier_for_path(path: Path):
    """Map a known tier CSV path → (brand, tier) for DB routing. None if not a tier file."""
    return {
        config.TIER_A_FS: ("FS", "A"),
        config.TIER_A_CS: ("CS", "A"),
        config.TIER_A_AMBIGUOUS: ("AMBIGUOUS", "A"),
        config.TIER_B: (None, "B"),
        config.TIER_C: (None, "C"),
        config.TIER_D_SUPPRESSION: (None, "D"),
    }.get(path)


def load_contacts(path: Path, limit: int | None = None) -> list[Contact]:
    """Load contacts. When a database is configured AND `path` is a known tier file,
    reads from Postgres; otherwise reads the CSV (runtime pools, ad-hoc files)."""
    if db.available():
        t = _tier_for_path(path)
        if t is not None:
            return db.load_tier(t[0], t[1], limit=limit)
    out = []
    for i, row in enumerate(_read_csv(path)):
        if limit is not None and i >= limit:
            break
        out.append(Contact.from_row(row))
    return out


def load_tier_a(brand: str | None = None, limit: int | None = None) -> list[Contact]:
    """Load Tier A pool, optionally filtered to a single brand."""
    paths = {
        "FS": config.TIER_A_FS,
        "CS": config.TIER_A_CS,
        "AMBIGUOUS": config.TIER_A_AMBIGUOUS,
    }
    if brand:
        return load_contacts(paths[brand], limit=limit)
    out = []
    for p in paths.values():
        out.extend(load_contacts(p))
        if limit is not None and len(out) >= limit:
            return out[:limit]
    return out


def iter_contacts(path: Path) -> Iterator[Contact]:
    """Memory-friendly streaming over a large pool (e.g. canonical-master)."""
    for row in _read_csv(path):
        yield Contact.from_row(row)


# ────────────────────────────────────────────────────────────────────────────
# Suppression set (fast in-CRM + flag lookups)
# ────────────────────────────────────────────────────────────────────────────

def load_suppression_emails() -> set[str]:
    """All normalized emails in Tier D (do-not-contact). Used by the pre-send filter."""
    if db.available():
        return db.suppression_emails()
    emails = set()
    if config.TIER_D_SUPPRESSION.exists():
        for row in _read_csv(config.TIER_D_SUPPRESSION):
            e = (row.get("email_norm") or "").strip().lower()
            if e:
                emails.add(e)
    return emails


def load_crm_emails() -> set[str]:
    """All emails already in either GHL workspace, from the unified crm-snapshot.

    Read-only. Never pulls GHL directly (master CLAUDE.md rate-limit rule).
    Returns empty set if the snapshot isn't present (dry-run tolerant).
    """
    emails: set[str] = set()
    snap = config.CRM_SNAPSHOT
    if not snap.exists():
        return emails
    try:
        data = json.loads(snap.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return emails

    # crm-master.json shape varies; defensively walk for any "email" fields.
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in ("email", "email_address", "emailaddress") and isinstance(v, str) and "@" in v:
                    emails.add(v.strip().lower())
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return emails


# ────────────────────────────────────────────────────────────────────────────
# Runtime state — per-campaign send logs + verified pools
# ────────────────────────────────────────────────────────────────────────────

def _runtime_path(*parts: str) -> Path:
    config.ensure_runtime_dir()
    p = config.RUNTIME_DIR.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_pool(contacts: list[Contact], name: str) -> Path:
    """Persist a working pool (e.g. a verified probe batch) to runtime/pools/."""
    path = _runtime_path("pools", f"{name}.csv")
    if not contacts:
        path.write_text("", encoding="utf-8")
        return path
    fieldnames = list(contacts[0].to_row().keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for c in contacts:
            w.writerow(c.to_row())
    return path


def read_pool(name: str) -> list[Contact]:
    path = _runtime_path("pools", f"{name}.csv")
    if not path.exists() or path.stat().st_size == 0:
        return []
    return load_contacts(path)


def append_send_event(event: SendEvent) -> None:
    """Record an engagement event — to Postgres when configured, else per-stream JSONL."""
    if db.available():
        db.append_event(event)
        return
    path = _runtime_path("events", f"{event.campaign_stream or 'unknown'}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event.to_row()) + "\n")


def read_send_events(campaign_stream: str) -> list[SendEvent]:
    if db.available():
        return db.read_events(campaign_stream)
    path = _runtime_path("events", f"{campaign_stream}.jsonl")
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(SendEvent(**json.loads(line)))
    return out


def log_dry_run(category: str, message: str, payload: dict | None = None) -> None:
    """Record what a live call WOULD have done. Central dry-run audit trail."""
    path = _runtime_path("dry-run", "dry-run.jsonl")
    rec = {"category": category, "message": message, "payload": payload or {}}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def read_dry_run_log() -> list[dict]:
    path = _runtime_path("dry-run", "dry-run.jsonl")
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
