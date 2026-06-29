# Cold-Email Learnings — FS/CS Outbound Build

This is the decision-grade reference for our Franchise Sellers / Company Sellers cold-email platform. It maps everything worth knowing from three external cold-email sources against what we have already built (187K deduped pool, 88 warmed Instantly mailboxes, 11-category reply classifier, deployed `/marketing` operator dashboard, half-built Stage0-4 qualification funnel), then tells you exactly what to adopt, what to skip, and what to verify before the first live send. Read the Executive Summary and the ADOPT NOW table first; everything else is supporting detail.

> **Note (2026-06-25):** Synthesized from three YouTube transcripts — one LeadGenJay video (LGJ) and two FindyMail-sponsored demos (FM1, FM2) — plus a teardown of the `cold-email-quickstart` "LeadGenJay" Claude skill (SKILL), all cross-checked against our own baseline inventory (BASE). This document is the merge of the working synthesis with an adversarial critique pass. Prose here follows Malcolm's voice rules: no em dashes, no random bolding for drama, short direct sentences.

---

## 1. Executive summary

The top eight takeaways, in priority order.

1. **We are ahead of every source on the hard parts.** Data (187K deduped from 1.3M), 3-layer suppression, LeadMagic-to-ZeroBounce verification waterfall, an 11-category reply classifier with dual-GHL routing, 88 warmed mailboxes, and a deployed RBAC operator dashboard. No source matches us. The videos top out at "monitor replies manually." Treat all three videos primarily as validation, not instruction.

2. **Qualification is the single biggest lever everyone agrees on, and it is our biggest open gap.** LGJ's exact framing: "scrape 10,000, 40% are gone immediately, the 60% remaining are the best," and "qualification is the fastest way to double or triple your reply rates." Our Stage0-4 qualification funnel is specced but only half-built (Stage 1 enrichment exists; the AI-judgment gates, geo targeter, and pre-send `qualification` object are still "build next"). Finishing the funnel is the highest-ROI work in the queue, and it saves verification spend on top of lifting replies (see #8).

3. **Adopt an explicit, code-enforced pre-send gate.** LGJ's deploy skill and SKILL's 8 gates converge: bounce <3%, warmup score OK, SPF/DKIM/DMARC present, open + link tracking OFF, plain-text, spintax present, enough A/B variants, ICP confirmed. We already enforce most of these implicitly in config. Make them one hard gate beside `CEO_DRY_RUN`, and add the two legal checks from Section 9 to it.

4. **Compliance is a category the sources never mention and we cannot skip.** None of the five extractions covers CAN-SPAM: physical postal address, functional opt-out in every message, honor within 10 business days. Our suppression set catches replies that say stop, but nothing confirms an opt-out line or a physical address exists in the outgoing template. This is a legal requirement, not best practice. See Section 9.

5. **Copywriting consensus is sharp and directly actionable.** Email 1 probes for the problem and never sells, per-segment pain vocabulary (no shared keywords), an anti-AI-tell scrubber pass, and a breakup final email. Most of this is a prompt-scaffold upgrade to our existing copy engine, not a rebuild. The breakup and cadence must be re-tuned for seller psychology, not copied from the SaaS sources verbatim (see ADOPT NOW P3).

6. **The Reverse Lead Magnet (instant seller valuation teaser) is our most strategically interesting idea, with a hard caveat.** It maps onto our existing CS valuation machinery. But an auto-generated "what your business could sell for" number is a valuation claim with real expectation-setting and credibility risk in brokerage. Frame it as a rough range with disclaimer language and route it through Theodore/Malcolm review before it ships. Upside is real; it is not free upside.

7. **The LeadGenJay skill is HARVEST-only. Do not install.** It is a `curl|bash` affiliate funnel coupled to Turso + Inbox Insiders + Consulti + an Instantly affiliate link, conflicting with our owned stack and our one-canonical-datastore principle. Lift the patterns (no installer run required); install nothing. See Section 7.

8. **Verify-last ordering is confirmed correct, and it is a cost win.** Every serious source puts AI qualification before email verification so verify credits are not spent on leads you will drop. Our funnel already defers ZeroBounce to Stage 4. Confirm enrichment and personalization also run only on post-verify survivors. Because ZeroBounce is metered and we run `uncertain_only`, finishing the funnel reduces verification spend, not just lifts replies.

---

## 2. Per-source TL;DR

**LGJ — LeadGenJay video.** The richest source. Pushes AI qualification before send as the top reply-rate lever ("10,000 scraped, 40% gone, 60% best"), a cheap-to-expensive funnel with verify in the middle, a pre-launch gate checklist, AI self-critique on copy, field/fallback test-add before bulk push, a breakup email, implicit-objection strategy scaffolding, and the Reverse Lead Magnet. Also warns to use CLI over a heavy MCP server to avoid context bloat. Heavily monetized (Instantly affiliate, Inbox Insiders) but the ideas are sound.

**FM1 — FindyMail-sponsored demo #1.** Lighter. Reinforces "email 1 starts a conversation, never sells," per-segment relevance, human-copywriting / anti-AI-tell, ICP-as-hypothesis with Claude as critic, keep your instinct as an A/B control, and "name skills explicitly, don't trust auto-load." Two skills, no DB, no qualification, no deliverability gates. Vendor angle is FindyMail sourcing + built-in verification.

**FM2 — FindyMail-sponsored demo #2.** Same author/pattern as FM1, reinforcing the same copy and operator-hygiene points with a parallel-A/B-test framing (segment x angle, double down on the winner). Carries the same explicit caveat as FM1: FindyMail's built-in verification does NOT replace our re-verify on a stale list. Confirms the "thin orchestrator + domain skills" pattern with less capability than LGJ.

**SKILL — `cold-email-quickstart` teardown.** The LeadGenJay Claude skill itself. Three orchestrator files that delegate every phase to 8 install-gated sub-skills fetched via `curl -sSL '...?items=...' | bash`. Ships an affiliate link (`refer.instantly.ai/lgj` / `LGJ10`), an immediate Inbox Insiders Stripe charge, a Turso data layer, and Consulti scrape+verify. Useful artifacts: the 8 pre-launch gates, the qualify-verify-personalize sandwich, numeric yardsticks (4wk warmup, warmup >=95, bounce <3%, >=9 variants split 3/2/2/2, re-verify if >30 days), and a resumable `.metadata.json` per-campaign state machine. Verdict: harvest, do not install.

---

## 3. Cross-cutting patterns (2+ sources agree = signal)

| Pattern | Sources | Signal |
|---|---|---|
| Cheap-to-expensive funnel; qualify before verify; enrich only survivors | LGJ, SKILL, BASE confirms | Strong. Our ordering is industry-correct and a cost win. |
| Qualification is the #1 reply lever (~2-3x) | LGJ, FM1/FM2 (segment relevance) | Strong. Justifies finishing our funnel. |
| Explicit pre-send gate / deploy-PAUSED-only | LGJ, SKILL | Strong. Mirror as one hard gate. |
| Email 1 = start a conversation, not sell | FM1, FM2 | Strong, concrete copy rule. |
| Per-segment pain vocabulary, never one generic blast | FM1, FM2, LGJ | Strong. |
| Anti-AI-tell scrubber + self-critique on copy | LGJ, FM1, FM2 | Strong. Matches Malcolm's voice rules. |
| Breakup / final email | LGJ, FM1, FM2 | Strong concept; re-tune for sellers (Section 4 P3). |
| Claude = operator; intelligence from tools+skills+you | FM1, FM2, LGJ | Strong. Already our architecture. |
| Strategy/ICP artifact produced first, feeds scrape + copy | LGJ, SKILL | Medium-strong. One upstream source of truth. |
| Database everything yourself; vendor analytics insufficient | LGJ, BASE does this | Medium. We already DB + route to GHL. |
| Keep your instinct as a control segment; A/B parallel; double down | FM1, FM2 | Medium. Adopt at first-send. |
| Don't trust skill auto-load; name skills explicitly | FM1, FM2 | Medium. Runbook hygiene for Malcolm. |
| Use CLI over heavy MCP server to avoid context bloat | LGJ | Validates our zero-dep engine path (Section 5). |
| 4-week warmup before send | LGJ, SKILL | Confirmed; we are already warmed. |

---

## 4. What we already do well (validated against BASE)

Do not "adopt" any of these. We have them, often stronger than the sources.

- **Data + dedupe.** 1.3M to 187K Tier A, reproducible no-data-loss dedup. Stronger than LGJ's single exclusion list; the videos have no dedupe at all.
- **3-layer suppression** (do-not-contact / in-CRM via read-only snapshot / cooldowns), applied once across all channels. SKILL only has `do_not_contact=1`; videos have none.
- **Verification waterfall** LeadMagic-to-ZeroBounce, `uncertain_only` cost mode, 90-day re-verify, free enrichment backfill. Smarter than "trust the vendor."
- **Verify-last ordering** already correct (ZeroBounce at Stage 4).
- **Copy engine.** Hand-written templates + surgical AI anchoring, deterministic spintax keyed by `canonical_id`, honest signal-anchor deletion, 6-CTA offer rotation, >=50% variation floor. We already do spintax + per-brand voice.
- **Sending posture.** 30 cold/mailbox/day cap, open + link tracking OFF by default, 60-120s jitter, brand-walls at send, >=100 bulk-write guardrail (chunked 50 + 1s cooldown), Cloudflare-UA fix, bounce/unsub circuit breakers.
- **Reply handling.** 11-category classifier (pinned `claude-sonnet-4-5`, heuristic fallback) + routing matrix to dual GHLs with brand-walls. No source has anything close.
- **Operations.** Deployed `/marketing` dashboard, FastAPI operator API, RBAC, 12 invocable skills, go-live runbook + selftest, `CEO_DRY_RUN` panic rollback.
- **Architecture.** Claude-as-operator + zero-dep design, the exact philosophy all three videos preach.

---

## 5. ADOPT NOW (prioritized)

| # | Change | Source | Why |
|---|---|---|---|
| P0 | **Finish the Stage0-4 qualification funnel.** Stand up Stage 0 hard filters, Stage 2 AI judgment (current-owner-active, franchise-vs-DBA detection, PE/public exclusion, owner-in-US), the geo-radius targeter, and the `qualification` result object + pre-send gate. | LGJ, SKILL; BASE gap | Qualification is the one lever all sources call 2-3x ("10,000 scraped, 40% gone, 60% best"). Our brokerage logic (CS rev <=$25M, FS locations <=25, DBA detection) makes our version stronger than any generic ICP match. It also saves ZeroBounce spend by dropping leads before verify. Expect Tier A to shrink; that is correct. |
| P0/P1 | **Re-verify the aged 187K pool before first send.** Run the full pool (or at least the first send batch) through the LeadMagic-to-ZeroBounce waterfall fresh, not on the 90-day window assumption. | LGJ, SKILL, BASE | Our list is a historical 1.3M dedup, potentially years old. Every source scrapes fresh data. Sellers close or sell businesses and emails die. Staleness is a bigger bounce + compliance risk for us than for any source. This is more urgent for us than for them. |
| P1 | **Explicit code-enforced pre-send gate beside `CEO_DRY_RUN`.** Bounce <3%, warmup score OK, open + link tracking OFF (verify live Instantly config honors it), plain-text, spintax present (>=50% variation), enough A/B variants ready, copy approved, ICP confirmed, **physical address block present, opt-out line present** (Section 9). Adopt deploy-PAUSED-only as an explicit dashboard state. | LGJ, SKILL | Cheap insurance; turns implicit config into a launch checklist and folds in the two legal checks. |
| P2 | **Field-exists + fallback test-add before bulk push to Instantly.** Test-add one lead, confirm every `{{variable}}` resolves with a fallback set, then bulk-push. | LGJ | Prevents broken-variable live sends at go-live. LGJ calls this "the step that screws up a bunch of people." Highest value / lowest effort here. |
| P3 | **Copy upgrades in `engine/copy_gen.py` + templates.** Email 1 = soft pain-probe, no pitch (verify our seller email 1 does not sell). Anti-AI-tell scrubber (kill "it's not X, it's Y", random bolding, em dashes) + a self-critique final pass ("reread as prospect / AI-smell scan / pain-specificity") using our existing Anthropic key. Per-segment pain vocabulary (FS franchise-resale vs CS private-business pains differ). Inject real proof points (deals closed; keep "hundreds of buyer inquiries each month" qualitative until the 250-400/mo stat is confirmed). **Breakup email re-tuned for seller psychology** ("no rush, if now isn't the time I'll check back") — do NOT copy LGJ's "point me to the right person" referral breakup; a sole owner has no one else who owns outbound. | FM1, FM2, LGJ | Concrete, agreed-on copy rules that land as a prompt scaffold, not a rebuild. Seller cadence is one-in-a-lifetime and emotionally loaded; the SaaS aggressive 3-4 email + referral breakup is wrong for us. |
| P4 | **Strategy-doc prompt scaffold** with implicit-objection pre-counters + buying triggers + exclude-titles, adapted to seller psychology. Pre-counter the real objections: "is my business even worth listing," "brokers take huge fees," "I'm not ready to sell." Make this ICP/strategy artifact the single upstream source the audience-builder and qualifier both read. | LGJ | One upstream source of truth; objection pre-counters tuned to sellers, not SaaS buyers. |
| P5 | **ICP-as-hypothesis / Claude-as-critic step** in Malcolm's audience builder. Have Claude critique a segment definition and propose alternatives before building the audience. Pair with keeping the original instinct as an A/B control. | FM1, FM2 | Our 0-100 scorer rates a list; this critiques the definition upstream, which we lack. |
| P6 | **Operator hygiene in Malcolm's runbook.** Document "name skills explicitly, don't trust auto-load" and file-persist state for session-limit restarts. | FM1, FM2 | Cheap reliability for the human operator. |

---

## 6. ADOPT LATER (worthwhile, not urgent)

- **Reverse Lead Magnet = instant seller valuation teaser** (LGJ). Reuse the CS `valuation/` machinery; offer a custom auto-generated estimate with URL-param auto-fill to remove friction. **Must carry range/disclaimer framing and Theodore/Malcolm review** — an instant "what your business could sell for" number is a regulated-adjacent valuation claim, not the SaaS "bestseller book topic" teaser LGJ gets away with. Highest upside, post-go-live spike. The 1-2% to 5% lift is unverified vendor marketing, but the instant-valuation hook is proven in our space.
- **Wire the existing Instantly inbox-placement test + blocklist sync** (BASE, Instantly API). These are NOT net-new builds. The Instantly API surface already exposes `inbox_placement_*` and `blocklist_*`. BASE flags inbox-placement as a "gap to consider" and notes Suppression "Layer B (Instantly global block list sync) is designed but not coded." Both are direct API wires. Stand up a seed-list inbox-placement test before the first big send and code Layer B blocklist sync.
- **Closed-loop 30-day learning** (LGJ). After real sends, run a Claude pass over our DB'd reply/title/industry/A-B data to propose new ICP filters + variants. We already DB everything; this is the analysis layer.
- **First-send A/B structure** (FM1, FM2). Parallel segment x angle tests with a control; double down on winners.
- **Perplexity Sonar as a cheaper research substrate** for Stage 2 judgment (LGJ, SKILL). Cost-compare vs Anthropic once Stage 2 is live. Note: Perplexity has no free API tier.
- **Resumable per-campaign `.metadata.json` state machine** with idempotent phase pre-checks (SKILL). Lets Malcolm pause/resume/redo a single campaign phase from the dashboard.
- **Vector-KB reply-draft bot** (LGJ). Natural layer atop our existing 11-category classifier.
- **Feed real broker/valuation call transcripts** as copy/strategy input (LGJ). We have GHL call data + valuation calls. For seller psychology specifically, real recorded seller-objection language is the highest-quality input for the per-segment pain vocabulary in P3. Stronger than intake forms; worth elevating once Stage 2 lands.
- **FindyMail / Consulti NL niche sourcing** (FM1, FM2, LGJ). Only if we exhaust the 187K pool or need a net-new vertical fast. Not now (~5yr runway). **Caveat: FindyMail's built-in verification does NOT replace our re-verify on a stale list** — both FM extractions say so explicitly. Never trust vendor-verified data blindly.

---

## 7. SKIP and why

- **Install the `cold-email-quickstart` skill / `curl|bash`.** Affiliate funnel, vendor lock-in, standing RCE dependency on a marketing domain holding our keys. Hard no.
- **Inbox Insiders mailbox provisioning** ($3.50/mbx/mo recurring). We already own 88 warmed mailboxes. Re-buying infra we have.
- **Turso / Supabase / Neon data layer.** Conflicts with our one-canonical-datastore principle; we have the 187K pool + engine.
- **Consulti scrape+verify.** Solves sourcing/verification we have already solved better (LeadMagic-to-ZeroBounce).
- **Email Bison / FindyMail MCPs as our sequencer/data source.** We are committed to Instantly (warmed, UA-fixed); these appear in the videos only as the alternate.
- **Two-Max-account session-limit hack** (LGJ). Our engine is a headless metered API, not interactive sessions. Also TOS-grey; do not institutionalize.
- **"Personalize on subscription tokens"** (LGJ). Our headless FastAPI service must use the metered Anthropic API; it cannot piggyback a Max plan server-side.
- **Instantly affiliate signup** (`refer.instantly.ai/lgj` / `LGJ10`). Already a customer.

---

## 8. LeadGenJay verdict — HARVEST IDEAS ONLY, do not install

**Reasoning.** The skill is a thin orchestrator with no real logic. Every phase delegates to 8 LGJ-exclusive sub-skills you only get via `curl -sSL 'leadgenjay.com/...?items=...' | bash` — a server-controlled, unsigned, querystring-versioned remote script run with full shell privileges that would hold our Instantly + Anthropic + GHL-adjacent keys. Structurally it is an affiliate funnel: Phase 1 = Instantly affiliate link, Phase 2 = immediate Stripe charge to Inbox Insiders, data layer = Turso, sourcing+verify = Consulti. We are strictly ahead on every layer that matters, and adopting it would have us re-buy infrastructure we own and fork our 187K pool into someone else's SQLite, violating our one-canonical-datastore rule.

**Important: harvesting needs no installer run.** The valuable patterns come from the documented behavior of the wrapper plus the videos. We capture the full value without ever executing the `curl|bash` installer, so this is not discarding un-evaluated value — it is taking the ideas and leaving the payload.

**Harvest exactly these (7 patterns):**

1. The 8 pre-launch gates as a code-enforced pre-send checklist (Section 5 P1).
2. Strategy-before-scrape: one ICP/strategy artifact feeding both audience-builder and qualifier (P4).
3. Cheap-to-expensive funnel with a hard verify gate in the middle; personalize only post-verify survivors (confirm in our funnel).
4. Deploy-PAUSED-only / human-activates discipline as an explicit dashboard state.
5. Resumable per-campaign `.metadata.json` state machine with idempotent phase pre-checks (ADOPT LATER).
6. Numeric yardsticks: 4wk warmup, warmup >=95, bounce <3%, >=9 variants (3/2/2/2), re-verify if >30 days before activation.
7. From LGJ's video specifically: AI self-critique copy loop, field/fallback test-add, breakup email (seller-tuned), implicit-objection scaffold, RLM valuation teaser (with disclaimer).

The FM1/FM2 videos do not change this verdict. They are a different (FindyMail) author and only weakly reinforce the "thin orchestrator + domain skills" pattern, with less capability (2 skills, no DB, no qualification, no deliverability gates).

---

## 9. Compliance (legal, not optional)

The sources never mention this. It is a legal requirement and must gate the first live send. At least items 1-2 belong on the pre-send gate alongside `CEO_DRY_RUN`.

1. **CAN-SPAM physical postal address.** Every commercial email must contain a valid physical mailing address. Our copy engine builds from markdown templates; nothing in BASE indicates a footer/address block exists. Verify and add to the gate before any live send.
2. **Functional opt-out in every message, honored within 10 business days.** BASE shows suppression on unsubscribe (`PERMANENT_SUPPRESSION_FLAGS`; the routing matrix "unsubscribe/no -> permanent suppression"), but nothing confirms an opt-out mechanism is in the outgoing email itself. For cold seller outreach, a plain-text "reply STOP, or let me know and I'll take you off my list" line is the right approach (list-unsubscribe headers are awkward on cold sends). Confirm every template carries an opt-out line, and confirm the reply-driven STOP path feeds the same suppression set.
3. **Honest subject lines, no deceptive headers.** Relevant because LGJ's recommended subjects ("quick favor," "pulled something for you") and the FM anti-AI-tell pass border on misleading-pretext territory for a brokerage. Keep subject lines truthful about who we are and why we are writing.
4. **DBA / sole-proprietor individual-address nuance.** Many seller prospects are sole proprietors or DBAs (our qualification spec explicitly does franchise-with-DBA detection). A DBA owner's email may be a personal/individual address, which raises the compliance bar above pure B2B. The SaaS-oriented sources never address this. Treat individual-looking addresses conservatively.

---

## 10. Deliverability + infra checklist (measured vs our 88-mailbox Instantly setup)

| Item | Best-practice (sources) | Our status | Action |
|---|---|---|---|
| Warmup before send | 4 weeks; warmup score >=95/mailbox (LGJ, SKILL) | 88 mailboxes warmed; 12/mailbox/day permanent warmup | Add a warmup-score readout to the pre-send gate (BASE notes no mailbox-reputation monitoring beyond bounce/unsub) |
| SPF / DKIM / DMARC | Required per mailbox (SKILL gate) | Not verified in BASE | **Verify** per sending domain; add to gate |
| Open tracking | OFF (SKILL) | OFF by default | Confirm live Instantly campaign honors it |
| Link tracking | OFF (SKILL) | OFF by default | Confirm in live config |
| Plain-text only | Yes (SKILL) | Templates are plain markdown | Confirm rendered send is plain-text |
| Spintax / variation | Present; >=9 A/B variants (LGJ, SKILL) | Deterministic spintax + >=50% variation floor + 6-CTA rotation | Confirm variant count meets the bar at deploy |
| Daily send cap | Conservative ramp | 30 cold/mailbox/day hard cap | Ahead |
| Bounce gate | Hard stop >3% (SKILL) | Halt >=5% / warn >=2% | **Adopt the 3% hard-stop.** Cost of cooking 88 warmed mailboxes is high; this is a decision, not a "consider" |
| Inbox-placement / seed testing | Not in sources | `mailbox-health` is a stub | **Wire the existing Instantly `inbox_placement_*` test** before first big send (not a net-new build) |
| Instantly global blocklist sync | — | Suppression Layer B designed, not coded | **Wire the existing Instantly `blocklist_*` endpoints** (not a net-new build) |
| Re-verify staleness | >30 days before activation (SKILL) | 90-day re-verify window | **Tighten to re-verify if >30 days** before a campaign activates; the aged 187K pool makes this urgent (Section 5 P0/P1) |
| Bulk-write throttle | — | >=100 push needs `approved=True`, chunked 50 + 1s cooldown | Ahead (honors GHL outage rules) |
| Cloudflare UA | — | `config.USER_AGENT` on every urllib Request | Already fixed |

**Net:** infra is our strong suit. Concrete to-dos: (1) verify SPF/DKIM/DMARC per domain, (2) wire the existing Instantly inbox-placement seed test before first send, (3) wire the existing Instantly blocklist sync (Layer B), (4) tighten re-verify to 30 days pre-activation, (5) adopt the 3% bounce hard-stop.

---

## 11. Open questions / to verify

1. **Does the live Instantly campaign config actually honor open-OFF / link-OFF / plain-text?** Defaults are in `config.py`; confirm the deployed payload reflects them.
2. **SPF/DKIM/DMARC** configured and passing on all FS + CS sending domains? Not evidenced in BASE.
3. **Does the funnel personalize/enrich ONLY on post-verify survivors?** Verify-last is confirmed; confirm enrichment is not spending on pre-verify leads.
4. **Does every template carry a physical address block and an opt-out line, and does the STOP path feed the suppression set?** (Section 9 items 1-2.)
5. **GHL FS+CS tokens + Anthropic key** present for live classification/routing? (Heuristic runs without Anthropic.)
6. **Malcolm's buyer-reach stat** (~250-400 inquiries/mo) is UNCONFIRMED and brand-ambiguous. Keep copy qualitative ("hundreds of buyer inquiries each month") until Theodore confirms.
7. **Expected post-qualification pool size.** If LGJ's ~40% drop holds, what does 187K Tier A become, and does that still clear our volume targets? Model before flipping the gate live.
8. **RLM valuation teaser.** Does the CS `valuation/` tool support URL-param pre-fill + instant output, or is that a net build? And what disclaimer/range language does Theodore/Malcolm approve?

**Resolved (do not re-open):**

- **Instantly REST vs MCP token blocker — RESOLVED.** The MEMORY note is unambiguous: the stored REST key was valid all along; the "MCP token not a REST key" go-live blocker was a misdiagnosis. Fixed 2026-06-09 via the Cloudflare-UA fix (`config.USER_AGENT` on every engine urllib Request). Dashboard reports `instantly ok:true` with 88 active mailboxes. BASE still lists it as the live-send blocker; that entry is stale.
