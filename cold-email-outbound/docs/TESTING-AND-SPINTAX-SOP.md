# Cold Email — Testing & Spintax Operating Procedure

**Who this is for:** Malcolm and Theodore. How we start a campaign with a test, how the wording-variation (spintax) works, and the cadence + timing for reading data and updating campaigns.

**The principle:** change one thing at a time, give it enough volume to mean something, and never let a test override a safety limit. Every number below is what the engine actually enforces in code (`engine/config.py`).

---

## 1. What we test: the offer

Everything in an email is held constant except **one variable: the offer line** (the call-to-action). That keeps every result clean: if variant B wins, you know it was the offer, not a different subject or a longer opener.

- **Control (A):** always the free **Opinion of Value** (`oov`). It is the baseline and never gets retired.
- **Challenger (B):** one of `comparable_sales`, `exit_readiness`, `buyer_match`, `strategy_call`, `succession`.
- **Split:** 50 / 50.
- **One challenger at a time.** Tests are **sequential**, not five-at-once. A winner becomes the new control for the next test.

Suggested test order (start at the top, move down as winners settle):
1. OOV vs Comparable sales report
2. OOV vs Exit-readiness assessment
3. OOV vs Active buyer match
4. (after the new valuation software ships) OOV vs paid premium valuation

---

## 2. How to start a campaign with a test

1. **Pick the segment + brand** (one brand, one segment for a clean read).
2. **Decide the challenger offer** for this round.
3. **Ask Claude to stage it in dry-run** with the challenger set:
   ```
   pipeline.run_campaign(stream, test_offer='comparable_sales')   # analysis only by default
   ```
4. **Review both variants** in the Copy Preview Pack on the dashboard; confirm the pre-send gate is green.
5. **Make sure each variant will reach ≥ 500 recipients.** Below that, a gap in reply rate is probably just noise. If the segment is small, run the test longer or widen the segment.
6. **Go live on the small starting batch** (Theodore flips `CEO_DRY_RUN=false`). The 50/50 split and the offer rotation are handled by the engine.

You are never editing two separate campaigns by hand. It is one campaign, one variable, split in half.

---

## 3. Spintax — how wording variation works

Sending 10,000 byte-identical emails is a spam signal. Spintax rotates small pieces of wording so no two sends look the same, without anyone hand-writing variants.

- **Syntax (in the template):** `{{RANDOM | option A | option B | option C }}`. The engine picks one option per recipient.
- **Deterministic per contact:** the same contact always gets the same variant (seeded by their ID), so a re-render never changes what they would receive. Different contacts get different ones.
- **Variation floor: 50%.** Across a batch, at least **50%** of the rendered copies must be unique (`min_spintax_variation_pct = 50`, measured by `copy_gen.variation_ratio()`). If a template's spin blocks are too thin to clear the floor, add more options before it ships.
- **Real example** (the day-11 soft close in the CS sequence):
  `{{RANDOM | Last note | One more then I'll stop | Closing the loop }} — if selling isn't on your mind right now, no worries at all.`

**The no-fake-personalization rule (related, and stronger than spintax):** templates can carry a "recent signal" line. If we have **no real signal** for a contact, the engine **deletes that whole line** rather than inventing a detail. Never paper over a missing signal with a fake "I saw that you recently…". A deleted line is correct behaviour, not a bug.

---

## 4. The metrics we steer by

Open-tracking and link-tracking are **off** (pixels hurt inbox placement in 2026), so we do **not** read opens or clicks. We steer by replies and health:

| Metric | What it tells you | Line in the sand |
|---|---|---|
| **Reply rate** | Is the message landing at all | the headline number |
| **Positive-reply rate** | Interested sellers (the one that matters) | the real win condition |
| **Bounce rate** | List quality + sender reputation | **warn at 2%**, **hard-halt at 3%** |
| **Unsubscribe rate** | Message relevance / fatigue | **hard-halt at 5%** |

**Circuit breakers (enforced in code):**
- `BOUNCE_WARN_PCT = 2.0` — investigate, and **do not raise volume** above this.
- `BOUNCE_HALT_PCT = 3.0` — the engine halts the campaign and queues a re-verify.
- `UNSUB_HALT_PCT = 5.0` — the engine halts the campaign.

These are not guidelines you can talk yourself out of. The engine stops the campaign for you.

---

## 5. When a test has enough data to call

- **Minimum:** ≥ 500 recipients per variant.
- **Read it on:** positive-reply rate first, then total reply rate. Bounce/unsub are health gates, not the win condition.
- **Calling a winner:** if one offer clearly leads on positive replies with both variants past 500, promote it to control and start the next challenger. If it is close, let it keep running; a tiny gap is noise.
- **Never** declare a winner off a few dozen sends or a single good reply.

---

## 6. The read-and-update cadence

| When | Do | Where |
|---|---|---|
| **First 48 hours of any live batch** | Watch bounce (<3%) and unsub (<2%). If a breaker trips, the campaign is already halted; re-verify and fix the source. | Dashboard — Send & monitor |
| **Weekly** | Pull the campaign report: sends, replies, positive %, bounce, unsub, per campaign and per variant. | Claude Code — `campaign-report.md` |
| **Weekly** | Decide the move: **hold** a clean campaign, **promote** a winning offer, or **scale** volume (only while bounce stays under 2%). | Decision → Claude re-runs |
| **Every ~14-30 days** | Run the copy-improvement pass on the lagging template (below). | Claude Code — `improve-copy.md` |
| **Continuous** | Non-repliers rest 60 days (`no_reply_days`), then re-enter a fresh sequence. Closed-lost rests 12 months. | Automatic |

**The scaling rule, restated because it is the one people break:** never raise volume on a campaign showing over 2% bounce or a rising unsub trend. Fix the list first.

---

## 7. The self-improving copy loop

When a template underperforms, the `improve-copy.md` skill runs a tight loop: it generates a tighter version, grades it against our rubric (Malcolm's voice rules, no AI-tells, per-segment pain language, one clear CTA, opt-out + address present, spintax ≥50% variation), regenerates until it passes, then shows Malcolm the real rendered output. It never auto-ships. Malcolm approves the change; it is git-tracked so brand voice can never silently drift. This is the engine that gets handed to Malcolm to tweak (see the upcoming copywriting-guide refinement, which adds a broker best-practices reference on top).

---

## 8. Guardrails recap (all enforced in `engine/config.py`)

- Open/link tracking **off**; plain-text; sends spaced 60-120s.
- Per-mailbox cap **30 cold/day**; conservative ramp, not the 2,580/day ceiling on day one.
- Spintax variation floor **50%**; no fake personalization (delete the line instead).
- Bounce warn **2%**, halt **3%**; unsub halt **5%**.
- Re-verify any address older than **30 days** before sending.
- Cold only from approved lookalike domains, never the main brand domains or staff inboxes.
- Nothing sends until `CEO_DRY_RUN=false`, flipped by Theodore on a small batch.
