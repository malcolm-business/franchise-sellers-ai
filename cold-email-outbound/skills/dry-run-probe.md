---
name: dry-run-probe
description: Analysis-only probe across all 5 Phase 1 streams. Shows pool sizes, ICP/suppression/verification funnel, copy preview + content variation per stream. Sends nothing. Use to review readiness before go-live.
---

# dry-run-probe

Runs each Phase 1 stream through the full pipeline in analysis mode (no push) and
returns a per-stream funnel: loaded → ICP-eligible → clean → deliverable →
rendered, plus content-variation % and avg word count.

## Run
```bash
cd cold-email-outbound
python3 -c "from engine import pipeline; import json; \
print(json.dumps({k: v.to_dict() for k,v in pipeline.run_all_phase1_probes(limit=500).items()}, indent=2))"
```

## Read the output
- `content_variation_pct` below 50 → needs more spintax before sending
- `verified_deliverable` ÷ `loaded` → projected list health (dry-run uses simulated decay)
- `suppression_reasons` → why contacts dropped (in_crm, on_tier_d, cooldown, etc.)
- `notes` → per-stream caveats (e.g. buyer source placeholder)
