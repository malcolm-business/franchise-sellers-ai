# Phase 0 — Database Audit

**Audit date:** 2026-05-21
**Auditor:** Claude (via Instantly MCP + local filesystem scan)
**Status:** Initial pass complete. Clay MCP IS wired — Audiences feature is currently disabled at the workspace level, so historical Clay tables are not yet queryable. See section 4 + "Gaps" below for the unblock path.

---

## Executive summary

The "100–500K contact database" lives in **three places**, with the bulk on Theodore's local machine and a smaller working subset inside Instantly. **Realistic active pool: ~80–100K validated contacts**, with another ~50K reactivation candidates that need re-verification. That's 24+ months of Phase 1 (3K/mo) volume even without net-new sourcing.

**Brand tagging is clean** — CS and FS records are separated at the workbook + campaign-naming layer. Re-deriving brand affiliation is not required.

**The big risk:** all local masters are dated Nov 2024 (6+ months stale). Email decay typically runs 20–30% over 6 months — verifier needs to run against everything before any send.

---

## Sources found

### 1. Local masters — `C:\Users\theod\OneDrive\Desktop\FS SAVE!\` (the canonical store)

| File | Modified | Size | Records | Status |
|---|---|---|---|---|
| `Master Company Sellers Data Desktop Save 11-26-24.xlsx` | 2024-11-26 | 12 MB | ~82K across 4 sheets | Canonical CS master |
| `Master Franchise List - Desktop Saved 11-23-24.xlsx` | 2024-11-23 | 8.4 MB | ~96K across 18 sheets | Canonical FS master |
| `Zoominfo Master Export SAVE.csv` | 2024-12-05 | 28 MB | 59,939 | Raw enrichment source export — likely heavily overlapping with the CS master |
| `GPT Upload Worksheet.xlsx` | 2024-11-29 | 558 KB | 19,733 (1 sheet) | Working file — probably superseded |

**CS Master breakdown:**
- `Owner` sheet — **61,266 records** (validated CS owners, the headline pool)
- `Owner Data Non-Valid Emails` — 12,290 records (failed verifier, reactivation candidates)
- `Zor Referrals` — 4,169 records (franchisor referral targets — separate sequence, not seller cold)
- `Biz Advisors` — 4,344 records (CPAs/attorneys/wealth advisors — referral partners)

**FS Master breakdown:**
- `Franchise Only` — **16,623 records** (active franchisee pool)
- `Master Work Sheet` — **10,696 records** (current FS working pool)
- `DNU Master` — 30,870 records (Do Not Use — historical, possibly reactivatable after 12-mo cooldown)
- `Invalid Emails` — 21,894 records (failed verifier)
- `Private Only` — 947 records (non-franchise / independent — these are CS-ish, not FS)
- `Not Target Market` — 1,830 records (excluded)
- `Personal Domain Emails` — 3,701 records (gmail/yahoo personal addresses — typically excluded from B2B cold)
- Plus several smaller bookkeeping sheets (Canada Emails, .org emails, Bad Domains, Address Only, Financial Services, Competition or Consultants, Franchise Brands reference list, etc.)

**Column quality:** Both masters have NeverBounce verification status preserved per row, plus full B2B fields (name, email, company, title, phone, LinkedIn, address, industry, sub-industry). Good shape for re-import.

### 2. Instantly — the sequenced subset

**14 named lead lists:**
- `All Leads` (master pool — exact count not measured this pass)
- `FS Verified Leads`, `FS Invalid Leads`, `FS Risky Leads`, `FS General Upload List` (status-based FS lists)
- `FS Automotive`, `FS Senior Care`, `FS Food & Beverage`, `FS Multi Unit General Industry` (vertical FS lists)
- `Franchisor`, `HCAOA Private`, `HCAOA Franchise`, `FLHC Conference 2025` (event/referral lists)
- `Test List Do Not Delete`

**~35 campaigns**, brand-prefixed:
- **CS:** 9 active campaigns. Largest: `CS: Consumer Services (Weekly Auto Run)` 10,508 leads · `CS: Health, Wellness & Fitness (2-10 Emp)` 8,910 · `CS: Food & Beverage 1-50 Emp` 8,949 · `CS: Health, Wellness & Fitness (11-50 Emp)` 3,197. Plus 5 smaller and 1 weekly auto-run.
- **FS:** 9 niche-specific (FS-Automotive-1-800 Radiator 467 · FS-Senior Care-FirstLight 678 · FS-Senior Care-Comfort Keepers 679 · FS-Food & Beverage-Ben & Jerry 713 · FS-Food & Beverage-Nekter 687 · FS-Education-Code Ninja 805 · FS-Automotive-Maaco 469 · FS-Consumer-House Doctors 1) plus `Franchise Testing` 14,641 · `FS-New Franchise-Existing-NO` 1,761 · `FS-New Franchise-Existing-YES` 1,687
- **Buyer-side (not seller cold):** `Buyer: UT & CO Breweries` 373 · `Buyer: FL Wind Mitigation` 619
- **Event:** `HCAOA Blast - Franchise` 1,353 · `HCAOA Oct 25 (Event) - Franchise` 1,353 · `HCAOA Blast - Private` 145 · `HCAOA Oct 25 (Event) - Private` 145 · `FLHC Pre/Post Event 2025` ~73 · `Post MUFC 2025 - Zee` 255 · `Post MUFC 2025 - Zor` 163 · `Exit Summit Pre Event 2025` 5,131
- **Referral partner outreach:** `Biz Advisor Testing` 4,900 · `Biz Advisor Clay Foundation` (status 3, count not in summary)
- **Foundation/test:** `FS Foundation`, `New FS Foundation`, `FS Foundation 2`, `FS Foundation - No Copy`, `CS: From Clay Owner Foundation Campaign`, `Clay Import Campaign` (0 leads), `Revreply Test Campaign` (1 lead), `Test Sarik` (1 lead)

**Volume rough-sum:** Total `leads_count` across all campaigns ≈ 80–85K. **Significant overlap** between campaigns (same contact in multiple sequences) so unique-count is lower — likely 40–60K unique in Instantly. The `All Leads` list count would be authoritative but wasn't paginated this pass.

**Reply rates observed:** 0.4–3.9% across campaigns. FS niche-targeted campaigns lead (3–4%); broader CS campaigns lag (0.4–2.6%). Consistent with the 2026 cold-email baseline (~3.4%) in `cold-email-research-playbook.md`.

**Campaign status:** Several are `status 3` (paused/completed), several `status 2` (paused). None show as actively sending right now (consistent with the 6-month pause).

### 3. Downloads folder — working/staging area (NOT canonical)

90+ CSVs at `C:\Users\theod\Downloads\` from prior engine runs:
- `instantly_leads*.csv` × 8 — Instantly export dumps
- `500_PERSON*.csv`, `28_PERSON*.csv`, etc. — Apollo/Zoominfo bulk-pull batches dated Nov 25 / Dec 3 2024
- `Contacts####.csv` — sized exports
- `Neverbounce Upload Master *-Valid.csv` / `-All.csv` — verifier outputs
- `FS 11-25 TB.csv`, `CS 11-25 2.csv` — Nov 25 2024 brand-split exports
- `Franchisor Database Updated 2024.csv` — franchisor list
- `cleaned_franchise_data*.csv` — processed franchise records
- Plus dozens of analysis/classification CSVs from a prior ChatGPT-driven cleanup pass

**Treatment:** these are working files, not authoritative sources. The masters in FS SAVE! supersede everything here. Don't re-import from Downloads unless something in Downloads is uniquely newer than what's in FS SAVE! — none appears to be.

### 4. Clay workspace — MCP wired, Audiences gated (correction 2026-05-21)

**Correction to earlier claim.** Clay IS connected via MCP (`mcp__83085bbe-...`). The MCP exposes:
- **Enrichment side (working):** `find-and-enrich-company`, `find-and-enrich-contacts-at-company`, `find-and-enrich-list-of-contacts`, `add-company-data-points`, `add-contact-data-points`. These hit Clay's enrichment engine and consume Clay credits. Usable for Phase 2 net-new sourcing.
- **Query side (gated):** `query-objects`, `ask-question-about-accounts`, `get-task-context`. These read Clay Audiences. **Audiences is not enabled for this workspace**, so historical Clay tables are not yet readable via MCP. Exact error returned by `query-objects`:

> "Clay Audiences is not enabled for this workspace, so no accounts are accessible through MCP. Only a Clay workspace admin enabling Audiences will resolve this — connecting a CRM, importing data, or other remediation will not unlock these tools."

**To unlock historical Clay data via MCP:** Theodore (workspace admin) enables Audiences in Clay settings. Path: Clay app → workspace settings → Audiences → enable. Once on, all the read-side tools become functional and we can paginate the historical contacts directly without any CSV exports.

**Fallback if Audiences is not enabled:** manual CSV export from the Clay UI → drop into `cold-email-outbound/data/clay-archive/` → I parse + merge with the FS SAVE! masters.

**The only Clay artifact found locally** is `Active Contacts-Clay Table 3_ Existing Franchisee's (5).csv` on Desktop (5,156 rows, dated Jun 2025) — a single table extract, useful as a sample but not the full picture.

---

## Total estimated pool

| Bucket | Records | Notes |
|---|---|---|
| **Tier A — immediately reactivatable** (high-confidence valid as of Nov 2024) | **~88K** | CS Owner (61K) + FS Franchise Only (17K) + FS Master Work Sheet (10K). Must re-verify before send. |
| **Tier B — reactivation after re-verification** | **~50K** | CS Non-Valid Emails (12K) + FS DNU (31K) + FS Personal Domain (4K) + FS Bad Domain (1.5K) + FS Invalid (22K — only a slice will recover). Aggressive estimate. |
| **Tier C — referral partner / non-cold sequences** | **~13K** | Zor Referrals (4K) + Biz Advisors (4K) + Franchisor list (~5K from Zoominfo Master / Franchisor lists) — needs its own sequence design, not seller cold. |
| **Tier D — exclude permanently** | **~5K** | Not Target Market, Competition or Consultants, Canada (different market), .org emails (often non-business). |
| **Unique inside Instantly today** | **40–60K** (overlap) | Already touched. Most are also in the FS SAVE! masters. |

**Tier A is the Phase 1 reactivation pool. At 3K/mo, that's ~29 months of runway.**

---

## Brand split (Tier A only)

| Brand | Pool | Source |
|---|---|---|
| Company Sellers | ~61K | CS Master `Owner` sheet |
| Franchise Sellers | ~27K | FS Master `Franchise Only` + `Master Work Sheet` |
| **Total Tier A** | **~88K** | |

The 61/27 split is heavily CS-weighted — consistent with the broader Zoominfo source export (60K records, mostly small/mid-business owners).

---

## Quality gates needed before Phase 1 send

1. **Re-verify every Tier A record** through the chosen verifier (NeverBounce / MillionVerifier / ZeroBounce). Expect 20–30% loss to email decay over 6 months → realistic post-verification pool ~62–70K.
2. **Job-change detection on a sample** (e.g., top 5K by ICP score) — PDL or Datagma. Most cost-effective on Tier A's highest-scored slice.
3. **Suppress against both GHLs** before any push to Instantly. Anyone already in either CRM gets locked out per the architecture's three-layer suppression rule.
4. **De-dup across sources.** CS Owner Master + Zoominfo Export overlap heavily — need a one-pass dedup by email + LinkedIn URL before treating any count as accurate.
5. **Confirm brand assignment on edge cases.** FS `Private Only` sheet (947 records) is labeled "Private" — those are actually independent owners, possibly CS-brand fits. Same with the FS `Master Work Sheet` if any non-franchise contacts crept in.

---

## Gaps & open questions

- **Clay workspace contents.** Unknown until Clay Audiences is enabled (Theodore admin action in Clay settings). Once enabled, I can paginate the historical tables directly via MCP and merge into this audit. If Audiences is not enabled, fallback is a manual CSV export to `cold-email-outbound/data/clay-archive/`.
- **Instantly `All Leads` list count.** Not paginated this pass — paginating 60K leads at 100/page = 600 API calls. Would take 5–10 min if we want the authoritative dedup'd Instantly count.
- **Suppression baseline.** No count yet of how many of the Tier A 88K are already in either GHL workspace. Need to cross-reference against the unified `crm-snapshot` master JSON once derive_buyermgr / a new derive_coldemail-suppression script is built.
- **Bounce rate prediction.** Without re-verification, the 6-month decay rate is just an estimate. First Phase 1 batch should be a small (~500-record) probe to measure actual bounce/reply numbers before scaling to 3K/mo.
- **Personal-domain handling.** ~3,700 FS records are at personal email addresses (gmail/yahoo/etc). These are higher-reply but worse for deliverability and harder to enrich. Decision needed: include in Phase 1 or exclude?

---

## Recommended next moves (in order)

1. **Theodore — enable Clay Audiences** in Clay workspace admin settings. Once on, I can paginate historical Clay tables directly through the MCP and merge into the audit — no CSV exports needed. (Fallback if you can't enable: manual export from Clay UI.)
2. **Wire RevyOps + connectors** (Phase 0 tasks #1, #4, #5, #6) — pre-req for everything downstream.
3. **Re-verify Tier A** as the first real load test of the new orchestration. Catch the ~20–30% decay before any send.
4. **Build `derive_coldemail_suppression.py`** that reads `crm-snapshot/crm-master.json` and produces an `in_crm` flag-set. This is the GHL→RevyOps suppression sync the architecture calls for, and it satisfies the workspace rule "never add another GHL puller."
5. **Phase 1 probe** — pull 500 records from Tier A, post-verifier and post-suppression, send through one Instantly campaign with a single offer variant. Measure bounce, reply, suppression-leak rate. Iterate before scaling to 3K/mo.

---

## What this audit did not do

- Did not paginate the Instantly `All Leads` list (would take 5–10 min of API calls).
- Did not de-dup CSV/xlsx files by email across sources. The overlap estimate is heuristic, not measured.
- Did not access Clay (no MCP/API available).
- Did not check the droplet (`165.227.206.190`) for cold-email contact files — based on master CLAUDE.md, the droplet only hosts dashboard data + IFPG, no cold email artifacts. Worth a quick `ls /root/` next session for completeness.
- Did not analyze copy quality of past Instantly campaigns. Could be a separate pass — extracting subject/body patterns from past campaigns would inform the spintax-template work.
