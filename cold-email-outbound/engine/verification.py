"""Cold Email Engine — email verification (MillionVerifier primary).

MillionVerifier verifies every record (default 'millionverifier' mode): ~6-7x
cheaper than ZeroBounce with comparable accuracy. LeadMagic is kept for ENRICHMENT
(company/owner/size/founded) and the legacy 'uncertain_only' mode; ZeroBounce is
retired (legacy modes only).

DRY-RUN: returns simulated verdicts (deterministic per email) and logs intent.
No credits spent, no calls made. Flip CEO_DRY_RUN=false + set keys to go live.

The live HTTP paths use urllib (stdlib) so the engine has zero pip dependencies.
"""
from __future__ import annotations

import json
import time
import hashlib
import urllib.request
import urllib.error
import urllib.parse

from . import config, data_layer
from .models import Contact


# ────────────────────────────────────────────────────────────────────────────
# Verdict normalization
# ────────────────────────────────────────────────────────────────────────────

def _normalize_verdict(provider: str, raw: dict) -> str:
    """Map a provider's response to one of: valid / invalid / catch-all / unknown.

    Verified against live responses 2026-06-08:
      LeadMagic  -> field 'email_status' (valid / invalid / catch_all / unknown / ...)
      ZeroBounce -> field 'status'       (valid / invalid / catch-all / unknown / ...)
    """
    if provider == "leadmagic":
        status = (raw.get("email_status") or raw.get("status") or raw.get("result") or "").lower()
    elif provider == "millionverifier":
        # MillionVerifier 'result': ok / catch_all / unknown / invalid / disposable / error
        status = (raw.get("result") or "").lower()
    else:  # zerobounce
        status = (raw.get("status") or "").lower()
    if status in ("valid", "deliverable", "ok"):
        return "valid"
    if status in ("catch-all", "catchall", "catch_all", "accept_all", "catch-all-safe"):
        return "catch-all-safe"
    if status in ("invalid", "undeliverable", "do_not_mail", "spamtrap", "abuse", "disposable"):
        return "invalid"
    return "unknown"


def backfill_from_leadmagic(contact, raw: dict) -> None:
    """Fill empty contact fields from a LeadMagic verification response (free enrichment).

    LeadMagic returns company industry/size/founded/LinkedIn + location on every
    email-validate call. We only fill fields that are currently empty (never overwrite
    existing data). Marks the contact enriched_by='leadmagic'.
    """
    if not raw:
        return
    filled = False

    def fill(attr, value):
        nonlocal filled
        if value and not getattr(contact, attr, ""):
            setattr(contact, attr, str(value)[:200])
            filled = True

    fill("company", raw.get("company_name"))
    fill("industry", raw.get("company_industry"))
    fill("company_size", raw.get("company_size"))
    fill("company_founded", raw.get("company_founded"))
    li = raw.get("company_linkedin_url")
    if li and not contact.linkedin_original:
        contact.linkedin_original = str(li)[:200]
        filled = True
    loc = raw.get("company_location") or {}
    if isinstance(loc, dict):
        fill("city", loc.get("locality"))
        fill("state", loc.get("region"))
        fill("country", loc.get("country"))
    if filled:
        contact.enriched_by = "leadmagic"


def _simulated_verdict(email: str) -> str:
    """Deterministic dry-run verdict so selftest is reproducible.

    ~78% valid, ~7% catch-all, ~15% invalid — mirrors realistic 6-18mo-old-list decay.
    """
    h = int(hashlib.sha256(email.encode()).hexdigest(), 16) % 100
    if h < 78:
        return "valid"
    if h < 85:
        return "catch-all-safe"
    return "invalid"


# ────────────────────────────────────────────────────────────────────────────
# Live provider calls (only reached when not DRY_RUN)
# ────────────────────────────────────────────────────────────────────────────

def _http_get_json(url: str, headers: dict | None = None, timeout: int = 20) -> dict:
    h = dict(headers or {})
    h.setdefault("User-Agent", config.USER_AGENT)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _verify_leadmagic_live(email: str) -> dict:
    key = config.require_key(config.VERIFICATION["leadmagic_key_env"])
    # LeadMagic email-validate endpoint (POST). Kept minimal + provider-agnostic.
    url = "https://api.leadmagic.io/email-validate"
    body = json.dumps({"email": email}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"X-API-Key": key, "Content-Type": "application/json",
                 "User-Agent": config.USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _verify_millionverifier_live(email: str) -> dict:
    key = config.require_key(config.VERIFICATION["millionverifier_key_env"])
    url = (f"https://api.millionverifier.com/api/v3/?api={urllib.parse.quote(key)}"
           f"&email={urllib.parse.quote(email)}&timeout=10")
    return _http_get_json(url)


def _verify_zerobounce_live(email: str) -> dict:
    key = config.require_key(config.VERIFICATION["zerobounce_key_env"])
    url = f"https://api.zerobounce.net/v2/validate?api_key={key}&email={urllib.parse.quote(email)}"
    return _http_get_json(url)


# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────

class Verifier:
    """Verifier implementing the configured waterfall mode.

    Default mode 'uncertain_only' (Theodore 2026-06-07): LeadMagic verifies every
    record; ZeroBounce re-checks ONLY the catch-all/unknown ones, as the trusted-but-
    expensive final stop. Minimizes ZeroBounce spend.
    """

    def __init__(self, leadmagic_credits: int | None = None, mode: str | None = None):
        self.leadmagic_credits = leadmagic_credits
        self.mode = mode or config.VERIFICATION["mode"]
        self.provider_used: dict[str, int] = {"millionverifier": 0, "leadmagic": 0, "zerobounce": 0, "simulated": 0}

    # ── single-provider primitives ───────────────────────────────────────
    def _millionverifier(self, email: str) -> dict:
        if config.DRY_RUN:
            v = _simulated_verdict(email)
            self.provider_used["simulated"] += 1
            data_layer.log_dry_run("verification", f"WOULD verify {email} via MillionVerifier",
                                   {"email": email, "simulated_verdict": v})
            return {"email": email, "verdict": v, "provider": "millionverifier(sim)", "raw": {}}
        try:
            raw = _verify_millionverifier_live(email)
            self.provider_used["millionverifier"] += 1
            return {"email": email, "verdict": _normalize_verdict("millionverifier", raw),
                    "provider": "millionverifier", "raw": raw}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            return {"email": email, "verdict": "unknown", "provider": "millionverifier", "raw": {"error": str(e)}}

    def _leadmagic(self, email: str) -> dict:
        if config.DRY_RUN:
            v = _simulated_verdict(email)
            self.provider_used["simulated"] += 1
            data_layer.log_dry_run("verification", f"WOULD verify {email} via LeadMagic",
                                   {"email": email, "simulated_verdict": v})
            return {"email": email, "verdict": v, "provider": "leadmagic(sim)", "raw": {}}
        try:
            raw = _verify_leadmagic_live(email)
            if self.leadmagic_credits is not None:
                self.leadmagic_credits -= 1
            self.provider_used["leadmagic"] += 1
            return {"email": email, "verdict": _normalize_verdict("leadmagic", raw), "provider": "leadmagic", "raw": raw}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            return {"email": email, "verdict": "unknown", "provider": "leadmagic", "raw": {"error": str(e)}}

    def _zerobounce(self, email: str) -> dict:
        if config.DRY_RUN:
            # Dry-run: simulate ZeroBounce resolving an uncertain one (mostly to valid/invalid)
            v = "valid" if _simulated_verdict(email + "zb") != "invalid" else "invalid"
            self.provider_used["simulated"] += 1
            data_layer.log_dry_run("verification", f"WOULD re-verify {email} via ZeroBounce (final stop)",
                                   {"email": email, "simulated_verdict": v})
            return {"email": email, "verdict": v, "provider": "zerobounce(sim)", "raw": {}}
        try:
            raw = _verify_zerobounce_live(email)
            self.provider_used["zerobounce"] += 1
            return {"email": email, "verdict": _normalize_verdict("zerobounce", raw), "provider": "zerobounce", "raw": raw}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            return {"email": email, "verdict": "unknown", "provider": "zerobounce", "raw": {"error": str(e)}}

    # ── batch (mode-aware) ────────────────────────────────────────────────
    def verify_batch(self, contacts: list[Contact]) -> list[Contact]:
        """Verify each contact; set verification_status per the configured mode."""
        throttle = config.VERIFICATION["throttle_ms"] / 1000.0
        uncertain = config.VERIFICATION["uncertain_verdicts"]
        floor = config.VERIFICATION["leadmagic_credit_floor"]

        for i, c in enumerate(contacts):
            if not c.email_norm:
                c.verification_status = "invalid"
                continue

            if self.mode == "millionverifier":
                c.verification_status = self._millionverifier(c.email_norm)["verdict"]

            elif self.mode == "zerobounce_all":
                c.verification_status = self._zerobounce(c.email_norm)["verdict"]

            elif self.mode == "credit_floor":
                use_zb = self.leadmagic_credits is not None and self.leadmagic_credits <= floor
                c.verification_status = (self._zerobounce if use_zb else self._leadmagic)(c.email_norm)["verdict"]

            else:  # "uncertain_only" (default)
                lm = self._leadmagic(c.email_norm)
                # Free double-duty: backfill empty fields from LeadMagic's company data
                backfill_from_leadmagic(c, lm.get("raw", {}))
                verdict = lm["verdict"]
                if verdict in uncertain:
                    # Expensive final stop only on the ambiguous ones
                    verdict = self._zerobounce(c.email_norm)["verdict"]
                c.verification_status = verdict

            if not config.DRY_RUN and (i + 1) % config.VERIFICATION["batch_size"] == 0:
                time.sleep(throttle)
        return contacts

    def stats(self) -> dict:
        return dict(self.provider_used)


def verify_contacts(contacts: list[Contact], leadmagic_credits: int | None = None) -> tuple[list[Contact], dict]:
    """Convenience: verify a batch, return (contacts, provider-usage stats)."""
    v = Verifier(leadmagic_credits=leadmagic_credits)
    v.verify_batch(contacts)
    return contacts, v.stats()


def split_deliverable(contacts: list[Contact]) -> tuple[list[Contact], list[Contact]]:
    """After verification, split into (deliverable, not). Catch-all-safe counts as deliverable."""
    deliverable, dead = [], []
    ok = config.VERIFICATION["deliverable_verdicts"]
    for c in contacts:
        (deliverable if c.verification_status in ok else dead).append(c)
    return deliverable, dead
