# Meta Ad Results Report — Playbook (SOP)

The repeatable process for reporting Meta (Facebook + Instagram) ad results to a client manager after a listing's campaign finishes. This is the **results** side. The ad-copy / campaign-build side is separate (see the `Meta Ads Copy Guidelines` and the `project_meta_ad_campaigns` memory).

Companion file: `META-AD-RESULTS-REPORT-TEMPLATE.md` (the fill-in email + metric glossary + a worked example).

---

## 1. Purpose & audience
- **Trigger:** a listing's Meta ad campaign shows **"Completed"** on the ads dashboard, or a CM asks how a run did.
- **Who it goes to: the CLIENT MANAGER only.** It is an internal reference for the CM. **The CM decides what, if anything, to share with the client.** Never send it to the client directly, and never to the seller.
- **Goal:** give the CM a clear, plain-English read on how the ad did: the numbers, what each one means, and whether the result was good or bad, so they can speak to it confidently.

## 2. What you need before drafting
- The listing's **internal ID** (e.g. 10072) and its **CM, brand, city, and listing type** (Toolkit vs Full Service). Pull from the CRM snapshot (§4).
- The **campaign metrics** from the Meta ad account (§3).

## 3. Pull the metrics (Meta Graph API, via the work droplet)
The token and ad account live on the droplet (`malcolm@165.227.206.190`, passwordless sudo). Run:

```bash
ssh malcolm@165.227.206.190 'sudo bash -s' <<'EOF'
set -a; source /root/cold-email-outbound/.env 2>/dev/null; set +a
TOKEN="${META_ACCESS_TOKEN}"
ACCT="${META_AD_ACCOUNT_IDS:-act_922460098250316}"; ACCT="${ACCT%%,*}"
curl -s -G "https://graph.facebook.com/v19.0/${ACCT}/insights" \
  --data-urlencode "level=campaign" \
  --data-urlencode "date_preset=last_90d" \
  --data-urlencode "fields=campaign_name,impressions,reach,frequency,clicks,ctr,cpc,cpm,spend,actions,cost_per_action_type,date_start,date_stop" \
  --data-urlencode "access_token=${TOKEN}" | python3 -m json.tool
EOF
```

- Match the campaign whose `campaign_name` **contains the internal ID** (campaigns are named like `10072 - Martial Arts Franchise (Michigan)`). Widen `date_preset` to `maximum` if a `last_90d` window misses it.
- Fields that matter: `impressions`, `reach`, `frequency`, `clicks`, `ctr`, `cpc`, `spend`, and the `actions` array.

### The lead-count gotcha (important)
Meta reports the SAME lead conversion under several `action_type` labels: `lead`, `onsite_web_lead`, `offsite_conversion.fb_pixel_lead`, `offsite_lead_add_20_s_calls`. **They are the same leads. Do NOT add them up.** The real lead count = the value of `lead` (equal to `onsite_web_lead`), which matches the "Website Leads" figure on the dashboard card. **Sanity check:** `spend / leads` should equal the "Per Lead" figure on the card.

### Which "clicks" number
- **Clicks to the listing** = the `link_click` action value (clicks that actually go toward the listing). Use this in the report bullets.
- `ctr` is Meta's **overall** click-through rate, and it counts ALL interactions, so it is higher than `link_click / impressions`. Cite it as the "overall" rate in the interpretation and label it that way, so it does not look inconsistent with the link-click count.
- `landing_page_view` = of those who clicked, how many actually loaded the page (usually a bit below link clicks; a small drop-off is normal).

## 4. Look up the CM + listing type (CRM snapshot)
```bash
ssh malcolm@165.227.206.190 "sudo python3 - <<'PY'
import json
d=json.load(open('/var/cache/crm-snapshot/crm-master.json'))
hit=[x for x in (d.get('listings_all') or []) if 'INTERNALID' in json.dumps(x)]
for x in hit[:1]:
    for k in ('internal_id','name','client_managers','owner_name','listing_type','city','state','franchise_brand','level_of_confidentiality','website_listing_link'):
        print(k,'=',x.get(k))
PY"
```
(Replace `INTERNALID` with the listing ID.)
- `client_managers` / `owner_name` = the CM to address (e.g. `['laura']` / `Laura Klinzmann`).
- `listing_type` = **Toolkit** or **Full Service**. This decides the leads-routing line (§6).
- `franchise_brand`, `city`, `state` for the intro line. The email is internal to the CM (who knows the listing), so naming the brand and city is fine even on a confidential listing.

## 5. Judge it: good or bad (benchmarks)
State a clear verdict. Rules of thumb:
- **CTR:** a typical Meta ad runs around **1%**. Above that is good; several times higher is strong (the creative + audience matched).
- **CPC:** lower is better. Under about **$1** is cheap for a business-for-sale audience.
- **Cost per lead:** for a business-buyer lead, **low double digits** is efficient. Context matters more than an absolute number.
- **Frequency:** about **1 to 2** is healthy (we did not over-show it). Climbing past ~3 to 4 on a longer run signals fatigue.
- **Reach** is capped by budget. A small spend means small reach. Call that out as the **limiter, not a failure**: the result can be efficient but small in absolute terms.

Lead with the verdict ("for a small run, this did well"), then support it with the numbers.

## 6. Draft the email (structure + routing)
Use `META-AD-RESULTS-REPORT-TEMPLATE.md`. Keep the structure:
1. **Intro** (name the listing, say we included spend so they see in vs out).
2. **Bulleted numbers:** Ad spend / Reach / Impressions / Clicks to the listing / Buyer leads (form fills).
3. **"A quick note on the terms:"** define Reach and Impressions (frequency inline).
4. **"On the leads:"** what a lead means, plus WHERE it routes:
   - **Toolkit** listing: inquiries route directly to the **seller**, who follows up.
   - **Full Service** listing: **Yvonne** (buyer manager) handles the inquiries.
5. **"Looking ahead:"** the attribution / dashboard note (tracking is being built; we cannot yet tie each lead to a specific buyer).
6. **"What this means:"** the good/bad verdict with the CTR benchmark and the return-for-spend context. Close the read with the seller's (Toolkit) or Yvonne's (Full Service) follow-up as what tells us lead quality.
7. **"Let me know if you have any questions."**

## 7. Guardrails (do not break)
- **CM only.** Internal reference; the CM shares with the client at their discretion. Never client- or seller-facing.
- **Always include the ad spend** (transparency: what went in vs what came back).
- **Real lead count only** (deduped per §3). Sanity-check against the dashboard card.
- **Attribution caveat included every time** (we cannot yet tie leads to specific buyers; dashboard tracking in progress).
- **No "run it again" language.** Present the results and let the CM / leadership decide next steps.
- **Explain every metric in plain language.** Assume the reader is not technical.
- **No em dashes** (Malcolm's copy rule). Use commas, colons, periods.
- **Claude drafts + pulls the data; a human sends.** Outlook is draft-only; Malcolm reviews and sends. Never auto-send.

## 8. Roles
- **Claude:** pull the metrics, look up the CM and listing type, draft the email.
- **Malcolm:** review and send to the CM.
- **CM:** uses it for reference; shares with the client as they see fit.

## 9. Run it in a fresh session (paste-in)
> "Meta ad results report. Listing [ID]. Read `AI Folders/Meta-Ad-Reporting/META-AD-RESULTS-REPORT-PLAYBOOK.md`, pull the campaign metrics from the droplet, look up the CM and listing type in the CRM snapshot, and draft the CM email from the template. CM only, real (deduped) lead count, include spend, no em dashes, no run-it-again language."

Related: `project_meta_ads_integration` (Meta data pull), `project_meta_ad_campaigns` (the ad-build side), `reference_people` (Yvonne = Buyer Manager), `feedback_no_em_dashes`.
