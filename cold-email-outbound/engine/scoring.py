"""Cold Email Engine — ICP scoring.

Scores each contact 0-100 on fit. Weights (from config.ICP_WEIGHTS):
  40% demographic + tenure
  40% behavioral + situational
  20% firmographic

Phase 1 reality: the reactivation pool lacks rich signals (no owner-age,
no tenure, no live M&A flags). So the v1 scorer works with what's actually
present — data completeness, source cross-verification, decision-maker title,
industry fit, contactability — and leaves headroom for Phase 2/3 signals
(job-change, M&A, bio language) to plug into the same weighted framework.

No network calls. Pure function of a Contact.
"""
from __future__ import annotations

import re

from . import config
from .models import Contact

# Titles that indicate an owner / decision-maker (worth more).
OWNER_TITLE_PATTERNS = [
    r"\bowner\b", r"\bfounder\b", r"\bco-?founder\b", r"\bpresident\b",
    r"\bceo\b", r"\bchief executive\b", r"\bprincipal\b", r"\bproprietor\b",
    r"\bmanaging (member|partner|director)\b", r"\bmanaging owner\b",
    r"\bfranchisee\b", r"\boperator\b", r"\bgm\b", r"\bgeneral manager\b",
]

# Industries that are strong M&A verticals (per 03-brands-and-icp.md).
STRONG_VERTICALS = {
    "hvac", "home services", "home health", "senior care", "elderly care",
    "manufacturing", "distribution", "professional services", "automotive",
    "wellness", "fitness", "food and beverage", "consumer services",
    "restaurants", "franchise",
}

# Excluded verticals (06-services-and-process.md — team passes on these).
EXCLUDED_VERTICALS = {
    "professional services - legal", "e-commerce", "ecommerce", "technology",
    "software", "saas", "information technology",
    # Real estate excluded per Theodore 2026-06-07 (different exit dynamics).
    "real estate", "real estate investment", "real estate brokerage",
}

# Real-estate franchise systems + brokerages to exclude by COMPANY name
# (Theodore 2026-06-07: exclude RE franchises from FS campaigns).
EXCLUDED_COMPANY_PATTERNS = [
    "homevestors", "exit realty", "re/max", "remax", "keller williams", "century 21",
    "coldwell banker", "berkshire hathaway home", "sotheby's international realty",
    "weichert", "realty one", "realty group", "real estate", "realtor", "realty",
    "we buy ugly houses", "we buy houses", "home buyers", "homebuyers",
]


def _is_excluded_company(company: str) -> bool:
    cl = (company or "").lower()
    if not cl:
        return False
    return any(p in cl for p in EXCLUDED_COMPANY_PATTERNS)


def _title_is_owner(title: str) -> bool:
    t = (title or "").lower()
    return any(re.search(p, t) for p in OWNER_TITLE_PATTERNS)


def _industry_fit(industry: str, sub_industry: str = "") -> float:
    """Return -1.0 (excluded) .. 1.0 (strong vertical), 0.0 neutral."""
    blob = f"{industry} {sub_industry}".lower()
    if not blob.strip():
        return 0.0
    for ex in EXCLUDED_VERTICALS:
        if ex in blob:
            return -1.0
    for sv in STRONG_VERTICALS:
        if sv in blob:
            return 1.0
    return 0.2  # has an industry, just not a flagged-strong one


def score_demographic_tenure(c: Contact) -> float:
    """0..1. Phase 1 proxy: decision-maker title + name completeness.

    Phase 2+ slots owner-age + tenure signals here (the real demographic drivers).
    """
    score = 0.0
    if _title_is_owner(c.title):
        score += 0.6
    elif c.title.strip():
        score += 0.2          # has a title, not clearly owner
    if c.first_name and c.last_name:
        score += 0.25         # real human name (not "Newark Signal88 Com")
    elif c.full_name and " " in c.full_name:
        score += 0.15
    if c.linkedin_norm:
        score += 0.15         # LinkedIn presence = verifiable individual
    return min(score, 1.0)


def score_behavioral_situational(c: Contact) -> float:
    """0..1. Phase 1 proxy: cross-source verification + contactability.

    Phase 2+ slots job-change / M&A / bio-language signals here (the real
    behavioral drivers). For now: a record cross-verified across many sources
    is more trustworthy and more likely to still be active.
    """
    score = 0.0
    n_sources = len(c.source_list)
    if n_sources >= 5:
        score += 0.5
    elif n_sources >= 3:
        score += 0.35
    elif n_sources >= 2:
        score += 0.2
    else:
        score += 0.05
    # Clay-enriched records carried the 6-provider waterfall = higher confidence
    if any("clay_" in s for s in c.source_list):
        score += 0.3
    # Phone present = another live contact channel
    if c.phone_primary:
        score += 0.2
    return min(score, 1.0)


def score_firmographic(c: Contact) -> float:
    """0..1 with a hard floor of 0 (excluded verticals zero this component)."""
    fit = _industry_fit(c.industry, c.sub_industry)
    if fit < 0:
        return 0.0            # excluded vertical
    score = 0.4 + (fit * 0.4)  # baseline 0.4, +0.4 for strong vertical, +0.08 if has-any
    if c.company:
        score += 0.2
    return min(score, 1.0)


def score_contact(c: Contact) -> tuple[int, dict]:
    """Return (0-100 score, breakdown dict). Excluded verticals cap the score low."""
    demo = score_demographic_tenure(c)
    behav = score_behavioral_situational(c)
    firmo = score_firmographic(c)

    # Excluded vertical or excluded company (real estate) → hard cap below threshold
    excluded_vertical = _industry_fit(c.industry, c.sub_industry) < 0
    excluded_company = _is_excluded_company(c.company)
    excluded = excluded_vertical or excluded_company

    w = config.ICP_WEIGHTS
    raw = (
        demo * w["demographic_tenure"]
        + behav * w["behavioral_situational"]
        + firmo * w["firmographic"]
    )
    score = int(round(raw * 100))
    if excluded:
        score = min(score, 10)  # well below the 60 threshold → never sequenced

    breakdown = {
        "demographic_tenure": round(demo, 3),
        "behavioral_situational": round(behav, 3),
        "firmographic": round(firmo, 3),
        "excluded_vertical": excluded_vertical,
        "excluded_company": excluded_company,
        "weighted_raw": round(raw, 3),
    }
    return score, breakdown


def apply_scores(contacts: list[Contact]) -> list[Contact]:
    """Score a list in place; set icp_score + icp_breakdown on each."""
    for c in contacts:
        s, b = score_contact(c)
        c.icp_score = s
        c.icp_breakdown = b
    return contacts


def filter_by_threshold(contacts: list[Contact], threshold: int | None = None) -> tuple[list[Contact], list[Contact]]:
    """Split into (eligible >= threshold, below). Scores must be applied first."""
    th = config.ICP_THRESHOLD if threshold is None else threshold
    eligible, below = [], []
    for c in contacts:
        s = c.icp_score if c.icp_score is not None else score_contact(c)[0]
        (eligible if s >= th else below).append(c)
    return eligible, below
