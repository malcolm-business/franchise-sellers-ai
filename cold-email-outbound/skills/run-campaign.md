---
name: run-campaign
description: Run one cold-email stream end-to-end (load → ICP score → suppress → verify → render → push → activate). Analysis-only unless do_push=True. In dry-run, push only logs intent.
---

# run-campaign

The main entry point. Runs a single `CampaignStream` through the full pipeline.

## Run (analysis only — default)
```bash
cd cold-email-outbound
python3 -c "from engine import pipeline; from engine.models import CampaignStream; \
print(pipeline.run_campaign(CampaignStream.SELLER_COLD_FS_NICHE, limit=500).to_dict())"
```

## Parameters
- `stream`: which `CampaignStream` (see engine/models.py)
- `limit`: max contacts to pull (default 500)
- `do_verify`: run LeadMagic→ZeroBounce verification (default True)
- `do_push`: create campaign + push leads to Instantly (default False)
- `activate`: start sending after push (default False)
- `test_offer`: A/B an alternative offer ("comparable_sales", "buyer_match", etc.)
- `require_verified`: drop unverified before send (default True)

## Go-live (per stream, after selftest passes + keys wired)
```bash
# in .env: CEO_DRY_RUN=false
python3 -c "from engine import pipeline; from engine.models import CampaignStream; \
print(pipeline.run_campaign(CampaignStream.SELLER_COLD_FS_NICHE, limit=500, \
  do_push=True, activate=True).to_dict())"
```
Live push of ≥100 leads requires `approved=True` in sending.push_leads (master CLAUDE.md rule).
