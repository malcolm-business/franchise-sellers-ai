"""Postcard channel — physical direct mail (Lob / PostGrid). STUB for later.

A postcard touch sends a physical card to the prospect's mailing address — a
high-impact, low-noise touch in a multi-channel sequence. Interface is defined so
it slots into the orchestrator; live sending wires a print-mail API (Lob or
PostGrid) when Theodore picks a vendor.

Needs a mailing address (we have street/city/state/country on many records) +
POSTCARD_API_KEY. Dry-run logs intent.
"""
from __future__ import annotations

from .. import config, data_layer
from ..models import Contact
from ..sequences import Touch
from .base import BaseChannel, register


class PostcardChannel(BaseChannel):
    name = "postcard"

    def is_available(self) -> bool:
        return bool(config.get_key("POSTCARD_API_KEY"))

    def can_reach(self, contact: Contact) -> bool:
        return bool(contact.city and contact.state)   # needs a mailing address

    def execute_touch(self, contact: Contact, touch: Touch, campaign: dict) -> dict:
        if not self.can_reach(contact):
            return {"channel": self.name, "ok": False, "error": "no mailing address"}
        if config.DRY_RUN:
            data_layer.log_dry_run("channel:postcard",
                                   f"WOULD mail postcard to {contact.display_name} ({contact.city}, {contact.state})",
                                   {"canonical_id": contact.canonical_id, "template": touch.template})
            return {"channel": self.name, "ok": True, "dry_run": True}
        # Live: Lob/PostGrid create-postcard API. Implement when a vendor is chosen.
        return {"channel": self.name, "ok": False, "error": "postcard vendor not wired yet"}


register(PostcardChannel())
