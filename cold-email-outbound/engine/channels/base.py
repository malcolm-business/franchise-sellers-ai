"""Channel abstraction — the common interface every channel implements.

The orchestrator only knows about BaseChannel. Each concrete channel (email,
linkedin, ads, postcard) handles its own API + dry-run gating. This is what makes
the platform extensible: a new channel is a new BaseChannel subclass + a register().
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Contact
from ..sequences import Touch


class BaseChannel(ABC):
    """Common interface for a marketing channel."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """True if this channel can run live (keys present). Dry-run works regardless."""
        ...

    @abstractmethod
    def can_reach(self, contact: Contact) -> bool:
        """True if the channel has what it needs to touch this contact
        (e.g. email channel needs an email; linkedin needs a LinkedIn URL)."""
        ...

    @abstractmethod
    def execute_touch(self, contact: Contact, touch: Touch, campaign: dict) -> dict:
        """Perform one touch on this contact. Returns an action-result dict.

        MUST honor config.DRY_RUN: in dry-run, log intent + return a simulated
        result, never make a live call.
        """
        ...

    def enroll(self, contacts: list[Contact], campaign: dict) -> dict:
        """Optional bulk enroll (e.g. add a whole audience to an ad list / LI campaign).
        Default: no-op; channels that support bulk override this."""
        return {"channel": self.name, "enrolled": 0, "note": "no bulk enroll for this channel"}


CHANNEL_REGISTRY: dict[str, BaseChannel] = {}


def register(channel: BaseChannel) -> None:
    CHANNEL_REGISTRY[channel.name] = channel


def get_channel(name: str) -> BaseChannel | None:
    return CHANNEL_REGISTRY.get(name)
