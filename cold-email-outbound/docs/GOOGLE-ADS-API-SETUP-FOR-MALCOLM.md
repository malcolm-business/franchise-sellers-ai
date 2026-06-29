# Google Ads API — Setup Guide (for Malcolm)

**Goal:** connect the **Franchise Sellers** and **Company Sellers** Google Ads accounts so the
marketing dashboard's **Google Ads** tab shows live campaign performance (spend, clicks,
conversions, etc.).

**Your job is just to create credentials** — you don't build anything. When you're done you'll
have **5 short values**. Send those to Theodore; he drops them into the system and the tab goes
live on the next refresh. Read-only reporting access is all we need.

You can do this yourself, or hand this whole file to your Claude / Claude Code — it's written so
an AI assistant can run the technical parts (the refresh-token step in particular) for you.

---

## What you're producing (the 5 deliverables)

Give these back to Theodore at the end:

| # | Value | Looks like |
|---|---|---|
| 1 | **Developer token** | `a1B2c3D4e5...` (22 chars) |
| 2 | **OAuth client ID** | `1234...apps.googleusercontent.com` |
| 3 | **OAuth client secret** | `GOCSPX-...` |
| 4 | **Refresh token** | `1//0g...` (long) |
| 5 | **Customer IDs** (FS + CS) | `1234567890,0987654321` (10 digits each, no dashes) |
| 5b | *Manager/MCC ID (only if you use one)* | `1112223333` |

> ⚠️ These are sensitive. Don't paste them into email/Slack in plain text — use whatever secure
> method you and Theodore prefer (password manager share, a call, etc.).

**Reference docs (Google's official):**
- Client libraries: https://developers.google.com/google-ads/api/docs/client-libs
- API version upgrades: https://developers.google.com/google-ads/api/docs/upgrade

---

## Step 1 — Developer token  *(start this first; it can need approval)*

1. Sign in to the Google Ads **manager (MCC) account** that sits above the FS + CS accounts.
   (If FS and CS are separate standalone accounts with no manager above them, you can do this in
   either account, but a manager account is cleaner — tell Theodore which setup you have.)
2. Go to **Tools (🔧) → Setup → API Center**.
3. Copy the **Developer token** → that's **value #1**.
4. If it says **Test account access only**, click **Apply for Basic access** and fill the short
   form (we only read reporting data). Approval can take a day or two, so start it now. You can
   finish the rest of the steps while it's pending.

---

## Step 2 — OAuth client (Google Cloud)  *(~5 minutes)*

1. Go to **https://console.cloud.google.com** and create a new project (e.g. "FS-CS Ads API")
   or pick an existing one.
2. **APIs & Services → Library** → search **"Google Ads API"** → **Enable**.
3. **APIs & Services → OAuth consent screen**:
   - User type: **Internal** if your company Google Workspace offers it (simplest). Otherwise
     **External** and add your own Google account under **Test users**.
   - App name / support email: anything reasonable. Save.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Desktop app**  ← important, this makes the refresh-token step easy.
   - Create, then copy the **Client ID** (#2) and **Client secret** (#3).

---

## Step 3 — Refresh token  *(the one technical step — let your Claude do it)*

A "refresh token" lets our system pull your Ads data automatically without you logging in each
time. The easiest way to mint one uses Google's own Python helper. **Give your Claude the block
below** (it has the client id + secret from Step 2):

> **Instructions for Claude / Claude Code:**
> 1. `pip install google-ads`
> 2. Download Google's official helper:
>    `https://raw.githubusercontent.com/googleads/google-ads-python/main/examples/authentication/generate_user_credentials.py`
> 3. Run it with the Desktop-app credentials from Step 2:
>    ```
>    python generate_user_credentials.py --client_id="<CLIENT_ID>" --client_secret="<CLIENT_SECRET>"
>    ```
> 4. It prints a Google sign-in URL. Malcolm opens it, signs in with **the Google account that has
>    access to the FS + CS Ads accounts**, and approves. Paste the returned code back into the prompt.
> 5. The script prints a **refresh token** (`1//0g...`) → that's **value #4**.
>
> The OAuth scope is `https://www.googleapis.com/auth/adwords`. The helper requests it automatically.

**No-code alternative (OAuth 2.0 Playground):** if you'd rather not run a script — in Step 2 create
a **Web application** OAuth client instead of Desktop, and add `https://developers.google.com/oauthplayground`
as an **Authorized redirect URI**. Then go to **developers.google.com/oauthplayground** → gear icon →
"Use your own OAuth credentials" → paste client id + secret → in the scope box enter
`https://www.googleapis.com/auth/adwords` → Authorize → sign in + consent → "Exchange authorization
code for tokens" → copy the **Refresh token**.

---

## Step 4 — Customer IDs

1. Open each Google Ads account (Franchise Sellers, then Company Sellers).
2. The **10-digit account ID** is at the **top right**, formatted like `123-456-7890`.
3. Write both down **without the dashes**, comma-separated → **value #5**, e.g. `1234567890,0987654321`.
4. If both accounts live under a **manager (MCC) account**, also grab the manager account's 10-digit
   ID → **value #5b**.

---

## Step 5 — Hand off to Theodore

Send Theodore the 5 values (securely). For reference, here's exactly where they land in our system
(`/root/cold-email-outbound/.env` on the server) — **Theodore does this part:**

```
GOOGLE_ADS_DEVELOPER_TOKEN=...        # value 1
GOOGLE_ADS_CLIENT_ID=...              # value 2
GOOGLE_ADS_CLIENT_SECRET=...          # value 3
GOOGLE_ADS_REFRESH_TOKEN=...          # value 4
GOOGLE_ADS_CUSTOMER_IDS=1234567890,0987654321   # value 5 (digits only, comma-separated)
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1112223333         # value 5b (only if using a manager account)
```

Once those are in, the dashboard's Google Ads tab flips from "not connected" to live on the next
data refresh. Theodore can confirm with a one-line test from the server.

---

## Notes (for Claude / whoever sets this up)

- **Our connector talks to the Google Ads REST API directly** (`engine/google_ads.py`, stdlib
  `urllib`, no client library at runtime). The `google-ads` Python library above is used **only** to
  generate the refresh token — it is not a runtime dependency.
- It's pinned to **API version `v17`**. If Google has sunset v17 by the time you set this up (see the
  "API version upgrades" doc), tell Theodore to bump `API_VERSION` in `engine/google_ads.py` — a
  one-line change.
- Scope: `https://www.googleapis.com/auth/adwords`. **Read-only reporting** is sufficient; you do not
  need write/management access.
- The Google account used in Step 3 must be able to see **both** Ads accounts (or the manager account
  above them), or the dashboard will only show the accounts it can reach.
- Nothing here sends email or changes campaigns — it only **reads** performance numbers for the
  dashboard.
```
