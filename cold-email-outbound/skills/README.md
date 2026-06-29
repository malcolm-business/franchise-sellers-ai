# Cold Email Engine — Skills Library

Invocable workflows that wrap `engine/`. Each skill is a documented entry point a
human (or a scheduled job) calls to run one part of the pipeline. They're thin —
the real logic lives in `engine/`. Everything respects `CEO_DRY_RUN`.

| Skill | What it does | Module(s) |
|---|---|---|
| `run-campaign` | Run one stream end-to-end (load→score→suppress→verify→render→push) | pipeline |
| `dry-run-probe` | Analysis-only probe across all 5 Phase 1 streams; review before go-live | pipeline |
| `verify-pool` | Re-verify a contact pool (MillionVerifier) | verification |
| `suppress-and-filter` | Apply the 3-layer suppression filter to a batch | suppression |
| `cold-email-strategy` | Interview → strategy doc that feeds targeting + copy | (strategy doc) |
| `generate-copy` | Render + preview copy for a stream without sending | copy_gen |
| `improve-copy` | Generate copy, self-critique vs rubric, regenerate until it passes | copy_gen |
| `classify-reply` | Classify a single reply (heuristic dry-run / Claude live) | classify |
| `route-reply` | Route a classified reply to the right destination | routing |
| `handle-webhook` | Process an Instantly webhook → event → classify → route | engagement, classify, routing |
| `campaign-report` | Per-stream performance: sent/reply/bounce/positive %, circuit-breaker | engagement |
| `mailbox-health` | (go-live) Weekly sending-domain reputation check | sending/Instantly MCP |
| `cooldown-reactivation` | Find contacts whose cooldown/re-engage date has passed → re-queue | data_layer |
| `selftest` | Run the whole engine in dry-run against real data; readiness gate | selftest |

## Running

From `cold-email-outbound/`:

```bash
# Readiness check (run this first, and before go-live)
python3 -m engine.selftest

# Dry-run probe across all 5 Phase 1 streams
python3 -c "from engine import pipeline; import json; \
  print(json.dumps({k: v.to_dict() for k,v in pipeline.run_all_phase1_probes().items()}, indent=2))"

# One stream
python3 -c "from engine import pipeline; from engine.models import CampaignStream; \
  print(pipeline.run_campaign(CampaignStream.SELLER_COLD_FS_NICHE, limit=500).to_dict())"
```

## Going live (weeks out)

1. `cp config/.env.example .env` and fill in keys
2. `python3 -m engine.selftest` → must be all-green
3. Set `CEO_DRY_RUN=false` in `.env` for ONE probe stream
4. Run that stream with `do_push=True, activate=True` on a 500-record probe
5. Watch `campaign-report` — halt if bounce >2% or unsub >5%
6. Repeat per stream as gates pass
