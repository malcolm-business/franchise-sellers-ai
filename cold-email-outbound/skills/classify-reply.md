---
name: classify-reply
description: Classify a single inbound reply into one of 11 intent categories + extract entities (re-engage date, referral name). Heuristic in dry-run, Claude API when live.
---

# classify-reply

The gap-fix vs the prior engine: 100% of replies get classified.

## Run
```bash
cd cold-email-outbound
python3 -c "from engine import classify; \
print(classify.classify_reply('Re: Quick question', 'Yes I would be interested, please send info'))"
```

## Categories
positive_meeting_ready · positive_curious · positive_with_timeline_objection ·
objection_not_now · objection_not_interested · wrong_person ·
wrong_intent_buyer_side · unsubscribe · out_of_office · referral ·
meeting_accepted · other

## Notes
- Dry-run uses the keyword heuristic (same logic as the historical reply analysis).
- Live uses Claude API (pinned model in config.ANTHROPIC.classify_model) with JSON output + entity extraction; falls back to heuristic on any API error.
