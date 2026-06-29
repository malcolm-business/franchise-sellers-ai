"""Pre-send gate + cold-sending domain allow-list.

The hard checks that run before a campaign goes live, beside the CEO_DRY_RUN
master switch:
  - check_gate(): a pass/fail checklist (tracking off, SPF/DMARC, warmup, no
    blacklist, bounce <3%, CAN-SPAM address + opt-out in the copy, copy/ICP sign-off).
    Reads the deliverability monitor's status JSON for the live DNS/warmup state.
  - is_cold_approved(): enforces that cold campaigns never use the primary domain,
    a reply.* subdomain, or a staff/warm-only mailbox.
"""
from __future__ import annotations

import json

from . import config


# ── cold-sending domain allow-list ───────────────────────────────────────────

def is_cold_approved(email: str) -> bool:
    """True if this mailbox may send COLD email — an approved lookalike, never the
    primary domain, a reply.* subdomain, or a staff/warm-only inbox."""
    e = (email or "").strip().lower()
    if not e or "@" not in e:
        return False
    domain = e.split("@", 1)[1]
    cs = config.COLD_SENDING
    if e in {m.lower() for m in cs["staff_mailboxes"]}:
        return False
    if domain in {d.lower() for d in cs["excluded_domains"]}:
        return False
    if any(domain.startswith(p) for p in cs["excluded_subdomain_prefixes"]):
        return False
    return True


def filter_cold_mailboxes(emails) -> tuple[list[str], list[str]]:
    """Split mailboxes into (approved_for_cold, excluded)."""
    approved, excluded = [], []
    for e in emails:
        (approved if is_cold_approved(e) else excluded).append(e)
    return approved, excluded


# ── pre-send gate ─────────────────────────────────────────────────────────────

def _monitor_status() -> dict:
    p = config.RUNTIME_DIR / "deliverability-status.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _bounce_pct(stream: str | None) -> float | None:
    if not stream:
        return None
    try:
        from . import engagement
        return engagement.bounce_rate(stream)
    except Exception:
        return None


def check_gate(stream: str | None = None, sample_body: str | None = None,
               copy_approved: bool = False, icp_confirmed: bool = False) -> dict:
    """Return {ok, checks, skipped}. `ok` is True only when every decisive check passes;
    checks with no data yet (e.g. no monitor run) are 'skipped', not failed."""
    checks: list[dict] = []

    def add(name: str, ok, detail: str = ""):
        checks.append({"check": name, "pass": (None if ok is None else bool(ok)), "detail": detail})

    s = config.SENDING
    add("open_tracking_off", s["open_tracking"] is False)
    add("link_tracking_off", s["link_tracking"] is False)

    st = _monitor_status()
    dns = st.get("dns", {})
    if dns:
        spf_n = sum(1 for d in dns.values() if d.get("spf"))
        dmarc_n = sum(1 for d in dns.values() if d.get("dmarc"))
        listed = [k for k, d in dns.items() if d.get("dbl") == "LISTED"]
        add("spf_all_domains", spf_n == len(dns), f"{spf_n}/{len(dns)} domains")
        add("dmarc_all_domains", dmarc_n == len(dns), f"{dmarc_n}/{len(dns)} domains")
        add("no_blacklist", not listed, ", ".join(listed) if listed else "clean")
        add("warmup_ok", st.get("warmup_below_floor", 1) == 0,
            f"{st.get('warmup_below_floor', '?')} below floor")
    else:
        add("dns_and_warmup", None, "no monitor status yet — run the health monitor")

    bp = _bounce_pct(stream)
    if bp is not None:
        add("bounce_under_hard_stop", bp < config.BOUNCE_HALT_PCT,
            f"{bp:.1f}% (< {config.BOUNCE_HALT_PCT}%)")

    if sample_body is not None:
        lb = sample_body.lower()
        add("physical_address_present", config.COMPLIANCE["mailing_address"] in sample_body)
        add("optout_present", "reply" in lb and ("take you off" in lb or "off my list" in lb))
    else:
        add("compliance_footer", None, "pass a sample rendered body to check")

    add("copy_approved", copy_approved)
    add("icp_confirmed", icp_confirmed)

    decisive = [c["pass"] for c in checks if c["pass"] is not None]
    skipped = [c["check"] for c in checks if c["pass"] is None]
    return {"ok": bool(decisive) and all(decisive), "checks": checks, "skipped": skipped}
