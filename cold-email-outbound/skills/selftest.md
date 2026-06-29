---
name: selftest
description: Run the whole cold-email engine in dry-run against real data. Readiness gate — run before any go-live step. Sends/spends nothing.
---

# selftest

Validates the engine end-to-end: data files present, suppression sets load, all 8
templates parse, 5 Phase 1 streams run load→score→suppress→verify→render→push in
dry-run, reply classify+route chain works, dry-run audit trail writes.

## Run
```bash
cd cold-email-outbound
python3 -m engine.selftest
```

Exit 0 = passed. Refuses to run if `CEO_DRY_RUN=false` (must validate in dry-run first).

## When to use
- After any engine change
- Before wiring API keys
- Before flipping `CEO_DRY_RUN=false`
