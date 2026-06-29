# Source / provenance

This `cold-email-outbound/` directory is a **copy** pulled in for Malcolm's planning and
copy work. It is **not** the source of truth.

- **Source repo:** `theodorebaird/fs-cs-internal-tools` (local clone at `C:\Franchise Sellers\fs-cs-internal-tools`)
- **Source branch:** `claude/practical-wozniak-2c8c43`
- **Copied from commit:** `44a2596eb55a6bb2c05433d6f2c38018ff1e2453` (re-pulled 2026-06-29; brought in Eric's ICP + updated copy guide. Originally copied from `ad5bb22`.)
- **Copied on:** 2026-06-29

After each re-pull, Malcolm's three revised seller templates are re-applied from
`_malcolm-revisions/` over `templates/`. Ted did not modify the seller templates
through `44a2596`, so re-applying was a clean overwrite with no reconciliation.

Ted is actively building this engine on that branch, so this copy **will drift** from his
source over time. Before relying on the engine code, configs, or templates, re-check the
branch. To refresh this copy:

```bash
cd "C:/Franchise Sellers/fs-cs-internal-tools"
git fetch origin
git archive origin/claude/practical-wozniak-2c8c43 cold-email-outbound | \
  tar -x -C "C:/Franchise Sellers/AI Folders" --strip-components=0
```

Any copy *tweaks Malcolm makes here* (e.g. template wording) are local to this repo until
they're carried back to Ted's branch.
