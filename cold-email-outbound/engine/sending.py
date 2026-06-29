"""Cold Email Engine — sending (Instantly).

Pushes a rendered, suppressed, verified batch into an Instantly campaign.
Brand-walls enforced: a campaign is tagged by brand and only draws from that
brand's domain pool (configured in Instantly).

DRY-RUN: logs the campaign-create + lead-add it WOULD perform; sends nothing.
LIVE: calls Instantly v2 API. Honors the master CLAUDE.md throttle posture
(no bulk writes >=100 without per-run approval; chunked with cooldowns).

The engine already has an Instantly MCP available for interactive use; this
module is the headless/scheduled path. Live HTTP uses urllib (stdlib).
"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.error

from . import config, data_layer
from .models import Contact, CampaignStream, STREAM_BRAND, SendStatus


# ────────────────────────────────────────────────────────────────────────────
# Payload builders
# ────────────────────────────────────────────────────────────────────────────

def build_campaign_payload(stream: CampaignStream, name: str, subjects: list[str],
                           steps: list[dict]) -> dict:
    """Build the Instantly campaign-create payload (sequence + schedule + settings)."""
    brand = STREAM_BRAND[stream]
    tag = config.INSTANTLY["brand_tag_prefix"][brand]
    seq_steps = []
    for st in steps:
        seq_steps.append({
            "delay": st.get("delay_days", 0),
            "type": "email",
            "variants": [{"subject": subj, "body": "<<rendered per-lead>>"} for subj in subjects],
        })
    return {
        "name": f"{tag} | {name}",
        "brand_tag": tag,
        "campaign_schedule": {
            "timing": {"from": "08:00", "to": "16:00"},
            "timezone": "America/Denver",
        },
        "sequences": [{"steps": seq_steps}],
        "settings": {
            "daily_limit_per_mailbox": config.SENDING["cold_per_mailbox_per_day"],
            "open_tracking": config.SENDING["open_tracking"],
            "link_tracking": config.SENDING["link_tracking"],
            "stop_on_reply": config.SENDING["stop_on_reply"],
            "stop_on_auto_reply": config.SENDING["stop_on_auto_reply"],
        },
    }


def build_lead_payload(contact: Contact, rendered_steps: dict[int, str]) -> dict:
    """One lead's payload incl. per-step rendered bodies as custom variables."""
    payload = {
        "email": contact.email_original or contact.email_norm,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "company_name": contact.company,
        "personalization": rendered_steps.get(1, ""),
        "custom_variables": {f"step_{n}_body": body for n, body in rendered_steps.items()},
        "canonical_id": contact.canonical_id,
    }
    return payload


# ────────────────────────────────────────────────────────────────────────────
# Live Instantly calls (only when not DRY_RUN)
# ────────────────────────────────────────────────────────────────────────────

def _instantly_post(path: str, body: dict) -> dict:
    key = config.require_key(config.INSTANTLY["key_env"])
    url = f"{config.INSTANTLY['base_url']}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": config.USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _instantly_get(path: str) -> dict:
    key = config.require_key(config.INSTANTLY["key_env"])
    url = f"{config.INSTANTLY['base_url']}{path}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {key}", "User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ────────────────────────────────────────────────────────────────────────────
# Cold-sending mailbox guard — NEVER send cold from the main brand domains
# (franchisesellers.com / companysellers.com), a reply.* subdomain, or a staff/
# warm-only inbox. Those live in Instantly only to stay warm. (Theodore 2026-06-27.)
# ────────────────────────────────────────────────────────────────────────────

def campaign_sending_mailboxes(campaign_id: str) -> list[str]:
    """Best-effort: the email accounts a campaign sends from, read from Instantly."""
    try:
        c = _instantly_get(f"/campaigns/{campaign_id}")
    except Exception:
        return []
    emails: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if (isinstance(v, str) and "@" in v and "." in v.split("@")[-1]
                        and any(t in k.lower() for t in ("email", "account", "mailbox", "sender", "from"))):
                    emails.add(v.strip().lower())
                else:
                    walk(v)
        elif isinstance(o, list):
            for it in o:
                walk(it)

    walk(c)
    return sorted(emails)


def assert_cold_safe(campaign_id: str) -> dict:
    """HARD GUARD (fail-closed): refuse to cold-send from a forbidden mailbox. Raises
    if a main-brand/staff inbox is attached, or if the mailbox list can't be confirmed."""
    from . import presend
    mboxes = campaign_sending_mailboxes(campaign_id)
    if not mboxes:
        raise RuntimeError(
            f"Cold-safety: could not read the sending mailboxes for campaign {campaign_id} "
            f"from Instantly, so cannot confirm none are franchisesellers.com / companysellers.com "
            f"or a staff inbox. Verify in Instantly that this campaign uses ONLY approved lookalike "
            f"domains, then re-run activate with cold_check_override=True.")
    approved, violations = presend.filter_cold_mailboxes(mboxes)
    if violations:
        raise RuntimeError(
            f"Cold-safety HARD STOP: campaign {campaign_id} has forbidden sending mailbox(es) "
            f"attached: {violations}. Cold email must NEVER come from the main brand domains or "
            f"staff/warm-only inboxes. Detach them in Instantly before activating.")
    return {"ok": True, "mailboxes": mboxes, "violations": []}


# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────

def create_campaign(stream: CampaignStream, name: str, subjects: list[str], steps: list[dict]) -> dict:
    """Create (or simulate) an Instantly campaign. Returns {campaign_id, ...}."""
    payload = build_campaign_payload(stream, name, subjects, steps)
    if config.DRY_RUN:
        data_layer.log_dry_run("sending", f"WOULD create Instantly campaign '{payload['name']}'",
                               {"stream": stream.value, "n_steps": len(steps), "subjects": subjects})
        return {"campaign_id": f"dryrun-{stream.value}-{abs(hash(name)) % 100000}", "dry_run": True, "payload": payload}
    resp = _instantly_post("/campaigns", payload)
    return {"campaign_id": resp.get("id"), "dry_run": False, "raw": resp}


def push_leads(campaign_id: str, stream: CampaignStream, leads: list[tuple[Contact, dict[int, str]]],
               approved: bool = False) -> dict:
    """Add leads to a campaign. `leads` = [(contact, {step_n: rendered_body}), ...].

    Safety: a live push of >=100 leads requires approved=True (master CLAUDE.md rule).
    Chunked with cooldowns. Dry-run logs every intended add.
    """
    n = len(leads)
    if config.DRY_RUN:
        for contact, rendered in leads:
            contact.send_status = SendStatus.QUEUED.value
            data_layer.log_dry_run("sending", f"WOULD add lead {contact.email_original} to {campaign_id}",
                                   {"canonical_id": contact.canonical_id, "stream": stream.value})
        return {"added": n, "dry_run": True, "campaign_id": campaign_id}

    if n >= 100 and not approved:
        raise RuntimeError(
            f"Refusing live push of {n} leads without approved=True "
            f"(master CLAUDE.md: no bulk writes >=100 without per-run approval). "
            f"Chunk it or pass approved=True after Theodore signs off."
        )

    added = 0
    chunk_size = 50
    for i in range(0, n, chunk_size):
        chunk = leads[i:i + chunk_size]
        for contact, rendered in chunk:
            _instantly_post(f"/campaigns/{campaign_id}/leads", build_lead_payload(contact, rendered))
            contact.send_status = SendStatus.QUEUED.value
            added += 1
        time.sleep(1.0)  # cooldown between chunks
    return {"added": added, "dry_run": False, "campaign_id": campaign_id}


def activate_campaign(campaign_id: str, cold_check_override: bool = False) -> dict:
    """Activate a campaign so it starts sending. Dry-run is a no-op log.

    LIVE: runs the cold-safety guard first — refuses to activate if any main-brand
    (franchisesellers.com / companysellers.com) or staff/warm-only inbox is attached.
    cold_check_override=True bypasses it only after manual verification in Instantly."""
    if config.DRY_RUN:
        data_layer.log_dry_run("sending", f"WOULD activate campaign {campaign_id} (after cold-safety check)",
                               {"campaign_id": campaign_id})
        return {"activated": False, "dry_run": True, "campaign_id": campaign_id}
    cold = {"override": True} if cold_check_override else assert_cold_safe(campaign_id)
    resp = _instantly_post(f"/campaigns/{campaign_id}/activate", {})
    return {"activated": True, "dry_run": False, "cold_safety": cold, "raw": resp}
