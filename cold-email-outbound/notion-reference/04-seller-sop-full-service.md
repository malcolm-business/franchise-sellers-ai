# Seller SOP — Deal Studio (Full Service)

> Source: Notion page "Seller SOP — Deal Studio (Full)" under Operations & SOP Library > Seller Pipeline. Last updated Nov 6, 2025.
> Owner: Sales & Admin Team. Applies to: Franchise Sellers & Company Sellers.
> ⚠️ This is the full strategic SOP with automation specs. For the day-to-day step-by-step, see the New Seller Lead Process page in Notion.

## 1 — New Seller Lead Intake

All entry points (referral/direct email, website forms, ads, LinkedIn, events) route to a single Lead Intake Form (Name, Email, Phone, Business Name, basics).

- Admin sends email template with booking link. First screen = discovery call calendar; next step = lead intake form (not DealBuilder). Form must be completed to confirm the call.
- **Ownership:** All new leads assigned to Admin Team
- If no booking occurs: automation triggers SMS/email nudges + follow-up task to Admin Team
- **Automation:** Booking Page → Lead Intake Form + Source Tagging + Ownership Rule + SMS/Email Workflow
- **Workflow:** Create new contact from form → creates new opportunity in Prospect Stage, Seller Pipeline
- **Automation addition:** When new lead added → connect on LinkedIn, add to Meta and Google audiences
- **Note:** Notification sent to sales team when new call is booked
- **Future:** AI pre-call summary for sales team (lead source, franchise brand history, business start date, revenue, website summary)

## 2 — Discovery Call Scheduling

Deal Studio auto-creates/updates the contact, creates the opportunity in Prospect, and sends email + SMS confirmations and reminders.

- **Automation:** Calendar Booking Trigger → Stage Update + Email/SMS

## 3 — Discovery Call Complete + OOV Prep

- Sales Team completes the post-discovery call form
- **Fields:** Discovery call completion date
- **Workflow:** Move opportunity to "Discovery Call" → emails lead the OOV template (DealBuilder intake form link) → 5 min later SMS sent → email & SMS FT at Day 4 → phone call at Day 8 → email & SMS FT at Day 15

**Upon DealBuilder seller intake form submission:**

- AI (ChatGPT via webhook) validates completeness and parses key metrics (Revenue, SDE, margins, trends, flags, confidence score)
- If complete/valid: CRM marks Financials Validated = TRUE → sends structured summary + confidence score to Eric via email → updates stage to "Ready for OOV"
- If incomplete: creates Admin Team task to request missing documents (with AI's reason)

## 4 — Financial Review & Opinion of Value (OOV)

- When OOV recasting is complete (AI or manual), notification sent to Eric to finish the valuation
- Eric is notified only when AI-validated summary is ready (email with contact data, metrics, and confidence score)
- Eric completes the valuation using internal OOV Delivery Form:
  - Upload Recast Excel
  - Paste Loom URL
  - Questions and Notes
- On submission: sends OOV email to client (with Loom) + confirming SMS → 3-day follow-up email → call 2 days later if no response

## 5 — Agreement & Onboarding

- When lead is ready to get started, trigger the workflow (Form or Custom Field — TBD during build)
- Route via correct package: Toolkit or Full Service, multiple locations, unique onboarding pricing?
- **Workflow:** E-signature agreement + payment link
- Workflow waits for BOTH: Agreement Signed = TRUE AND Payment Complete = TRUE
- When both true: Move to "Onboarding"

## 6 — Transition to Listing (DealBuilder)

**Auto-created Task Checklist Template within the Opportunity:**

- Create/verify Data Room structure
- Confirm redaction complete (approval checkbox)
- Generate CIM via DealBuilder CIM AI Tool
- Admin Team reviews CIM (improve/polish)
- Client Manager review
- Publish listing

**Additional steps to evaluate:**

- Send to Village Wealth?
- Start social buyer ads?
- Send internal buyer blast?

**Custom Fields for reporting:** New Listing Date, Listing Type, Profitability
