"""Cold Email Engine — data models + enums.

Pure definitions. No I/O, no network. These describe the shape of records,
campaign streams, reply categories, and send statuses used across the engine.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


# ────────────────────────────────────────────────────────────────────────────
# Campaign streams — first-class concept (SYSTEM-DESIGN.md)
# ────────────────────────────────────────────────────────────────────────────

class CampaignStream(str, Enum):
    SELLER_COLD_FS_NICHE = "seller_cold_fs_niche"
    SELLER_COLD_FS_BROAD = "seller_cold_fs_broad"
    SELLER_COLD_CS = "seller_cold_cs"
    BUYER_REACTIVATION = "buyer_reactivation"
    REFERRAL_PARTNER_ADVISOR = "referral_partner_advisor"
    REFERRAL_PARTNER_ZOR = "referral_partner_zor"
    EVENT_PRE = "event_pre"
    EVENT_POST = "event_post"


# Which brand each stream sends under (drives sending-domain pool + CRM routing).
STREAM_BRAND = {
    CampaignStream.SELLER_COLD_FS_NICHE: "FS",
    CampaignStream.SELLER_COLD_FS_BROAD: "FS",
    CampaignStream.SELLER_COLD_CS: "CS",
    CampaignStream.BUYER_REACTIVATION: "FS",   # buyer-side default FS; overridable per-list
    CampaignStream.REFERRAL_PARTNER_ADVISOR: "CS",
    CampaignStream.REFERRAL_PARTNER_ZOR: "FS",
    CampaignStream.EVENT_PRE: "FS",
    CampaignStream.EVENT_POST: "FS",
}


# ────────────────────────────────────────────────────────────────────────────
# Reply classification categories (Claude API output)
# ────────────────────────────────────────────────────────────────────────────

class ReplyCategory(str, Enum):
    POSITIVE_MEETING_READY = "positive_meeting_ready"
    POSITIVE_CURIOUS = "positive_curious"
    POSITIVE_WITH_TIMELINE_OBJECTION = "positive_with_timeline_objection"
    OBJECTION_NOT_NOW = "objection_not_now"
    OBJECTION_NOT_INTERESTED = "objection_not_interested"
    WRONG_PERSON = "wrong_person"
    WRONG_INTENT_BUYER_SIDE = "wrong_intent_buyer_side"
    UNSUBSCRIBE = "unsubscribe"
    OUT_OF_OFFICE = "out_of_office"
    REFERRAL = "referral"
    MEETING_ACCEPTED = "meeting_accepted"
    OTHER = "other"


# Categories that should permanently suppress the contact from cold.
SUPPRESSING_REPLIES = {
    ReplyCategory.OBJECTION_NOT_INTERESTED,
    ReplyCategory.UNSUBSCRIBE,
}

# Categories that route into a CRM / pipeline (positive intent).
ROUTING_REPLIES = {
    ReplyCategory.POSITIVE_MEETING_READY,
    ReplyCategory.POSITIVE_CURIOUS,
    ReplyCategory.MEETING_ACCEPTED,
    ReplyCategory.WRONG_INTENT_BUYER_SIDE,
    ReplyCategory.REFERRAL,
}

# Categories that set a cooldown / re-engage timer.
COOLDOWN_REPLIES = {
    ReplyCategory.OBJECTION_NOT_NOW,
    ReplyCategory.POSITIVE_WITH_TIMELINE_OBJECTION,
    ReplyCategory.OUT_OF_OFFICE,
}


# ────────────────────────────────────────────────────────────────────────────
# Send status
# ────────────────────────────────────────────────────────────────────────────

class SendStatus(str, Enum):
    PENDING = "pending"          # in pool, not yet sequenced
    QUEUED = "queued"            # pushed to Instantly, not yet sent
    SENT = "sent"                # at least one step delivered
    REPLIED = "replied"          # got a reply (see reply_category)
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    COMPLETED = "completed"      # finished sequence, no reply
    SUPPRESSED = "suppressed"    # filtered out before send


# ────────────────────────────────────────────────────────────────────────────
# Canonical contact record
# ────────────────────────────────────────────────────────────────────────────

# Matches the columns produced by scripts/dedup/run_dedup.py canonical-master.csv
CANONICAL_COLUMNS = [
    "canonical_id", "email_norm", "email_original", "linkedin_norm", "linkedin_original",
    "first_name", "last_name", "full_name", "company", "title", "industry", "sub_industry",
    "phone_primary", "phone_alt", "city", "state", "country", "website",
    "brand_tag", "verification_status", "source_files", "source_categories",
    "suppression_flags", "tier", "raw_notes",
]


@dataclass
class Contact:
    """A single canonical contact. Mirrors canonical-master.csv plus runtime fields."""
    canonical_id: str
    email_norm: str = ""
    email_original: str = ""
    linkedin_norm: str = ""
    linkedin_original: str = ""
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    company: str = ""
    title: str = ""
    industry: str = ""
    sub_industry: str = ""
    phone_primary: str = ""
    phone_alt: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    website: str = ""
    brand_tag: str = "UNKNOWN"
    verification_status: str = "unknown"
    source_files: str = "[]"          # JSON array string
    source_categories: str = "[]"     # JSON array string
    suppression_flags: str = "[]"     # JSON array string
    tier: str = ""
    raw_notes: str = ""

    # Enrichment from LeadMagic (Stage 1 company lookup) — see engine/enrichment.py
    company_size: str = ""            # headcount band string, e.g. "11-50"
    company_founded: str = ""         # founding year, e.g. "2014"
    company_employees: int | None = None  # parsed exact/estimated headcount (the <=50 gate)
    revenue_band: str = ""            # revenue estimate band (Stage 3, soft signal)
    location_count: int | None = None     # franchise unit / location count if known (Stage 3, rare)
    enriched_by: str = ""             # e.g. "leadmagic" when fields were backfilled

    # Runtime enrichment context (not persisted — used in-memory to ground the AI judge)
    company_description: str = ""        # LeadMagic company blurb (rich for tiny firms)
    company_ownership_status: str = ""   # LeadMagic "private"/"public"/... hint

    # Runtime fields (not in canonical-master; added during a campaign run)
    icp_score: int | None = None
    icp_breakdown: dict = field(default_factory=dict)
    campaign_stream: str = ""
    send_status: str = SendStatus.PENDING.value
    reply_category: str = ""
    re_engage_date: str = ""          # ISO date when a cooldown lifts
    last_verified_date: str = ""
    last_sent_date: str = ""

    # ── helpers ──────────────────────────────────────────────────────────
    @property
    def suppression_list(self) -> list[str]:
        try:
            return json.loads(self.suppression_flags) if self.suppression_flags else []
        except (json.JSONDecodeError, TypeError):
            return []

    @property
    def source_list(self) -> list[str]:
        try:
            return json.loads(self.source_categories) if self.source_categories else []
        except (json.JSONDecodeError, TypeError):
            return []

    def add_suppression(self, flag: str) -> None:
        flags = set(self.suppression_list)
        flags.add(flag)
        self.suppression_flags = json.dumps(sorted(flags))

    @property
    def display_name(self) -> str:
        return self.full_name or f"{self.first_name} {self.last_name}".strip() or self.email_original

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Contact":
        """Build a Contact from a csv/dict row, ignoring unknown columns."""
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        clean = {k: ("" if v is None else v) for k, v in row.items() if k in known}
        return cls(**clean)  # type: ignore[arg-type]

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


# ────────────────────────────────────────────────────────────────────────────
# Send event (engagement tracking)
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class SendEvent:
    canonical_id: str
    campaign_stream: str
    event_type: str        # sent | reply | bounce_hard | bounce_soft | unsubscribe | open | click
    timestamp: str         # ISO
    step: int = 0
    detail: str = ""
    reply_body: str = ""
    reply_category: str = ""

    def to_row(self) -> dict[str, Any]:
        return asdict(self)
