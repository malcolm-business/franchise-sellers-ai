# RESUME — Cold Email Outbound → Multi-Channel Marketing Platform

**Newest entry on top.** Each session adds a dated block summarizing current state, decisions made, and what's next.

---

## ▶ START HERE NEXT SESSION (2026-06-28)

**🎯 GOAL: first cold-email campaign LIVE by EOD Thursday 2026-07-02.** Still 100% behind `CEO_DRY_RUN=true` — nothing has been emailed to anyone.

**Shipped today (2026-06-28) — the "experience the system + copy" layer:**
- **Interactive campaign SIMULATOR** live at `/marketing/simulator.html` (🎮 button on the dashboard + a button in the Send & monitor card). Self-contained sandbox, walks the full create → monitor → maintain lifecycle with test inputs. Nothing sends; the switch never reaches LIVE.
- **`docs/OPERATING-MODEL.md`** (what runs in Claude vs the dashboard + the weekly cadence) and **`docs/TESTING-AND-SPINTAX-SOP.md`** (how Malcolm/Theodore start a campaign with an A/B test + the read-and-update timing).
- **`docs/BROKER-COPY-PLAYBOOK.md`** — researched best-practices + swipe library + seller psychology (70+ 2026 sources), integrated into `docs/COLD-EMAIL-COPY-FOR-MALCOLM.md` and the `improve-copy` skill rubric. **#1 copy fix flagged: replace the unprovable "sold for more than they expected" line in all 3 live templates with a credibility statement (Eric's confirmed 27 years, confidentiality, our process).**
- **`docs/CLAUDE-VS-DASHBOARD.pdf`** — long-term "run it from the dashboard" vision (answer: yes, ~80% becomes one-click, a thin slice stays Claude-assisted by design).
- **Copy Preview Pack** now linked on the dashboard (③ Campaign copy) and has a "what this is / why" explainer at the top. 27-years credential confirmed in the copy guide.

**CRITICAL PATH to first live send (unchanged):**
1. Verify the 1,429 qualified with MillionVerifier (fresh re-verify).
2. Stage the first campaign in Instantly (dry-run): pull qualified+verified → build → push leads.
3. **Malcolm approves copy** (he has the preview pack + copy guide + playbook; handoff message sent 06-28).
4. Theodore flips `CEO_DRY_RUN=false` on a SMALL batch (~200-300, one brand), watch bounce<3% / unsub<2% / replies for 48h, then ramp.

**Waiting on:** Malcolm = copy review by Thursday (the #1 fix + strip em dashes + differentiate subjects). Eric = ICP form (sharpens targeting + per-segment language; NOT a blocker for the first send). Theodore = the live flip.

---

## 2026-06-27 (state snapshot)

**State:** The cold-email system is BUILT, VERIFIED end-to-end in dry-run, and the **first real qualified list is generated**. Still 100% behind `CEO_DRY_RUN=true` — nothing has been emailed to anyone. Focus is the **cold-email section only** (Theodore, getting it live the week of 2026-06-29).

**What's ready right now:**
- **Qualification funnel FINISHED + verified** (Stage 0 free filters → Stage 1 LeadMagic company lookup → Stage 2 Perplexity+Claude judge → brand/product/caps, pass-on-unknown). 1,000-lead LeadMagic test: 93% company match, 85% employees, 70% founded → LeadMagic clears the bar, no Surfe/Apollo needed.
- **First qualification batch DONE:** ~2,000 leads (1,000 CS + 1,000 FS) → 1,414 qualified in the batch; **1,429 qualified now in Neon** (815 CS-brand + 614 FS-brand). Top drops: not_current_owner 350, pe_backed 115, owner_not_us 43; Stage-1 caps caught cs_too_many_employees 23 + a few revenue/age. Pull them: `db.pull_qualified(brand, limit, min_confidence=0.5)`.
- **86 warmed lookalike cold mailboxes** ready (~2,580/day). ONLY franchisesellers.com + companysellers.com are excluded; `sending.activate_campaign()` hard-blocks (fail-closed) any campaign with a main-brand/staff mailbox attached.
- **Marketing dashboard REDESIGNED + live** at https://dashboard.franchisesellers.com/marketing — header tabs (Email Marketing | Google Ads), dark/light toggle, collapsible sections, process-ordered email tab (mock-labeled stat dashboard + 6 steps with ? help bubbles), deliverability health strip. Google Ads tab scaffolded for the DIRECT Google Ads API (`engine/google_ads.py`, pending creds from Malcolm).
- **Copy preview pack** live (`/marketing/COPY-PREVIEW-PACK.html`); health monitor cron running daily.

**CRITICAL PATH to first live send (resume here):**
1. **Verify the qualified survivors** with MillionVerifier on the 1,418 qualified leads (fresh re-verify before sending).
2. **Stage the first campaign** in Instantly (dry-run): pull qualified+verified → build campaign → push leads.
3. **Theodore flips** `CEO_DRY_RUN=false` on a SMALL batch (~200-300, one brand), watch bounce<3% / unsub<2% / replies for 48h, then ramp per the 60-day plan.

**Waiting on people:** Malcolm = copy review (guide + preview pack delivered, on GitHub) + Google Ads creds (LATER). Eric = ICP form (fillable PDF sent). Theodore = first-send go.

**Operate it (all on the droplet `/root/cold-email-outbound/`):**
- Qualify a batch: `./.venv/bin/python scripts/qualify/run_batch.py --cs N --fs N --workers 6`  ← MUST use `.venv` python (has the anthropic SDK; system python3 does NOT). ~$13-30/1k.
- Cold readiness: `./.venv/bin/python scripts/monitor/cold_readiness.py`
- LeadMagic coverage test: `./.venv/bin/python scripts/enrich/test_enrichment.py --test N --brand CS --workers 8`
- Selftest: `python3 -m engine.selftest` (dry-run, all-green).

**Logins (RBAC):** `leadership` (Eric, Theodore) → all · `david`/`malcolm` (`Franchise#1`) → all but Company Report · ops users → toolkit/buyers/full-service. Marketing dashboard = internal tier.

**Git:** branch `claude/practical-wozniak-2c8c43` PUSHED to origin (github.com/theodorebaird/fs-cs-internal-tools), 67 commits. NOT merged to master (master is 112 ahead — open a PR if you want it there). Malcolm (`malcolm-business`) is an admin collaborator.

**New docs this session:** `docs/PROCESS-FLOWCHART.pdf` (refreshed, accurate) · `docs/HEALTH-MONITOR.pdf` · `docs/ICP-REVIEW-ERIC.pdf` (fillable) · `docs/COLD-EMAIL-COPY-FOR-MALCOLM.md` · `docs/GOOGLE-ADS-API-SETUP-FOR-MALCOLM.md`.

**Engine map:** `engine/` (config, models, data_layer, db, enrichment, qualification, research, verification, scoring, suppression, copy_gen, presend, sending, engagement, classify, routing, sequences, channels/, audiences, orchestrator, pipeline, google_ads, selftest). Data layer = Neon Postgres (`engine/db.py`); flat-file fallback preserved.

---

## 2026-06-27 (big session) — Stage 1 finished, dashboard redesigned, first qualified list

A long build session that took cold email from "Stage 1 half-built" to "first qualified list in hand."

- **Stage 1 (company lookup) BUILT + tested.** New `engine/enrichment.py` (LeadMagic company-search, zero-pip, dry-run-aware, `live=` override so coverage tests run without unlocking sends). Rewired `qualification.py` to the real funnel (Stage 0 → enrich → Stage 1 employees+age+product hint → AI judge → derive); CS caps pass-on-unknown; fixed the hardcoded CS product split; added revenue-band + franchise-scale AI signals (soft). Persist firmographics on Neon (`db.py` + `migrate_to_neon.py` + `models.py`). 1,000-lead test: 93% match / 85% employees / 70% founded — LeadMagic clears the bar (test-then-evaluate rule satisfied; no Surfe/Apollo). Full funnel verified 3/3 e2e. Qualification runs with the **`.venv` python** (anthropic).
- **First qualification batch:** 1,000 CS + 1,000 FS → **1,414 qualified** (1,429 total in Neon: 815 CS-brand / 614 FS-brand).
- **Marketing dashboard redesign** (tabs, dark/light, collapsible sections, process-ordered email tab, mock stat dashboard, deliverability strip). `engine/google_ads.py` direct-API connector built (pending creds). Ads tab shows honest "not connected" state.
- **Cold-sending safety:** hard-block at `activate_campaign` (fail-closed) so cold never sends from franchisesellers.com / companysellers.com / staff inboxes. Per Theodore, ONLY those two domains excluded; 86 lookalike mailboxes cold-ready (~2,580/day).
- **Deliverables:** refreshed process flowchart PDF, health-monitor explainer PDF, fillable ICP PDF for Eric (sent), copywriting guide + Google Ads setup guide for Malcolm (pushed to GitHub).
- **Decisions:** DB stays LeadMagic for Stage 1 (test proved it); keep all lookalike domains incl. thecompanysellers.com/companysellers.co for cold; first batch = 1,000 each brand; Google Ads = direct API (Malcolm sets up, later).

---

## 2026-06-07 (session end) — Platform deployed + RBAC + landing card

Closed out the platform pivot with full production deployment:
- **Marketing dashboard deployed** to https://dashboard.franchisesellers.com/marketing (nginx `^~` location + basic auth + no-cache; files in `/var/www/dashboard/marketing/`). Verified live.
- **Full RBAC rollout** across ALL dashboards — 3 tiers (`.htpasswd-leadership` / `-internal` / `-ops`), Theodore's access matrix enforced, existing shared logins preserved (no lockouts). Caught + fixed a 500 (cp dropped www-data group on htpasswd files). Every user×dashboard curl-verified.
- **Landing hub** now has the Marketing Platform card (6 cards total). Caught + handled local/prod drift (prod had buyer-manager+sales cards not in git; pulled live first to avoid reverting).
- **HeyReach key wired** → LinkedIn channel now live. Ads shows a setup note for Malcolm on the dashboard.
- Deploy safety throughout: backups to `/root/nginx-backups/`, `nginx -t` + rollback guards, exhaustive verification.

---

## 2026-06-07 (latest) — PIVOT: cold-email engine → multi-channel marketing PLATFORM

Theodore expanded the vision: not a cold-email tool, a **professional multi-channel
marketing platform**. Identify a prospect once → run them through ONE personalized
sequence spanning email + LinkedIn + online ads + (later) postcards, all coordinated
+ suppression-aware. Deliverable: a system handed to **Malcolm** (new marketing hire)
that's built + ready — he sets up copy, picks audiences, runs campaigns.

**All keys now wired** (found + pulled, incl. from the droplet):
- LeadMagic + ZeroBounce (live-tested), GHL FS+CS, **Instantly + Anthropic (pulled from droplet `/root/crm-reporting/.env` over SSH)**. All 8 in the gitignored `.env`.
- Instantly + Anthropic were never in local folders — they live on the droplet (dashboard-api reads them there). Local mirror is stale (missing 7 keys).
- ⚠️ Rotate-keys reminder stands (several leaked into transcripts over time).

**Platform built (all dry-run-gated, CEO_DRY_RUN=true):**
- `engine/sequences.py` — Channel enum + Touch/Sequence models + default multi-channel sequence library (e.g. fs_niche = ads d0 → email d1 → LI connect d2 → email d5 → LI msg d7 → email d11).
- `engine/channels/` — BaseChannel ABC + registry + 4 channels: **email** (Instantly, live), **linkedin** (HeyReach REST, needs HEYREACH_API_KEY), **ads** (Google Customer Match + Meta Custom Audiences, SHA-256 hashed, needs ad-account access), **postcard** (Lob/PostGrid stub).
- `engine/audiences.py` — segment builder (filter pool by brand/tier/industry/system/geo/ICP/reachability; preview counts; save re-runnable JSON specs).
- `engine/orchestrator.py` — `run_multichannel_campaign()`: cross-channel suppression ONCE (one unsub kills all channels), verify, bulk-enroll ads+LinkedIn, dispatch every touch to the right channel. Verified: 2000-contact CS segment → 1681 deliverable → 8076 coordinated touches across ads/email/LinkedIn.
- `engine/channels/` all register; email live, others available=False until keys.

**Malcolm's dashboard** — `cold-email-outbound/dashboard/` → deploys to **dashboard.franchisesellers.com/marketing**:
- `index.html` operator UI (pool tiles, channel status, audiences, sequence plans, offers, how-to; auto-refresh; read-only v1).
- `snapshot.py` → aggregate `marketing-snapshot.json` (no PII).
- `deploy/README-deploy.md` runbook (nginx /marketing + basic auth + cron).
- **Login created on droplet:** user `malcolm`, htpasswd at `/etc/nginx/.htpasswd-marketing` (password NOT in git).
- ⚠️ **NOT yet deployed to production nginx** — the /marketing location block + file copy + reload is a deliberate approved step (see runbook). Login + files are ready.

**Channel key status:** email ✅ live · LinkedIn ⬜ needs HEYREACH_API_KEY · ads ⬜ needs Google/Meta ad-account API access · postcard ⬜ vendor TBD.

**What's next:**
- Deploy the /marketing dashboard to production (approved step, runbook ready)
- Malcolm: copy + audiences + run campaigns
- Wire HeyReach key (LinkedIn live) + Google/Meta ad access (ads live)
- Data note: CS pool lacks state/geo data — LeadMagic enrichment fills it during verify over time.

---

## 2026-06-07 (late) — Go-live prep: keys wired, verification LIVE-tested, copy pack ready

Post-build polish + first live integration, all after the engine was built.

**API keys wired into `.env` (gitignored):**
- LeadMagic `lm_live_...9479` ✅ live-tested
- ZeroBounce `3b56fd...90ce` ✅ live-tested
- Still pending: Instantly, both GHL (location+token), Anthropic
- `config._load_dotenv()` added so `.env` loads with no pip dependency.
- ⚠️ Both keys are in the chat transcript in plaintext — rotate after go-live if the transcript could be seen by others.

**Verification stack LIVE-TESTED (first real external calls):**
- 20-contact CS batch through the real LeadMagic→ZeroBounce waterfall.
- Waterfall confirmed: LeadMagic ran on all 20, ZeroBounce on only the 2 uncertain ones (the cost-optimal `uncertain_only` mode working as designed).
- Result: 9/20 deliverable (45%) on an auto-heavy CS sample. Real list decay — VALIDATES mandatory re-verify (would've been ~55% bounce without it). Small sample; expect ~60-75% on the full pool.
- Bug fixed: LeadMagic returns `email_status` (not `status`) — normalizer corrected + live-verified.
- Bonus: LeadMagic returns company industry/size/founded/LinkedIn = free enrichment to capture later.
- Engine confirmed back in DRY_RUN after the test (per-process env override; `.env` unchanged).

**Polish completed:**
- Real-estate franchises EXCLUDED (Theodore's call): 935 FS records (HomeVestors 604, EXIT Realty 170, RE/MAX, Keller Williams, Weichert…) now score 10, never sequenced.
- buyer_reactivation CORRECTED to deferred: Theodore confirmed buyers always lived in the GHL CRM, never the cold archive → no cold source. Removed from active Phase 1 streams.
- 16,585 ambiguous-brand records disambiguated → effective Tier A: FS ~10,600 (post-RE-exclusion) / CS ~176K.
- Copy polish: FS niche "a"→"another" (grammar + social proof); advisor template spintax 23%→96% variation.
- Clay decision reversed: keep account, defer drop/keep to Phase 2.

**Copy preview pack generated:** `data/runtime/COPY-PREVIEW-PACK.md` (gitignored — real names/companies). Every active stream's full sequence rendered against real contacts. **Theodore to review + approve copy.** Regenerate via `scripts/generate_copy_pack.py`.

**Active Phase 1 streams (4):** seller_cold_fs_niche, seller_cold_fs_broad, seller_cold_cs, referral_partner_advisor (+ event_pre/post when an event is scheduled).

**Remaining for go-live:** review/approve copy pack · wire Instantly + GHL + Anthropic keys · confirm cooldowns (60d/12mo) · then flip `CEO_DRY_RUN=false` on one probe → first real send.

---

## 2026-06-07 — Dedup complete + ENTIRE ENGINE BUILT (dry-run, ready to flip on)

Two big milestones this session.

### 1. Full dedup + Tier A audit (Phase 0 task #3 DONE)
- Deduped **1.31M raw rows → 405,693 canonical records** across 42 files (Clay + Airtable + Dropbox + FS SAVE!). 69% dedup rate. No data lost (safety contract enforced; suppression is a flag, not a delete).
- **Tier A sendable pool: 187,490** (CS 160,699 · FS 10,206 · Ambiguous 16,585). At 3K/mo that's ~5 years runway — no net-new sourcing needed for Phase 1.
- Tier B (re-verify candidates) 155,498 · Tier C (referral partners) 5,774 · Tier D (suppression) 56,931.
- **KEY CORRECTION:** the 172K-row "DNU Master Data TB.xlsx" was NOT a suppression list — it's a workflow/verification-queue archive (~100% overlap with active sources). Removing it from suppression jumped FS Tier A from 126 → 10,206. See `data/dedup-output/DEDUP-REPORT.md`.
- Tier A profile in `data/dedup-output/TIER-A-PROFILE.md`: CS is the powerhouse (70% Clay-enriched); FS is fragmented across long-tail systems (senior care is the biggest cluster ~600).
- Scripts: `scripts/dedup/run_dedup.py` + `scripts/dedup/profile_tier_a.py` (reproducible).

### 2. The entire engine — built dry-run-first
Per Theodore's directive ("build the whole system so we're ready in a few weeks, no sending/verifying yet"), the full engine is constructed and **passes selftest in dry-run against real data.** Going live = flip `CEO_DRY_RUN=false` + wire `.env`, not a build.

- **14 engine modules** in `engine/`: config, models, data_layer, scoring, suppression, copy_gen, verification, sending, engagement, classify, routing, pipeline, selftest.
- **8 stream templates** in `templates/` (from retrospective winners).
- **4 config files** in `config/` (JSON, no yaml dep) + `.env.example`.
- **12 skills** in `skills/` (invocable workflows wrapping the engine).
- Zero pip dependencies (urllib + stdlib; `anthropic` lazy-imported only when live).
- Every external API touchpoint gated by `config.DRY_RUN` (default true). 2,347 would-be calls logged in dry-run, zero made.
- `python3 -m engine.selftest` → **ALL GREEN.**

### Decisions logged (05-decisions-log.md, 2026-06-07)
- **Email verification: LeadMagic primary → ZeroBounce fallback** (both accounts exist; LeadMagic also finds emails). Closes the "confirm verifier" open decision.
- **Data layer: NOT Airtable** as permanent SoR (de-prioritized); RevyOps if/when needed. Phase 1 runs on flat files (dedup output + runtime logs).

### What's next (go-live prep — all in BUILD-PLAN.md)
- Theodore: wire API keys into `.env`, confirm cooldowns (60d/12mo)
- Polish before send: disambiguate 16,585 ambiguous-brand; build a buyer-flagged source (buyer_reactivation currently uses Tier A placeholder); add spintax to referral_partner_advisor (23% variation); fix "a/an [system]" grammar in fs_niche or use curated system lists; FS pool composition gut-check (HomeVestors/EXIT Realty fit?)
- Then: flip `CEO_DRY_RUN=false` on one probe → first real send → watch campaign-report

**Engine is feature-complete. The next session is go-live prep + polish, not core building.**

---

## 2026-05-21 (end of day) — Database archive captured across all sources

**Massive progress on Phase 0 task #3.** Final session activity:

**Decision reaffirmed:** Drop Clay. Audiences feature is gated to Clay's Enterprise plan tier — not worth the upgrade for a tool being decommissioned. Manual CSV export was the path. See updated entry in `05-decisions-log.md`.

**Clay archive complete:** 28 files, ~414K rows across both Clay folders (Company Sellers + Franchise Sellers). Located in `data/clay-archive/cs/` and `data/clay-archive/fs/`. PII gitignored. Catalog in `data/clay-archive/INVENTORY.md`.

**Surprise find — `FS_-Franchisee-(Block-List)` (22,425 rows × 30 cols)** — pre-built do-not-contact list of franchisees. Drops straight into the suppression layer. Theodore had this and didn't realize it was a critical asset.

**Airtable archive complete:** 6 tables, 140,075 rows. Located in `data/airtable-archive/`. PII gitignored. Catalog in `data/airtable-archive/INVENTORY.md`.

**Dropbox archive complete:** 80+ files across `data/dropbox-archive/cs/` and `data/dropbox-archive/fs/`. Theodore flagged upfront that most isn't cold-email relevant. Triage in `data/dropbox-archive/INVENTORY.md` classified into 3 tiers. **4 Tier-1 finds** worth merging:
- `DNU Master Data TB.xlsx` — **172,489-row historical suppression list**. Massive find. Critical for the 3-layer suppression architecture.
- `Master Franchise List.xlsx` — 188,327 rows × 21 sheets. Likely newer/more-complete version of FS SAVE!'s master.
- `Zoominfo FS Master List.xlsx` — 64,351 net-new FS enrichment.
- `MUFC 2025.xlsx` — 4,587 current-year franchise conference attendees.

**Updated suppression picture:** gross suppression input is now ~250K rows across Clay Block List + DNU + Airtable Archived + Pipedrive 2022 + SMS Blast data. After dedup the actual reactivation pool will be substantially smaller than the headline 660K total.

**Important PII note:** the 2026-05-21 commit `1a78678` accidentally tracked 7 non-CSV files (a 242KB .xls of conference attendees + Outlook .msg + PDFs + folder notes.txt) before the gitignore was tightened. Fixed in `86d1bd0`. **The PII is still in git history at `1a78678`.** Acceptable for a private repo; if the repo is ever made public, history rewriting (git filter-repo) is required.

**🚨 New strategic question raised by Airtable contents — Airtable vs. RevyOps.** Airtable's `Active Contacts` table is already cross-referencing Clay, Instantly, and Pipedrive (columns like `Master Email (Work & Personal) - Clay`, `Instantly Lookup Status`, `Email Campaign Lead Status - Instantly`, `Pipedrive Lookup - Clay`). Structurally, Airtable is already serving the data-layer role that RevyOps was supposed to take. Three options to consider:
1. Keep Airtable, skip RevyOps, build orchestration around Airtable
2. Migrate Airtable → RevyOps as originally planned (decommission Airtable)
3. Two layers: Airtable for CRM-like seller state + RevyOps for cold-email pipeline state

**No decision made yet — this needs a real conversation in the next session.**

**Total data layer now:** ~660K rows across Clay + Airtable + FS SAVE! local masters + the prior 88K Tier A estimate. Realistic unique-contact pool post-dedup is probably 200–250K, but that's a guess until the dedup actually runs.

**Architecture finding:** the original audit estimate of "100–500K" was conservative. We're at the upper end. Phase 1's 3K/mo target = many years of runway from existing pools alone, no net-new sourcing needed.

**Tasks queued for next session (priority order):**

1. **Decide the Airtable vs. RevyOps question.** Affects everything downstream — particularly how the dedup output is structured.
2. **Run the dedup + Tier A audit.** ~60–90 min of code work. Reads all 37 source files (28 Clay + 6 Airtable + 3 FS SAVE!), dedupes by email + LinkedIn URL, applies suppression (Franchisee Block List + Airtable Archived Contacts), and produces the final Tier A reactivation pool count + brand-tagged segments. Output goes into `PHASE-0-DATABASE-AUDIT.md`.
3. **Update audit doc with real numbers** (replaces the heuristic 88K Tier A estimate from the initial pass).
4. **Spintax template + signal-anchor library v1** — parallel design work, no external dependencies.
5. **Resolve the 4 Notion discrepancies** still flagged in `notion-reference/00-source-notes.md`.

**External actions still pending on Theodore:**
- Create RevyOps account (only if option 2 or 3 is chosen above)
- Confirm email verification provider (NeverBounce / MillionVerifier / ZeroBounce)
- Locate API keys: Instantly, both GHL workspaces, verifier, Apollo (if any)

**Open Clay-cancellation status:** archive is captured, BUT do not cancel Clay until the dedup confirms the archive is usable. Once the audit confirms it, Clay can be cancelled safely. Estimated savings: $349–799/mo.

---

## 2026-05-21 (mid-day) — Phase 0 task #3 (database audit) initial pass complete

**What happened.** Probed Instantly via MCP + searched local disk for the existing 100–500K contact pool. Full findings in `PHASE-0-DATABASE-AUDIT.md`.

**Headline numbers.**
- **Tier A reactivation pool: ~88K** validated contacts (61K CS Owners + 27K FS franchisees). At Phase 1's 3K/mo, that's ~29 months of runway even without net-new sourcing.
- **Tier B reactivation candidates: ~50K** invalid/DNU/bad-domain records that may recover with re-verification.
- **Tier C referral partners: ~13K** (Zor referrals 4K + Biz Advisors 4K + Franchisor lists ~5K) — needs its own sequence, not seller cold.
- Brand tagging is clean — CS and FS records are separated at the workbook + Instantly campaign-naming layer. No re-derivation needed.

**Where the data lives.**
1. **Local (canonical)** — `C:\Users\theod\OneDrive\Desktop\FS SAVE!\` holds the CS Master xlsx (82K records, 4 sheets), FS Master xlsx (96K records, 18 sheets), and Zoominfo Master Export CSV (60K records).
2. **Instantly** — 14 named lead lists + ~35 campaigns. ~80K leads_count summed across campaigns (heavy overlap → 40–60K unique). Past reply rates 0.4–3.9%; FS niche-targeted campaigns lead at 3–4%.
3. **Downloads folder** — 90+ working CSVs from prior engine runs. NOT canonical, superseded by FS SAVE! masters.
4. **Clay** — MCP IS wired (`mcp__83085bbe-...`). Enrichment side works (useful for Phase 2 net-new sourcing). Query side ("Clay Audiences") is **disabled at the workspace level** — needs Theodore to enable Audiences in Clay admin settings to unlock the historical tables via MCP. Fallback: manual CSV export from Clay UI.

**Big risk.** All local masters are Nov 2024 (6+ months stale). Expect 20–30% email decay → realistic post-verification Tier A pool ~62–70K. Re-verifier must run before any send.

**What's still outstanding on task #3.**
- Clay workspace export (Theodore action item)
- Instantly `All Leads` list — paginate to get authoritative dedup'd count (~5–10 min of API calls)
- Cross-source dedup pass (CS Owner Master + Zoominfo Export overlap heavily)
- Cross-reference Tier A against current GHL state to estimate `in_crm` suppression overlap

**What to do next session.**
- Either: Theodore enables Clay Audiences in Clay admin settings → I paginate Clay tables via MCP and extend the audit
- Or: move to the next critical-path Phase 0 task (RevyOps signup → connector wiring) if Theodore has unblocked them
- Or: start the spintax template + signal-anchor library design work in parallel — no external dependencies

---

## 2026-05-21 — Transferred from Claude COWORK into Claude CODE

**What happened.** Project moved out of `Claude COWORK/Cold Email Outbound/` and into this folder (`Claude CODE/cold-email-outbound/`) so it lives alongside the other active engineering projects (`dashboard-*`, `crm-snapshot`, `IFPG Resales`, etc.). Cowork copy left intact as a backup.

**No content changed** in this transfer — all 9 working docs + the 10 notion-reference files are byte-for-byte the same. Last meaningful content update was 2026-05-03 in the cowork workspace.

**Where we are.**

- **Phase 0 — Foundation.** Workspace setup is the only task that's even partially complete. All other Phase 0 tasks still pending.
- **Decisions locked:** hybrid architecture (1 Instantly, 1 RevyOps, 2 GHLs, Claude Code orchestration), OOV as baseline + 7-offer portfolio for sequential A/B testing, 3-layer suppression (RevyOps SoT → pre-send filter → Instantly global block list), volume ramp 3K → 6K → 10K+/mo, 60-day no-reply cooldown, 12-month closed-lost cooldown. See `05-decisions-log.md` for full reasoning.
- **Critical path next:**
  1. Theodore creates RevyOps account (task #1)
  2. Claude Code orientation session (task #2)
  3. Audit the 100–500K contact DB (task #3) — runs in parallel
  4. Wire connectors (Instantly #4, both GHLs #5, RevyOps #6)
  5. Reconnect verifier (#8)
  6. Build suppression infrastructure (#11)

**Open discrepancies needing Theodore's resolution** (flagged in `notion-reference/00-source-notes.md`):
1. Full Service pricing — does the $1,000 onboarding fee still apply on top of 8% / $20K minimum, or is the $20K minimum the replacement?
2. Toolkit pricing — multi-location tier ($3,500 first / $2,500 each additional / $750 3-mo extension) is in synthesized doc but the Reply Handling SOP in Notion still shows old single-fee version.
3. Brand-age framing — old Notion script credits brand with "25 years," but reality is brands are 5–10 years old and the 27 years belongs to Eric Payne. Cold copy must credit experience to "our broker president," not the brand.
4. Xponential / FitnessTogether — special franchisor pricing exists. If those franchisees land in a cold campaign, need exclusion segment or special spintax variant.

**Theodore's open action items** (do on your own time):
- Sign up for RevyOps (account only — we configure together)
- Confirm the existing email verification provider (MillionVerifier? NeverBounce? ZeroBounce?) and that the account is still active
- Locate API keys for: Instantly, both GHL workspaces, verifier, existing Apollo account if any

**Open decisions still to settle in Phase 0:**
- Final no-reply cooldown (proposed default: 60 days)
- Final closed-lost cooldown (proposed default: 12 months)
- Secondary enrichment provider (PDL vs. Datagma vs. other)
- LinkedIn outreach tooling (defer to Phase 3)

**What to do next session:**
- Pick up the critical path item that Theodore has unblocked (most likely #1 RevyOps + #2 Claude Code orientation)
- If neither of those is ready, work on #3 (database audit) since it doesn't depend on RevyOps
- If still not ready, draft the spintax template structure + signal-anchor pattern library so it's ready when sourcing comes online
