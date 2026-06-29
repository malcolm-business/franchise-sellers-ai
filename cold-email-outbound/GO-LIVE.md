# Go-Live Runbook — Cold Email Engine

The exact, ordered steps to take the engine from dry-run to sending. Follow top to
bottom. Nothing here sends until **Step 6**. Stop at any gate that fails.

**Current state:** engine built + selftest green; LeadMagic + ZeroBounce keys wired
and live-tested; everything else in dry-run (`CEO_DRY_RUN=true`).

---

## Pre-flight (do once, in order)

### 1. Confirm remaining API keys are in `.env`
Edit `cold-email-outbound/.env` (gitignored). Needed before first send:

| Key | Gates | Have it? |
|---|---|---|
| `LEADMAGIC_API_KEY` | verification + enrichment | ✅ wired + tested |
| `ZEROBOUNCE_API_KEY` | verification final-stop | ✅ wired + tested |
| `INSTANTLY_API_KEY` | sending | ⬜ |
| `GHL_FS_LOCATION_ID` + `GHL_FS_TOKEN` | FS reply routing | ⬜ |
| `GHL_CS_LOCATION_ID` + `GHL_CS_TOKEN` | CS reply routing | ⬜ |
| `ANTHROPIC_API_KEY` | live reply classification | ⬜ (heuristic works without) |

> You only need Instantly to start sending. GHL + Anthropic can be wired before the
> first replies arrive (a few days into the sequence).

### 2. Confirm settings
- Cooldowns in `config/suppression-rules.json`: 60-day no-reply, 12-month closed-lost. Change if desired.
- Sending caps in `engine/config.py` `SENDING`: 30 cold/mailbox/day, open+click tracking OFF. (Leave as-is.)

### 3. Review + approve the copy
```bash
cd cold-email-outbound
python3 scripts/generate_copy_pack.py
# open data/runtime/COPY-PREVIEW-PACK.md, read every stream, edit templates/ as needed
```
Templates are plain markdown in `templates/`. Re-run the pack after edits.

### 4. Green selftest (dry-run)
```bash
python3 -m engine.selftest      # must print ✅ SELFTEST PASSED
```

### 5. Verify a real probe batch (spends LeadMagic credits, NOT sending yet)
Pick the first stream (suggest `seller_cold_cs` — biggest pool — or `seller_cold_fs_niche`
with a curated franchise-system list). Verify ~500 contacts:
```bash
# still CEO_DRY_RUN=true in .env; this script overrides per-process for verification only
CEO_DRY_RUN=false python3 scripts/verify_live_test.py batch 500
```
**Gate:** if deliverable rate is reasonable (>50%) and the dead ones are genuinely bad
emails, proceed. If bounce risk looks high, the list is too stale — re-source or pick a
fresher segment.

---

## Send (the flip)

### 6. Flip the switch on ONE stream
1. In `.env`: set `CEO_DRY_RUN=false`
2. Run one stream as a real campaign:
```bash
python3 -c "from engine import pipeline; from engine.models import CampaignStream; \
print(pipeline.run_campaign(CampaignStream.SELLER_COLD_CS, limit=500, \
  do_verify=True, do_push=True, activate=True).to_dict())"
```
- This verifies (LeadMagic→ZeroBounce), suppresses, renders, pushes to Instantly, activates.
- A live push of ≥100 leads requires `approved=True` in `sending.push_leads` — add it once you've eyeballed the batch.
3. **Immediately set `CEO_DRY_RUN=true` again** until you're ready for the next stream. (Keeps everything else inert.)

### 7. Wire reply handling (within a day or two of sending)
- Point an Instantly webhook at an endpoint that calls `engagement.handle_webhook(payload)`.
- Or run `engagement.poll_events()` on a schedule as the catch-up path.
- Wire `ANTHROPIC_API_KEY` for live classification (heuristic runs without it).
- Wire both GHL tokens so positive replies route to the right workspace.

---

## Monitor (daily while a campaign runs)

```bash
python3 -c "from engine import engagement; print(engagement.circuit_breaker_check('seller_cold_cs'))"
```

| Metric | Good | HALT |
|---|---|---|
| Bounce rate | < 2% | ≥ 5% → stop, re-verify the list |
| Unsub rate | < 2% | ≥ 5% → stop, re-check copy/targeting |
| Positive reply % | hit the stream's target (config/campaign-streams.json) | far below → iterate copy |

Per-stream positive-% targets: FS niche 6% · CS 3% · advisor 4% · event 8%.

---

## Scale (after a stream clears its gates)

1. Raise that stream's volume toward the monthly target (3K → 6K → 10K+ across all streams).
2. Bring the next stream online (repeat Steps 5–6).
3. Run `scripts/dedup/run_dedup.py` again if you add new source data.
4. `cooldown-reactivation` (skill) weekly to re-queue contacts whose cooldown lifted.

---

## Rollback / panic

- Set `CEO_DRY_RUN=true` in `.env` — instantly stops all external calls on the next run.
- In Instantly directly: pause the campaign.
- A halted stream's contacts keep their state; fix the issue and re-run.

---

## Phase 2 (later — net-new sourcing)

When the existing pool runs low (years out at 3K/mo): wire Apollo for sourcing, decide
Clay-keep-vs-rebuild, add PDL for deep enrichment + job-change signals. See SYSTEM-DESIGN.md.
