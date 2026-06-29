"""Stage 1 — company lookup (firmographic enrichment).

Looks up each contact's company (employee count, founding year, industry, revenue
band) so the qualification funnel can apply the cheap structured filters before
spending on the AI judge. Provider today is LeadMagic's company-search endpoint
(keyed off the company domain, falling back to company name).

Design (mirrors research.py):
  * zero pip deps — urllib + stdlib only
  * never raises — returns a result dict and degrades gracefully on any error
  * DRY-RUN aware — simulated firmographics unless `live=True` is passed OR
    CEO_DRY_RUN=false. `live=True` lets the 1,000-lead coverage TEST hit the real
    API (a paid read) while the master send switch stays locked — enrichment
    spends credits but sends nothing.

The result of an enrichment is written to the Contact (company_size / founded /
company_employees / revenue_band / industry) and, when a DB is configured and the
call was live, persisted via db.save_enrichment so a lead is enriched once.

Per the test-then-evaluate rule: if a real test shows LeadMagic under-covers the
fields we need, swap the provider here (config.QUALIFICATION['enrichment_provider'])
— the rest of the funnel reads the normalized Contact fields, not the raw API.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request

from . import config

LEADMAGIC_COMPANY_URL = "https://api.leadmagic.io/company-search"


def available() -> bool:
    return bool(config.get_key(config.VERIFICATION["leadmagic_key_env"]))


# ── domain / parsing helpers ─────────────────────────────────────────────────

def domain_from_website(website: str) -> str:
    """Reduce a website/URL to a bare registrable domain (best-effort)."""
    w = (website or "").strip().lower()
    if not w:
        return ""
    w = re.sub(r"^[a-z]+://", "", w)          # strip scheme
    w = w.split("/")[0].split("?")[0]          # strip path/query
    if w.startswith("www."):
        w = w[4:]
    w = w.strip().strip(".")
    # must look like a domain (has a dot, no spaces/@)
    if "@" in w or " " in w or "." not in w:
        return ""
    return w


def _first(raw: dict, *keys):
    for k in keys:
        if k in raw and raw[k] not in (None, "", [], {}):
            return raw[k]
    return None


def _to_int(value) -> int | None:
    """Coerce an exact count to int. Returns None if not a clean number."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    m = re.search(r"\d[\d,]*", str(value))
    return int(m.group(0).replace(",", "")) if m else None


def _employees_from(raw: dict) -> tuple[int | None, str]:
    """Return (exact_or_estimated_headcount, band_string). Tolerant of LeadMagic's
    several shapes: employee_count (int), employee_count_range ({start,end}|str),
    company_size / size (band string)."""
    exact = _to_int(_first(raw, "employee_count", "employees", "headcount",
                           "num_employees", "employeeCount", "employee_count_exact"))
    band = ""
    rng = _first(raw, "employee_count_range", "company_size", "size",
                 "employeeCountRange", "employee_range")
    lo = hi = None
    if isinstance(rng, dict):
        lo, hi = _to_int(rng.get("start") or rng.get("min")), _to_int(rng.get("end") or rng.get("max"))
        band = f"{lo or ''}-{hi or ''}".strip("-")
    elif rng:
        band = str(rng)
        nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", band)]
        if nums:
            lo = nums[0]
            hi = nums[1] if len(nums) > 1 else None
    if exact is None and lo is not None:
        # midpoint of the band (or the floor when it's open-ended like "201+")
        exact = (lo + hi) // 2 if hi is not None else lo
    return exact, band[:60]


def _founded_year_from(raw: dict) -> str:
    val = _first(raw, "founded", "founded_year", "year_founded", "company_founded",
                 "foundedYear", "founded_on", "foundedOn")
    if val is None:
        return ""
    if isinstance(val, dict):
        y = val.get("year")
        return str(y) if y else ""
    m = re.search(r"(19|20)\d{2}", str(val))
    return m.group(0) if m else ""


def _revenue_band_from(raw: dict) -> str:
    # Prefer a human-formatted band ("$1.2M") over a raw number.
    val = _first(raw, "revenue_formatted", "formattedRevenue", "revenue_range",
                 "revenueRange", "annual_revenue", "estimated_revenue",
                 "revenue_printed", "annualRevenue", "revenue")
    if val is None:
        return ""
    if isinstance(val, dict):
        val = val.get("range") or val.get("printed") or val.get("formatted") or ""
    return str(val)[:60]


def _office_count_from(raw: dict) -> int | None:
    """Count of LeadMagic 'locations' = LinkedIn OFFICE addresses, NOT franchise
    units. Captured for reporting only — never used as the FS location gate."""
    locs = _first(raw, "locations", "office_locations")
    if isinstance(locs, list):
        return len(locs)
    return None


def normalize_company(raw: dict) -> dict:
    """Map a raw LeadMagic company record to our Contact firmographic fields."""
    employees, band = _employees_from(raw)
    desc = _first(raw, "description", "tagline") or ""
    return {
        "company": _first(raw, "companyName", "company_name", "name", "company") or "",
        "industry": _first(raw, "industry", "company_industry") or "",
        "company_size": band,
        "company_employees": employees,
        "company_founded": _founded_year_from(raw),
        "revenue_band": _revenue_band_from(raw),
        # Extra signals LeadMagic returns for small firms even when employees/revenue
        # are null — fed to the AI judge to ground its size/revenue/ownership calls.
        "ownership_status": _first(raw, "ownership_status") or "",
        "stock_ticker": _first(raw, "stock_ticker") or "",
        "description": str(desc)[:700],
        "_office_count": _office_count_from(raw),   # diagnostic only (offices != units)
    }


# ── live API call ────────────────────────────────────────────────────────────

def _company_search_live(domain: str = "", name: str = "") -> dict:
    key = config.require_key(config.VERIFICATION["leadmagic_key_env"])
    body: dict = {}
    if domain:
        body["company_domain"] = domain
    elif name:
        body["company_name"] = name
    else:
        return {}
    req = urllib.request.Request(
        LEADMAGIC_COMPANY_URL, data=json.dumps(body).encode("utf-8"),
        headers={"X-API-Key": key, "Content-Type": "application/json",
                 "User-Agent": config.USER_AGENT}, method="POST")
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _simulated_company(contact) -> dict:
    """Deterministic dry-run firmographics so the funnel is testable for free."""
    import hashlib
    seed = int(hashlib.sha256((contact.company or contact.canonical_id).encode()).hexdigest(), 16)
    bands = ["1-10", "11-50", "51-200", "201-500"]
    mids = {"1-10": 5, "11-50": 30, "51-200": 125, "201-500": 350}
    band = bands[seed % len(bands)]
    year = 1985 + (seed % 38)   # 1985..2022
    return {"company_name": contact.company, "company_industry": contact.industry,
            "company_size": band, "employee_count": mids[band], "founded": str(year)}


# ── public API ───────────────────────────────────────────────────────────────

def enrich_contact(contact, live: bool = False, persist: bool = False) -> dict:
    """Look up the contact's company and fill its firmographic fields (only empty
    ones — never overwrites). Returns a result dict for tallying coverage:
        {matched, source, fields, office_count, raw_keys, error}
    `live=True` forces a real (paid) API call even under CEO_DRY_RUN."""
    do_live = live or (not config.DRY_RUN)
    domain = domain_from_website(contact.website)
    name = (contact.company or "").strip()

    if not do_live:
        raw = _simulated_company(contact)
        source = "simulated"
    else:
        if not domain and not name:
            return {"matched": False, "source": "leadmagic", "fields": {},
                    "office_count": None, "raw_keys": [], "error": "no_domain_or_name"}
        try:
            raw = _company_search_live(domain=domain, name=name)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
            return {"matched": False, "source": "leadmagic", "fields": {},
                    "office_count": None, "raw_keys": [], "error": f"{type(e).__name__}:{e}"}
        source = "leadmagic"

    norm = normalize_company(raw or {})
    matched = bool(norm.get("company_employees") or norm.get("company_founded") or norm.get("company"))

    # Fill empty Contact fields only (never overwrite real pool data).
    def fill(attr, value):
        if value not in (None, "") and not getattr(contact, attr, ""):
            setattr(contact, attr, value)

    fill("company", norm["company"])
    fill("industry", norm["industry"])
    fill("company_size", norm["company_size"])
    fill("company_founded", norm["company_founded"])
    fill("revenue_band", norm["revenue_band"])
    fill("company_description", norm.get("description", ""))
    fill("company_ownership_status", norm.get("ownership_status", ""))
    if norm["company_employees"] is not None and contact.company_employees in (None, ""):
        contact.company_employees = norm["company_employees"]
    if matched and source == "leadmagic":
        contact.enriched_by = "leadmagic"

    if persist and matched and source == "leadmagic":
        try:
            from . import db
            if db.available():
                db.save_enrichment(contact.canonical_id, {
                    "company_size": contact.company_size or None,
                    "company_founded": contact.company_founded or None,
                    "company_employees": contact.company_employees,
                    "revenue_band": contact.revenue_band or None,
                    "enriched_by": "leadmagic",
                })
        except Exception:
            pass   # persistence is best-effort; never break the funnel

    return {"matched": matched, "source": source, "fields": norm,
            "office_count": norm.get("_office_count"),
            "raw_keys": sorted((raw or {}).keys()), "error": ""}


def _blank_stats() -> dict:
    return {
        "attempted": 0, "matched": 0, "errors": 0,
        "has_employees": 0, "has_founded": 0, "has_revenue": 0, "has_office_locs": 0,
        "no_domain_or_name": 0, "had_domain": 0,
        "error_samples": [], "sample_raw_keys": [], "sample_records": [],
    }


def _record(stats: dict, c, r: dict) -> None:
    """Fold one enrichment result into the running coverage stats (call serially)."""
    stats["attempted"] += 1
    if domain_from_website(c.website):
        stats["had_domain"] += 1
    if r.get("error") == "no_domain_or_name":
        stats["no_domain_or_name"] += 1
    if r.get("error"):
        stats["errors"] += 1
        if len(stats["error_samples"]) < 8:
            stats["error_samples"].append(r["error"])
        return
    if r.get("matched"):
        stats["matched"] += 1
        f = r.get("fields", {})
        if f.get("company_employees") is not None:
            stats["has_employees"] += 1
        if f.get("company_founded"):
            stats["has_founded"] += 1
        if f.get("revenue_band"):
            stats["has_revenue"] += 1
        if r.get("office_count"):
            stats["has_office_locs"] += 1
        if not stats["sample_raw_keys"] and r.get("raw_keys"):
            stats["sample_raw_keys"] = r["raw_keys"]
        if len(stats["sample_records"]) < 5:
            stats["sample_records"].append({
                "company": c.company, "domain": domain_from_website(c.website),
                "employees": f.get("company_employees"), "size": f.get("company_size"),
                "founded": f.get("company_founded"), "revenue": f.get("revenue_band"),
            })


def enrich_batch(contacts, live: bool = False, cap: int | None = None,
                 persist: bool = True, throttle_ms: int = 120) -> dict:
    """Enrich a batch SERIALLY; return coverage stats. Throttles between live calls."""
    stats = _blank_stats()
    do_live = live or (not config.DRY_RUN)
    for c in contacts:
        if cap is not None and stats["attempted"] >= cap:
            break
        r = enrich_contact(c, live=live, persist=persist)
        _record(stats, c, r)
        if do_live and throttle_ms:
            time.sleep(throttle_ms / 1000.0)
    return stats


def enrich_batch_concurrent(contacts, workers: int = 8, persist: bool = True) -> dict:
    """Enrich a batch CONCURRENTLY (LeadMagic's name lookup is ~7s each; threads make a
    1,000-lead run finish in minutes). Only the API calls run in parallel; the stats
    tally stays serial, so it's thread-safe. Always live (the coverage test)."""
    from concurrent.futures import ThreadPoolExecutor

    def work(c):
        try:
            return c, enrich_contact(c, live=True, persist=persist)
        except Exception as e:   # never let one lead kill the batch
            return c, {"matched": False, "error": f"{type(e).__name__}:{e}",
                       "fields": {}, "office_count": None, "raw_keys": []}

    stats = _blank_stats()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for c, r in ex.map(work, contacts):   # ex.map preserves input order
            _record(stats, c, r)
    return stats
