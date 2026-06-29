# Cold Email Outbound → Multi-Channel Marketing Platform

A Claude Code-orchestrated **multi-channel marketing platform** for **Franchise Sellers** and **Company Sellers**. Identify a prospect once, then run them through one personalized sequence that spans **email · LinkedIn · online ads · (later) postcards** — coordinated, suppression-aware, measured. Output: targeted, qualified seller-side conversations into the GHL CRMs.

> Started as a cold-email engine (the original docs `00`–`06` + research playbook reflect that origin); expanded into the full multi-channel platform. The cold-email engine is Channel #1.

## Start here
1. **`RESUME.md`** — current state + "start here next session" (read this first).
2. **`SYSTEM-DESIGN.md`** + **`system-flowchart.html`** — the architecture (open the HTML in a browser).
3. **`GO-LIVE.md`** — the exact steps to flip from dry-run to sending.

## What's built (all dry-run-gated until `CEO_DRY_RUN=false`)
- **`engine/`** — the platform: config, models, data_layer, ICP scoring, 3-layer suppression, copy_gen (spintax + signal anchoring), verification (LeadMagic→ZeroBounce), sending (Instantly), engagement, reply classification (Claude API), CRM routing, multi-channel sequences, `channels/` (email/linkedin/ads/postcard), audiences (segment builder), orchestrator, pipeline, selftest.
- **`templates/`** — 8 stream copy templates (from the historical retrospective's winners).
- **`config/`** — streams, scoring, suppression (JSON) + `.env.example`.
- **`skills/`** — 12 invocable operator workflows.
- **`dashboard/`** — Malcolm's operator UI (deploys to `/marketing`) + snapshot generator + deploy runbook.
- **`data/`** — the deduped prospect pool (PII gitignored): `dedup-output/` (187K Tier A), `clay-archive/`, `airtable-archive/`, `dropbox-archive/`. Catalogs (`INVENTORY.md`, `DEDUP-REPORT.md`, `TIER-A-PROFILE.md`) are committed; raw CSVs are not.
- **`scripts/`** — dedup, profiling, disambiguation, copy-pack + verification-test tools.

## Run
```bash
cd cold-email-outbound
python3 -m engine.selftest                      # confirm everything green (dry-run)
python3 dashboard/snapshot.py                   # refresh the dashboard data
python3 scripts/generate_copy_pack.py           # regenerate the copy preview (HTML+MD)
```

## Live
- Landing hub: https://dashboard.franchisesellers.com/
- Marketing dashboard: https://dashboard.franchisesellers.com/marketing (logins in RESUME.md)

## Channels
| Channel | Status |
|---|---|
| Email (Instantly) | ✅ live (verification live-tested) |
| LinkedIn (HeyReach) | ✅ live |
| Ads (Google Customer Match + Meta Custom Audiences) | ⬜ interface ready — Malcolm wires ad-account access |
| Postcards (Lob/PostGrid) | 🔜 stubbed |

**Master safety switch:** `CEO_DRY_RUN` in `.env` (default `true`). Nothing verifies/sends/spends until flipped.

Last updated: 2026-06-07
