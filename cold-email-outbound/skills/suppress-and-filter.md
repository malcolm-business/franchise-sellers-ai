---
name: suppress-and-filter
description: Apply the Layer A pre-send suppression filter to a batch — removes anyone on the do-not-contact set, already in CRM, on a permanent flag, in an active cooldown, or missing/unverified email. Every drop logged with a reason.
---

# suppress-and-filter

The gate that protects deliverability + brand. Run on every batch before sending.

## Run
```bash
cd cold-email-outbound
python3 -c "from engine import data_layer, suppression; \
c = data_layer.load_tier_a('FS', limit=1000); \
f = suppression.SuppressionFilter(require_verified=False); \
clean, supp = f.filter_batch(c); \
print(f'clean={len(clean)} suppressed={len(supp)}'); \
print('reasons:', f.summary(supp))"
```

## Suppression sources (union)
1. Tier D do-not-contact set (Franchisee Block List + Airtable Archived)
2. In either GHL workspace (crm-snapshot, read-only)
3. Permanent flags (unsubscribed, hard_bounced, complaint, in_crm)
4. Active cooldown / re-engage date in the future
5. Missing email; optionally unverified (require_verified=True)
