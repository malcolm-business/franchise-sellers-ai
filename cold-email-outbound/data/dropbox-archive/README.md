# Dropbox Archive

Contact and lead data exported from Dropbox. Captured 2026-05-21 as part of the Phase 0 database audit — third and final pre-rebuild data source after Clay and Airtable.

**PII — files are gitignored at the repo root.** Only this README and the INVENTORY.md catalog get committed.

## Folder structure

```
dropbox-archive/
├── README.md
├── INVENTORY.md           ← I'll generate this once files are in
├── cs/                    ← Company Sellers files
└── fs/                    ← Franchise Sellers files
```

Same brand-wall convention as `clay-archive/`. Anything in `cs/` is tagged brand=CS in code; anything in `fs/` is tagged brand=FS. No filename inspection needed.

## How to add files

Copy files directly from Dropbox (Dropbox desktop app, dropbox.com download, or any other route) into the appropriate `cs/` or `fs/` subfolder. Keep original filenames so the source is traceable.

Supported formats:
- `.csv` — preferred
- `.xlsx` — fine; I'll parse with openpyxl
- `.tsv` — fine

If files are in subfolders inside Dropbox, you can either:
- Flatten them into `cs/` or `fs/` and rename for clarity if needed, OR
- Preserve the subfolder structure inside `cs/` / `fs/` and I'll walk it recursively

## What to grab

- Contact lists (cold email targets — past or current)
- Enriched-data exports
- Suppression / do-not-contact lists
- Buyer lists (if relevant — but flag them separately, those go to a different sequence)
- Anything labeled "leads", "prospects", "outreach", "campaign", "list"

## What to skip

- Sales / closed deal data (lives in GHL now)
- Internal documents, contracts, OOVs
- Marketing assets, copy drafts (we have those elsewhere)
- Anything older than ~2 years unless it's a confirmed historical pool worth re-verifying

When in doubt, drop it in — I'll triage during the dedup pass and skip anything that isn't contact data.
