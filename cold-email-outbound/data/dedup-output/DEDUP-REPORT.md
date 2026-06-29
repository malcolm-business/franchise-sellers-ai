# Cold Email Dedup Run — Audit Report

**Run:** 2026-06-07T23:19:25.162361 → 2026-06-07T23:32:30.991627

## Reconciliation

- Total input rows across all sources: **1,312,388**
- Canonical (unique) records after merge: **405,693**
- Duplicates collapsed: **906,695** (69.1% dedup rate)
- Records preserved in full in `canonical-master.csv` — no data lost.

## Tier breakdown

| Tier | Count | Description |
|---|---:|---|
| **A** | **187,490** | Sendable today (valid email, no suppression) |
| B | 155,498 | Re-verification candidates (invalid/missing email) |
| C | 5,774 | Referral partners (advisors + franchisors) |
| D | 56,931 | Suppression — do not contact |

## Brand × Tier matrix

| Brand | Tier A | Tier B | Tier C | Tier D | Total |
|---|---:|---:|---:|---:|---:|
| FS | 10,206 | 1,877 | 0 | 38,680 | 50,763 |
| CS | 160,699 | 145,673 | 0 | 1 | 306,373 |
| REFERRAL | 0 | 0 | 5,774 | 27 | 5,801 |
| AMBIGUOUS | 16,585 | 7,948 | 0 | 18,223 | 42,756 |
| UNKNOWN | 0 | 0 | 0 | 0 | 0 |

## Per-source row counts

| Source file | Category | Rows extracted |
|---|---|---:|
| `DNU Master Data TB.xlsx` | `dropbox_dnu` | 172,478 |
| `Master Franchise List.xlsx` | `dropbox_mfl` | 146,246 |
| `Master Franchise List - Desktop Saved 11-23-24.xlsx` | `fs_save_fs` | 91,196 |
| `Master Company Sellers Data.xlsx` | `dropbox_mcsd` | 82,069 |
| `Master Company Sellers Data Desktop Save 11-26-24.xlsx` | `fs_save_cs` | 82,069 |
| `Master Contact Data-Master View.csv` | `airtable_master` | 72,687 |
| `Zoominfo FS Master List.xlsx` | `dropbox_zoominfo_fs` | 64,347 |
| `Zoominfo Master Export SAVE.xlsx` | `dropbox_zoominfo_master` | 59,939 |
| `Zoominfo Master Export SAVE.csv` | `fs_save_zoominfo` | 59,939 |
| `Health,-Wellness-and-Fitness-(2-10-Emp)-LinkedIn-Default-view-export-1779376757834.csv` | `clay_cs` | 50,020 |
| `Food-and-Beverage-1-50-Emp-Default-view-export-1779387263827.csv` | `clay_cs` | 45,617 |
| `Food-and-Beverage-1-50-Emp-Default-view-export-1779376817539.csv` | `clay_cs` | 45,562 |
| `Archived Contacts-Grid view (4).csv` | `airtable_archived` | 38,547 |
| `Manufacturing-1-10-Emp-Default-view-export-1779386764335.csv` | `clay_cs` | 38,249 |
| `Manufacturing-1-10-Emp-Default-view-export-1779376809842.csv` | `clay_cs` | 34,965 |
| `Consumer-Services-LinkedIn-Default-view-export-1779386267368.csv` | `clay_cs` | 33,200 |
| `Consumer-Services-Runs-Weekly-Default-view-export-1779386553239.csv` | `clay_cs` | 33,169 |
| `Manufacturing-11-50-Emp-Default-view-export-1779386782112.csv` | `clay_cs` | 24,301 |
| `FS_-Franchisee-(Block-List)-Default-view-export-1779387573400.csv` | `clay_fs` | 22,425 |
| `Active Contacts-Master View (3).csv` | `airtable_active` | 18,931 |
| `Manufacturing-11-50-Emp-Default-view-export-1779376789656.csv` | `clay_cs` | 15,557 |
| `Health,-Wellness-and-Fitness-(2-10-Emp)-Default-view-export-1779386559606.csv` | `clay_cs` | 14,918 |
| `Health,-Wellness-and-Fitness-(11-50-Emp)-Default-view-export-1779386587874.csv` | `clay_cs` | 12,676 |
| `Health,-Wellness-and-Fitness-(11-50-Emp)-LinkedIn-Default-view-export-1779376743658.csv` | `clay_cs` | 12,660 |
| `Business Advisors-Grid view (5).csv` | `airtable_advisors` | 5,212 |
| `Automotive-LinkedIn-Default-view-export-1779376565331 (1).csv` | `clay_cs` | 4,522 |
| `Automotive-Runs-Weekly-Default-view-export-1779386408235.csv` | `clay_cs` | 4,394 |
| `MUFC 2025.xlsx` | `dropbox_mufc` | 4,055 |
| `Home-Health-Runs-Weekly-Default-view-export-1779386428924.csv` | `clay_cs` | 3,771 |
| `Home-Health-LinkedIn-Default-view-export-1779376586462.csv` | `clay_cs` | 3,710 |
| `Food-and-Beverage-1-50-Emp-Default-view-export-1779387386268.csv` | `clay_fs` | 3,660 |
| `Health,-Wellness-and-Fitness-(2-10-Emp)-Default-view-export-1779387309424.csv` | `clay_fs` | 3,225 |
| `Health,-Wellness-and-Fitness-(11-50-Emp)-Default-view-export-1779387371076.csv` | `clay_fs` | 1,573 |
| `Final-Results-Table-Default-view-export-1779386348156.csv` | `clay_cs` | 1,497 |
| `Manufacturing-1-10-Emp-Default-view-export-1779387429044.csv` | `clay_fs` | 1,189 |
| `Manufacturing-11-50-Emp-Default-view-export-1779387448950.csv` | `clay_fs` | 976 |
| `FS_-Storage-Leads-(Sent-to-Instantly)-Default-View-export-1779387514004.csv` | `clay_fs` | 904 |
| `Home-Health-Default-view-export-1779387261729.csv` | `clay_fs` | 816 |
| `Franchisors-Grid view.csv` | `airtable_franchisors` | 617 |
| `Automotive-Default-view-export-1779387250775.csv` | `clay_fs` | 311 |
| `FS_-Storage-Leads-(Not-to-Instantly)-Default-View-export-1779387478960.csv` | `clay_fs` | 176 |
| `Master-LinkedIn-Import-Default-view-export-1779386275289.csv` | `clay_cs` | 13 |

## Suppression composition (Tier D)

| Suppression source | Records flagged |
|---|---:|
| `airtable_archived` | 38,523 |
| `airtable_master_archived` | 31,347 |
| `franchisee_block_list` | 22,201 |

## Multi-source overlap (richest records)

| # of source categories per record | Records |
|---|---:|
| 1 | 215,813 |
| 2 | 46,282 |
| 3 | 49,674 |
| 4 | 8,694 |
| 5 | 23,627 |
| 6 | 13,620 |
| 7 | 12,529 |
| 8 | 13,834 |
| 9 | 5,050 |
| 10 | 8,627 |
| 11 | 2,393 |
| 12 | 4,601 |
| 13 | 669 |
| 14 | 149 |
| 15 | 55 |
| 16 | 70 |
| 17 | 4 |
| 18 | 1 |
| 19 | 1 |

Records appearing in 3+ source categories are the highest-confidence canonical records.

## Safety contract verification

- ✅ Every input row accounted for: input (1,312,388) = canonical (405,693) + merged-duplicates (906,695)
- ✅ No record deleted — duplicates merged into canonical with full field union
- ✅ Suppression is additive (a flag) — Tier D records preserve full data
- ✅ Brand tagging from source + explicit field; AMBIGUOUS flagged (not deleted)
- ✅ Run is reproducible: same input → same output (deterministic hashes)

## Outputs

All in `cold-email-outbound/data/dedup-output/` (PII files gitignored):

- `canonical-master.csv` — every unique person, all fields unioned
- `tier-a-fs.csv` — Tier A FS reactivation pool (10,206)
- `tier-a-cs.csv` — Tier A CS reactivation pool (160,699)
- `tier-a-ambiguous.csv` — Tier A with ambiguous brand tag, needs review (16,585)
- `tier-b.csv` — re-verification candidates (155,498)
- `tier-c.csv` — referral partners (5,774)
- `tier-d-suppression.csv` — do-not-contact list (56,931)
- `audit-merge-log.csv` — dedup decisions log
- `source-row-counts.csv` — per-source extraction counts
- `DEDUP-REPORT.md` — this file (committed to git)
