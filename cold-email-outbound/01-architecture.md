# System Architecture

## The four layers

**1. Sending layer — Instantly (one account).**
Two domain pools inside one Instantly workspace. Roughly 30 sending domains for Franchise Sellers, roughly 30 for Company Sellers. Each domain carries 2–5 mailboxes. Campaigns are tagged by brand and only pull from the matching domain pool. Recipients always see a "from" address that matches the brand they're being contacted under.

**2. Data layer — RevyOps (one account).**
The permanent system of record for outbound. Every contact, send, reply, bounce, suppression flag, and brand affiliation lives here. RevyOps is *not* the CRM — it's the deeper layer underneath the CRM. Records flow into it from sourcing, get enriched and scored, get pushed to Instantly when sequenced, and stay here forever.

**3. CRM layer — two GoHighLevel accounts (one per brand, configured by Deal Studio).**
A contact only enters GHL after a prospect agrees to a discovery call. This is by design — pre-conversation records stay out of the CRM to keep it clean for the sales team. Claude Code routes new GHL contacts based on the `brand` tag on the originating RevyOps record. Once a contact is in GHL, RevyOps marks them as `in_crm` and they are immediately suppressed from any cold outreach.

**4. Orchestration layer — Claude Code.**
The brain. Reads from RevyOps, writes to Instantly, syncs both directions with both GHLs, runs the suppression filter, generates spintax variants, runs scheduled jobs, builds weekly dashboards. Lives on Theodore's machine for now; eventually moves to a small always-on cloud VM for unattended scheduled runs.

## End-to-end data flow

```
Sourcing  →  Enrichment  →  Scoring & dedup  →  Suppression filter  →  Push to Instantly  →  Send
   ↓              ↓                ↓                    ↓                       ↓                ↓
RevyOps ←────  RevyOps ←────  RevyOps  ←──────  RevyOps  ←──────────────  Instantly events ──→ RevyOps
                                                                                      ↓
                                                                                Reply intelligence
                                                                                      ↓
                                                                              Routes to right GHL
                                                                                      ↓
                                                                            RevyOps flag: in_crm
```

Plain-language version of the loop:

Claude Code pulls a fresh batch of candidates from RevyOps that match the campaign criteria (brand, ICP segment, signal trigger). The pre-send suppression filter removes anyone who's in either GHL, has replied recently, has been emailed inside the cooldown window, has unsubscribed, or has hard-bounced. The clean batch gets enriched-on-demand if any fields are missing, gets scored, and gets pushed into the matching brand's Instantly campaign. Sends happen on Instantly's schedule. Replies, bounces, and opens write back to RevyOps. Positive replies route to the matching brand's GHL via Claude Code, and the moment a contact lands in GHL, RevyOps flips their suppression flag.

## Suppression model

Three sync directions keep the suppression list accurate.

**GHL → RevyOps.** Any contact added to either GHL workspace (a discovery call gets booked, the team manually adds them, anything) gets flagged in RevyOps as `in_crm` and locked from outbound. Sync runs hourly at minimum. Event-driven via webhooks where supported.

**Instantly → RevyOps.** Send events, replies, bounces, and opens write back. Once a contact replies (any reply), they're flagged. Once they're in an active campaign, they're flagged for the campaign duration plus the no-reply cooldown.

**Manual flags.** Unsubscribes from email footer links, list-uploaded suppressions, complaints, do-not-contact requests — all written into RevyOps with reason and timestamp.

**Pre-send filter (the gate).** Every batch Claude Code preps for Instantly does:

```
pull candidates from RevyOps  →  apply suppression rules  →  log what got suppressed and why  →  push only the clean records
```

**Belt and suspenders — Instantly global block list.** Every few hours, Claude Code syncs every GHL contact (both workspaces) into Instantly's global block list. If any record somehow slipped through orchestration, Instantly itself refuses to send.

Default cooldowns and full rule set: see `04-offer-concepts.md` for offer-specific rules; full suppression policy lives below.

## Suppression rules (default)

| Status | Rule | Cooldown |
|--------|------|----------|
| In either GHL CRM | Permanent suppression unless flag manually removed | — |
| Replied (any reply, any campaign) | Global suppression pending review | — |
| Unsubscribed via footer link | Permanent suppression | Permanent |
| Hard bounced | Permanent suppression | Permanent |
| Soft bounce x3 | Suppression pending re-verification | — |
| Recently emailed (no reply) | No-reply cooldown | **60 days** (default — revisit before Phase 1 launch) |
| Closed Lost in GHL | Cooldown until eligible again | **12 months** (default — revisit before Phase 1 launch) |
| Customer (Closed Won) | Permanent suppression for cold; eligible only for separate upsell sequences | Permanent for cold |
| Job change detected | Status: `needs_re-research` until re-verified | — |
| Complaint received | Permanent suppression + flagged for compliance review | Permanent |

## Tech stack reference

| Layer | Tool | Status |
|-------|------|--------|
| Sending | Instantly | Existing, ~60 warmed domains |
| Sequencer | Instantly | Active |
| Email verification | MillionVerifier / NeverBounce / ZeroBounce class | Existing — confirm provider, reconnect |
| Firmographic + contact source | Apollo | New — provision in Phase 0 |
| Person enrichment / job change | PDL or Datagma | New — provision in Phase 2 |
| Email find / verify | Hunter or Snov | New — Phase 0 or 2 |
| Data layer | RevyOps | Account to be created in Phase 0 |
| CRM (Franchise Sellers) | GoHighLevel | Existing, configured by Deal Studio |
| CRM (Company Sellers) | GoHighLevel | Existing, configured by Deal Studio |
| Orchestration | Claude Code | Installed; orientation pending |
| LinkedIn outreach | TBD (HeyReach or similar) | Phase 3 |
| Call recording / transcription | TBD (Gong or Fathom) | Phase 3+ |

## What lives where (file reference)

The rule we'll follow in this folder: this file (`01-architecture.md`) is the canonical reference for *how the system works*. `02-phase-0-plan.md` is the live task list. `05-decisions-log.md` records *why* architectural choices were made. `cold-email-research-playbook.md` is the external research that informed the architecture.
