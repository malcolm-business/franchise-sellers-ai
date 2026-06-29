# Source / provenance

This `cold-email-outbound/` directory is a **copy** pulled in for Malcolm's planning and
copy work. It is **not** the source of truth.

- **Source repo:** `theodorebaird/fs-cs-internal-tools` (local clone at `C:\Franchise Sellers\fs-cs-internal-tools`)
- **Source branch:** `claude/practical-wozniak-2c8c43`
- **Copied from commit:** `ad5bb2205de08e0c646bc27f57ca40ca1f1574f4`
- **Copied on:** 2026-06-29

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
