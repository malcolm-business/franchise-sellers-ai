# Decisions Log

A running log of architectural and operational decisions, with the reasoning that produced them. Append-only — when a decision is reversed, log the reversal as a new entry rather than editing the old one. This keeps the rationale chain auditable.

---

## 2026-05-03

### Decision: Adopt the Ben Reed / RevyOps framework as the architectural model

**What:** Use RevyOps as the permanent data layer; orchestrate the cold email engine via Claude Code; replace Clay with direct API enrichment; use spintax-driven copy with personalized signal anchoring.

**Why:** Theodore is following Ben Reed's published frameworks on LinkedIn. The framework is well-thought-through, public, and matches the goals (sharper offer, durable infrastructure, observable system). Adopting an established model saves weeks of architecture-level decision-making.

**Trade-offs accepted:** Ben's published examples assume HubSpot as the CRM; we're on GoHighLevel. We accept slightly more custom integration work on the CRM side. RevyOps is a younger product than Clay; we accept the platform risk in exchange for the cleaner architectural fit.

---

### Decision: Hybrid brand structure — shared infrastructure, brand-separated sending and CRMs

**What:** One Instantly account (with brand-tagged campaigns drawing from brand-specific domain pools), one RevyOps instance (records tagged with `brand`), two separate GoHighLevel CRMs (one per brand). Claude Code orchestrates across all of it.

**Why:** Three options were considered: (a) fully shared single engine, (b) two fully parallel engines, (c) hybrid. Option (a) creates deliverability and brand-trust risk because recipients could receive emails from the wrong brand. Option (b) doubles infrastructure cost and maintenance with no proportional benefit for a one-operator setup. Option (c) preserves brand integrity at the recipient layer (where it matters most) and consolidates everything else (where it doesn't).

**Trade-offs accepted:** Slightly more orchestration complexity than option (a) — every record carries a brand tag and Claude Code routes accordingly. Acceptable cost.

---

### Decision: Replace Clay with Claude Code calling enrichment APIs directly

**What:** Drop Clay from the stack. Claude Code calls Apollo (firmographic + contact), a secondary deep-enrichment provider (PDL or Datagma — TBD), and an email find/verify provider (Hunter or Snov) directly via API.

**Why:** Theodore's vision is to consolidate enrichment logic inside Claude Code so it's all reasoning over one orchestration layer. Direct APIs are cheaper at volume than Clay's bundled access. Ben Reed's framework explicitly supports this path ("None → Connect Direct APIs, Start with Apollo API").

**Trade-offs accepted:** Loss of Clay's no-code visual fallback. More setup work upfront wiring each API. Claude Code becomes responsible for credit/budget management across multiple providers. All acceptable given the architectural simplicity gained.

---

### Decision: Existing OOV offer remains the baseline; build a portfolio of alternatives to A/B test against it

**What:** Don't replace the free Opinion of Value. Run it as control. Build 6 alternative offer concepts (Comparable Sales Report, Exit Readiness Assessment, Industry Exit Guide, Buyer Match, 15-Minute Exit Strategy Call, Succession Planning Conversation) — see `04-offer-concepts.md` — and test them against the OOV baseline one at a time once volume supports it.

**Why:** Theodore named offer improvement as a strategic priority but doesn't want to abandon what works. The OOV is the industry default — predictable performance, good baseline. The alternatives map to different mental phases of the prospect's exit thinking, which is the deeper reason the same offer doesn't work for everyone.

**Trade-offs accepted:** A/B testing requires volume (~500 per variant for meaningful results). At 10K/month volume that's about a week per test, so this is manageable but means we can't test all six alternatives against the OOV simultaneously without diluting statistical signal. Tests run sequentially.

---

### Decision: Suppression model — RevyOps single source of truth, Claude Code pre-send filter, Instantly global block list as belt-and-suspenders

**What:** Three sync layers ensure no contact in either GHL workspace ever receives cold email: (1) GHL → RevyOps hourly sync flags `in_crm` status; (2) Claude Code's pre-send filter checks every batch against suppression rules before any push to Instantly; (3) GHL contacts also sync into Instantly's global block list every few hours.

**Why:** Theodore raised this as a critical architectural concern — emailing someone already working with the team is brand-damaging and erodes deliverability. Three independent layers ensure that no single point of failure (a missed webhook, a stale sync, a code bug) can result in a cold email going to a CRM contact.

**Trade-offs accepted:** Triple-redundancy means more moving parts to maintain. Acceptable cost for the protection it buys.

---

### Decision: Default cooldowns — 60 days no-reply, 12 months closed-lost

**What:** A contact who has been emailed but didn't reply rests for 60 days before becoming eligible again. A contact whose deal closed lost in GHL rests for 12 months.

**Why:** Standard middle-ground for the brokerage / M&A space. 60 days lets the same contact see roughly 4–5 distinct touches per year across different angles without feeling spammed. 12 months for closed-lost respects that exit timelines often shift over a 6–12 month window — re-engaging earlier risks irritation, later misses the window when the owner's mind has changed.

**Status:** Default — revisit before Phase 1 launch with Theodore.

---

### Decision: Volume ramp — 3K/mo → 6K/mo → 10K+/mo

**What:** Phase 1 sends 3K/month (reactivation), Phase 2 sends 6K/month (with enrichment pipeline online), Phase 3+ sends 10K+/month (full ramp with offer iteration and reply intelligence).

**Why:** Conservative restart after a six-month pause. Lets us validate the orchestration before pushing volume, and matches our risk tolerance for testing the rebuilt system. With ~60 warmed domains and 100–500K contacts, this ramp is well below capacity — the constraint is operator confidence, not infrastructure.

---

### Decision: Phase 1 reactivation uses the existing 100–500K contact database

**What:** Phase 1 (3K/month) draws exclusively from the existing database from the prior engine, not from net-new sourcing. Contacts get re-verified before sending; some get re-enriched for job-change detection.

**Why:** The existing data is sunk cost — already paid for, already enriched. Reactivating it is the cheapest way to validate the engine and generate revenue. Net-new sourcing is more expensive and only becomes necessary when the existing pool is exhausted, which won't happen until well into year one at the proposed volumes.

**Trade-offs accepted:** Existing data is 6 months stale. Job changes, role changes, and email-validity decay are real. Mitigated by the email re-verification step before any send.

---

## 2026-05-21

### Decision: Reaffirm dropping Clay — manual CSV export of historical tables before cancellation

**What:** Reaffirms the 2026-05-03 decision to drop Clay. Theodore explicitly re-interrogated the call ("I'm not convinced unless we can build the system without Clay") and confirmed the direction. Path forward: Theodore manually exports every keeper Clay table to CSV → archives to `cold-email-outbound/data/clay-archive/` → Claude parses + merges into the audit pool → Clay subscription cancelled once exports are verified complete.

**Why:** Three considerations: (1) Clay's Audiences feature (which would have made tables queryable via MCP without exports) sits behind Clay's Enterprise plan tier, which Theodore is not on and is not worth the price jump for a tool being decommissioned. (2) Building waterfall enrichment + AI-built columns directly in Claude Code via Apollo + PDL/Datagma + Hunter is 1–2 weeks of dev time but produces a stack we own outright and that costs less per credit at the 10K/mo target volume. (3) The CSV exports preserve all already-paid-for enrichments permanently — the sunk cost is recovered regardless of whether Clay stays.

**Alternative considered (and rejected this session):** Keep Clay as the enrichment layer, enable Audiences, defer the keep/drop decision 3–6 months. Rejected because Theodore wants ownership of the orchestration-plus-enrichment layer in Claude Code rather than depending on a third-party tool whose Audiences feature he can't currently access.

**Trade-offs accepted:** Manual export of dozens of tables (a few hours of clicking, no bulk export available without API access). Loss of Clay's no-code visual workspace. ~1–2 weeks of Claude Code dev work to build the waterfall enrichment + AI-column equivalents. All acceptable given the strategic preference for ownership.

---

## 2026-06-07

### Decision: Email verification + finding — LeadMagic primary, ZeroBounce fallback

**What:** Use LeadMagic as the primary email finder + verifier. When monthly LeadMagic credits are exhausted, fall back to ZeroBounce for verification. Theodore has active accounts on both.

**Why:** Both accounts already exist (no new procurement). LeadMagic does email *finding* AND verification, so it serves double duty in the enrichment waterfall (Layer 2) and the pre-send verification gate (Layer 5 / before any send). ZeroBounce is a high-accuracy verifier for overflow. This replaces the earlier placeholder options (NeverBounce / MillionVerifier / Hunter / Snov / Findymail) for the verification + finding roles.

**Impact on the design:**
- Layer 2 enrichment waterfall email-finder = LeadMagic (→ ZeroBounce verify on overflow)
- Layer 5 pre-send verification gate = LeadMagic verify (→ ZeroBounce when credits out)
- The "confirm verifier provider" open decision is now CLOSED.

**Trade-offs accepted:** Two-provider credit management (Claude Code tracks LeadMagic credit balance, switches to ZeroBounce when depleted). Acceptable — both are already paid for.

---

### Decision: Data layer — NOT Airtable as the permanent system of record; RevyOps if/when a dedicated layer is needed

**What:** Move away from Airtable as the cold-email data layer. Airtable was the proto-RevyOps (Active Contacts cross-referenced Clay/Instantly/Pipedrive) but Theodore does not want to build the permanent engine on it unless it proves to be the best structure. If a dedicated data layer is needed, the choice is RevyOps.

**Why:** Theodore's preference. Airtable's value was as a snapshot of historical state (already captured in the dedup archive). Building the live engine on Airtable risks the scaling cliff (~100K rows) and ties the system to a tool whose role overlaps with what RevyOps is purpose-built for.

**What this means for Phase 1:** The dedup output (`canonical-master.csv` + tier files) is the current source of truth — flat files Claude Code reads + writes directly. This is sufficient for Phase 1 reactivation (no live data layer dependency). The RevyOps-vs-flat-files-vs-other decision gets made at the Phase 2 point when live campaign-state management at scale actually requires it.

**Trade-offs accepted:** Phase 1 runs on flat-file state (canonical-master.csv + per-campaign send logs) rather than a queryable live database. Acceptable for reactivation volume; revisit when concurrent campaign state across streams gets complex.

**Status:** Airtable de-prioritized as data layer. RevyOps = leading candidate if/when needed. Decision deferred to Phase 2.

---

### Decision (revision): Keep Clay account active; defer drop/keep to Phase 2 — do NOT cancel now

**What:** Softens the 2026-05-03 + 2026-05-21 "drop Clay" decisions. Clay account stays active. The drop-vs-keep call is deferred to Phase 2 (net-new sourcing), not made now.

**Why:** Phase 1 reactivates the existing ~187K Tier A pool, which needs *verification* (LeadMagic + ZeroBounce), not *enrichment*. The pool is already enriched from when Clay built it. Clay's value (waterfall enrichment + AI-research columns) only matters at Phase 2 net-new sourcing — which is years away at 3K/mo given 187K Tier A + ~155K re-verifiable Tier B. Theodore noted some operators still rely on Clay's features even in the Claude era; no reason to force the cancel before we know which features we actually need. The archive is already captured, so nothing is lost by keeping the account open.

**Net:** Engine does NOT depend on Clay. Account stays active. Revisit at Phase 2. Cancel only if/when we confirm Claude Code + direct APIs (Apollo + LeadMagic + PDL) fully cover the enrichment we need.
