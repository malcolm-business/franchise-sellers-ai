# Build Plan — Cold Email Engine

**Goal:** Build the entire system now so it's ready to flip on in a few weeks. **No live verification, sending, or credit spend until `DRY_RUN=false` + keys wired.**

**Principle:** Every external-API touchpoint is dry-run-gated. Logic is complete + tested against real data. Going live = config flip, not a build.

Status legend: ⬜ not started · 🔨 in progress · ✅ done · 🔑 needs API key to go live (built dry-run)

---

## Foundation (no API, pure logic)

| Module | Purpose | Status |
|---|---|---|
| `engine/config.py` | Paths, brands, rate limits, cooldowns, ICP threshold, DRY_RUN flag, env-key loading | ✅ |
| `engine/models.py` | Canonical record schema, campaign-type enum, reply-category enum, send-status enum | ✅ |
| `engine/data_layer.py` | Flat-file read/write — canonical-master + per-campaign send logs + suppression state | ✅ |

## Logic layers (no API, pure logic)

| Module | Purpose | Status |
|---|---|---|
| `engine/scoring.py` | ICP 0–100 scoring (40% demo/tenure, 40% behavioral, 20% firmographic) | ✅ |
| `engine/suppression.py` | Layer A pre-send filter — 5-source union + cooldowns + bounce/unsub | ✅ |
| `engine/copy_gen.py` | Spintax expansion + signal-anchor slotting + offer rotation | ✅ |
| `templates/*.md` | 8 stream templates (hand-written from retrospective winners) | ✅ |

## API layers (built dry-run, 🔑 to go live)

| Module | Purpose | Status |
|---|---|---|
| `engine/verification.py` | LeadMagic primary → ZeroBounce fallback. Credit tracking. Dry-run returns simulated results. | ✅ 🔑 |
| `engine/sending.py` | Instantly push (campaign create + lead add). Dry-run logs intended sends. | ✅ 🔑 |
| `engine/engagement.py` | Instantly webhook handler / poll → writes events to data layer. | ✅ 🔑 |
| `engine/classify.py` | Reply classification via Claude API → 11 categories + entity extraction. Dry-run uses keyword heuristic. | ✅ 🔑 |
| `engine/routing.py` | CRM routing — brand-tagged to GHL FS/CS, buyer→Yvonne, referral→nurture. Dry-run logs intended routes. | ✅ 🔑 |

## Orchestration + config

| Item | Purpose | Status |
|---|---|---|
| `engine/pipeline.py` | End-to-end orchestrator — wires all layers into a campaign run | ✅ |
| `config/campaign-streams.yaml` | 8 stream definitions (audience, list source, template, routing) | ✅ |
| `config/icp-scoring.yaml` | Tunable scoring weights + signal definitions | ✅ |
| `config/suppression-rules.yaml` | Cooldowns, suppression sources, bounce thresholds | ✅ |
| `config/.env.example` | API-key template (LeadMagic, ZeroBounce, Instantly, GHL x2, Anthropic) | ✅ |
| `skills/*.md` | 12 Claude Code skills (invocable workflows) | ✅ |

## Verification / readiness checks (before go-live)

| Check | Status |
|---|---|
| `python -m engine.selftest` runs all modules in dry-run against real Tier A data | ✅ ALL GREEN |
| First dry-run probe across 5 streams (no send) → review output | ✅ (selftest covers this) |
| Disambiguate 16,585 ambiguous-brand records | ⬜ |
| FS pool composition gut-check (HomeVestors/EXIT Realty fit?) | ⬜ |
| Build buyer-flagged source (buyer_reactivation uses Tier A placeholder) | ⬜ |
| Add spintax to referral_partner_advisor (23% variation, below 50% floor) | ⬜ |
| Fix "a/an [system]" grammar in seller_cold_fs_niche (or use curated system lists) | ⬜ |
| Theodore: wire API keys into `.env` | ⬜ 🔑 |
| Theodore: confirm cooldowns (60d / 12mo) | ⬜ |
| Flip `CEO_DRY_RUN=false` on one small probe → first real send | ⬜ 🔑 |

---

## ✅ BUILD COMPLETE (2026-06-07)

The entire engine is built and passes selftest in dry-run against real data.
14 engine modules + 8 templates + 4 config files + 12 skills. Zero pip
dependencies (urllib + stdlib; anthropic lazy-imported when live). Every
external touchpoint dry-run-gated.

**Going live is now a config flip, not a build:**
1. `cp config/.env.example .env`, fill keys, set `CEO_DRY_RUN=false`
2. `python3 -m engine.selftest` (must stay green)
3. Run one stream probe with `do_push=True, activate=True`
4. Watch `campaign-report`; halt if bounce >2%

Remaining items above are polish/go-live prep, not core build.

---

## Go-live checklist (the "flip on" moment, weeks out)

1. Wire API keys into `cold-email-outbound/.env` (from `.env.example`)
2. Run `python -m engine.selftest` — confirm all green in dry-run
3. Run LeadMagic re-verification on one stream's 500-record probe
4. Review verified pool + bounce projection
5. Generate copy for the probe → human review
6. Flip `DRY_RUN=false` → push probe to Instantly
7. Monitor: bounce <2%, classify replies, route positives
8. If gates pass → scale that stream; repeat per stream
