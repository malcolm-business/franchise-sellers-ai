# Malcolm's copy revisions — 2026-06-29

First copy pass on the three live seller streams, reviewed against the Broker
Copywriting Playbook + our locked voice rules. Structure, merge tags, slots
(`{{signal_anchor}}`, `{{offer_cta}}`), spintax, 1/4/6 cadence, and the auto
footer are all unchanged. Only the words changed. Ted, these are ready to load
unless a flagged item below needs your call.

## What changed in all three streams

1. **Removed the unprovable "sold for more than they expected / thought possible" claim** (the Playbook's #1 pre-launch fix). Replaced with credibility we can stand behind: Eric's confirmed 27 years + confidentiality. — fs_niche S1, cs S1.
2. **Stripped every em dash** (voice-rule break). They were in all three STEP 3s, fs_broad S1, fs_niche S1, cs S1.
3. **Reader-first openers.** STEP 1 no longer opens "We help…". Each now opens on the owner and leads with valuation curiosity ("what's it worth / what comes next"), not "do you want to sell."
4. **Confidentiality named early** in every STEP 1 — defuses the owner's #1 silent fear.
5. **Differentiated the subject lines** per stream toward specific, honest, exit-themed lines. Retired the fatigued "Quick question {{firstName}}" / "Thoughts {{firstName}}" that all three shared.

## Per-stream notes

- **fs_broad:** added the "plan early = options" reframe to STEP 2. STEP 1 keeps `{{audience_descriptor}}`.
- **fs_niche:** kept the `{{franchise_system}}` naming hook (the stream's whole reply-rate advantage) in S1, S2, S3. Removed the exclamation point and formal tone in S2.
- **cs:** broke up the "value / opinion of value / value" repetition (now worth / number / what it could sell for). Opener is now a segment-level truth using `{{industry_lower}}`. Updated the frontmatter `description` to match the new approach (was "industry-peer social proof," now "segment-level valuation hook + credibility").

## Second pass (same day) — brevity + spintax

After the first pass, tightened every email for read time and added light spin zones.

**Length standard we're now writing to** (matches the engine + Playbook):
- **Email 1: ~50–80 words, one idea.** Data: 50–125 words gets ~2.4x the reply rate of 200+ word emails. The reader is a "15-second stranger" — target a ~10–20 second read.
- **Each follow-up shorter than the last.** Email 2 < Email 1; Email 3 is the shortest.
- Short sentences, no fluff. If the same point fits in fewer words, use fewer words.
- The engine tracks `word_count` per render, so this is measurable. (Word count excludes the auto CAN-SPAM footer, which is fixed and required.)
- My first pass had drifted long (the FS-broad opener nearly doubled Ted's). This pass pulls each STEP 1 back to roughly Ted's original length while keeping the no-claim / reader-first / confidentiality / no-em-dash gains.

**Spintax — kept light on purpose** (not heavy, per Ted's SOP + Playbook):
- The only requirement is **≥50% of rendered copies unique across a batch** (`min_spintax_variation_pct = 50`). The per-recipient merge fields (`{{firstName}}`, `{{company}}`, `{{industry}}`, `{{franchise_system}}`) already do most of that.
- Heavy per-word synonym-swapping is discouraged — it reads robotic and some filters flag it. We use a few **whole-phrase** spin zones only.
- **Added one CTA spin zone to STEP 1 and STEP 2** in all three streams (STEP 3 already had one). Every spin option is written to the same brevity + voice bar — no weak alternates.
- Rule going forward: when you add or edit a `{{RANDOM | a | b | c}}` block, all options must independently be short, on-voice, and a complete thought.

## Open questions — need a call before go-live

1. **The "reply with 'no'" line in STEP 1** (all three). The Playbook says don't stack a "reply yes" CTA against a "reply no" opt-out in the same email — it reads as two asks. I left it in because I assume it feeds reply-routing/suppression in the engine. **Ted: does a "no" reply trigger suppression? If not, I'd cut this line** (the CAN-SPAM footer already handles opt-out).
2. **Subject-line merge gating.** Several new subjects use `{{company}}`. Confirm a clean company name renders (not a messy legal string) and a generic fallback fires when it's missing/messy.
3. **CS `{{industry_lower}}` quality.** "another owner in home care" reads fine; "hvac services" reads like a typo and a blank reads awkward. Need the clean CS industry-label list before this ships, or a fallback.
4. **A/B the subjects.** Three per stream are loaded as variants — worth testing the no-merge exit-themed line vs. the `{{company}}` line per the Playbook.
5. **Still waiting on Eric's ICP** for the `{{signal_anchor}}` data and per-brand FS-vs-CS language. Until then the signal line stays stripped (correct).
