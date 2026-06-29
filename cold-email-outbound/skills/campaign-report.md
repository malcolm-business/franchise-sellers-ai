---
name: campaign-report
description: Per-stream performance from logged events — sent/reply/bounce/unsub counts, positive %, and the circuit-breaker status (halt if bounce ≥5% or unsub ≥5%).
---

# campaign-report

Reads the engagement event log and reports per-stream health. Run weekly (or after
any send batch) to catch deliverability problems early.

## Run
```bash
cd cold-email-outbound
python3 -c "from engine import engagement; \
print(engagement.circuit_breaker_check('seller_cold_cs'))"
```

## Output
- `bounce_pct`, `unsub_pct`
- `warn` (bounce ≥ 2%) → investigate copy/list
- `halt` (bounce ≥ 5% or unsub ≥ 5%) → STOP the stream, re-verify the list
- `reason` → which threshold tripped

## Gates (from SYSTEM-DESIGN.md)
Bounce < 2% target / > 5% halt · Unsub < 2% target / > 5% halt.
Per-stream positive-% targets live in config/campaign-streams.json.
