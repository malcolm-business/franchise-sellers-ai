---
name: cold-email-strategy
description: Run a short strategy interview for a campaign and produce a strategy doc that feeds BOTH targeting (qualification + audience filters) and copy (the improve-copy skill). Use before building a new campaign — strategy precedes scraping/sending.
---

# cold-email-strategy

Turns a brief interview with the operator (Malcolm) into one **strategy doc** per campaign.
This is the guardrail layer: it captures our positioning + ICP + pain + objections once,
so targeting and copy stay consistent and Malcolm can spin up + test new angles fast.

Run **before** building an audience or writing copy. The output drives the qualification
filters (`engine/qualification.py`), the audience builder, and `improve-copy`.

## Inputs to ask the operator for
Ask for whatever exists; never block on missing pieces (fall back to what we know):
1. **Campaign name** (slug, e.g. `fs-hvac-q3`) and **brand** (FS or CS).
2. **Best input:** paste real **sales-call / discovery-call transcripts** or notes — these are
   the highest-quality source for pain vocabulary and objections.
3. **Segment**: who exactly (industry / franchise system / geo / size band).
4. **Offer / primary CTA** (default: free OOV; alternatives in `engine/copy_gen.OFFERS`).
5. Any **proof points** (deals closed, "hundreds of buyer inquiries each month" — keep the
   ~250-400/mo stat qualitative until Theodore confirms it).

## Produce the strategy doc
Write to `data/runtime/strategies/<campaign>.md` with these sections:
- **Positioning** — one paragraph: who we help + the single sharpest reason they'd reply.
- **ICP filters** — concrete: titles to TARGET + titles to EXCLUDE, industries, geos
  (states / radius), size band. These map straight to qualification + audience filters.
- **Per-segment pain vocabulary** — the words THIS segment uses (FS franchise-resale pains
  ≠ CS private-business pains). Pull from the transcripts. No shared generic keywords.
- **Buying triggers** — what makes someone reply now (retirement, burnout, a recent offer).
- **Objections to pre-counter** — the real seller objections ("is it even worth listing",
  "brokers take huge fees", "I'm not ready"), each with a one-line reframe.
- **AI-qualification prompt** — any segment-specific addendum to the standard current-owner /
  US / franchise-vs-private / no-PE checks in `engine/qualification.py`.
- **Tone & angles** — 2-3 messaging angles to A/B (e.g. peer-proof, speed, confidentiality).
- **Sequence architecture** — number of steps + cadence (default sellers `[1,4,6]`).

## Then
- Hand the doc to **`improve-copy`** to generate the sequence against this strategy.
- Hand the ICP filters to the **audience builder** (`/marketing` dashboard) + qualification.

## Rules
- Strategy is the single upstream source of truth — copy and targeting both read it.
- Keep it short and concrete; it's a working doc Malcolm edits, not a deck.
- One strategy doc per campaign; revise in place as tests teach us what works.
