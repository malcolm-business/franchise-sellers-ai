"""Cold Email Engine — CRM routing.

Routes a classified reply to the right destination:
  - positive (seller) -> matching brand's GHL workspace (FS or CS), trigger workflow
  - buyer-side intent  -> Buyer Manager (Yvonne) pipeline, NOT seller CRM
  - referral           -> Theodore direct + new warm-intro record
  - cooldown/timeline  -> set re-engage date, no CRM action
  - unsubscribe/no     -> permanent suppression, no CRM action

Brand-walls: a record's brand_tag decides which GHL workspace receives it.
NEVER cross-route. Closed-lost/closed-won downstream handled by reading
crm-snapshot (not here).

DRY-RUN: logs the intended GHL action; creates nothing. LIVE: calls GHL.
Honors master CLAUDE.md GHL rate-limit rules (single-record creates only here,
never bulk; retries with backoff at go-live).
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

from . import config, data_layer
from .models import Contact, ReplyCategory, SUPPRESSING_REPLIES, ROUTING_REPLIES, COOLDOWN_REPLIES


# ────────────────────────────────────────────────────────────────────────────
# Destinations
# ────────────────────────────────────────────────────────────────────────────

def _ghl_destination(contact: Contact) -> dict:
    brand = contact.brand_tag if contact.brand_tag in config.BRANDS else "CS"
    binfo = config.BRANDS[brand]
    return {
        "brand": brand,
        "location_id_env": binfo["ghl_location_env"],
        "token_env": binfo["ghl_token_env"],
    }


def _ghl_create_contact_live(contact: Contact, workflow: str) -> dict:
    dest = _ghl_destination(contact)
    location_id = config.require_key(dest["location_id_env"])
    token = config.require_key(dest["token_env"])
    body = {
        "locationId": location_id,
        "email": contact.email_original or contact.email_norm,
        "firstName": contact.first_name,
        "lastName": contact.last_name,
        "companyName": contact.company,
        "source": "Cold Email",
        "tags": ["cold-email", contact.campaign_stream, f"workflow:{workflow}"],
    }
    req = urllib.request.Request(
        "https://services.leadconnectorhq.com/contacts/",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Version": "2021-07-28",
                 "Content-Type": "application/json", "User-Agent": config.USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ────────────────────────────────────────────────────────────────────────────
# Routing decision
# ────────────────────────────────────────────────────────────────────────────

def route_reply(contact: Contact, category_value: str, re_engage_hint: str = "",
                referral_name: str = "") -> dict:
    """Apply the routing matrix for one classified reply. Returns an action dict.

    Mutates the contact's send_status / re_engage_date / suppression as appropriate.
    """
    try:
        category = ReplyCategory(category_value)
    except ValueError:
        category = ReplyCategory.OTHER

    action = {"canonical_id": contact.canonical_id, "category": category.value, "destination": "none", "detail": ""}

    # Suppress
    if category in SUPPRESSING_REPLIES:
        flag = "unsubscribed" if category == ReplyCategory.UNSUBSCRIBE else "replied_not_interested"
        contact.add_suppression(flag)
        contact.send_status = "unsubscribed" if category == ReplyCategory.UNSUBSCRIBE else "replied"
        action["destination"] = "suppression"
        action["detail"] = flag
        return action

    # Cooldown / re-engage
    if category in COOLDOWN_REPLIES:
        days = config.COOLDOWNS["no_reply_days"]
        if category == ReplyCategory.OUT_OF_OFFICE:
            days = config.COOLDOWNS["out_of_office_retry_buffer_days"] + 7
        elif "year" in re_engage_hint.lower():
            days = 365
        elif any(y in re_engage_hint for y in ("2026", "2027")):
            days = 180
        contact.re_engage_date = (datetime.utcnow().date() + timedelta(days=days)).isoformat()
        contact.send_status = "replied"
        action["destination"] = "cooldown"
        action["detail"] = f"re_engage_date={contact.re_engage_date} (hint='{re_engage_hint}')"
        return action

    # Route to a pipeline
    if category in ROUTING_REPLIES:
        if category == ReplyCategory.WRONG_INTENT_BUYER_SIDE:
            action["destination"] = "buyer_manager"
            action["detail"] = "route to Yvonne / Buyer Manager pipeline"
            contact.add_suppression("buyer_side_lead")
            contact.send_status = "replied"
            _do_ghl(contact, workflow="buyer_intake", action=action, buyer_side=True)
            return action
        if category == ReplyCategory.REFERRAL:
            action["destination"] = "referral_new_record"
            action["detail"] = f"referral_name={referral_name}"
            contact.send_status = "replied"
            return action
        # positive seller intent -> GHL
        workflow = "discovery_call" if category in (ReplyCategory.POSITIVE_MEETING_READY,
                                                    ReplyCategory.MEETING_ACCEPTED) else "oov_intake"
        contact.send_status = "replied"
        _do_ghl(contact, workflow=workflow, action=action, buyer_side=False)
        return action

    # OTHER / wrong_person -> flag for human review, no CRM action
    action["destination"] = "human_review"
    action["detail"] = "needs manual triage"
    return action


def _do_ghl(contact: Contact, workflow: str, action: dict, buyer_side: bool) -> None:
    dest = _ghl_destination(contact)
    if config.DRY_RUN:
        data_layer.log_dry_run(
            "routing",
            f"WOULD create GHL contact for {contact.email_original} in {dest['brand']} workspace (workflow={workflow})",
            {"canonical_id": contact.canonical_id, "brand": dest["brand"], "workflow": workflow,
             "buyer_side": buyer_side},
        )
        action["destination"] = f"ghl_{dest['brand'].lower()}" if not buyer_side else "buyer_manager"
        action["detail"] += f" | DRY-RUN (would create in GHL {dest['brand']}, workflow={workflow})"
        return
    resp = _ghl_create_contact_live(contact, workflow)
    contact.add_suppression("in_crm")
    action["destination"] = f"ghl_{dest['brand'].lower()}"
    action["detail"] += f" | created GHL id={resp.get('contact', {}).get('id', '?')}"
