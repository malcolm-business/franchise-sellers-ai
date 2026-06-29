"""Cold Email Engine -> Multi-Channel Marketing Platform — sequence model.

A Sequence is an ordered set of Touches that span channels. A prospect is enrolled
once and the orchestrator walks them through every touch on its scheduled day,
dispatching each to the right channel (email / LinkedIn / ads / postcard).

This is the abstraction that turns the cold-email engine into a multi-channel
platform: the same prospect, one personalized sequence, many channels, coordinated.

No network calls here — pure model + the default sequence library.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum


class Channel(str, Enum):
    EMAIL = "email"          # Instantly
    LINKEDIN = "linkedin"    # HeyReach
    ADS = "ads"              # Google Customer Match + Meta Custom Audiences
    POSTCARD = "postcard"    # Lob / PostGrid (later)


@dataclass
class Touch:
    """One step in a sequence, on one channel."""
    channel: str             # Channel value
    step: int                # ordinal within the sequence
    delay_days: int          # days after enrollment this touch fires
    action: str              # e.g. "send_email", "connect", "message", "add_to_audience", "send_postcard"
    template: str = ""       # template filename (email/postcard) or message key (linkedin)
    params: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Sequence:
    """An ordered multi-channel touch plan."""
    name: str
    brand: str               # FS / CS
    touches: list[Touch] = field(default_factory=list)
    description: str = ""

    def channels_used(self) -> set[str]:
        return {t.channel for t in self.touches}

    def to_dict(self) -> dict:
        return {"name": self.name, "brand": self.brand, "description": self.description,
                "touches": [t.to_dict() for t in self.touches]}


# ────────────────────────────────────────────────────────────────────────────
# Default multi-channel sequence library
# ────────────────────────────────────────────────────────────────────────────
#
# These are starting templates Malcolm can clone + tune. Each maps a campaign
# stream to a coordinated cross-channel plan. Email steps reference the existing
# templates/ files; LinkedIn/ads steps reference channel actions.

def _email(step, delay, template):
    return Touch(Channel.EMAIL.value, step, delay, "send_email", template=template)


def _li_connect(step, delay):
    return Touch(Channel.LINKEDIN.value, step, delay, "connect",
                 params={"note": "personalized connection request"})


def _li_message(step, delay, message_key):
    return Touch(Channel.LINKEDIN.value, step, delay, "message", template=message_key)


def _ads_add(step, delay, audience):
    return Touch(Channel.ADS.value, step, delay, "add_to_audience",
                 params={"audience": audience})


DEFAULT_SEQUENCES: dict[str, Sequence] = {
    # Seller cold, FS niche — email-led, LinkedIn reinforce, ads retarget
    "seller_cold_fs_niche": Sequence(
        name="seller_cold_fs_niche",
        brand="FS",
        description="Email-led 3-step + LinkedIn touch + ad retargeting for named-system franchisees.",
        touches=[
            _ads_add(0, 0, "fs_seller_retargeting"),          # day 0: start seeing ads
            _email(1, 1, "seller_cold_fs_niche.md"),          # day 1: email 1
            _li_connect(2, 2),                                 # day 2: LinkedIn connect
            _email(3, 5, "seller_cold_fs_niche.md"),          # day 5: email 2 (bump)
            _li_message(4, 7, "li_followup_fs"),               # day 7: LinkedIn message
            _email(5, 11, "seller_cold_fs_niche.md"),         # day 11: email 3 (soft close)
        ],
    ),
    "seller_cold_fs_broad": Sequence(
        name="seller_cold_fs_broad", brand="FS",
        description="Email 3-step + LinkedIn + ads for long-tail franchisees.",
        touches=[
            _ads_add(0, 0, "fs_seller_retargeting"),
            _email(1, 1, "seller_cold_fs_broad.md"),
            _li_connect(2, 3),
            _email(3, 5, "seller_cold_fs_broad.md"),
            _email(4, 11, "seller_cold_fs_broad.md"),
        ],
    ),
    "seller_cold_cs": Sequence(
        name="seller_cold_cs", brand="CS",
        description="Email 3-step + LinkedIn + ads for independent business owners.",
        touches=[
            _ads_add(0, 0, "cs_seller_retargeting"),
            _email(1, 1, "seller_cold_cs.md"),
            _li_connect(2, 3),
            _email(3, 5, "seller_cold_cs.md"),
            _email(4, 11, "seller_cold_cs.md"),
        ],
    ),
    "referral_partner_advisor": Sequence(
        name="referral_partner_advisor", brand="CS",
        description="Email 2-step + LinkedIn connect for CPAs/advisors.",
        touches=[
            _email(1, 1, "referral_partner_advisor.md"),
            _li_connect(2, 2),
            _email(3, 6, "referral_partner_advisor.md"),
            _li_message(4, 8, "li_followup_advisor"),
        ],
    ),
    "referral_partner_zor": Sequence(
        name="referral_partner_zor", brand="FS",
        description="Email 2-step + LinkedIn for franchisor partnerships.",
        touches=[
            _email(1, 1, "referral_partner_zor.md"),
            _li_connect(2, 2),
            _email(3, 6, "referral_partner_zor.md"),
        ],
    ),
    "event_pre": Sequence(
        name="event_pre", brand="FS",
        description="Single email + LinkedIn touch ahead of an event.",
        touches=[
            _email(1, 0, "event_pre.md"),
            _li_connect(2, 1),
        ],
    ),
    "event_post": Sequence(
        name="event_post", brand="FS",
        description="Email 2-step + LinkedIn after an event.",
        touches=[
            _email(1, 0, "event_post.md"),
            _li_connect(2, 1),
            _email(3, 4, "event_post.md"),
        ],
    ),
}


# LinkedIn message copy (kept here; Malcolm edits). Email copy stays in templates/.
LINKEDIN_MESSAGES = {
    "li_followup_fs": "Hi {{firstName}} — sent you a note about valuing/selling your franchise. "
                      "No pressure, just happy to share what {{franchise_system}} owners are seeing in 2026 if useful.",
    "li_followup_advisor": "Hi {{firstName}} — reached out about partnering on business valuations for your clients. "
                           "Open to a quick chat on how the referral relationship works?",
}


def get_sequence(name: str) -> Sequence | None:
    return DEFAULT_SEQUENCES.get(name)
