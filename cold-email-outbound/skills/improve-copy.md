---
name: improve-copy
description: Generate or refine a stream's email copy, then self-critique against our rubric and regenerate until it passes — the Karpathy autoresearch "self-improving skill" pattern, applied to copywriting. Produces a candidate template for Malcolm to approve.
---

# improve-copy

Writes / refines the email sequence for a stream, then **grades its own output against a
rubric and rewrites until it passes** (usually 1-2 loops), before showing Malcolm. Based on
Andrej Karpathy's `autoresearch` self-improving pattern (https://github.com/karpathy/autoresearch).

Input: the campaign's `strategy.md` (from `cold-email-strategy`) + the target stream/template.
Output: a candidate template in `templates/<stream>.md` for human review — never auto-shipped.

## The loop
1. **Generate** the sequence (subjects + steps) for the stream, grounded in the strategy doc's
   pain vocabulary, angles, offer, and objections.
2. **Self-critique** against the Rubric below. Score each item pass/fail with a one-line reason.
3. If anything fails, **revise the copy** to fix it and go back to step 2. Converge (cap 3 loops).
4. When all rubric items pass, **render it** through the engine and show Malcolm the real output:
   ```bash
   cd cold-email-outbound
   python3 -c "from engine import config, data_layer, copy_gen; \
   tpl = copy_gen.parse_template(config.TEMPLATES_DIR / '<stream>.md'); \
   c = data_layer.load_tier_a('<BRAND>', limit=5); \
   [print('---', x.display_name, '---\n', copy_gen.render(tpl['steps'][0]['body'], x, brand='<BRAND>')[0]) for x in c]"
   ```

## Rubric (every item must pass)
> Source of truth for these rules and the broker-specific ones below: [`docs/BROKER-COPY-PLAYBOOK.md`](../docs/BROKER-COPY-PLAYBOOK.md). Read it before grading.

- **Email 1 starts a conversation, never sells.** A soft pain-probe / question. No pitch, no offer dump.
- **Anti-AI-tell.** No em dashes, no "it's not X, it's Y", no random **bolding**, no corporate filler
  ("leverage", "synergy", "I hope this email finds you well"). Reads like a real person typed it.
- **Per-segment pain vocabulary.** Uses THIS segment's words from the strategy doc — not generic.
- **One clear CTA** per email. A low-friction ask (reply / quick question), not a hard close.
- **Seller-tuned breakup** on the final step. "No rush, if now isn't the time I'll check back."
  Do NOT use the SaaS "point me to the right person" referral breakup — a sole owner IS the contact.
- **Short.** Email 1 under ~80 words; each follow-up shorter.
- **Spintax present** where it helps, and ≥50% content variation across a batch
  (`copy_gen.variation_ratio([...])`). Never fake a signal — leave `{{signal_anchor}}` for the
  engine to delete if no real data.
- **Compliance** — the engine auto-appends the address + opt-out footer; confirm it renders
  (`config.COMPLIANCE`). Subject lines must be honest (no deceptive pretext).

### Broker-specific rubric (selling-a-business outreach)
- **Credibility over result claims.** No unprovable outcome ("sold for more than they expected", "6x", "40% over asking"). Use what we can stand behind: Eric's confirmed 27 years, confidentiality, our process.
- **Lead with valuation curiosity, not the sale.** Implied ask is "do you know what it's worth?", not "do you want to sell?"
- **Confidentiality named early.** One line that staff/customers/competitors won't find out, nothing happens without their say-so.
- **OOV framed honestly.** A free, no-obligation broker's market opinion, "not a formal appraisal", no exact/guaranteed value.
- **No specific cold-email buyer claim.** Never "I have a buyer for your business" (reads as acquisition phishing).
- **Honest, specific subject.** Exit-themed and specific ("a quick one about {{company}}"), not the fatigued generic "Quick question {{firstName}}", and never a fake pretext.
- **No calendar link / no second ask in email 1.** Booking link only after a positive reply; one reply mechanic per email.
- **Cadence stays 3 emails, 1/4/6 days** (do not extend to the generic 4-7 touch SaaS pattern).

## Self-modifying-skill option (gated)
The autoresearch pattern can let the skill **rewrite its own rubric/file** as it learns what
converts. Keep that **opt-in and git-tracked**: propose the diff, let Malcolm approve, commit it.
Never let the skill silently change our brand voice. Best uses: this copy skill + reverse-lead-magnet creative.

## Rules
- Templates are plain markdown in `templates/` — edit directly; the candidate is reviewed, then committed.
- After ~14-30 days of real sends, re-run with the campaign's reply/A-B data to propose sharper copy.
