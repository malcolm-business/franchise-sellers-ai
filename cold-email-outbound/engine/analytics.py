"""Pool analytics — efficient aggregates for the marketing dashboard.

Reads the tier CSVs and aggregates columns (brand, industry, state, franchise
system, verification, channel reachability) without scoring the whole pool, so
it's fast enough to run in the hourly snapshot cron.

No network calls.
"""
from __future__ import annotations

import csv
from collections import Counter

from . import config

csv.field_size_limit(10_000_000)

# Compact franchise-system keyword list (mirrors scripts/dedup/profile_tier_a.py)
FRANCHISE_SYSTEMS = [
    "home instead", "caring transitions", "comforcare", "comfort keepers", "firstlight",
    "visiting angels", "senior helpers", "right at home", "brightstar", "homewatch",
    "code ninja", "kumon", "mathnasium", "goldfish swim", "primrose", "sylvan",
    "maaco", "1-800 radiator", "meineke", "midas", "valvoline", "take 5",
    "ace hardware", "ben & jerry", "nekter", "tropical smoothie", "jersey mike",
    "anytime fitness", "orangetheory", "pure barre", "club pilates", "f45",
    "servpro", "puroclean", "chem-dry", "chemdry", "stanley steemer",
    "two men and a truck", "college hunks", "the ups store", "fastsigns",
    "house doctors", "mr. handyman", "ace handyman", "molly maid", "merry maids",
    "elements massage", "massage envy", "hand and stone", "sport clips",
    "express employment", "bricks 4 kidz", "rhea lana", "cruise planners",
]

PERSONAL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "aol.com", "outlook.com", "icloud.com",
    "comcast.net", "msn.com", "live.com", "me.com", "sbcglobal.net", "verizon.net",
}


def _read(path, limit=None):
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8", newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if limit and i >= limit:
                break
            yield row


def _detect_systems(rows_company):
    c = Counter()
    for comp in rows_company:
        cl = (comp or "").lower()
        if not cl:
            continue
        for s in FRANCHISE_SYSTEMS:
            if s in cl:
                label = s.replace("chemdry", "chem-dry")
                c[label] += 1
                break
    return c


def pool_analytics() -> dict:
    """Aggregate the Tier A pool for the dashboard. Fast column counting."""
    fs = list(_read(config.TIER_A_FS))
    cs = list(_read(config.TIER_A_CS))
    amb = list(_read(config.TIER_A_AMBIGUOUS))

    def domain(e):
        return (e or "").split("@")[-1].lower() if "@" in (e or "") else ""

    def coverage(rows):
        n = len(rows) or 1
        return {
            "with_email": sum(1 for r in rows if r.get("email_norm")),
            "with_linkedin": sum(1 for r in rows if r.get("linkedin_norm")),
            "with_phone": sum(1 for r in rows if r.get("phone_primary")),
            "personal_domain": sum(1 for r in rows if domain(r.get("email_original")) in PERSONAL_DOMAINS),
            "pct_linkedin": round(sum(1 for r in rows if r.get("linkedin_norm")) / n * 100),
        }

    # FS franchise systems (FS + ambiguous pools)
    fs_systems = _detect_systems(r.get("company", "") for r in fs)
    amb_systems = _detect_systems(r.get("company", "") for r in amb)
    combined_systems = fs_systems + amb_systems

    # CS industries
    cs_industries = Counter((r.get("industry") or "No Industry").strip() for r in cs)

    # States (both)
    states = Counter()
    for r in fs + cs:
        st = (r.get("state") or "").strip()
        if st:
            states[st] += 1

    return {
        "brand_split": {"FS": len(fs), "CS": len(cs), "Ambiguous": len(amb)},
        "top_fs_systems": combined_systems.most_common(12),
        "top_cs_industries": cs_industries.most_common(12),
        "top_states": states.most_common(10),
        "coverage": {"FS": coverage(fs), "CS": coverage(cs)},
        "geo_known_pct": round(len(states) and sum(states.values()) / max(len(fs) + len(cs), 1) * 100),
    }


def tier_funnel() -> dict:
    """Counts for the prospect funnel visual."""
    def count(path):
        if not path.exists():
            return 0
        with open(path, "r", encoding="utf-8", newline="") as f:
            return max(sum(1 for _ in f) - 1, 0)
    return {
        "canonical_total": count(config.CANONICAL_MASTER),
        "tier_a": count(config.TIER_A_FS) + count(config.TIER_A_CS) + count(config.TIER_A_AMBIGUOUS),
        "tier_b": count(config.TIER_B),
        "tier_c": count(config.TIER_C),
        "tier_d": count(config.TIER_D_SUPPRESSION),
    }
