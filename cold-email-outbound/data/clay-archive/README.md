# Clay Archive

CSV exports of every keeper Clay table, captured before cancelling the Clay subscription. Created 2026-05-21 per the reaffirmed decision to drop Clay (see `05-decisions-log.md`).

## Folder structure

- `cs/` — Company Sellers brand exports (from the "Company Sellers" folder in Clay)
- `fs/` — Franchise Sellers brand exports (from the "Franchise Sellers" folder in Clay)

This split mirrors the architecture's brand-wall principle. When deduping or merging, code can tag everything in `cs/` as brand=CS and everything in `fs/` as brand=FS without filename inspection.

## How to add files

1. In Clay, open a table you want to keep.
2. Top-right `⋯` (More) menu → **Export as CSV**.
3. Save the file directly into this folder. Use Clay's existing table name as the filename — don't rename.
4. Repeat for every keeper table.
5. Ping Claude when you're done — I'll parse + dedupe against the existing FS SAVE! masters and update `PHASE-0-DATABASE-AUDIT.md`.

## ⚠️ CRITICAL: Unhide all columns before each export

Clay exports **only the columns currently visible in the active view**. The columns chip near the top of the table (e.g. "9/51 columns") tells you how many are visible vs total. If the two numbers don't match, click the chip and unhide all hidden columns BEFORE clicking Download CSV.

Discovered the hard way 2026-05-21 — Consumer-Services-LinkedIn first export came through as a 9-column stub when the table actually had 51 columns. Lost the waterfall email enrichment, owner names, and AI columns. Had to re-export.

## What to skip

Don't export:
- Test/scratch/template tables
- Tables with < 50 rows that are clearly working files
- Tables where every column is empty or partially-filled "in progress" enrichment

When in doubt, export it — disk is cheap, redoing a missing export is not.

## What to prioritize if you can't export everything

In order:
1. Tables with **validated email + first/last name + company + title** (the contact gold standard)
2. Tables with **specific franchise system, M&A signals, or tenure data** (ICP gold)
3. Tables with **referral partner contacts** (CPAs, attorneys, wealth advisors — separate sequence)
4. Tables with **buyer-side contacts** (separate from seller cold)
5. Everything else
