---
name: mailbox-health
description: (Go-live) Weekly check on sending-domain + mailbox reputation across the ~60 warmed domains. Flags domains drifting toward spam so you can pause them before they hurt the pool.
---

# mailbox-health

A go-live operational skill. Pulls account + warmup status from Instantly and
flags mailboxes/domains with degrading reputation, high bounce, or paused warmup.

## Status
Built as an integration seam — wire to the Instantly MCP (`list_accounts`,
`get_warmup_analytics`) at go-live. The MCP is already available interactively;
this skill is the scheduled/headless wrapper.

## Intended run (go-live)
```bash
cd cold-email-outbound
# via Instantly MCP: list_accounts (status, warmup) per brand domain pool
# flag: status != active, warmup paused, bounce trending up
```

## Why
The Maaco precedent (8.57% bounce → 0.21% reply) showed a bad list/domain kills a
campaign. Weekly health checks catch reputation drift before it spreads.
Keep warmup running permanently on every mailbox.
