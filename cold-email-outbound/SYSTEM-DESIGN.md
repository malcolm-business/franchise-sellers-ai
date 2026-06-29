# Cold Email Outbound — System Design v1

**Date:** 2026-05-21
**Status:** Initial design, ready for review + iteration before Phase 1 implementation.
**Companion:** `system-flowchart.html` (visual diagram, same content).

This document is the canonical buildout for the cold email outbound engine. Every architectural decision, tool selection, and build phase lives here. When something changes, log a new entry in `05-decisions-log.md` and update this doc.

---

## TL;DR

**Architecture:** Claude Code orchestrates a 10-layer pipeline that pulls leads from existing archives + new sourcing APIs, enriches them through a waterfall, scores + dedupes + suppresses against 5 sources, generates signal-anchored copy with 3-step sequences, sends through Instantly, classifies every reply via Claude API, and routes positives to the matching destination (GHL CRM for sellers, Buyer Manager pipeline for buyers, referral nurture for partners).

**The system runs multiple campaign streams in parallel** — seller cold (FS niche, FS broad, CS), buyer reactivation, referral partner outreach (CPAs/advisors and franchisor-side), and event-tied micro-campaigns. Each stream shares the same underlying engine (sourcing, enrichment, suppression, sending, classification) but has its own template library, ICP filter, list source, and routing destination.

**What's new vs. the prior engine:** Claude Code is the brain (replaces Clay's no-code orchestration). Copy stops being full-AI-generated paragraphs (`{{Paragraph One}} {{Paragraph Two}}`) and shifts to hand-written templates with surgical AI signal-anchoring. Every reply gets classified — fixing the largest gap in your current system. Multiple campaign types are first-class concepts in the data layer, each tracked + measured + scaled independently.

**Build phases:**
- **Phase 1 (weeks 1–4):** Build the framework that supports all campaign types. Ship probe campaigns across all major streams (seller cold FS, seller cold CS, buyer reactivation, referral partners, event-tied). Reactivate existing archive. No net-new sourcing.
- **Phase 2 (weeks 5–8):** Add net-new sourcing pipeline (Apollo + waterfall enrichment). Scale aggregate volume to 6K/month across streams.
- **Phase 3 (months 2+):** Add intent-signal sourcing (M&A, job changes). Scale to 10K+/month. Move toward semi-autonomous campaign generation.

---

## Campaign types (first-class concept)

The system supports multiple concurrent campaign streams. Each is a configuration over the same engine — same sourcing/enrichment/suppression/sending/classification pipeline, but different templates, ICP filters, list sources, and routing destinations.

| Campaign type | Audience | List source | Template family | Reply routes to |
|---|---|---|---|---|
| **`seller_cold_fs_niche`** | Franchisees of a specific named system (Code Ninja, FirstLight, etc.) | Tier A FS pool filtered by system | "We recently helped a [system] franchisee sell..." | GHL FS workspace |
| **`seller_cold_fs_broad`** | Franchisees, multi-system, signal-anchored | Tier A FS pool by ICP score | Generic franchisee opener + signal anchor | GHL FS workspace |
| **`seller_cold_cs`** | Independent business owners by industry | Tier A CS pool filtered by industry × size | Industry peer social proof opener (rebuilt — no `{{Paragraph One}}` template) | GHL CS workspace |
| **`buyer_reactivation`** | Prior franchise-buy inquirers, business-buy inquirers | Airtable Active Contacts with buyer flag | "The franchise business you looked at..." / "your business for sale inquiry" | Yvonne / Buyer Manager pipeline |
| **`referral_partner_advisor`** | CPAs, attorneys, wealth managers, CEPAs | Airtable Business Advisors (5,212) + Dropbox WestCo lists | "Where do you send clients with valuation questions?" | Theodore direct + light nurture |
| **`referral_partner_zor`** | Franchise HQ contacts (franchisor side) | Dropbox Franchisor research folder + Airtable Franchisors | Partnership / referral framing | Theodore direct + zor-prospecting workflow |
| **`event_pre`** | Confirmed attendees of a specific upcoming event (FLHC, MUFC, HCAOA) | Event-specific list filtered to confirmed registrants | "Are you attending [event] this week? Look for us..." | Theodore direct + meeting booking |
| **`event_post`** | Confirmed attendees, post-event | Same event list | "Great connecting at [event] — here's the follow-up..." | Theodore direct + meeting booking |

**Why this matters:**
- **Suppression is shared.** A prospect on the Franchisee Block List is suppressed across every campaign type. A prospect already in GHL is suppressed across every campaign type. The 3-layer suppression model from Layer 5 applies system-wide.
- **Sending infrastructure is shared.** All streams send through the same Instantly mailbox pool (with brand-walls enforced at the FS vs CS layer).
- **Classification is shared.** Every reply, regardless of stream, runs through the same Claude API classifier — but the routing destination differs based on the originating campaign type.
- **Templates are NOT shared.** Each campaign type has its own template library because the audience + offer language is fundamentally different.

**Operating principle:** the engine is the same; the campaign-type record on each contact decides which template to apply and where to route the reply.

---

## The 10-layer architecture

### Layer 1 — Sourcing

**Phase 1 (no external cost):**
- ✅ Existing archive: ~660K rows across Clay, Airtable, FS SAVE!, Dropbox
- ✅ Already deduped pool (see `PHASE-0-DATABASE-AUDIT.md`)

**Phase 2+ (new):**
- **Apollo API** — primary firmographic + contact sourcing (230M+ contact DB). Target: $$$/mo
- **State franchise registries** — public records (CA, NY, IL register active franchisees). Free
- **FDD databases** — franchise system financial filings. Free
- **Industry publications** — Business Journals lists, Franchise Times, FBR reports. Free / one-time

**Phase 3 (intent-signal):**
- **PDL job-change detection** — flags owners who just transitioned
- **News API + Claude** — detects M&A activity in target verticals → triggers micro-campaigns
- **LinkedIn Sales Navigator (manual or Apify)** — tenure + bio language signals

### Layer 2 — Enrichment Waterfall

Order matters. Each tool fills gaps the prior one couldn't, cheapest first.

| Order | Tool | What it adds | Cost model |
|---|---|---|---|
| 1 | Apollo | Firmographic, basic contact, work email candidate | $$$ /mo subscription |
| 2 | PDL or Datagma | Owner age, tenure, education, bio signals | $$ /credit |
| 3 | Hunter / Snov / Findymail | Email finder waterfall (try one, fall back to next) | $$ /credit per lookup |
| 4 | NeverBounce / MillionVerifier | Final verifier — gates 5%+ bounce | $ /verify |
| 5 | Claude API | Per-row AI research (M&A signals, "why now" extraction) | $$ /token |

**Theodore decisions still open:**
- PDL vs. Datagma (suggest start with PDL — bigger DB, established)
- Hunter vs. Snov vs. Findymail (suggest Findymail — fastest, highest accuracy for B2B work emails per recent benchmarks)
- Verifier provider (confirm if you have an active account anywhere)

### Layer 3 — Data Layer (the open architectural question)

Three options — **defer hard commit until Phase 2.**

**Option A — Airtable stays as data layer (recommended for Phase 1):**
- Already proto-built. Active Contacts (18,931 rows × 48 cols) cross-references Clay + Instantly + Pipedrive — exactly what RevyOps would do.
- Cost: existing subscription
- Risk: Airtable scales poorly past ~100K rows; performance + cost degrade

**Option B — RevyOps replaces Airtable:**
- Purpose-built data layer for outbound. Ben Reed's framework.
- Cost: $$$ /mo (Ben Reed's product, unconfirmed pricing tier)
- Risk: another tool to integrate, less direct evidence it pays back vs. Airtable for your scale

**Option C — Both (hybrid):**
- Airtable for CRM-like seller state (buyer matching, listing pipeline)
- RevyOps for cold-email pipeline state (sequences, suppression, send history)
- Cost: highest
- Risk: complexity + two-system sync

**Recommendation:** **Option A for Phase 1.** Migrate to B if Airtable performance degrades or if the retrospective re-runs show RevyOps' specific features pay back. Decision in `05-decisions-log.md` when made.

**Records carry:**
- `brand` (FS / CS)
- `icp_score` (0–100)
- `enrichment` (Apollo + PDL + Hunter outputs nested)
- `suppression` (in_crm, replied, bounced_hard, unsubscribed, on_block_list_*, cooldown_until)
- `campaign_history` (which sequences, when, what step, last status)
- `reply_classification` (latest reply category + body + classification timestamp)
- `re_engage_date` (set when cooldown / not-now is detected)

### Layer 4 — Dedupe + ICP Scoring

**Claude Code orchestration:**

```
For each candidate record:
  1. Normalize email (lowercase, strip aliases)
  2. Normalize LinkedIn URL
  3. Match against data layer:
     - If existing record (by email or LinkedIn) → merge, update enrichment
     - If new → insert
  4. Compute ICP score:
     - Demographic + tenure (40% weight)
     - Behavioral / situational signals (40% weight)
     - Firmographic match (20% weight)
  5. If score >= 60 → eligible for sequencing
     If score < 60 → archive (don't sequence)
  6. Brand assignment if not pre-tagged:
     - Franchisee indicators → FS
     - Independent business indicators → CS
```

### Layer 5 — Suppression (3-layer)

**Layer A — Pre-send filter (Claude Code, runs every batch):**

Suppression sources merged into a single check:
1. In either GHL CRM (FS or CS) — query `crm-snapshot/crm-master.json`
2. **Franchisee Block List** — 22,425 rows from Clay archive (Layer 5 source)
3. **Airtable Archived Contacts** — 38,547 rows with `Archived Reason` preserved
4. **Airtable Master Contact Data archive flags** — subset with `Archived Reason` populated
5. **Pipedrive Export 2022** — 4,493 rows (anyone previously in old CRM)
6. **SMS Blast Data** — 11,991 rows (don't email + SMS the same person back-to-back)
7. Cooldown active: 60-day no-reply / 12-month closed-lost
8. Recent hard bounce / unsubscribe within data layer

Combined gross input: ~90K rows of suppression. Real unique post-dedup ~60-80K.

> **Correction 2026-06-07:** The 172,489-row `DNU Master Data TB.xlsx` was initially listed here as a suppression source. Investigation during the first dedup run revealed it is actually a *workflow tracking archive* (sheets named "Master List" with categorizations like "Canadian Email List" and "Neverbounce Upload" as a verification queue), not a permanent block list. ~100% of records also appear in active sources. Removed from suppression model. See `data/dedup-output/DEDUP-REPORT.md`.

**Layer B — Instantly global block list (synced every 4 hours):**
- Claude Code cron pushes every record that should never be emailed into Instantly's block list
- Belt-and-suspenders — even if Layer A misses one, Instantly refuses to send

**Layer C — Live Instantly settings:**
- `stop_on_reply: true` (universal)
- `stop_on_auto_reply: true` (don't follow up to OOO)

### Layer 6 — Copy Generation (Spintax + Signal Anchoring)

**Winning template (per the historical retrospective):**

```
SUBJECT VARIANTS (3 per step, rotated):
- Quick question {{firstName}}
- Thoughts {{firstName}}
- {{firstName}}, [system or signal hook]

STEP 1 BODY (target 55–90 words):
Hey {{firstName}},

We help {{audience_descriptor}} value and sell their businesses.
Recently, we helped a {{franchise_system_or_industry_peer}} owner
sell for more than they thought possible — and faster than they expected.

{{optional_signal_anchor}}

If you're curious about selling, we'd be happy to provide a
complimentary, no-obligation business opinion of value.

Let me know if you'd like to explore this further!

Theodore Baird
{{brand_name}}

If this is not relevant to you, simply reply with 'no'

STEP 2 BODY (delay 3-5 days, ~50 words):
Hey {{firstName}},

As a business owner, I know emails can easily get buried. Bumping this
one up to the top of your inbox!

If you are thinking about selling your franchise business, we'd be happy
to offer you a complimentary valuation to help in your decision making.

Want to chat next week?

Theodore Baird
{{brand_name}}

STEP 3 BODY (delay 5-7 days, soft close — TBD):
[design and test]
```

**Variables (filled per-row by Claude API):**
- `{{firstName}}` — from enrichment
- `{{audience_descriptor}}` — "franchise business owners" / "[industry] business owners"
- `{{franchise_system_or_industry_peer}}` — specific named system (FS) or recent comparable sale (CS)
- `{{optional_signal_anchor}}` — "I noticed [specific recent event]" — only if signal data exists; otherwise omit (don't fake)
- `{{brand_name}}` — "Franchise Sellers" or "Company Sellers"

**Spintax discipline:**
- Min **50% content variation** on initial emails (industry guidance for spam-filter avoidance)
- 3 subject variants per step, rotated by Instantly
- Body uses `{{RANDOM | a | b | c}}` sparingly — over-spinning destroys specificity (FS-Maaco was the example of "too much spintax + bad list")
- Signal-anchor takes precedence over surface variation

**Offer rotation (A/B testing infrastructure):**
- Each prospect assigned to OOV control variant by default
- Periodic test cohorts (every ~500 records) get assigned to one alternative offer (see `04-offer-concepts.md`)
- Track downstream: positive reply rate, OOV-delivered rate, listing conversion rate

### Layer 7 — Sending (Instantly)

**Configuration per brand:**
- 1 organization, brand-tagged campaigns (FS-* and CS:*)
- ~30 sending domains per brand (already warmed)
- 2-3 mailboxes per domain (~60-90 sending addresses per brand)
- Cold send cap: **25-30 emails per mailbox per day** (after warmup volume)
- Continuous warmup: ~10-15 emails/mailbox/day in background, permanent
- Inter-send gap: 60-120s with random jitter
- Daily campaign limit per mailbox: enforce hard cap

**Brand-walls enforced:** campaigns only pull from matching brand's domain pool. No FS prospect ever sees a CS sending domain.

### Layer 8 — Engagement Tracking

**Instantly webhooks → Claude Code → Data Layer:**

| Webhook event | Claude Code action |
|---|---|
| `email_sent` | Update `last_sent_at` + step counter on record |
| `email_reply_received` | Pull full reply via `get_email` → classify → update record + trigger routing |
| `email_bounced` (hard) | Mark permanent suppression, push to Instantly block list |
| `email_bounced` (soft x3) | Mark `needs_re-verification`, halt this contact |
| `email_unsubscribed` | Permanent suppression, push to all 3 layers |
| `email_open` | (optional — open tracking can hurt deliverability; default OFF) |
| `link_click` | Same — default OFF |

**Open + click tracking:** **disabled by default.** 2026 deliverability research shows open-pixel tracking flags as commercial mail and reduces inbox placement. Track replies + opportunities only.

### Layer 9 — Reply Classification (Claude API, per message)

Every inbound reply triggers a Claude API call to classify intent:

| Category | Trigger language examples | Routing action |
|---|---|---|
| `positive_meeting_ready` | "Let's chat", "Yes, book a call", "Sounds good", calendar acceptance | Create GHL contact (matching brand) + trigger Discovery Call workflow + suppress all sequences |
| `positive_curious` | "Tell me more", "Send me the info", "I'd be interested" | Auto-respond with OOV/info delivery + create soft GHL lead + light nurture |
| `positive_with_timeline_objection` | "Yes but not for 2 years", "Interested but not ready" | Set cooldown to stated timeline + capture date + suppress |
| `objection_not_now` | "Not at this time", "Touch base end of 2026" | Extract date if mentioned → cooldown until date. Default 6 months if no date. |
| `objection_not_interested` | "No thanks", "Not interested", "NO" alone, "Not for sale" | Permanent suppression for cold; eligible for offer-variant retesting after 12mo |
| `wrong_person` | "I'm not the right contact", "Talk to X" | Mark this record `wrong_person=true`; if referred name given, parse for new record |
| `wrong_intent_buyer_side` | "I'm interested in resales", "Acquiring not selling" | Route to Buyer Manager (Yvonne) pipeline, NOT cold suppression |
| `unsubscribe` | "Unsubscribe", "Remove me", "Take me off your list" | Permanent suppression in all 3 layers + write to GDPR log |
| `out_of_office` | OOO auto-reply | Extract return date → schedule retry then |
| `referral` | "Talk to my CFO/partner/etc" | Parse referred name, create new lead record, flag for warm-intro sequence |
| `meeting_accepted` | Calendar invitation acceptance | Same as `positive_meeting_ready` |
| `other` | Anything not matching above | Flag for human review (Theodore inbox) |

**Implementation:** Claude API system prompt provides the categories + examples. Per-reply prompt includes the original cold email subject, the reply body, and the prospect's metadata. Returns category + extracted entities (date, referral name, etc.) as structured JSON.

**The big win vs. the historical engine:** 100% of replies get classified going forward. Within 30-60 days you have a clean dataset that lets you re-run the reply-content analysis from `INSTANTLY-CAMPAIGN-RETROSPECTIVE.md` with proper data.

### Layer 10 — CRM Routing

**Routing matrix:**

| Reply category | Action in matching GHL workspace | Action in data layer |
|---|---|---|
| `positive_meeting_ready` / `meeting_accepted` | Create contact, source=Cold Email, trigger Discovery Call workflow | `in_crm=true`, `crm_record_id` set |
| `positive_curious` | Create lead, status=Info Request, trigger OOV-only workflow | `in_crm=true`, light nurture flag |
| `positive_with_timeline_objection` | Don't create yet | Cooldown date + re-engage scheduled |
| `wrong_intent_buyer_side` | Route to Buyer Manager workflow (separate from cold) | Mark as `buyer_side_lead` |
| `referral` (with name) | Create lead with `referral_source` = original prospect | New record with `warm_intro_pending` |
| All others | None | Update suppression, no CRM action |

**Brand routing:** `brand` field on the data-layer record determines which GHL workspace receives the contact. **Never** cross-route.

**Once in GHL:** the existing workflows take over (OOV intake, Toolkit vs. Full Service routing, etc.). Claude Code's job is done for this contact — except for monitoring the GHL state via `crm-snapshot/crm-master.json` for downstream events (closed-lost → 12mo cooldown, closed-won → permanent customer flag).

---

## Tools matrix — What's Claude Code vs. External

### Claude Code does (no per-call cost beyond Anthropic API):
- All orchestration logic
- Pulls/pushes to all APIs
- Dedup + ICP scoring
- Suppression filter (Layer A)
- Spintax + signal-anchor generation
- Pushes batches to Instantly
- Polls Instantly webhooks
- Classifies every reply (Claude API call per message)
- Routes to GHL
- Builds weekly performance dashboards
- Scheduled jobs (cron on droplet, eventually)
- Skills library for Theodore to invoke ad-hoc

### External tools — Phase 1 (essential, ~$500–800/mo total)

| Tool | Role | Status | Monthly cost (rough) |
|---|---|---|---|
| **Instantly** | Sending only | ✅ Existing subscription | $$$ (you're already paying) |
| **Anthropic API** | Reasoning + reply classification | ✅ Existing access | $50–150 (usage-based) |
| **Airtable** | Data layer | ✅ Existing | $$ (existing tier) |
| **GHL FS** | Post-conversion CRM (FS brand) | ✅ Existing | $$ |
| **GHL CS** | Post-conversion CRM (CS brand) | ✅ Existing | $$ |
| **Email Verifier** | Pre-send bounce gate | ⚠️ Confirm provider | $50–100 |
| **Anthropic Claude.ai** | (Optional — for direct interaction) | ✅ Existing | flat |

### External tools — Phase 2 (sourcing + enrichment, ~$600–1,000/mo additional)

| Tool | Role | Why now | Cost |
|---|---|---|---|
| **Apollo** | Firmographic + contact sourcing | When existing pool is exhausted (12+ months out) | $$$ (~$300–600/mo) |
| **Hunter / Snov / Findymail** | Email finder waterfall | When sourcing real-time emails for new contacts | $$ (~$100–200/mo) |
| **PDL or Datagma** | Deep person enrichment, job-change signals | Phase 2+ when adding signal-anchored sourcing | $$$ (~$200–500/mo) |

### Drop / Cancel after Phase 0:

| Tool | Reason |
|---|---|
| **Clay** | Replaced by Claude Code + direct APIs. Archive complete. Cancel saves $349–799/mo. |
| **RevyOps** | Defer — only buy if Airtable proves insufficient at scale. |

---

## Build phases

### Phase 0 — Foundation (✅ MOSTLY DONE)

- ✅ Workspace setup + scaffolding
- ✅ Decision log + design docs
- ✅ Historical campaign analysis (`INSTANTLY-CAMPAIGN-RETROSPECTIVE.md`)
- ✅ Database archive across 4 sources (`PHASE-0-DATABASE-AUDIT.md`)
- ⏳ Settle Airtable-vs-RevyOps (defer to Phase 2 decision point)
- ⏳ Confirm email verifier provider
- ⏳ Locate API keys: Instantly (we have MCP), both GHLs (we have data via crm-snapshot), Airtable, Anthropic
- ⏳ Run full dedup + Tier A audit (Task #6)

### Phase 1 — Build the framework + ship probes across all streams (weeks 1–4)

**Goal:** Build a framework that runs every campaign type as a first-class stream. Ship 500-record probe campaigns across each stream from the existing archive. No net-new sourcing yet. Validate orchestration end-to-end across all stream types.

**Streams to probe in parallel:**

1. **`seller_cold_fs_niche`** — pick 2-3 specific franchise systems from the Tier A FS pool (e.g., FirstLight, Comfort Keepers, Code Ninja) → 500 contacts each → 3-step sequence with system-named opener.
2. **`seller_cold_cs`** — pick 1-2 industries with the cleanest list quality from Tier A CS pool (e.g., Home Health, Consumer Services) → 500 contacts each → rebuilt template (no `{{Paragraph One}}`).
3. **`buyer_reactivation`** — Airtable Active Contacts with buyer flag → 500 contacts → "the franchise business you looked at" / "your business for sale inquiry" templates.
4. **`referral_partner_advisor`** — Airtable Business Advisors (5,212 CPAs/Wealth Managers/CEPAs) → 500 contacts → partnership framing.
5. **`event_pre`** — confirmed upcoming-event attendee list (whichever event is next) → templated pre-event touch.

**Why ship probes in parallel:** each stream has a different audience, different reply patterns, different routing. The framework needs to handle all of them from day one. Sequential rollout would mean the framework is incomplete and we'd be re-architecting on the fly.

**Deliverables:**
- Suppression engine built + tested (Layer A + B), shared across all streams
- Template library v1 with at least one template per stream
- Reply classifier wired up + tested across stream types (routing branches by `campaign_type`)
- 5 probe campaigns running concurrently (one per stream above)
- CRM routing tested on positive replies for each stream
- Weekly dashboard v1 with per-stream metrics

**Per-stream success gates (probes ship to full volume when met):**

| Stream | Positive % target | Investigate below | Bounce halt | Unsub halt |
|---|---:|---:|---:|---:|
| `seller_cold_fs_niche` | 6% | 3% | > 5% | > 5% |
| `seller_cold_cs` (rebuilt) | 3% | 1% | > 5% | > 5% |
| `buyer_reactivation` | 10% | 5% | > 5% | > 5% |
| `referral_partner_advisor` | 4% | 2% | > 5% | > 5% |
| `event_pre` | 8% | 4% | > 5% | > 5% |

**Note on targets:** these are conservative. Historical data showed some streams hitting much higher (buyer reactivation up to 22%, event-tied up to 9%). Setting "investigate below" thresholds where new replication of historical performance starts to look concerning, not setting the historical ceiling as the target.

**System-wide Phase 1 success:**
- All 5 stream probes deliverable end-to-end (lead → send → reply → classify → route)
- ≥ 60% classifier coverage (non-`other`) across all streams
- ≤ 5 min reply-to-routing latency
- No cross-brand mistakes (FS prospect never sees CS sending domain, CS prospect never lands in FS CRM)

### Phase 2 — Net-new sourcing (weeks 5–8)

**Goal:** 6K/month volume. Add Apollo + waterfall enrichment + sourcing pipeline.

**Deliverables:**
- Apollo integration wired
- Enrichment waterfall built (Hunter → Findymail → PDL fallback)
- ICP scoring engine refined with new signal weights based on Phase 1 outcomes
- Net-new sourcing pipeline producing ~500 fresh leads / week
- Spintax library expanded with industry-specific signal anchors

**Architectural decision point:** evaluate whether Airtable is holding up at 100K+ rows. If not, evaluate RevyOps.

### Phase 3 — Intent-signal + scale (months 2+)

**Goal:** 10K+/month. Move toward semi-autonomous campaign generation.

**Deliverables:**
- PDL job-change detection feeding micro-campaigns
- M&A activity detection (news API + Claude)
- LinkedIn signal extraction (bio language, transitions)
- Per-vertical micro-campaign generation (10–25 small campaigns/month vs 2-3 big)
- Continuous reply-classification feedback loop refines copy weekly

---

## Skills library (Claude Code Skills to build)

Following the Salesforge pattern, build reusable skills callable via prompts:

| Skill | What it does | Inputs |
|---|---|---|
| `source-leads` | Pull from Apollo + existing archive matching ICP criteria | Industry, geography, employee range, signal filters |
| `enrich-batch` | Run enrichment waterfall on a batch | List of candidate records |
| `dedupe-and-score` | Match against data layer, compute ICP score | Enriched batch |
| `suppress-and-filter` | Apply 3-layer suppression | Scored batch |
| `generate-sequence-variants` | Produce spintax variants for a sequence | Template + brand + ICP segment |
| `pre-launch-audit` | Verify campaign config before activation | Campaign ID |
| `push-to-instantly` | Create / update campaign + push leads | Validated batch + sequence ID |
| `classify-reply` | Classify a single reply via Claude API | Email body + thread context |
| `route-positive` | Push positive replies into matching GHL | Classified reply |
| `mailbox-health-check` | Daily check on sending domain reputation | (none — runs weekly) |
| `campaign-performance-report` | Weekly per-campaign performance summary | Date range |
| `cooldown-reactivation` | Find prospects whose cooldown is up | (runs daily) |

Each skill lives under `cold-email-outbound/skills/<skill-name>.md` (Claude Code's Skills convention) with the prompt + tool list + example invocation.

---

## Open decisions (settle before Phase 1 starts)

1. **Airtable vs. RevyOps** — recommendation: Airtable for Phase 1.
2. **PDL vs. Datagma for deep enrichment** — recommendation: PDL.
3. **Hunter vs. Snov vs. Findymail for email finder** — recommendation: Findymail.
4. **Email verifier provider** — Theodore action: confirm which provider you used previously and reactivate.
5. **No-reply cooldown duration** — default 60 days. Confirm.
6. **Closed-lost cooldown duration** — default 12 months. Confirm.
7. **Step 3 (soft close) email design** — to be drafted.
8. **4 Notion discrepancies** — still pending (FS pricing onboarding fee, Toolkit multi-location pricing, brand-age framing, Xponential special pricing). Resolve before any seller-cold copy ships.

---

## Risk register

| Risk | Mitigation |
|---|---|
| **List quality kills good copy** (Maaco precedent: 8.57% bounce → 0.21% reply) | Mandatory re-verification before any send. Halt if bounce >5%. |
| **CS broad-industry template re-emerges as default** because it's easy | Explicit decision-log entry to deprecate. Don't ship CS broad without signal-anchoring. |
| **Reply classification quality drift** as Claude API model versions change | Pin model version in classifier. Re-eval quarterly with sample audit. |
| **GHL rate limits cause suppression sync failures** (per master CLAUDE.md outage history) | Use existing `crm-snapshot/` master JSON for in_crm checks. Never add another GHL puller. |
| **Airtable scaling cliff at 100K+ rows** | Monitor row count + query times. Migrate plan if cliff hits. |
| **Two GHL workspaces drift in field definitions** | Document field map per brand. Don't auto-create new fields from cold-email engine. |
| **Domain reputation collapse from a single bad campaign** | Mailbox-health-check skill flags weekly. Halt any campaign with >2% bounce. |
| **Reply volume exceeds human capacity** for review of `other`/unclassified replies | Aggregate weekly. If `other` rate >20%, refine classifier prompts. |

---

## Measurement framework

**Phase 1 per-stream success metrics (per-stream gates from the Phase 1 section above):**

System-wide must-hits:
- Classifier coverage (non-`other`): > 60% (investigate below 40%)
- Time from reply → routing: < 5 min (investigate above 15 min)
- Bounce rate (any campaign): < 2% (halt above 5%)
- Unsubscribe rate: < 2% (halt + re-eval copy above 5%)
- Zero cross-brand routing errors

**Phase 2 success (volume + quality maintained):**
- 6K/month sustained for 4 weeks
- Phase 1 quality metrics held within ±20%
- New sourcing pipeline producing >= 500 leads/week at >= 60 ICP score

**Phase 3 success (scale):**
- 10K+/month
- 30%+ of opportunities come from signal-anchored micro-campaigns (vs. broad reactivation)
- Cost per opportunity decreasing month-over-month
