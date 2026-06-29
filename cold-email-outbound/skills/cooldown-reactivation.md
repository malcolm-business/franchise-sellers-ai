---
name: cooldown-reactivation
description: Find contacts whose cooldown / re-engage date has passed and re-queue them for a fresh touch. Run on a schedule (e.g. weekly).
---

# cooldown-reactivation

Contacts who said "not now" or didn't reply get a re_engage_date. This skill
surfaces the ones whose date has arrived so they re-enter a campaign.

## Run
```bash
cd cold-email-outbound
python3 -c "from datetime import date; from engine import data_layer; \
m = data_layer.iter_contacts(__import__('engine.config', fromlist=['CANONICAL_MASTER']).CANONICAL_MASTER); \
due = [c for c in m if c.re_engage_date and c.re_engage_date <= date.today().isoformat()]; \
print(f'{len(due)} contacts due for re-engagement')"
```

## Notes
- re_engage_date is set by routing.route_reply on cooldown categories.
- Defaults: 60 days (no-reply), 180 days (gave a 2026/2027 timeframe), 365 days
  ("in a few years"), 12 months (closed-lost in GHL).
- Re-queued contacts pass back through suppression + verification before sending.
