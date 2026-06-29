"""Ads channel — Google Customer Match + Meta Custom Audiences.

The ad touch doesn't "send" anything — it adds a prospect's hashed email to a
Custom Audience so they start seeing your ads while the email/LinkedIn sequence
runs. This is the "surround them" layer: a prospect in a sequence sees your brand
in their inbox, on LinkedIn, AND in their Google/Facebook/Instagram feed.

INTERFACE IS COMPLETE + plug-in-ready. Live calls need ad-account API access:
  - Google Ads: GOOGLE_ADS_* (developer token, OAuth client, customer id) + a
    Customer Match user list id
  - Meta: META_ACCESS_TOKEN + a Custom Audience id
These aren't wired yet — Theodore/Malcolm grant account access. Until then this
runs in dry-run (logs intent) exactly like the other channels.

Emails are SHA-256 hashed before any upload (both platforms require + expect this).
"""
from __future__ import annotations

import hashlib

from .. import config, data_layer
from ..models import Contact
from ..sequences import Touch
from .base import BaseChannel, register


def hash_email(email: str) -> str:
    """SHA-256 of normalized email — the format Google + Meta both require."""
    return hashlib.sha256((email or "").strip().lower().encode()).hexdigest()


class AdsChannel(BaseChannel):
    name = "ads"

    def is_available(self) -> bool:
        # Live requires at least one ad platform configured
        return bool(config.get_key("GOOGLE_ADS_DEVELOPER_TOKEN") or config.get_key("META_ACCESS_TOKEN"))

    def can_reach(self, contact: Contact) -> bool:
        return bool(contact.email_norm)   # audience match is email-based

    def execute_touch(self, contact: Contact, touch: Touch, campaign: dict) -> dict:
        audience = touch.params.get("audience", "default_retargeting")
        if not contact.email_norm:
            return {"channel": self.name, "ok": False, "error": "no email for audience match"}
        if config.DRY_RUN:
            data_layer.log_dry_run("channel:ads",
                                   f"WOULD add {contact.email_original} to ad audience '{audience}'",
                                   {"canonical_id": contact.canonical_id, "audience": audience,
                                    "email_sha256": hash_email(contact.email_norm)[:12] + "…"})
            return {"channel": self.name, "ok": True, "dry_run": True, "audience": audience}
        # LIVE — batched at enroll() level normally; single-add falls through to enroll
        return self.enroll([contact], {**campaign, "audience": audience})

    def enroll(self, contacts: list[Contact], campaign: dict) -> dict:
        """Bulk-add an audience's hashed emails to Google + Meta custom audiences."""
        audience = campaign.get("audience", "default_retargeting")
        hashed = [hash_email(c.email_norm) for c in contacts if c.email_norm]
        if config.DRY_RUN:
            data_layer.log_dry_run("channel:ads",
                                   f"WOULD upload {len(hashed)} hashed emails to ad audience '{audience}'",
                                   {"count": len(hashed), "audience": audience,
                                    "platforms": self._platforms()})
            return {"channel": self.name, "enrolled": len(hashed), "dry_run": True,
                    "platforms": self._platforms()}
        results = {}
        if config.get_key("GOOGLE_ADS_DEVELOPER_TOKEN"):
            results["google"] = self._google_customer_match(hashed, campaign)
        if config.get_key("META_ACCESS_TOKEN"):
            results["meta"] = self._meta_custom_audience(hashed, campaign)
        return {"channel": self.name, "enrolled": len(hashed), "dry_run": False, "results": results}

    def _platforms(self) -> list[str]:
        p = []
        if config.get_key("GOOGLE_ADS_DEVELOPER_TOKEN"):
            p.append("google")
        if config.get_key("META_ACCESS_TOKEN"):
            p.append("meta")
        return p or ["(none configured — dry-run only)"]

    # ── live upload stubs (wired when ad-account access is granted) ───────
    def _google_customer_match(self, hashed_emails: list[str], campaign: dict) -> dict:
        # Google Ads API: OfflineUserDataJobService -> add hashed emails to a
        # Customer Match user list. Requires google-ads OAuth + developer token +
        # customer id + user_list_id. Implement at go-live with the granted creds.
        return {"status": "not_implemented_until_google_ads_access", "would_add": len(hashed_emails)}

    def _meta_custom_audience(self, hashed_emails: list[str], campaign: dict) -> dict:
        # Meta Marketing API: POST /{custom_audience_id}/users with SHA-256 emails.
        # Requires META_ACCESS_TOKEN + custom_audience_id. Implement at go-live.
        return {"status": "not_implemented_until_meta_access", "would_add": len(hashed_emails)}


register(AdsChannel())
