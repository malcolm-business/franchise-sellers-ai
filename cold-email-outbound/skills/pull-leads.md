---
name: pull-leads
description: Pull N qualified, deliverable leads from the database for a campaign — qualified=true, correct brand, not suppressed, with a confidence floor. The operator's weekly "give me this week's leads" step.
---

# pull-leads

Pulls a campaign-ready batch of **qualified** leads from Neon: contacts that passed the
qualification funnel (current owner, correct brand, US, no PE/public), are not suppressed,
and clear a confidence floor. This is the weekly "pull N leads" step.

## Run
```bash
cd cold-email-outbound
python3 -c "from engine import db; \
leads = db.pull_qualified(brand='CS', limit=300, min_confidence=0.5); \
print(len(leads), 'qualified CS leads'); \
[print(' ', c.display_name, '|', c.company, '|', c.email_norm) for c in leads[:10]]"
```

## Knobs
- `brand='FS'|'CS'` — brand wall (omit for both)
- `limit=N` — how many this week (start small per the 60-day cadence)
- `min_confidence=0.5` — drop low-confidence AI verdicts (recommended floor)

## Where the qualified pool comes from
Qualification runs as a paid batch over Tier A: Stage 0 (free) → Stage 1 LeadMagic
company lookup (`live_enrich=True`) → Stage 2 AI judge, writing `qualified` /
`qual_brand` / `qualification` + the firmographic columns to each row:
```bash
# MUST use the project venv python — it has the anthropic SDK (system python3 does NOT,
# so the AI judge fails with ModuleNotFoundError). Verified 2026-06-27.
cd /root/cold-email-outbound
./.venv/bin/python -c "from engine import data_layer, qualification; \
batch = data_layer.load_tier_a('CS', limit=500); \
qualification.qualify_batch(batch, ai_cap=500, force_ai=True, live_enrich=True, save=True)"   # METERED: LeadMagic + Perplexity + Claude per lead
```
Run that first (Theodore approves the batch size / spend), then pull from the survivors here.
LeadMagic Stage-1 coverage on the real pool (1,000-lead test 2026-06-27): 93% company match,
85% employees, 70% founded year — enough to hard-gate CS employees≤50 + age≥3yr with
pass-on-unknown. Revenue stays a soft AI-estimated signal (16% structured coverage).

## Then
- Re-verify the pulled batch fresh (MillionVerifier) → `verify-pool`.
- Run the pre-send gate → `engine.presend.check_gate(stream, sample_body=..., copy_approved=True, icp_confirmed=True)`.
- Build the campaign → `run-campaign` (still dry-run until `CEO_DRY_RUN=false`).

## Weekly cadence
Volume ramps per the 60-day plan (Wk1 ~300 → Wk8 ~8-10k/week). Never raise volume on a
campaign showing >2% bounce. Qualified counts + recent activity show on `/marketing`.
