"""Qualification funnel — who we contact + under which brand (rebuilds the Clay logic).

Three jobs: FILTER (eligible?), ROUTE (which brand?), via a cheap->expensive funnel:
  Stage 0  free hard filters    — US business only, optional geo target   (no spend)
  Stage 1  company lookup       — LeadMagic firmographics: employees + age + size,
           (engine/enrichment)    plus a CS product (full-service vs toolkit) hint
  Stage 2  AI judgment          — current owner active? owner US-based? franchise-vs-
           (research + Claude)    private (brand)? no PE/public? + revenue band + franchise scale

Thresholds follow Eric's ICP (locked 2026-06-29): a $1M revenue floor on BOTH brands (5+
employees as the proxy when revenue is unknown); CS by industry, $1-10M revenue, age>=3yr,
avoid construction/education/retail/real-estate-heavy; FS = franchisees of SYSTEMS with
50-1000 locations, $1-5M revenue. All PASS-ON-UNKNOWN — a missing data point never drops a
lead; only an explicit over/under-threshold value does, and only when enforcement is on
(config.QUALIFICATION['enforce_caps']). Applied in _derive AFTER the AI sets the brand.

Result is a Qualification object saved to the contacts row (qualification jsonb +
qualified/qual_brand columns). Respects DRY_RUN: the batch funnel skips the paid AI step
unless force_ai=True, and enrichment is simulated unless live_enrich=True (a paid read
that still sends nothing). Canonical spec: QUALIFICATION-SPEC.md.
"""
from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass, field, asdict

from . import config, research, db, enrichment
from .models import Contact

# ── US detection ─────────────────────────────────────────────────────────────
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}
US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island",
    "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming",
    "district of columbia",
}
US_COUNTRY_TOKENS = {
    "", "us", "u.s.", "u.s.a.", "usa", "united states", "united states of america",
    "america", "united states minor outlying islands",
}


def _is_us_state(state: str) -> bool:
    s = (state or "").strip()
    return s.upper() in US_STATES or s.lower() in US_STATE_NAMES


def stage0(contact: Contact, geo: dict | None = None) -> tuple[bool, str]:
    """Free filters. Drops only CONFIRMED non-US businesses (and outside-geo when a
    geo target is given); uncertain cases pass through to the AI stage."""
    country = (contact.country or "").strip().lower()
    if country and country not in US_COUNTRY_TOKENS and not _is_us_state(contact.state):
        return False, f"non_us_country:{country[:20]}"
    if geo and geo.get("states"):
        st = (contact.state or "").strip().lower()
        names = [s.strip().lower() for s in geo["states"] if s.strip()]
        if names and not any(n == st or n in st or st in n for n in names if st):
            return False, "outside_geo_target"
    return True, ""


# ── result ───────────────────────────────────────────────────────────────────
@dataclass
class Qualification:
    qualified: bool = False
    brand: str = ""          # FS | CS | ""
    product: str = ""        # toolkit | full_service | ""
    stage0_pass: bool = False
    checks: dict = field(default_factory=dict)   # rule -> {verdict/pass, reason}
    failed_rule: str = ""
    confidence: float = 0.0
    method: str = ""         # stage0_drop | stage0_only | ai | ai_error:* | dry_run
    review_flags: list = field(default_factory=list)  # soft flags -> manual review, NOT auto-drop

    def to_dict(self) -> dict:
        return asdict(self)


# ── Stage 1: company lookup → structured signals ─────────────────────────────
@dataclass
class Stage1:
    employees: int | None = None
    age_years: int | None = None
    franchise_first_pass: str = "unknown"   # franchise | unknown (cheap keyword hint)
    product_hint: str = ""                   # full_service | toolkit (CS routing hint)
    checks: dict = field(default_factory=dict)


def _company_age_years(founded: str) -> int | None:
    m = re.search(r"(19|20)\d{2}", founded or "")
    if not m:
        return None
    age = datetime.date.today().year - int(m.group(0))
    return age if 0 <= age < 200 else None


def _franchise_first_pass(c: Contact) -> str:
    """Cheap keyword hint only. The AI (Stage 2) is authoritative on franchise-vs-
    private (it catches the franchise-with-DBA case keywords miss)."""
    blob = f"{c.title} {c.industry} {c.sub_industry} {c.company}".lower()
    return "franchise" if "franchis" in blob else "unknown"


def stage1(contact: Contact) -> Stage1:
    """Cheap structured signals from the company lookup. Computes numeric employees +
    business age + a CS product hint. Records signals; does NOT hard-drop here — the
    CS-only caps need the brand (set by the AI next), so they're enforced in _derive
    (pass-on-unknown). FS has no employee/age cap."""
    emp = contact.company_employees
    if not isinstance(emp, int):
        emp = enrichment._to_int(emp)
    age = _company_age_years(contact.company_founded)
    fp = _franchise_first_pass(contact)
    thr = config.QUALIFICATION["cs_toolkit_employee_threshold"]
    if emp is None:
        hint = "full_service"            # unknown size -> default to the focus product
    else:
        hint = "toolkit" if emp < thr else "full_service"
    checks = {"employees": emp, "age_years": age, "franchise_first_pass": fp,
              "size_band": contact.company_size or "", "enriched": bool(contact.enriched_by)}
    return Stage1(employees=emp, age_years=age, franchise_first_pass=fp,
                  product_hint=hint, checks=checks)


# ── AI judge (Stage 2) ───────────────────────────────────────────────────────
AI_SYSTEM = """You qualify cold-outreach prospects for two US business-brokerage brands:
- Franchise Sellers (FS): helps FRANCHISE owners sell their franchise business.
- Company Sellers (CS): helps owners of PRIVATE (independent, non-franchise) businesses sell.

You get a prospect (person + company), known firmographics, and brief web research. Judge
ONLY what the evidence supports; when evidence is thin, answer "unknown" rather than guessing.

Judge each:
1. current_owner: Is this person CURRENTLY the owner/operator of this company — NOT retired,
   NOT someone who already sold/exited, NOT a former owner? "yes" only with evidence of a
   current role; "no" if clearly retired/sold/former; else "unknown".
2. owner_us_based: Is the owner located in the United States? "yes"/"no"/"unknown".
3. business_type: Is the company a FRANCHISE (a franchisee of a brand — even if it trades under
   a DBA that looks independent) or a PRIVATE independent business? "franchise"/"private"/"unknown".
4. ownership: Privately held by an individual/small group, or PRIVATE-EQUITY owned, or a PUBLIC
   company? "private"/"pe_backed"/"public"/"unknown".
5. revenue_band: Estimate the company's ANNUAL revenue band from the evidence (employee count is
   a fair proxy). One of: "<$1M" / "$1-5M" / "$5-10M" / "$10-25M" / "$25M+" / "unknown".
   Estimate conservatively; answer "unknown" unless there is a real basis.
6. franchise_system_size: ONLY if business_type is "franchise" — roughly how many TOTAL locations
   does the FRANCHISE BRAND/SYSTEM operate nationwide (the whole brand, NOT just this owner)?
   "<50" / "50-1000" / ">1000" / "unknown". For a non-franchise, answer "unknown".

Return STRICT JSON only, no prose:
{"current_owner":{"verdict":"yes|no|unknown","reason":"<=14 words"},
 "owner_us_based":{"verdict":"yes|no|unknown","reason":"<=14 words"},
 "business_type":{"verdict":"franchise|private|unknown","reason":"<=14 words"},
 "ownership":{"verdict":"private|pe_backed|public|unknown","reason":"<=14 words"},
 "revenue_band":{"verdict":"<$1M|$1-5M|$5-10M|$10-25M|$25M+|unknown","reason":"<=14 words"},
 "franchise_system_size":{"verdict":"<50|50-1000|>1000|unknown","reason":"<=14 words"},
 "confidence":0.0-1.0}"""

# Revenue-band sets mapped to Eric's ICP cutoffs (the AI's coarse bands -> thresholds).
_REV_BELOW_FLOOR = {"<$1M"}                       # under the $1M floor (both brands)
_FS_REV_OVER = {"$5-10M", "$10-25M", "$25M+"}     # over the FS $5M cap
_CS_REV_OVER = {"$10-25M", "$25M+"}               # over the CS $10M cap


def ai_judge(contact: Contact, context: str) -> dict:
    """Call Claude to judge the rules. Returns the parsed verdict dict."""
    import anthropic  # lazy
    client = anthropic.Anthropic(api_key=config.require_key(config.ANTHROPIC["key_env"]))
    user = (
        f"Prospect:\n"
        f"name: {contact.display_name}\n"
        f"title: {contact.title}\n"
        f"company: {contact.company}\n"
        f"industry: {contact.industry}\n"
        f"employees: {contact.company_employees or contact.company_size or 'unknown'}\n"
        f"founded: {contact.company_founded or 'unknown'}\n"
        f"ownership_hint: {contact.company_ownership_status or 'unknown'}\n"
        f"location: {contact.city}, {contact.state}, {contact.country}\n"
        f"linkedin: {contact.linkedin_norm or contact.linkedin_original}\n"
        f"website: {contact.website}\n"
        f"company_description: {contact.company_description or '(none)'}\n\n"
        f"Web research:\n{context or '(no web results found)'}\n"
    )
    resp = client.messages.create(
        model=config.ANTHROPIC["classify_model"], max_tokens=800,
        system=AI_SYSTEM, messages=[{"role": "user", "content": user}])
    text = resp.content[0].text.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def _derive(contact: Contact, v: dict, s1: Stage1, enforce_caps: bool | None = None) -> Qualification:
    """Map AI verdicts + Stage-1 signals -> qualified / brand / product. Only explicit
    disqualifiers fail; 'unknown' passes with lower confidence. CS caps apply here
    (brand is known) and are pass-on-unknown; the FS location cap is a soft review flag."""
    if enforce_caps is None:
        enforce_caps = config.QUALIFICATION["enforce_caps"]
    cap = config.QUALIFICATION

    q = Qualification(stage0_pass=True, method="ai")
    q.confidence = float(v.get("confidence", 0) or 0)
    co = (v.get("current_owner") or {}).get("verdict", "unknown")
    ous = (v.get("owner_us_based") or {}).get("verdict", "unknown")
    bt = (v.get("business_type") or {}).get("verdict", "unknown")
    own = (v.get("ownership") or {}).get("verdict", "unknown")
    rev = (v.get("revenue_band") or {}).get("verdict", "unknown")
    fss = (v.get("franchise_system_size") or {}).get("verdict", "unknown")
    q.checks = {k: v.get(k, {}) for k in
                ("current_owner", "owner_us_based", "business_type", "ownership",
                 "revenue_band", "franchise_system_size")}
    q.checks["stage0"] = {"pass": True}
    q.checks["stage1"] = s1.checks

    # universal disqualifiers (both brands)
    if co == "no":
        q.failed_rule = "not_current_owner"; return q
    if ous == "no":
        q.failed_rule = "owner_not_us"; return q
    if own in ("pe_backed", "public"):
        q.failed_rule = own; return q
    if bt == "unknown":
        q.failed_rule = "brand_unknown"; return q

    q.brand = "FS" if bt == "franchise" else "CS"

    # universal FLOOR (Eric ICP): under $1M revenue drops; when revenue is unknown, fall
    # back to a 5+ employee floor. Pass-on-unknown when neither signal is available.
    if rev in _REV_BELOW_FLOOR:
        q.checks["min_revenue"] = {"pass": False, "band": rev}
        if enforce_caps:
            q.failed_rule = "below_min_revenue"; return q
        q.review_flags.append("below_min_revenue")
    elif rev in ("", "unknown") and s1.employees is not None and s1.employees < cap["min_employees"]:
        q.checks["min_employees"] = {"pass": False, "value": s1.employees}
        if enforce_caps:
            q.failed_rule = "below_min_employees"; return q
        q.review_flags.append("below_min_employees")

    if q.brand == "CS":
        q.product = s1.product_hint or "full_service"
        # avoid-industries (Eric): construction / education / retail / real-estate-heavy
        blob = f"{contact.industry} {contact.sub_industry} {contact.company}".lower()
        hit = next((kw for kw in cap["cs_avoid_industries"] if kw in blob), "")
        if hit:
            q.checks["cs_industry"] = {"pass": False, "avoid_match": hit}
            if enforce_caps:
                q.failed_rule = "cs_avoid_industry"; return q
            q.review_flags.append(f"cs_avoid_industry:{hit}")
        # business age >= 3yr (pass-on-unknown)
        if s1.age_years is not None and s1.age_years < cap["cs_min_age_years"]:
            q.checks["cs_age"] = {"pass": False, "value": s1.age_years}
            if enforce_caps:
                q.failed_rule = "cs_too_young"; return q
            q.review_flags.append("cs_under_min_age")
        # revenue <= $10M (AI band; drop only on an unambiguous over-cap band)
        if rev in _CS_REV_OVER:
            q.checks["cs_revenue"] = {"pass": False, "band": rev}
            if enforce_caps:
                q.failed_rule = "cs_revenue_over_cap"; return q
            q.review_flags.append("cs_revenue_over_cap")
    else:  # FS
        q.product = "toolkit"
        # franchise SYSTEM must have >=50 total locations (Eric: floor at 50, no top cap)
        if fss == "<50":
            q.checks["fs_system_size"] = {"pass": False, "size": fss}
            if enforce_caps:
                q.failed_rule = "fs_system_too_small"; return q
            q.review_flags.append("fs_system_under_50")
        # FS business revenue <= $5M (over $5M goes to a different M&A firm)
        if rev in _FS_REV_OVER:
            q.checks["fs_revenue"] = {"pass": False, "band": rev}
            if enforce_caps:
                q.failed_rule = "fs_revenue_over_cap"; return q
            q.review_flags.append("fs_revenue_over_cap")

    if not contact.revenue_band and rev not in ("", "unknown"):
        contact.revenue_band = rev
    q.qualified = True
    return q


def qualify_contact(contact: Contact, geo: dict | None = None, use_ai: bool = True,
                    enrich: bool = True, live_enrich: bool = False,
                    enforce_caps: bool | None = None) -> Qualification:
    ok0, reason0 = stage0(contact, geo)
    if not ok0:
        q = Qualification(stage0_pass=False, failed_rule=reason0, method="stage0_drop")
        q.checks = {"stage0": {"pass": False, "reason": reason0}}
        return q
    # Stage 1 — company lookup + structured signals (simulated unless live_enrich)
    if enrich:
        enrichment.enrich_contact(contact, live=live_enrich, persist=live_enrich)
    s1 = stage1(contact)
    if not use_ai:
        return Qualification(stage0_pass=True, failed_rule="pending_ai", method="stage0_only",
                             checks={"stage0": {"pass": True}, "stage1": s1.checks})
    context = research.context_for_contact(contact)
    try:
        verdicts = ai_judge(contact, context)
    except Exception as e:
        return Qualification(stage0_pass=True, failed_rule="ai_error",
                             method=f"ai_error:{type(e).__name__}",
                             checks={"stage0": {"pass": True}, "stage1": s1.checks})
    return _derive(contact, verdicts, s1, enforce_caps=enforce_caps)


def qualify_batch(contacts: list[Contact], geo: dict | None = None,
                  ai_cap: int | None = None, force_ai: bool = False,
                  save: bool = False, enrich: bool = True, live_enrich: bool = False,
                  enforce_caps: bool | None = None) -> list[Qualification]:
    """Funnel a batch: Stage 0 on all (free), Stage 1 lookup, AI only on survivors
    (up to ai_cap). In DRY_RUN the AI step is skipped unless force_ai=True and
    enrichment is simulated unless live_enrich=True. Optionally persist to the DB."""
    use_ai = (not config.DRY_RUN) or force_ai
    if save and db.available():
        db.ensure_qualification_columns()
        db.ensure_enrichment_columns()
    out: list[Qualification] = []
    ai_done = 0
    for c in contacts:
        run_ai = use_ai and (ai_cap is None or ai_done < ai_cap)
        q = qualify_contact(c, geo, use_ai=run_ai, enrich=enrich,
                            live_enrich=live_enrich, enforce_caps=enforce_caps)
        if q.method == "ai":
            ai_done += 1
        if save and db.available() and q.method == "ai":
            db.save_qualification(c.canonical_id, q.to_dict(), q.qualified, q.brand)
        out.append(q)
    return out
