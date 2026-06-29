---
stream: event_pre
brand: FS
description: Confirmed attendees of a specific upcoming event. Historical winner ONLY when sent to actual registrants (FLHC Pre 9.59%); broad blasts bombed. {{event_name}}, {{event_location}}, {{event_session}} are passed in per-campaign. Routes to Theodore direct + meeting booking.
subjects:
  - {{event_name}}
  - Are you attending {{event_name}}?
  - {{firstName}}, see you at {{event_name}}?
delays_days: [0]
default_offer: strategy_call
---
## STEP 1
Hey {{firstName}},

Are you attending {{event_name}} {{signal_anchor}}? If so, look for us — we'd love to connect!

At our session we'll cover a few key topics around business valuation and planning for a future exit. If that's on your radar, stop by.

{{sender_name}}
{{brand_name}}

If this is not relevant to you, simply reply with 'no'
