---
name: handle-webhook
description: Process one Instantly webhook payload — turn it into a send event, and on a reply, auto-classify and route it. The live inbound pipeline.
---

# handle-webhook

The inbound entry point. Instantly POSTs an event → this transforms it into a
SendEvent, writes it to the data layer, and on a reply runs classify → route.

## Run (test with a sample payload)
```bash
cd cold-email-outbound
python3 -c "from engine import engagement; \
ev = engagement.handle_webhook({'event_type':'reply','canonical_id':'abc','campaign_stream':'seller_cold_cs','reply_body':'Yes please send info','subject':'Re: Quick question'}); \
print(ev.event_type, ev.reply_category)"
```

## Event types handled
sent · reply (→ classify → route) · bounce_hard · bounce_soft · unsubscribe

## Go-live wiring
Point an Instantly webhook at an endpoint that calls `handle_webhook(payload)`.
Until that endpoint exists, `engagement.poll_events()` is the catch-up fallback.
Open/click tracking is OFF by design (2026 deliverability).
