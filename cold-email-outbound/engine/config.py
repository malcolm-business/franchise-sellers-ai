"""Cold Email Engine — central configuration.

Everything tunable lives here or in config/*.yaml. Nothing in this module makes
network calls or spends credits. API keys are read from environment (.env) and
are only *used* by the API-layer modules when DRY_RUN is False.

DRY_RUN is the master safety switch:
    DRY_RUN = True  (default) → no external API call sends/verifies/spends.
                                 API modules return simulated results + log intent.
    DRY_RUN = False           → live. Only flip when keys are wired + you're ready.
"""
from __future__ import annotations

import os
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────
# .env loader (no python-dotenv dependency — parse KEY=VALUE ourselves)
# ────────────────────────────────────────────────────────────────────────────

def _load_dotenv() -> None:
    """Load cold-email-outbound/.env into os.environ if present.

    Does not overwrite vars already set in the real environment (env wins over file).
    Silently does nothing if the file is absent. Keys with empty values are skipped.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


_load_dotenv()


# ────────────────────────────────────────────────────────────────────────────
# Master safety switch
# ────────────────────────────────────────────────────────────────────────────

# Read from env (or .env) so it can be flipped without editing code. Defaults to dry-run.
DRY_RUN: bool = os.environ.get("CEO_DRY_RUN", "true").strip().lower() != "false"


# ────────────────────────────────────────────────────────────────────────────
# Paths
# ────────────────────────────────────────────────────────────────────────────

# engine/ -> cold-email-outbound/
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
DEDUP_DIR = DATA_DIR / "dedup-output"
TEMPLATES_DIR = PROJECT_DIR / "templates"
CONFIG_DIR = PROJECT_DIR / "config"
RUNTIME_DIR = DATA_DIR / "runtime"  # per-campaign logs, verified pools, state (created on demand)

# The dedup outputs are the Phase 1 source of truth (flat-file data layer)
CANONICAL_MASTER = DEDUP_DIR / "canonical-master.csv"
TIER_A_FS = DEDUP_DIR / "tier-a-fs.csv"
TIER_A_CS = DEDUP_DIR / "tier-a-cs.csv"
TIER_A_AMBIGUOUS = DEDUP_DIR / "tier-a-ambiguous.csv"
TIER_B = DEDUP_DIR / "tier-b.csv"
TIER_C = DEDUP_DIR / "tier-c.csv"
TIER_D_SUPPRESSION = DEDUP_DIR / "tier-d-suppression.csv"

# Unified CRM snapshot (read-only, for in_crm suppression checks). Never pull GHL directly.
CRM_SNAPSHOT = PROJECT_DIR.parent / "crm-snapshot" / "crm-master.json"


# ────────────────────────────────────────────────────────────────────────────
# Brands
# ────────────────────────────────────────────────────────────────────────────

BRANDS = {
    "FS": {
        "name": "Franchise Sellers",
        "color": "#dc2626",          # red-600
        "audience": "franchise business owners",
        "ghl_location_env": "GHL_FS_LOCATION_ID",
        "ghl_token_env": "GHL_FS_API_KEY",   # matches workspace convention (shared .env)
        "sender_name": "Theodore Baird",
    },
    "CS": {
        "name": "Company Sellers",
        "color": "#3b82f6",          # blue-500
        "audience": "business owners",
        "ghl_location_env": "GHL_CS_LOCATION_ID",
        "ghl_token_env": "GHL_CS_API_KEY",   # matches workspace convention (shared .env)
        "sender_name": "Theodore Baird",
    },
}


# ────────────────────────────────────────────────────────────────────────────
# Sending rate limits (Instantly) — conservative 2026 deliverability posture
# ────────────────────────────────────────────────────────────────────────────

SENDING = {
    "cold_per_mailbox_per_day": 30,      # hard cap incl. headroom
    "warmup_per_mailbox_per_day": 12,    # continuous, permanent
    "inter_send_gap_seconds": (60, 120), # min/max jitter
    "open_tracking": False,              # 2026: pixel tracking hurts inbox placement
    "link_tracking": False,
    "stop_on_reply": True,
    "stop_on_auto_reply": True,
    "min_spintax_variation_pct": 50,     # min content variation across variants
}


# ────────────────────────────────────────────────────────────────────────────
# CAN-SPAM compliance — physical address + opt-out in EVERY email (legal)
# ────────────────────────────────────────────────────────────────────────────

COMPLIANCE = {
    # Valid physical postal address (Theodore 2026-06-27: the Denver coworking
    # suite used on the website — correct for CAN-SPAM; never a home address).
    "mailing_address": "1001 Bannock St., Suite 475, Denver, CO 80204",
    "optout_line": "Not interested? Just reply and I'll take you off my list.",
    "footer_separator": "--",
}


# ────────────────────────────────────────────────────────────────────────────
# Cold-sending domain allow-list — NEVER the primary domain, a reply.* subdomain,
# or a staff/warm-only mailbox (Theodore 2026-06-27).
# ────────────────────────────────────────────────────────────────────────────

COLD_SENDING = {
    # The ONLY domains excluded from cold are the two MAIN brand domains — they host
    # real client email. EVERY other domain in Instantly (including the lookalikes
    # thecompanysellers.com / companysellers.co) is for cold. (Theodore 2026-06-27.)
    "excluded_domains": {"franchisesellers.com", "companysellers.com"},
    # GHL uses reply.<brand> / mail.<brand> for transactional mail — never cold there.
    "excluded_subdomain_prefixes": ("reply.", "mail."),
    "staff_mailboxes": set(),
}


# ────────────────────────────────────────────────────────────────────────────
# Suppression + cooldowns (defaults — confirm with Theodore before go-live)
# ────────────────────────────────────────────────────────────────────────────

COOLDOWNS = {
    "no_reply_days": 60,            # emailed, no reply → rest 60 days
    "closed_lost_months": 12,       # GHL closed-lost → rest 12 months
    "soft_bounce_limit": 3,         # soft-bounce x3 → needs re-verification
    "out_of_office_retry_buffer_days": 1,  # retry OOO this many days after return date
}

# Suppression sources that permanently exclude from cold (a record being on ANY
# of these → Tier D / never-send). The dedup engine already applies these; this
# list is the runtime cross-check.
PERMANENT_SUPPRESSION_FLAGS = {
    "franchisee_block_list",
    "airtable_archived",
    "airtable_master_archived",
    "unsubscribed",
    "hard_bounced",
    "complaint",
    "in_crm",  # already a customer/lead in GHL
}

# Bounce-rate circuit breakers
BOUNCE_HALT_PCT = 3.0      # any campaign above this → halt + re-verify (2026-06-27: tightened 5->3)
BOUNCE_WARN_PCT = 2.0      # above this → investigate
UNSUB_HALT_PCT = 5.0


# ────────────────────────────────────────────────────────────────────────────
# ICP scoring
# ────────────────────────────────────────────────────────────────────────────

ICP_THRESHOLD = 60            # records >= this get sequenced
ICP_WEIGHTS = {
    "demographic_tenure": 0.40,
    "behavioral_situational": 0.40,
    "firmographic": 0.20,
}


# ────────────────────────────────────────────────────────────────────────────
# Verification — MillionVerifier primary; LeadMagic kept for enrichment
# ────────────────────────────────────────────────────────────────────────────

VERIFICATION = {
    "primary": "millionverifier",
    "millionverifier_key_env": "MILLIONVERIFIER_API_KEY",
    "leadmagic_key_env": "LEADMAGIC_API_KEY",     # kept for enrichment (company/owner/size/founded)
    "zerobounce_key_env": "ZEROBOUNCE_API_KEY",   # RETIRED; optional spot-check only
    # Verifier mode:
    #   "millionverifier" — MillionVerifier on everything (DEFAULT, 2026-06-27). ~6-7x
    #     cheaper than ZeroBounce, comparable accuracy. LeadMagic stays for enrichment.
    #   "uncertain_only"  — legacy: LeadMagic verify + ZeroBounce on catch-all/unknown.
    #   "zerobounce_all" / "credit_floor" — legacy.
    "mode": "millionverifier",
    "uncertain_verdicts": {"catch-all-safe", "unknown"},
    "leadmagic_credit_floor": 50,
    # Verification verdicts considered safe to send.
    "deliverable_verdicts": {"valid", "deliverable", "catch-all-safe"},
    # Re-verify any record whose last verification is older than this. Tightened
    # 90 -> 30 per the deliverability review (the 187K is an aged dedup).
    "reverify_after_days": 30,
    "batch_size": 100,        # records per API batch
    "throttle_ms": 200,       # between batches
}


# ────────────────────────────────────────────────────────────────────────────
# Qualification funnel (cheap → expensive) — see QUALIFICATION-SPEC.md
#   Stage 0 free filters · Stage 1 company lookup (LeadMagic) · Stage 2 AI judge
# Caps are CS-only (FS uses the location cap). Everything is PASS-ON-UNKNOWN:
# a missing data point never drops a lead — only an explicit over-cap value does,
# and only when enforcement is on. Enforcement can be turned off to MEASURE
# enrichment coverage first (the 1,000-lead test) before trusting the gate.
# ────────────────────────────────────────────────────────────────────────────

QUALIFICATION = {
    "enforce_cs_caps": True,        # hard-gate CS employees<=50 + age>=3yr (pass-on-unknown)
    "cs_employee_cap": 50,          # CS: over this = too big (rule #3)
    "cs_min_age_years": 3,          # CS: under this = no real financials yet (rule #9)
    "cs_revenue_cap_label": "$25M", # CS: over this = too big (rule #2, AI-estimated band, SOFT)
    "fs_location_cap": 25,          # FS: over this = too big (rule #4, AI soft review-flag only)
    # CS routing: bigger qualified private business -> Full Service (the focus);
    # smaller -> Toolkit (deprioritized). Tunable; employees below this -> toolkit.
    "cs_toolkit_employee_threshold": 10,
    # The company-lookup enrichment provider (Stage 1). LeadMagic today; the
    # test-then-evaluate rule says swap if coverage proves insufficient.
    "enrichment_provider": "leadmagic",
}


# ────────────────────────────────────────────────────────────────────────────
# Enrichment providers (Phase 2 — placeholders, not used in Phase 1)
# ────────────────────────────────────────────────────────────────────────────

ENRICHMENT = {
    "email_finder": "leadmagic",   # LeadMagic also finds emails
    "firmographic": "apollo",      # Phase 2
    "deep_person": "pdl",          # Phase 2 (PDL preferred over Datagma)
    "apollo_key_env": "APOLLO_API_KEY",
    "pdl_key_env": "PDL_API_KEY",
}


# ────────────────────────────────────────────────────────────────────────────
# Anthropic (reply classification + signal extraction)
# ────────────────────────────────────────────────────────────────────────────

ANTHROPIC = {
    "key_env": "ANTHROPIC_API_KEY",
    # Pin the model so classification quality is stable; bump deliberately.
    "classify_model": "claude-sonnet-4-5",
    "signal_model": "claude-sonnet-4-5",
    "max_tokens": 1024,
}


# ────────────────────────────────────────────────────────────────────────────
# Instantly
# ────────────────────────────────────────────────────────────────────────────

INSTANTLY = {
    "key_env": "INSTANTLY_API_KEY",
    "base_url": "https://api.instantly.ai/api/v2",
    # Brand → tag used on campaigns/domains so brand-walls hold at the send layer.
    "brand_tag_prefix": {"FS": "FS", "CS": "CS"},
}

# Default User-Agent for ALL outbound HTTP. Instantly sits behind Cloudflare, which
# 403s the default `Python-urllib/x.y` UA with "error code: 1010" (browser-signature
# ban). Any non-default UA passes. Every urllib Request in the engine must send this
# header or live calls (incl. actual sends) get blocked. (Diagnosed 2026-06-09.)
USER_AGENT = "FS-Outbound/1.0 (+franchisesellers.com)"


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def get_key(env_name: str) -> str | None:
    """Read an API key from environment. Returns None if unset (dry-run tolerant)."""
    v = os.environ.get(env_name, "").strip()
    return v or None


def require_key(env_name: str) -> str:
    """Read a key, raising if missing. Only call from live (non-dry-run) paths."""
    v = get_key(env_name)
    if not v:
        raise RuntimeError(
            f"Missing required API key env var: {env_name}. "
            f"Set it in cold-email-outbound/.env (see config/.env.example), "
            f"or keep CEO_DRY_RUN=true to run without it."
        )
    return v


def ensure_runtime_dir() -> Path:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIR


def status_banner() -> str:
    mode = "DRY-RUN (no external calls)" if DRY_RUN else "LIVE (external calls ENABLED)"
    return f"[Cold Email Engine] mode={mode}"
