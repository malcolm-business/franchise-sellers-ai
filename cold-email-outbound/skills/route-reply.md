---
name: route-reply
description: Route a classified reply to its destination — positive seller → matching GHL workspace, buyer-side → Buyer Manager, referral → new record, cooldown → re-engage date, unsub/no → suppression. Brand-walled, never cross-routes.
---

# route-reply

Applies the routing matrix. Mutates the contact (send_status, re_engage_date,
suppression) and returns the action taken.

## Run
```bash
cd cold-email-outbound
python3 -c "from engine import data_layer, routing; \
c = data_layer.load_tier_a('FS', limit=1)[0]; \
print(routing.route_reply(c, 'positive_meeting_ready'))"
```

## Routing matrix
| Category | Destination |
|---|---|
| positive_meeting_ready / meeting_accepted | GHL (brand), Discovery Call workflow |
| positive_curious | GHL (brand), OOV Intake workflow |
| positive_with_timeline_objection / objection_not_now / out_of_office | cooldown + re-engage date |
| wrong_intent_buyer_side | Buyer Manager (Yvonne) pipeline |
| referral | new warm-intro record |
| unsubscribe / objection_not_interested | permanent suppression |
| wrong_person / other | human review |

Dry-run logs the intended GHL create; live honors GHL single-record + rate-limit rules.
