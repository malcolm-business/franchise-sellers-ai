# Cold Email Outbound — Claude project guide

Start each session with `RESUME.md` (newest entry on top). This file is for conventions, file ownership, and gotchas — things you'd be sad to forget but that don't change session-to-session.

---

## Project shape

- **Type:** outbound email engine, not a dashboard. No webroot, no nginx vhost. No cron crons here.
- **Stack target:** RevyOps (data) · Instantly (sending) · 2 GoHighLevel CRMs (FS + CS) · enrichment APIs direct (Apollo + PDL/Datagma + Hunter/Snov + verifier) · Claude Code (orchestration brain).
- **Current state:** all design docs, zero code. Phase 0 plumbing not yet started beyond this workspace.
- **Future code home:** TBD — Python orchestration scripts will likely land in this folder under `scripts/` once Phase 0 starts wiring the connectors. No script files exist yet (2026-05-21).

## File ownership

| File | Role | Update cadence |
|---|---|---|
| `README.md` | Folder-level orientation for any teammate or future Claude | Rarely |
| `RESUME.md` | **Read first every session.** Newest on top. | Every session |
| `CLAUDE.md` | This file — conventions, gotchas, file map | When a new convention emerges |
| `00-project-overview.md` | Vision, why we're rebuilding, current state | When strategy shifts |
| `01-architecture.md` | Canonical reference for how the system works | When architecture changes |
| `02-phase-0-plan.md` | Live task list — Phase 0 only | When tasks change status |
| `03-brands-and-icp.md` | Both brands, audiences, ICP scoring framework | When ICP signals refine |
| `04-offer-concepts.md` | OOV baseline + portfolio of 7 alternatives + test plan | When new offers added or test results land |
| `05-decisions-log.md` | Append-only decision log with reasoning. Reversals = new entry, not edits. | Every meaningful decision |
| `06-services-and-process.md` | Current services, pricing, lead-to-close process | When pricing/process changes |
| `cold-email-research-playbook.md` | 2026 best-practice research that informed the architecture | Rarely — historical |
| `notion-reference/` | Verbatim Notion source pages (SOPs, OOV questionnaire, reply playbooks, Zor framework). See `notion-reference/00-source-notes.md` for index + open discrepancies. | When new source pages added |

## Conventions

- **Both brands, one engine.** Brand walls are at the *sending domain* layer only. Everything else (database, orchestration, analytics) is shared. Every record carries a `brand` tag.
- **CRM = post-conversation, not pre-conversation.** A prospect only lands in GHL after they agree to a discovery call. Pre-conversation records stay in RevyOps. Don't write code that pushes raw outbound contacts into GHL.
- **Suppression is sacred.** Three layers — RevyOps single source of truth → Claude Code pre-send filter → Instantly global block list as belt-and-suspenders. Never bypass any of them.
- **OOV stays as the control.** New offers are *additions to the portfolio*, not replacements. A/B testing is sequential (one at a time), 500-record minimum per variant for statistical signal. See `04-offer-concepts.md` test order.
- **Cooldowns default:** 60 days no-reply, 12 months closed-lost. Revisit before Phase 1 launch.
- **Decision log is append-only.** Reversing a decision = new dated entry, not editing the old one. Keeps reasoning chain auditable.
- **Notion-reference is verbatim** — captured 2026-05-03. If something there conflicts with `06-services-and-process.md`, the synthesized doc is the latest verbal truth from Theodore. Open conflicts are listed in `notion-reference/00-source-notes.md`.

## Gotchas

- **Notion source-doc discrepancies are real and unresolved** as of 2026-05-21. Don't trust the Reply Handling SOP pricing or the Zor framework's "25 years" framing — both have been overridden by Theodore verbally. See `notion-reference/00-source-notes.md` for the full discrepancy list.
- **No code lives here yet.** If you find yourself about to write a script, first confirm whether it should live here or in the existing `crm-snapshot/` (if it has to read from the unified master snapshot) or elsewhere. The unified-snapshot principle from the master CLAUDE.md applies: **never add another GHL puller**. Any cold-email script that needs CRM contacts should derive from the existing master snapshot, not pull fresh.
- **GHL rate-limit rules apply here too.** This project will touch GHL for the suppression sync (GHL → RevyOps `in_crm` flag). All the strict rules from the master CLAUDE.md (no bulk writes ≥100 without approval, retry helper, business-hours-only for heavy ops) apply. Read `feedback_ghl_rate_limit_strict.md` before writing any GHL-touching script.
- **Existing 100–500K contact database** lives outside this folder — exact location TBD during Phase 0 task #3 (database audit). Likely on the droplet or in the prior Clay export. Don't write code assuming any particular shape until the audit is done.
- **No FastAPI, no nginx, no dashboard pattern.** This is not a dashboard project. It's an orchestration/automation project. The output is sent emails, not a static HTML site.

## Related projects in this workspace

- `crm-snapshot/` — the unified GHL data layer. Cold email's GHL-suppression sync will likely derive from the master JSON here, not from a direct GHL pull. Read `crm-snapshot/ARCHITECTURE.md` before wiring suppression.
- `IFPG Resales/` — only other Python automation project in this workspace that runs as a scheduled job. Worth reading its deploy pattern when we get to deploying cold-email orchestration on the droplet.
- Master `CLAUDE.md` (one level up) — workspace-wide rate-limit rules, naming conventions, and infrastructure notes.

## What this project is *not*

- Not a dashboard. Not a webroot. Not nginx-served.
- Not Clay. We explicitly replaced Clay with direct API calls in Claude Code.
- Not a system for sending email to CRM contacts. It's pre-CRM by design.
- Not LinkedIn outreach (Phase 3, separate tooling TBD).
- Not buyer-side. Sellers only — buyer-side is the Buyer Manager Hub dashboard's concern.
