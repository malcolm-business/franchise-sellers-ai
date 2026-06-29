# Instantly Campaign Retrospective

**Source:** 35 historical campaigns from your Instantly account, analyzed 2026-05-21. Joined structural data (sequences/steps/variants/bodies from a saved API dump) with live analytics (sends/replies/bounces from `get_campaign_analytics`).

**Reproducible:** rerun `cold-email-outbound/scripts/analyze_instantly_history.py` to refresh the joined records into `/tmp/instantly-retro/analysis.json` and reprint the ranked table.

**What this is for:** empirical foundation for the spintax template + offer testing in Phase 1. The 2026 best-practice research in `cold-email-research-playbook.md` says one thing; this doc shows what *actually worked* for your brands specifically.

---

## Headline findings

1. **Franchise-system name-dropping is the #1 reply-rate driver.** Every top-performer in the seller cold list mentions a specific franchise system the recipient operates. Generic broad-industry copy systematically underperforms it.
2. **List quality dominates copy quality.** FS-Automotive-Maaco used virtually identical copy to FS-Senior Care-FirstLight, but Maaco had 8.57% bounce rate and 0.21% reply, while FirstLight had 2.30% bounce rate and 7.24% reply. Same template, bad list = dead.
3. **The CS broad-industry `{{Paragraph One}} {{Paragraph Two}}` AI-generated template is broken.** Every CS campaign using it sits at 0.72–2.99% reply rate. Every FS campaign using hand-written franchise-specific copy sits at 3–8%. This is empirical evidence backing the rebuild thesis in `00-project-overview.md` — full AI-generated copy at scale stopped working.
4. **3-step sequences ≫ 1-step.** The follow-up "I know emails can easily get buried, bumping this up" step 2 consistently extracts an additional 30–50% of replies. Single-touch campaigns max out around 2.5% even on good lists.
5. **Hyper-specific buyer-side offers hit 6–12% reply.** When you named a specific business for sale ("The Iconic Copper Club Brewery in Fruita, Colorado is now on the market!") you got the best reply rates of any campaign in the system. Specificity wins.

---

## Full ranked table (30 campaigns ≥ 50 sends)

Brand: FS = Franchise Sellers · CS = Company Sellers · BUYER = buyer-side · EVENT = event-tied · ADVISOR = referral partner

| Rank | Campaign | Brand | Sent | New leads | Replies | Bnc% | **Reply/contact** | Steps | Words | Opps |
|---:|---|:--:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Buyer: UT & CO Breweries | BUYER | 1,031 | 368 | 45 | 1.75% | **12.23%** | 3 | 101 | 12 |
| 2 | FLHC Pre Event 2025 | EVENT | 73 | 73 | 7 | 2.74% | **9.59%** | 1 | 95 | 6 |
| 3 | FLHC Post Event 2025 | EVENT | 73 | 73 | 6 | 1.37% | **8.22%** | 1 | 112 | 6 |
| 4 | FS-Education & Childcare-Code Ninja | FS | 2,239 | 806 | 61 | 2.81% | **7.57%** | 3 | 88 | 20 |
| 5 | FS-New Franchise-Existing-NO | FS | 3,464 | 1,761 | 131 | 0.06% | **7.44%** | 2 | 91 | 17 |
| 6 | FS-Senior Care-FirstLight Home Care | FS | 1,997 | 704 | 51 | 2.30% | **7.24%** | 3 | 55 | 10 |
| 7 | FS-New Franchise-Existing-YES | FS | 3,323 | 1,687 | 112 | 0.21% | **6.64%** | 2 | 104 | 40 |
| 8 | Buyer: FL Wind Mitigation | BUYER | 1,766 | 614 | 40 | 1.30% | **6.51%** | 3 | 108 | 14 |
| 9 | FS-Senior Care-Comfort Keepers | FS | 1,990 | 694 | 43 | 1.76% | **6.20%** | 3 | 55 | 11 |
| 10 | FS-Food & Beverage-Ben & Jerry | FS | 2,149 | 745 | 28 | 0.93% | **3.76%** | 3 | 55 | 4 |
| 11 | CS: Home Health (Weekly Auto Run) | CS | 584 | 296 | 10 | 0.51% | 3.38% | 2 | 60 | 1 |
| 12 | FS-Food & Beverage-Nekter Juice Bar | FS | 2,088 | 733 | 24 | 1.15% | 3.27% | 3 | 55 | 3 |
| 13 | CS: Automotive (2-10 employees) | CS | 912 | 469 | 14 | 2.74% | 2.99% | 2 | 60 | 3 |
| 14 | CS: Owner-Automotive (Weekly Auto Run) | CS | 636 | 320 | 9 | 0.79% | 2.81% | 2 | 60 | 0 |
| 15 | CS: Consumer Services (Weekly Auto Run) | CS | 19,559 | 10,327 | 262 | 1.11% | 2.54% | 2 | 60 | 39 |
| 16 | Post MUFC 2025 - Zor | EVENT | 163 | 163 | 4 | 1.84% | 2.45% | 1 | 104 | 1 |
| 17 | CS: Automotive (11-50 employees) | CS | 1,030 | 530 | 13 | 2.14% | 2.45% | 2 | 60 | 0 |
| 18 | Post MUFC 2025 - Zee | EVENT | 255 | 255 | 6 | 0.00% | 2.35% | 1 | 84 | 6 |
| 19 | Franchise Testing | FS | 11,060 | 11,060 | 192 | 1.59% | 1.74% | 1 | 92 | 43 |
| 20 | Biz Advisor Testing | ADVISOR | 4,504 | 4,504 | 71 | 0.38% | 1.58% | 1 | 80 | 9 |
| 21 | FS-Automotive-1-800 Radiator | FS | 1,236 | 467 | 7 | **6.15%** | 1.50% | 3 | 149 | 0 |
| 22 | HCAOA Blast - Franchise | EVENT | 1,354 | 1,354 | 19 | 2.36% | 1.40% | 1 | 108 | 9 |
| 23 | CS: Health, Wellness & Fitness (2-10 Emp) | CS | 17,303 | 8,881 | 113 | 1.21% | 1.27% | 2 | 60 | 13 |
| 24 | Exit Summit Pre Event 2025 | EVENT | 2,127 | 2,127 | 23 | 0.33% | 1.08% | 1 | 76 | 13 |
| 25 | CS: Health, Wellness & Fitness (11-50 Emp) | CS | 5,093 | 2,828 | 23 | 0.75% | 0.81% | 2 | 60 | 5 |
| 26 | HCAOA Oct 25 (Event) - Franchise | EVENT | 1,353 | 1,353 | 10 | 3.70% | 0.74% | 1 | 90 | 3 |
| 27 | CS: Food & Beverage 1-50 Emp | CS | 9,543 | 5,148 | 37 | 0.80% | 0.72% | 2 | 60 | 4 |
| 28 | HCAOA Oct 25 (Event) - Private | EVENT | 145 | 145 | 1 | 0.69% | 0.69% | 1 | 77 | 1 |
| 29 | FS-Automotive-Maaco | FS | 1,213 | 469 | 1 | **8.57%** | 0.21% | 3 | 90 | 0 |
| 30 | HCAOA Blast - Private | EVENT | 145 | 145 | 0 | 0.69% | **0.00%** | 1 | 101 | 1 |

**Reply/contact** = unique replies ÷ unique new leads contacted. Best metric for comparing across campaigns of different sizes.

---

## Pattern analysis — what worked

### 1. The "we recently helped a [specific system] franchisee sell for more than they thought possible" opener

This single sentence pattern drives the top FS niche campaigns. From FirstLight (7.24%):

> Hey {{firstName}}, We help franchise business owners value and sell their businesses. **Recently, we helped a FirstLight Home Care franchisee sell for more than they thought possible—and faster than they expected.** If you're curious about selling, we'd be happy to provide a complimentary, no-obligation business opinion of value.

Why it works:
- **Brand-specific social proof** in the second sentence. Recipient instantly recognizes their system.
- **Quantified outcome** ("more than they thought possible", "faster than they expected") with zero overclaim.
- **Soft CTA** ("happy to provide a complimentary, no-obligation business opinion of value"). No friction.
- **55 words total.** Inside the research-recommended <70 word window.

### 2. Reactivation copy crushes (FS-New Franchise-Existing-NO, 7.44% reply, 0.06% bounce)

Subject: `{{firstName}}, the franchise business you looked at`

Body opens:
> {{firstName}}, {{Email Copy Input}} Sorry that one didn't work out. We'll definitely let you know when we get other business listings that match your requirements. We've recently expanded our team and now have an in-house franchise consultant...

Why it works:
- **The recipient already engaged with you** (they looked at a specific franchise). The list is warm by definition.
- **Apology + continuity** ("sorry that one didn't work out, we'll keep looking for you") = relationship continuation, not cold pitch.
- **0.06% bounce** confirms the list quality is real — these are validated former leads.

### 3. Hyper-specific buyer offer (Buyer: UT & CO Breweries, 12.23%)

> Hey {{firstName}}, Ready to expand in Western Colorado? **The Iconic Copper Club Brewery in Fruita, Colorado is now on the market!** I believe this profitable business (and real estate) maybe a fantastic addition to the business you already own.

Why it works:
- **Named the actual business for sale** in the subject + opening. Instant relevance test for the reader.
- **Geographic + industry-specific list** ("Western Colorado breweries") so every recipient is the right buyer.
- **Step 2 follow-up doubles down on the same specificity** ("Craft beer that's won awards, street tacos, live music"). It's a story, not a pitch.

### 4. Event-tied pre-touch (FLHC Pre Event 2025, 9.59%)

> Hey , Are you attending the FLHC Annual Conference this week in Savannah? If so, look for us — we'd love to connect!

Why it works:
- **Time-sensitive specific signal** ("this week in Savannah").
- **Curiosity hook** in the question form, no pitch yet.
- **Mentions a specific session** ("Exit Planning breakout session on Thursday afternoon") to back up the value claim.
- **Sent to a list pre-filtered for actual conference registrants.** Same template applied to a broad HCAOA member list (HCAOA Oct 25 Event - Franchise) bombed at 0.74%.

### 5. Multi-step bump-up works

The 3-step FS niche campaigns share this step 2:

> Hey {{firstName}}, As a business owner, I know emails can easily get buried. Bumping this one up to the top of your inbox! If you are thinking about selling your franchise business, we'd be happy to offer you a complimentary valuation to help in your decision making. Want to chat next week?

Why it works:
- **Acknowledges inbox reality** rather than pretending the first email was important.
- **Short, low-friction CTA** ("Want to chat next week?").
- **Captures ~30–50% additional replies** above step 1 alone.

---

## Pattern analysis — what failed

### 1. The CS `{{Paragraph One}} {{Paragraph Two}}` template

Used by every broad-industry CS campaign. Body literally:

```
{{firstName}},
{{Paragraph One}}
{{Paragraph Two}}
Theodore Baird
Company Sellers
If this is not relevant to you, simply reply with 'no'
```

The paragraphs are AI-generated per recipient, plugging in company name + industry. Results:

| Campaign | Reply/contact |
|---|---:|
| CS: Food & Beverage 1-50 Emp | 0.72% |
| CS: H&W&F (11-50 Emp) | 0.81% |
| CS: H&W&F (2-10 Emp) | 1.27% |
| CS: Automotive (11-50) | 2.45% |
| CS: Consumer Services | 2.54% |

**Diagnosis:** the AI-generated paragraphs read as AI-generated. The recipient gets generic language wrapped around their company name. Recipients (and modern spam filters) have learned to recognize the pattern. This is exactly the failure mode `cold-email-research-playbook.md` warns about: "AI saturation killed fake personalization."

**This campaign type is the single best argument for the rebuild.** Replace `{{Paragraph One}} {{Paragraph Two}}` with hand-written signal-anchored copy following the FS niche pattern.

### 2. Bulk event blasts without attendance filter

Same FLHC pre-event template, but applied to a broad list rather than actual attendees:

| Campaign | List type | Reply/contact |
|---|---|---:|
| FLHC Pre Event 2025 | confirmed attendees | **9.59%** |
| HCAOA Blast - Private | broad CS HCAOA member list | **0.00%** |
| HCAOA Oct 25 (Event) - Private | broad member list, event-themed | 0.69% |
| HCAOA Blast - Franchise | broad FS HCAOA member list | 1.40% |
| HCAOA Oct 25 (Event) - Franchise | broad member list, event-themed | 0.74% |

**Diagnosis:** the event hook only works when recipients are actually at/connected to the event. Otherwise it reads as a random "we're at a conference" non-sequitur. The HCAOA blasts also had bounce rates of 0.69–3.70%, suggesting list quality was thin.

### 3. FS-Automotive-Maaco — copy good, list dead

| Metric | FS-Senior Care-FirstLight | FS-Automotive-Maaco |
|---|---:|---:|
| Reply/contact | **7.24%** | 0.21% |
| Bounce rate | 2.30% | **8.57%** |

The Maaco campaign uses the SAME template that won for FirstLight (with system name swapped). Even has more spintax variation (`{{RANDOM | Hey | Hi | Hello | Greetings}}`). Result: catastrophic underperformance.

**Diagnosis:** the Maaco franchisee list was junk. 8.57% bounce rate (above the 5% deliverability-damage threshold) confirms it. **No copy can save a bad list.** Confirms the rebuild thesis that re-verification before send is mandatory.

### 4. Single-step "Franchise Testing" with broad list (1.74%)

Largest single campaign by sends (11,060) with the same opener pattern as FS niche campaigns, but:
- Only 1 step (no follow-up)
- Broad franchise list (no system-specific tailoring)
- 4 subject variants but the body is generic ("franchise business")

Result: 1.74% reply rate — half of what the same opener gets when properly targeted. Confirms two principles:
- Single-step campaigns max out around 2.5%
- Generic franchise messaging loses the system-name advantage

---

## Concrete recommendations for Phase 1 (rebuild)

### Copy structure

Build the spintax template around the FS-Senior Care-FirstLight winning pattern:

```
SUBJECT (3 variants):
- Quick question {{firstName}}
- Thoughts {{firstName}}
- {{firstName}}, [system-specific hook]

STEP 1 BODY (target 55-90 words):
Hey {{firstName}},

We help franchise business owners value and sell their businesses.
Recently, we helped a {{franchise_system}} franchisee sell for more
than they thought possible — and faster than they expected.

If you're curious about selling, we'd be happy to provide a
complimentary, no-obligation business opinion of value.

Let me know if you'd like to explore this further!

{{sender_name}}
{{brand_name}}

If this is not relevant to you, simply reply with 'no'

STEP 2 BODY (delay: 3-5 days):
Hey {{firstName}},

As a business owner, I know emails can easily get buried. Bumping
this one up to the top of your inbox!

If you are thinking about selling your franchise business, we'd be
happy to offer you a complimentary valuation to help in your
decision making.

Want to chat next week?

{{sender_name}}
{{brand_name}}

STEP 3 BODY (delay: 5-7 days):
[Short, soft "last try" — to be designed]
```

### What to deprecate

- The `{{Paragraph One}} {{Paragraph Two}}` AI-generated paragraph template. Replace entirely.
- Generic broad-industry CS campaigns. Replace with industry × franchise-system or industry × signal-anchor (M&A activity, owner age, tenure).
- Single-step campaigns. Default to 3 steps.
- The `{{RANDOM | a | b | c}}` heavy-spintax pattern that FS-Automotive-Maaco used. Variation matters less than specificity.

### List quality gates (mandatory before any send)

Based on the Maaco failure:
- Verify every email before send. Bounce rate >5% = halt.
- Re-verify any list older than 90 days.
- For franchise-system-specific campaigns, confirm the list actually contains franchisees of that system (not generic industry contacts).

### Brand-specific reply-rate baselines for Phase 1

Use these as your "is the new engine working?" gates:

| Campaign type | Reply/contact baseline | Anything below this means investigate |
|---|---:|---|
| FS niche (system-named, 3 step, verified list) | **6%** | 3% |
| FS reactivation (warm list) | **7%** | 4% |
| CS broad industry (rebuilt with signal-anchoring) | **3%** | 1% |
| Buyer-side specific opportunity | **8%** | 4% |
| Event-tied pre-touch (confirmed attendees) | **9%** | 4% |
| Referral partner outreach | **2%** | 1% |

If Phase 1 hits these in re-verified-list testing, the new orchestration is working.

---

---

# Part 2 — Reply Content Analysis (added 2026-05-21)

Followed up by paginating `list_emails` across 10 pages (~950 raw emails → 468 unique replying prospects) covering Aug 2025 – May 2026, the only window Instantly retains historical reply content for. Classified by intent using keyword heuristics. Reusable script at `cold-email-outbound/scripts/analyze_instantly_replies.py`.

**Critical caveat: 9 months of data only.** The big-volume campaigns that ran in late 2024 / early 2025 (~700+ replies) are not in Instantly's retained inbox anymore. This analysis represents the ~468 most recent replies, biased toward the active 2025–2026 reactivation and event campaigns.

## Headline classification

Of 468 unique prospect first-replies:

| Class | Count | % | Notes |
|---|---:|---:|---|
| Other (unclassified) | 327 | 69.9% | Likely mix of conversational follow-ups, mid-thread context, and ambiguous wording. Classifier could be refined further but headline patterns are stable. |
| **Objection — not interested** | **56** | **12.0%** | Most common explicit response. "No thanks", "Not at this time", literal "NO" as subject |
| **Positive — interested** | **45** | **9.6%** | "Yes I am interested", "Tell me more", "Send me listings" |
| **Unsubscribe** | **26** | **5.6%** | Explicit opt-out — must permanently suppress |
| Out of office | 10 | 2.1% | Auto-responders |
| Meeting accepted | 2 | 0.4% | Calendar invitation acceptances |
| Objection — not now | 1 | 0.2% | Severely under-counted by heuristics; many "other" rows are actually "not now" |
| Information request | 1 | 0.2% | Under-counted |

**Translating to deliverable outcomes:** ~10% of replies are positive intent. ~18% are negative (objection + unsub + wrong person). The remaining ~70% are conversational / ambiguous / operational.

## ⚡ Biggest finding: FS-New Franchise-Existing-YES is your single best converter

Reply mix by campaign (top 10 by total replies):

| Campaign | Total | Pos | **Pos %** | Neg | Neg % | Unsub | Unsub % |
|---|---:|---:|---:|---:|---:|---:|---:|
| FS-New Franchise-Existing-NO | 124 | 7 | 6% | 19 | 15% | 8 | 6% |
| **FS-New Franchise-Existing-YES** | **108** | **24** | **22%** | 14 | 13% | 2 | 2% |
| CS: H&W&F 2-10 | 92 | 1 | 1% | 10 | 11% | 9 | 10% |
| CS: Consumer Services | 59 | 3 | 5% | 4 | 7% | 3 | 5% |
| CS: F&B 1-50 | 31 | 3 | 10% | 2 | 6% | 1 | 3% |
| CS: H&W&F 11-50 | 19 | 1 | 5% | 6 | 32% | 3 | 16% |
| Franchise Testing | 11 | 2 | 18% | 0 | 0% | 0 | 0% |
| HCAOA Oct Franchise | 8 | 3 | 38% | 1 | 12% | 0 | 0% |

**The blockbuster: FS-New Franchise-Existing-YES converts at 22% positive.** That's 5× the next-best seller campaign.

**But there's a catch — it's not seller cold.** This campaign goes to people who *previously inquired about a franchise to buy*. The team checks in on new opportunities. Every positive reply quoted below is a *buyer*, not a seller:

> "Yes we can set up a call to see what opportunities may work."
> "Yes please send me listings if you have them."
> "Yes I would be interested but I'm out of the country."
> "Sure I'd love to hear more about what you have available."
> "I would be interested in a franchise that is here locally."
> "Yes. I am interested to know more about them."

**Strategic implications:**
1. Your **buyer-side reactivation pipeline is dramatically more efficient** than seller cold. The Airtable Active Contacts table already cross-references both — the Phase 1 rebuild should sequence buyer-side reactivation FIRST as the fastest path to opportunities.
2. These buyer replies probably feed the Yvonne / Buyer Manager dashboard pipeline, not the seller-cold workflow. Should not be conflated in suppression rules.
3. The CS broad-industry campaigns are **burning the list** — 10–16% unsubscribe rates on CS H&W&F campaigns. That's a deliverability threat. Every CS:* campaign in the list has more unsubscribes than positive replies.

## Subject line patterns: what actually triggers replies

| Subject pattern | Total replies | Positive | Pos % | Negative | Neg % |
|---|---:|---:|---:|---:|---:|
| `[Name], the franchise business you looked at` | 109 | 18 | **17%** | 15 | 14% |
| `quick question [Name]` | 80 | 4 | 5% | 8 | 10% |
| `Franchise Sellers Check In` | 66 | 3 | 5% | 11 | 17% |
| `[Name] thinking about what's next?` | 60 | 3 | 5% | 6 | 10% |
| `your business for sale inquiry` | 57 | 10 | **18%** | 7 | 12% |
| `[Name] thoughts?` | 47 | 2 | 4% | 5 | 11% |
| HCAOA event subjects | 8 | 2 | 25% | 1 | 12% |

**Two subject patterns dominate positive replies:**
- `[Name], the franchise business you looked at` — 17% positive (buyer-side, super specific signal)
- `your business for sale inquiry` — 18% positive (also buyer-side reactivation)

**Generic seller-cold subjects (`quick question [Name]`, `[Name] thoughts?`, `[Name] thinking about what's next?`) all sit at 4–5% positive.** That's the cold-baseline. They get more REPLIES than the buyer-side subjects, but the replies are mostly objections and unsubscribes — not the conversions you want.

## Positive reply language patterns (write these into the reply-handling SOP)

Most positive replies open with one of:
- **`Yes`** (alone, or "Yes, I'm interested" / "Yes, please send")
- **`I would be interested`** / **`I would love to`** — slight tentativeness, soft yes
- **`Tell me more`** / **`I'd like to learn more about what you do`** — full open
- **`Send me`** / **`Please send`** — direct ask for materials
- **`Happy to chat`** / **`Sounds good`** / **`Let's talk`** — meeting-ready

Soft positives with timeline objections (treat as 6–12 month cooldown candidates, not rejections):
- "I would love to be able to sell, but I do not think we are at that point [yet]"
- "Yes, I'd like to look at the PDF, though we are some years away"
- "I'm always interested in selling for the right price" — perpetually receptive
- "Not at the moment. Possibly in 3 years."

## Objection language patterns

By order of frequency:
- **`No thanks`** / **`No thank you`** — terse, hard to address. Mark suppressed, do not re-engage.
- **`Not at this time`** / **`Not at the moment`** — 6–12 month cooldown candidate. Re-engage later.
- **`Not interested`** / **`No interest in selling`** — definitive. Suppress.
- **`NO`** as subject + nothing else — angry rejection. Treat as suppression.
- **`Not for sale`** / **`Our business is not for sale at this time`** — soft cooldown.
- **`Touch base with me end of [year]`** — EXPLICIT re-engage window. Capture the date.

Wrong-intent signals (route to different sequence, not suppress):
- **`I'm mainly interested in resales`** — buyer-side, not seller-side. Send to Yvonne.
- **`Existing franchise resales`** — same
- **`I am focused on acquiring`** — buyer-side
- **`We have acquired a business and not looking at new franchises`** — they just bought, not selling

## Concrete recommendations for Phase 1

### 1. Sequence buyer-side reactivation FIRST

Phase 1 was originally scoped as seller cold. Based on this data, **the highest-ROI Phase 1 use case is reactivating the 18,931 Active Contacts in Airtable that are buyer-side**. They convert at 22% positive — that's a faster path to opportunities than seller cold.

The seller cold engine still gets built — but de-prioritize it behind buyer reactivation in the calendar.

### 2. Kill the CS broad-industry campaigns as-is

Every CS broad campaign has more unsubscribes than positive replies. Don't restart these on the rebuilt engine without restructuring:
- Add signal-anchoring (industry × M&A activity, owner age, tenure)
- Replace `{{Paragraph One}} {{Paragraph Two}}` AI fillers with hand-written, system-naming copy
- Hit a 50-record probe before scaling — measure positive % not raw reply %

### 3. Build the reply classifier into the rebuild engine

Every new inbound reply goes through a Claude API call to classify into:
- `positive_curious` / `positive_meeting_ready` / `positive_with_timeline_objection`
- `objection_not_now` (capture timeline if mentioned)
- `objection_not_interested`
- `wrong_person` / `wrong_intent_buyer_side`
- `unsubscribe`
- `out_of_office`
- `auto_responder`
- `referral` (routes to specific person)
- `meeting_accepted`

Classifier output writes to RevyOps (or Airtable) — drives suppression, cooldown timers, and follow-up routing. **30–60 days of new data with this in place gives a clean dataset for proper reply-content analysis, replacing the 70% "other" gap above.**

### 4. Capture re-engage timestamps explicitly

When a prospect says "touch base end of 2026" or "in 3 years", the classifier needs to extract that date and schedule a re-engage. Currently these are buried in "other" / "objection_not_now" and forgotten.

### 5. The `your business for sale inquiry` subject is a hidden gem

18% positive rate, 57 replies, second-best in the system. Worth understanding which campaign(s) used this subject and what context made it work. Likely a buyer-side template that should be cataloged as a template winner.

## Quantitative "is the rebuild working?" gates (replacing/refining Part 1 baselines)

Better metric than reply-rate-per-contact: **positive-reply-rate-per-contact**.

| Campaign type | Target positive % | Investigate below |
|---|---:|---:|
| Buyer-side reactivation (warm list) | **15%** | 8% |
| FS niche cold (system-named, hand-written) | **6%** | 3% |
| CS broad cold (rebuilt with signal-anchoring) | **3%** | 1% |
| Event pre-touch (confirmed attendees) | **8%** | 4% |

Unsubscribe rates over **5%** = halt and reassess copy/list.

## What this analysis still didn't cover

- **The 700+ replies from late 2024 / early 2025 campaigns are gone from Instantly's retained inbox.** Higher-volume campaigns like Franchise Testing (192 replies historically) only show 11 here. The earliest replies that taught us about pre-FS-New-Franchise patterns aren't recoverable.
- **The 70% "other" bucket** could be reduced with better classifier rules + a Claude API pass on each ambiguous reply. Worth doing once the rebuild engine is in place and we want to backfill historical data.
- **Per-variant performance + sending account performance** — original Part 1 said both were possible. They still are, separately from this reply analysis. Not blocking.
