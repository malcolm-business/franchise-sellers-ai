# Airtable Archive

CSV exports of contact/lead tables from Airtable. Captured 2026-05-21 as part of the Phase 0 database audit. Same archival pattern as `clay-archive/` — captured because Airtable is one of the historical homes of contact data for the cold email engine.

**PII — `.csv` files are gitignored at the repo root.** Only this README and the INVENTORY.md catalog get committed.

## Folder structure

Use one subfolder per Airtable **base** (Airtable's term for a workspace/database). Inside each base subfolder, drop one CSV per table.

```
airtable-archive/
├── README.md
├── INVENTORY.md           ← I'll generate this once all files are in
├── <base-name-1>/         ← one folder per Airtable base
│   ├── <table-1>.csv
│   └── <table-2>.csv
└── <base-name-2>/
    └── <table-1>.csv
```

If you only have one base or you're not sure how to split, just dump everything flat in `airtable-archive/` and I'll sort it.

## How to export from Airtable

1. Open the table you want to export
2. Click the view dropdown (top-left, usually labeled "Grid view" or similar)
3. Look for the **⋯ menu** on the view or use **... → Download CSV**
4. Save the CSV file into the appropriate base subfolder under `airtable-archive/`

## ⚠️ Watch out for view filters

Like Clay, Airtable exports **only what's visible in the active view**. If a view has filters applied, the export will only include filtered rows. To get the full table:

- Use the "Grid view" (the default unfiltered view), OR
- Clear all filters before exporting, OR
- Create a temporary new unfiltered view and export from that

## What to skip

- Empty tables
- Test/sandbox tables
- Tables that are just lookups or junction tables for relational links (those are reconstructable from the related tables)

When in doubt, export it — disk is cheap, re-exporting is annoying.
