# Project Overview

## What we're building

A cold email outbound engine for two business brokerage brands — **Franchise Sellers** and **Company Sellers** — rebuilt from the ground up after a six-month pause. The engine runs at 10K+ emails per month at full ramp, generates qualified seller-side conversations, and feeds Theodore's two GoHighLevel CRMs only after a prospect agrees to a discovery call. Claude Code orchestrates the whole pipeline.

The build follows the framework Benjamin Reed (founder of RevyOps) publishes on LinkedIn — RevyOps as the permanent data layer, Claude Code as the orchestrator, direct API enrichment instead of Clay, spintax-driven copy, multi-channel sequences, and reply intelligence written back to the CRM automatically.

## Why we're rebuilding

The prior engine — Clay → AI-research → AI-written copy → Instantly — worked at a baseline level (10K sends/month) but had three structural weaknesses: full AI-generated copy at scale started looking like full AI-generated copy at scale (a known 2026 deliverability and reply-rate killer), the offer (free Opinion of Value) was the industry default and didn't differentiate, and the system had no shared data layer that would let analytics or Claude Code reason across the whole pipeline.

The rebuild keeps the parts that worked (Instantly, the existing 100–500K contact database, the OOV as a baseline offer) and replaces the parts that didn't with sharper alternatives (high-skill spintax instead of full AI copy, a curated offer portfolio with the OOV as control, RevyOps as the system of record, Claude Code as the brain).

## Current state (as of 2026-05-03)

**Decided:**
- Architecture: hybrid (one Instantly account with brand-tagged campaigns, one RevyOps, two GHL CRMs)
- Clay is out — Claude Code calls Apollo + secondary enrichment APIs directly
- OOV stays as the baseline offer, with an alternatives portfolio to A/B test against it (see `04-offer-concepts.md`)
- Suppression model: RevyOps is single source of truth; pre-send filter in Claude Code; Instantly global block list as safety net (see `01-architecture.md`)
- Volume ramp: 3K month 1 → 6K month 2 → 10K+ from month 3 onward

**In progress:**
- Phase 0 (foundation) — see `02-phase-0-plan.md`
- Workspace setup (this folder)

**Outstanding:**
- RevyOps account creation (Theodore action)
- Claude Code orientation session (Theodore + collaborative)
- Database audit (where the 100–500K contacts actually live and in what shape)
- Phase 1 (reactivation) — Month 1, 3K target — pending Phase 0
- Phase 2 (enrichment pipeline) — Month 2, 6K target
- Phase 3 (offer iteration + reply intelligence) — Month 3+, 10K+ target

## Operating principles

These came out of conversation; they shape every decision we make from here.

**Be efficient.** Small budget. Don't pay agencies; don't buy shiny tools that duplicate what we can build. Spend on list quality and personalization data (the 2–5× reply-rate levers), not on generic automation.

**Targeting beats volume.** With 60 warmed domains we have 6–12× more sending capacity than we need. The constraint is list quality and signal-anchored personalization. We'd rather send 3K signal-targeted emails at 8% reply than 10K generic ones at 2%.

**Brand walls hold at the sending layer.** Recipients see the right "from" address every time; deliverability reputation stays clean per brand. Internal infrastructure (database, analytics, orchestration) is shared.

**No prospect already in the CRM ever gets cold email.** Cross-system suppression is enforced at three layers — orchestration filter, GHL→RevyOps sync, and Instantly's global block list as belt-and-suspenders.

**Referrals are part of the engine, not a side project.** 84% of B2B sales start with referrals; referred deals close 5× faster. CPA, attorney, and wealth advisor partnerships get the same outbound discipline as cold seller outreach.
