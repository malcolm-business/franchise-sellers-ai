# Dropbox Archive — Inventory

Captured: 2026-05-21. **PII — files are gitignored.**

Theodore flagged upfront that much of this is not cold-email relevant. Triage below.

## Tier 1 — High-value keepers (merge into dedup pass)

| File | Rows | Brand | Role |
|---|---:|:---:|---|
| `fs/Archived Contact Data - SAVE/DNU Master Data TB.xlsx` | 172,489 | MIXED | ⚠ **Correction 2026-06-07:** initially classified as suppression. Investigation showed it's a workflow tracking archive — "Master List" sheet (98,931 rows) has "Research Completed" categorizations (e.g., "Canadian Email List"), "Neverbounce Upload" sheet (73,558 rows) is a verification queue. ~100% of records also appear in active sources. **Treat as regular contact archive, not suppression.** |
| `fs/Data for Email Marketing/Master Franchise List.xlsx` | 188,327 (21 sheets) | FS | Newer / more complete version of FS SAVE!'s Master Franchise List. Likely supersedes. |
| `fs/Archived Contact Data - SAVE/Franchisee Data/Zoominfo FS Master List.xlsx` | 64,351 | FS | FS-side Zoominfo enrichment — net-new source vs. FS SAVE! masters |
| `fs/MUFC 2025.xlsx` | 4,587 | FS | Current-year franchise conference attendees (Multi-Unit Franchising Conference 2025). High-intent. |

## Tier 2 — Real but lower-priority

| File | Rows | Notes |
|---|---:|---|
| `cs/Master Data/Master Company Sellers Data.xlsx` | 82,073 | Likely same as FS SAVE!'s 82K Owner sheet — verify in dedup |
| `cs/Master Data/Seamless/Business Owners.csv` | 2,647 | Small Seamless.ai export |
| `fs/Archived Contact Data - SAVE/Zoominfo Master Export SAVE.xlsx` | 59,940 | Same as FS SAVE!'s .csv version |
| `fs/Archived Contact Data - SAVE/Franchisee Data/FranChimp Master List.xlsx` | 17,642 | Franchisee enrichment source |
| `fs/Archived Contact Data - SAVE/Franchisee Data/Seamless Master List.xlsx` | 27,006 | Franchisee enrichment source |
| `fs/CEPA URL Scrape.xlsx` | 289 | Referral partners (Certified Exit Planning Advisors) |
| `fs/Seamless Export - General - 11-14-2024.csv` | 557 | Small Seamless export |
| `fs/Archived Contact Data - SAVE/IFPG/*.xlsx` (3 files) | ~1,410 | IFPG broker association reference/contacts |
| `fs/Archived Contact Data - SAVE/Pipedrive Exports/Pipedrive Export People 2022.xlsx` | 4,493 | Old CRM export. Useful for suppression cross-ref (touched-before) |
| `fs/Archived Contact Data - SAVE/SMS Blast Data/*` (3 files) | ~11,991 | Historical SMS recipients — suppression context |
| `fs/Archived Contact Data - SAVE/Event Attendee Lists/` (~17 files) | ~20K | Real attendees of franchise events 2022–2024. Reactivation candidates with re-verification. |
| `fs/Review, Clean & Sort/Franchisor/*` (~30 files) | ~33K total | Franchisor (zor) contact research. For the FS partnership/referral program — separate sequence from seller cold. Heavy duplicate-iteration overlap; one canonical pool should emerge after dedup. |
| `fs/Archived Contact Data - SAVE/Business Advisors/WestCo Accountants CPAs Attorneys (Final).xlsx` | 91 | CPAs/attorneys referral partners. Tiny — heavy overlap with Airtable Business Advisors (5,212 rows) which is the canonical version. |

## Skip — not cold-email relevant

- `fs/Archived Contact Data - SAVE/Buyers Related Data/` — buyer profiles (separate sequence, goes to Buyer Manager dashboard, not cold email)
- `cs/Master Data/Buyer Blast Copper Club*` — buyer list
- `fs/Archived Contact Data - SAVE/Holiday Gift List/` — holiday gift recipients
- `fs/Archived Contact Data - SAVE/Misc/Donald Luria - Finalized Resume.pdf` — resume, irrelevant
- `fs/Archived Contact Data - SAVE/Misc/RE_ Franchisors & Franchisees Lists To Buy.msg` — email, not data
- `fs/Archived Contact Data - SAVE/Misc/Video Questions with Curtis McCoy.xlsx` — interview prep
- `fs/Archived Contact Data - SAVE/Misc/Denise Local Advisors List.xlsx` — 4 rows, abandoned
- `fs/Archived Contact Data - SAVE/Stats from Julie Norman/` — stats report, no contacts
- `cs/Keywords-Business & Franchise.xlsx`, `fs/Archived Contact Data - SAVE/Keywords/*` — SEO keywords, not contacts
- `fs/Archived Contact Data - SAVE/SBA Franchise Directory/` — public franchise registry reference
- `fs/Archived Contact Data - SAVE/Franchise Brands/` — franchise system reference list
- `cs/NAGGL List*` and `cs/NAGGL_Virtual_Conference_2020*` — very old (2020) SBA lender event, ~320 rows total
- `cs/Boomerang _ CPA (Private & 5+ Years).xlsx` — empty (0 rows in default sheet)

## Suppression notes (important)

When the dedup pass runs, suppression inputs are now:

1. **Clay `FS_-Franchisee-(Block-List)`** — 22,425 rows (FS-side)
2. **Dropbox `DNU Master Data TB.xlsx`** — 172,489 rows (FS-side, much larger)
3. **Airtable `Archived Contacts`** — 38,547 rows (mostly CS, with `Archived Reason`)
4. **Pipedrive Export People 2022** — 4,493 rows (anyone previously in CRM)
5. **SMS Blast Data** — 11,991 rows (anyone touched via SMS)

Combined gross suppression input ≈ **250K rows** — heavy overlap, real unique post-dedup probably 150–200K.

This is *bigger than the live cold pool*. After applying suppression, the Phase 1 reactivation list will be substantially smaller than the headline 660K total.
