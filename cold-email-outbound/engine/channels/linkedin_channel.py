"""LinkedIn channel — HeyReach.

HeyReach runs the LinkedIn outreach (connection requests + messages) from your
warmed LinkedIn accounts. Campaigns are built in the HeyReach app; this channel
ADDS leads to the right HeyReach campaign and sends messages — the same pattern
as Instantly (the platform holds the sending infra; we feed it leads).

DRY-RUN: logs intent, no calls. LIVE: HeyReach public REST API (needs
HEYREACH_API_KEY — not yet in .env; the HeyReach MCP is connected for interactive
use, but the headless engine needs the raw key).

Zero pip deps (urllib).
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error

from .. import config, data_layer
from ..models import Contact
from ..sequences import Touch, LINKEDIN_MESSAGES
from .base import BaseChannel, register

HEYREACH_BASE = "https://api.heyreach.io/api/public"


class LinkedInChannel(BaseChannel):
    name = "linkedin"

    def is_available(self) -> bool:
        return bool(config.get_key("HEYREACH_API_KEY"))

    def can_reach(self, contact: Contact) -> bool:
        return bool(contact.linkedin_norm or contact.linkedin_original)

    def _headers(self):
        return {"X-API-KEY": config.require_key("HEYREACH_API_KEY"),
                "Content-Type": "application/json", "User-Agent": config.USER_AGENT}

    def _post(self, path: str, body: dict) -> dict:
        req = urllib.request.Request(f"{HEYREACH_BASE}{path}",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))

    def execute_touch(self, contact: Contact, touch: Touch, campaign: dict) -> dict:
        li = contact.linkedin_original or contact.linkedin_norm
        if not li:
            return {"channel": self.name, "ok": False, "error": "no LinkedIn URL"}

        action = touch.action  # "connect" or "message"
        heyreach_campaign_id = campaign.get("heyreach_campaign_id")

        if config.DRY_RUN:
            detail = {"canonical_id": contact.canonical_id, "linkedin": li, "action": action}
            if action == "message":
                detail["message_key"] = touch.template
            data_layer.log_dry_run("channel:linkedin",
                                   f"WOULD {action} on LinkedIn: {contact.display_name} ({li})",
                                   detail)
            return {"channel": self.name, "ok": True, "dry_run": True, "action": action}

        # LIVE
        if action == "connect":
            if not heyreach_campaign_id:
                return {"channel": self.name, "ok": False, "error": "no heyreach_campaign_id on campaign"}
            resp = self._post("/campaign/AddLeadsToCampaignV2", {
                "campaignId": heyreach_campaign_id,
                "leads": [{"profileUrl": li, "firstName": contact.first_name,
                           "lastName": contact.last_name, "companyName": contact.company}],
            })
            return {"channel": self.name, "ok": True, "dry_run": False, "raw": resp}
        elif action == "message":
            msg = LINKEDIN_MESSAGES.get(touch.template, "")
            # message sending in HeyReach is typically driven by the campaign sequence;
            # direct-message API used here for ad-hoc follow-ups
            resp = self._post("/inbox/SendMessage", {
                "profileUrl": li, "message": _fill(msg, contact),
            })
            return {"channel": self.name, "ok": True, "dry_run": False, "raw": resp}
        return {"channel": self.name, "ok": False, "error": f"unknown action {action}"}

    def enroll(self, contacts: list[Contact], campaign: dict) -> dict:
        """Bulk-add an audience to a HeyReach campaign (connect-led)."""
        reachable = [c for c in contacts if self.can_reach(c)]
        if config.DRY_RUN:
            data_layer.log_dry_run("channel:linkedin",
                                   f"WOULD enroll {len(reachable)} leads into HeyReach campaign",
                                   {"count": len(reachable),
                                    "heyreach_campaign_id": campaign.get("heyreach_campaign_id")})
            return {"channel": self.name, "enrolled": len(reachable), "dry_run": True}
        cid = campaign.get("heyreach_campaign_id")
        if not cid:
            return {"channel": self.name, "enrolled": 0, "error": "no heyreach_campaign_id"}
        leads = [{"profileUrl": (c.linkedin_original or c.linkedin_norm),
                  "firstName": c.first_name, "lastName": c.last_name,
                  "companyName": c.company} for c in reachable]
        resp = self._post("/campaign/AddLeadsToCampaignV2", {"campaignId": cid, "leads": leads})
        return {"channel": self.name, "enrolled": len(leads), "dry_run": False, "raw": resp}


def _fill(msg: str, contact: Contact) -> str:
    return (msg.replace("{{firstName}}", contact.first_name or "there")
               .replace("{{franchise_system}}", contact.company or "your franchise"))


register(LinkedInChannel())
