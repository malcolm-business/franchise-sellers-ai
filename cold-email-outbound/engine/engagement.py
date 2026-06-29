"""Cold Email Engine — engagement tracking.

Turns Instantly events (sent / reply / bounce / unsubscribe) into SendEvents in
the data layer, and triggers downstream classification + routing on replies.

Two ingestion modes:
  - handle_webhook(payload): process a single Instantly webhook POST (push)
  - poll_events(): pull recent events via the Instantly MCP/API (fallback / catch-up)

DRY-RUN: handle_webhook still works on a provided payload (it's pure transform);
poll_events returns nothing (no live call). Open/click tracking is OFF by design.
"""
from __future__ import annotations

from datetime import datetime

from . import config, data_layer
from .models import SendEvent, SendStatus
from . import classify as classify_mod


# Map Instantly event names -> our event_type vocabulary
EVENT_MAP = {
    "email_sent": "sent",
    "sent": "sent",
    "reply_received": "reply",
    "email_reply": "reply",
    "reply": "reply",
    "email_bounced": "bounce_hard",
    "hard_bounce": "bounce_hard",
    "soft_bounce": "bounce_soft",
    "lead_unsubscribed": "unsubscribe",
    "unsubscribe": "unsubscribe",
}


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def handle_webhook(payload: dict) -> SendEvent | None:
    """Process one Instantly webhook payload into a SendEvent + side effects.

    Pure transform + data-layer writes; safe in dry-run. On a reply, also runs
    classification (heuristic in dry-run, Claude API live) and records the category.
    """
    raw_type = (payload.get("event_type") or payload.get("type") or "").lower()
    event_type = EVENT_MAP.get(raw_type, raw_type or "unknown")
    canonical_id = payload.get("canonical_id") or payload.get("custom_variables", {}).get("canonical_id", "")
    stream = payload.get("campaign_stream") or payload.get("campaign_tag") or "unknown"
    ts = payload.get("timestamp") or _now_iso()

    event = SendEvent(
        canonical_id=canonical_id,
        campaign_stream=stream,
        event_type=event_type,
        timestamp=ts,
        step=int(payload.get("step", 0) or 0),
        detail=payload.get("detail", ""),
        reply_body=payload.get("reply_body", "") or payload.get("body", ""),
    )

    # On reply, classify
    if event_type == "reply":
        result = classify_mod.classify_reply(
            subject=payload.get("reply_subject", "") or payload.get("subject", ""),
            body=event.reply_body,
            original_subject=payload.get("original_subject", ""),
        )
        event.reply_category = result["category"]
        event.detail = (event.detail + f" | classified={result['category']} ({result['method']})").strip(" |")

    data_layer.append_send_event(event)
    return event


def poll_events(since_iso: str | None = None) -> list[SendEvent]:
    """Catch-up poll for events (when webhooks miss). Live path uses Instantly API.

    DRY-RUN returns []. Live implementation would page the Instantly emails endpoint
    filtered to received/reply since `since_iso` and run each through handle_webhook.
    """
    if config.DRY_RUN:
        data_layer.log_dry_run("engagement", "WOULD poll Instantly for events", {"since": since_iso})
        return []
    # Live: implemented against Instantly /emails (received) — wired at go-live.
    # Intentionally left as the integration seam; webhooks are the primary path.
    return []


def bounce_rate(stream: str) -> float:
    """Compute bounce rate for a stream from logged events. Drives the circuit breaker."""
    events = data_layer.read_send_events(stream)
    sent = sum(1 for e in events if e.event_type == "sent")
    bounced = sum(1 for e in events if e.event_type in ("bounce_hard", "bounce_soft"))
    if sent == 0:
        return 0.0
    return bounced / sent * 100


def unsub_rate(stream: str) -> float:
    events = data_layer.read_send_events(stream)
    sent = sum(1 for e in events if e.event_type == "sent")
    unsub = sum(1 for e in events if e.event_type == "unsubscribe")
    if sent == 0:
        return 0.0
    return unsub / sent * 100


def circuit_breaker_check(stream: str) -> dict:
    """Return {halt, warn, bounce_pct, unsub_pct, reason}. Halt if over thresholds."""
    bp = bounce_rate(stream)
    up = unsub_rate(stream)
    halt = bp >= config.BOUNCE_HALT_PCT or up >= config.UNSUB_HALT_PCT
    warn = bp >= config.BOUNCE_WARN_PCT
    reason = ""
    if bp >= config.BOUNCE_HALT_PCT:
        reason = f"bounce {bp:.1f}% >= {config.BOUNCE_HALT_PCT}%"
    elif up >= config.UNSUB_HALT_PCT:
        reason = f"unsub {up:.1f}% >= {config.UNSUB_HALT_PCT}%"
    return {"halt": halt, "warn": warn, "bounce_pct": round(bp, 2), "unsub_pct": round(up, 2), "reason": reason}
