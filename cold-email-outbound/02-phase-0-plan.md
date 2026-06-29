# Phase 0 — Foundation

**Goal:** Get the plumbing in place. No campaigns send during Phase 0. By the end of Phase 0, Claude Code can read and write all four systems (Instantly, RevyOps, both GHLs, all enrichment APIs) and the project workspace is set up.

**Estimated duration:** 1–2 weeks of calendar time, but most blocks are short — total work is well under a full week.

## Task list

| # | Task | Owner | Blocked by | Status |
|---|------|-------|------------|--------|
| 1 | Create RevyOps account | Theodore | — | Pending |
| 2 | Run Claude Code orientation session | Theodore + collab | — | Pending |
| 3 | Audit and consolidate existing 100–500K contact database | Collab | — | ✅ Initial audit 2026-05-21 (see `PHASE-0-DATABASE-AUDIT.md`). Tier A pool ≈ 88K. Clay export + Instantly `All Leads` pagination still outstanding. |
| 4 | Wire Instantly connection in Claude Code and validate | Collab | — | Pending |
| 5 | Wire both GoHighLevel CRMs in Claude Code | Collab | — | Pending |
| 6 | Wire RevyOps connection in Claude Code | Collab | #1 | Pending |
| 7 | Provision enrichment APIs (Apollo + secondary) | Collab | — | Pending |
| 8 | Reconnect existing email verification provider | Theodore + collab | — | Pending |
| 9 | Set up Cold Email Outbound project workspace | Collab | — | ✅ Complete 2026-05-21 (transferred to Claude CODE + scaffolded) |
| 10 | Define cross-system suppression rules | Collab | — | Pending (defaults in `01-architecture.md`) |
| 11 | Build cross-system suppression infrastructure | Collab | #4, #5, #6 | Pending |

## What unlocks Phase 1

Phase 1 (reactivation, 3K sends/month) cannot start until tasks #1, #3, #4, #5, #6, #8, #9, #11 are all complete. Tasks #7 and #10 are nice-to-haves for Phase 1 and required for Phase 2.

The fastest critical path is:

1. Create RevyOps account (#1)
2. Audit database (#3) — can run in parallel with everything else
3. Run Claude Code orientation (#2) — required before collaborative tasks
4. Wire connectors (#4, #5, #6) — can run in parallel once orientation is done and RevyOps exists
5. Reconnect verifier (#8)
6. Build suppression infrastructure (#11)

## Theodore's action items (do these on your own time)

- Sign up for **RevyOps** (account only — we configure it together)
- Open **Claude Code** and have it ready for orientation
- Confirm which **email verification provider** you used previously (MillionVerifier? NeverBounce? ZeroBounce? something else?) and that the account is still active
- Locate **API keys / login credentials** for: Instantly, both GHL workspaces, your verifier, and your existing Apollo account if you have one

## Open decisions to settle during Phase 0

- Final no-reply cooldown (default proposed: 60 days)
- Final closed-lost cooldown (default proposed: 12 months)
- Secondary enrichment provider (PDL vs. Datagma vs. other)
- LinkedIn outreach tooling (Phase 3 — defer)
