---
name: verify-pool
description: Re-verify a contact pool's emails via the LeadMagic → ZeroBounce waterfall. Gates the sendable pool. Dry-run simulates verdicts; live spends credits.
---

# verify-pool

Runs email verification on a batch. LeadMagic primary; falls back to ZeroBounce
when LeadMagic credits hit the floor (config.VERIFICATION.leadmagic_credit_floor).

## Run
```bash
cd cold-email-outbound
python3 -c "from engine import data_layer, verification; \
c = data_layer.load_tier_a('CS', limit=500); \
verified, stats = verification.verify_contacts(c); \
d, dead = verification.split_deliverable(verified); \
print(f'deliverable={len(d)} dead={len(dead)} providers={stats}')"
```

## Notes
- Dry-run returns deterministic simulated verdicts (~78% valid). No credits spent.
- Live: set LEADMAGIC_API_KEY + ZEROBOUNCE_API_KEY, CEO_DRY_RUN=false.
- Re-verify anything older than config.VERIFICATION.reverify_after_days (90).
- HALT a campaign if real bounce rate exceeds 5% (the data was stale).
