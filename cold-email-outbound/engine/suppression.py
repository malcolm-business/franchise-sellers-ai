"""Cold Email Engine — Layer A pre-send suppression filter.

The gate that protects deliverability + brand. Every batch passes through here
before any push to Instantly. A contact is suppressed if ANY of:

  1. On the Tier D do-not-contact set (Franchisee Block List, Airtable Archived)
  2. Already in either GHL workspace (in_crm) — from crm-snapshot
  3. Carries a permanent suppression flag (unsubscribed, hard-bounced, complaint)
  4. Inside an active cooldown (no-reply 60d / closed-lost 12mo / re-engage date)
  5. Missing a usable email
  6. Email not verified deliverable (when require_verified=True)

Every suppression decision is logged with a reason so the batch is auditable.
No network calls — reads the flat-file suppression set + crm-snapshot.
"""
from __future__ import annotations

from datetime import datetime, date

from . import config, data_layer
from .models import Contact


class SuppressionFilter:
    """Holds the suppression sets once (loaded from disk) and filters batches fast."""

    def __init__(self, require_verified: bool = False, today: date | None = None):
        self.require_verified = require_verified
        self.today = today or _utc_today()
        # Load once — these are reused across every batch in a run.
        self.suppression_emails = data_layer.load_suppression_emails()
        self.crm_emails = data_layer.load_crm_emails()

    # ── single-contact decision ──────────────────────────────────────────
    def reason_to_suppress(self, c: Contact) -> str | None:
        """Return a reason string if the contact should be suppressed, else None."""
        email = (c.email_norm or "").strip().lower()

        if not email:
            return "no_email"

        if email in self.suppression_emails:
            return "on_tier_d_suppression"

        if email in self.crm_emails:
            return "in_crm"

        flags = set(c.suppression_list)
        hit = flags & config.PERMANENT_SUPPRESSION_FLAGS
        if hit:
            return f"permanent_flag:{sorted(hit)[0]}"

        # Active cooldown / re-engage date in the future
        if c.re_engage_date:
            try:
                reengage = datetime.fromisoformat(c.re_engage_date).date()
                if reengage > self.today:
                    return f"cooldown_until:{c.re_engage_date}"
            except ValueError:
                pass

        if self.require_verified:
            if c.verification_status not in config.VERIFICATION["deliverable_verdicts"]:
                return f"not_verified_deliverable:{c.verification_status}"

        return None

    # ── batch filter ─────────────────────────────────────────────────────
    def filter_batch(self, contacts: list[Contact]) -> tuple[list[Contact], list[tuple[Contact, str]]]:
        """Return (clean, suppressed_with_reason)."""
        clean, suppressed = [], []
        for c in contacts:
            reason = self.reason_to_suppress(c)
            if reason:
                c.send_status = "suppressed"
                suppressed.append((c, reason))
            else:
                clean.append(c)
        return clean, suppressed

    def summary(self, suppressed: list[tuple[Contact, str]]) -> dict[str, int]:
        """Count suppressions by reason (reason prefix, so cooldown dates collapse)."""
        counts: dict[str, int] = {}
        for _, reason in suppressed:
            key = reason.split(":")[0]
            counts[key] = counts.get(key, 0) + 1
        return counts


def _utc_today() -> date:
    # Avoid bare datetime.now() per workflow-script rules; this is normal runtime code
    # but we keep it centralized so tests can inject `today`.
    return datetime.utcnow().date()


def filter_contacts(contacts: list[Contact], require_verified: bool = False) -> tuple[list[Contact], list[tuple[Contact, str]]]:
    """Convenience one-shot filter."""
    return SuppressionFilter(require_verified=require_verified).filter_batch(contacts)
