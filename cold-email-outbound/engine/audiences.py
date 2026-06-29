"""Audience / segment builder.

Lets Malcolm define a target audience from the deduped pool with simple filters
(brand, tier, industry, franchise system, geography, ICP, channel-reachability),
preview the count, and save it by name so any multi-channel campaign can pull it.

Segments are saved as JSON specs (the filter definition, not the contacts) under
runtime/segments/ — so they're re-runnable as the pool grows. No network calls.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict

from . import config, data_layer, scoring
from .models import Contact


@dataclass
class SegmentSpec:
    name: str
    brand: str = ""                       # "FS" / "CS" / "" (any)
    tier: str = "A"                       # A / B / C / D
    industry_contains: list[str] = field(default_factory=list)   # any-match (OR)
    company_contains: list[str] = field(default_factory=list)    # any-match (OR) — franchise systems
    states: list[str] = field(default_factory=list)              # any-match (OR)
    min_icp: int = 0
    require_email: bool = True
    require_linkedin: bool = False
    exclude_excluded_company: bool = True  # drop real-estate / excluded companies
    limit: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _tier_source(brand: str, tier: str):
    if tier == "A":
        return {"FS": config.TIER_A_FS, "CS": config.TIER_A_CS}.get(brand)  # None => both
    return {"B": config.TIER_B, "C": config.TIER_C, "D": config.TIER_D_SUPPRESSION}.get(tier)


def _matches(c: Contact, spec: SegmentSpec) -> bool:
    if spec.require_email and not c.email_norm:
        return False
    if spec.require_linkedin and not (c.linkedin_norm or c.linkedin_original):
        return False
    if spec.industry_contains:
        blob = f"{c.industry} {c.sub_industry}".lower()
        if not any(x.lower() in blob for x in spec.industry_contains):
            return False
    if spec.company_contains:
        comp = (c.company or "").lower()
        if not any(x.lower() in comp for x in spec.company_contains):
            return False
    if spec.states:
        st = (c.state or "").lower()
        if not any(x.lower() in st for x in spec.states):
            return False
    return True


def build_segment(spec: SegmentSpec) -> list[Contact]:
    """Apply a SegmentSpec against the pool. Returns matching, scored contacts."""
    # Load candidate pool
    if spec.tier == "A":
        if spec.brand in ("FS", "CS"):
            contacts = data_layer.load_tier_a(spec.brand)
        else:
            contacts = data_layer.load_tier_a()   # all brands
    else:
        src = _tier_source(spec.brand, spec.tier)
        contacts = data_layer.load_contacts(src) if src else []

    scoring.apply_scores(contacts)

    out = []
    for c in contacts:
        if spec.exclude_excluded_company and c.icp_breakdown.get("excluded_company"):
            continue
        if (c.icp_score or 0) < spec.min_icp:
            continue
        # brand filter (when pool is mixed)
        if spec.brand and c.brand_tag != spec.brand and spec.brand in ("FS", "CS"):
            # allow ambiguous to pass into either brand
            if c.brand_tag not in ("AMBIGUOUS", "UNKNOWN"):
                continue
        if _matches(c, spec):
            out.append(c)
        if spec.limit and len(out) >= spec.limit:
            break
    return out


def build_segment_capped(spec: SegmentSpec, cap: int = 600, scan: int = 8000) -> list[Contact]:
    """Fast representative subset for a dashboard simulation: reservoir-sample `scan`
    rows, score + filter, return up to `cap` matches. Avoids loading/scoring the full
    pool (used by the dry-run endpoint so it responds in seconds)."""
    if spec.tier == "A" and spec.brand in ("FS", "CS"):
        path = {"FS": config.TIER_A_FS, "CS": config.TIER_A_CS}[spec.brand]
        rows, _ = _reservoir_sample(path, scan)
    elif spec.tier == "A":
        rows = []
        for path in (config.TIER_A_FS, config.TIER_A_CS, config.TIER_A_AMBIGUOUS):
            r, _ = _reservoir_sample(path, scan // 3)
            rows += r
    else:
        src = _tier_source(spec.brand, spec.tier)
        rows, _ = _reservoir_sample(src, scan)
    scoring.apply_scores(rows)
    out = []
    for c in rows:
        if spec.exclude_excluded_company and c.icp_breakdown.get("excluded_company"):
            continue
        if (c.icp_score or 0) < spec.min_icp:
            continue
        if _matches(c, spec):
            out.append(c)
        if len(out) >= cap:
            break
    return out


def preview(spec: SegmentSpec) -> dict:
    """Return summary stats for a segment without materializing it for a campaign."""
    contacts = build_segment(spec)
    from collections import Counter
    industries = Counter((c.industry or "n/a") for c in contacts)
    states = Counter((c.state or "n/a") for c in contacts)
    with_li = sum(1 for c in contacts if c.linkedin_norm or c.linkedin_original)
    return {
        "name": spec.name,
        "count": len(contacts),
        "with_email": sum(1 for c in contacts if c.email_norm),
        "with_linkedin": with_li,
        "top_industries": industries.most_common(8),
        "top_states": states.most_common(8),
        "avg_icp": round(sum((c.icp_score or 0) for c in contacts) / max(len(contacts), 1), 1),
    }


def _reservoir_sample(path, k: int):
    """Random representative sample of k Contacts from a CSV in one pass (no full
    load). Avoids the first-N ordering bias (the pool CSVs are grouped by source)."""
    import csv as _csv
    import random as _random
    from .models import Contact
    if not path or not path.exists():
        return [], 0
    sample, total = [], 0
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in _csv.DictReader(f):
            total += 1
            if len(sample) < k:
                sample.append(Contact.from_row(row))
            else:
                j = _random.randint(0, total - 1)
                if j < k:
                    sample[j] = Contact.from_row(row)
    return sample, total


def preview_sampled(spec: SegmentSpec, sample: int = 4000) -> dict:
    """Fast interactive preview: random-sample the pool, score it, extrapolate the
    match rate to the full pool. Representative (reservoir sample) + fast."""
    from collections import Counter
    if spec.tier == "A" and spec.brand in ("FS", "CS"):
        path = {"FS": config.TIER_A_FS, "CS": config.TIER_A_CS}[spec.brand]
        rows, full = _reservoir_sample(path, sample)
    elif spec.tier == "A":
        rows, full = [], 0
        for path in (config.TIER_A_FS, config.TIER_A_CS, config.TIER_A_AMBIGUOUS):
            r, t = _reservoir_sample(path, sample // 3)
            rows += r; full += t
    else:
        src = _tier_source(spec.brand, spec.tier)
        rows, full = _reservoir_sample(src, sample)

    scoring.apply_scores(rows)
    matched = []
    for c in rows:
        if spec.exclude_excluded_company and c.icp_breakdown.get("excluded_company"):
            continue
        if (c.icp_score or 0) < spec.min_icp:
            continue
        if _matches(c, spec):
            matched.append(c)
    n = len(rows) or 1
    rate = len(matched) / n
    industries = Counter((c.industry or "n/a") for c in matched)
    return {
        "sample_size": n,
        "sample_matched": len(matched),
        "match_rate_pct": round(rate * 100, 1),
        "estimated_count": int(round(rate * full)),
        "full_pool": full,
        "with_linkedin_pct": round(sum(1 for c in matched if c.linkedin_norm or c.linkedin_original) / max(len(matched), 1) * 100),
        "avg_icp": round(sum((c.icp_score or 0) for c in matched) / max(len(matched), 1), 1),
        "top_industries": industries.most_common(6),
    }


def _count_rows(path) -> int:
    if not path or not path.exists():
        return 0
    with open(path, "r", encoding="utf-8", newline="") as f:
        return max(sum(1 for _ in f) - 1, 0)


def save_segment(spec: SegmentSpec) -> str:
    path = data_layer._runtime_path("segments", f"{spec.name}.json")
    path.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")
    return str(path)


def load_segment(name: str) -> SegmentSpec | None:
    path = data_layer._runtime_path("segments", f"{name}.json")
    if not path.exists():
        return None
    return SegmentSpec(**json.loads(path.read_text(encoding="utf-8")))


def list_segments() -> list[str]:
    seg_dir = config.RUNTIME_DIR / "segments"
    if not seg_dir.exists():
        return []
    return sorted(p.stem for p in seg_dir.glob("*.json"))
