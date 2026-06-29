# Toolkit SOP — Deal Studio

> Source: Notion page "Toolkit SOP — Deal Studio" under Operations & SOP Library > Toolkit Service. Last updated 2025.
> Owner: Toolkit Manager. Applies to: Franchise Sellers & Company Sellers.

## 1. Listing Trigger & Creation

**Now (Deal Studio):**

When agreement signed + payment received:

- Deal Studio creates a Seller Opportunity and a DealBuilder Listing
- Sets Listing Type = Toolkit to route workflows
- Assigns Toolkit Manager as owner
- Notifies Admin Team + Toolkit Manager

**Automation:** E-signature + payment → create listing → set Listing Type → owner + notifications

## 2. Seller Onboarding & Ad Copy (with Marketing Manager Approval)

- Admin Team drafts ad copy (AI assist allowed)
- Once draft is ready, automation sends Marketing Manager an approval email with two trigger links:
  - ✅ **Approve to Publish** → goes live via automation
  - ❌ **Needs Revision** → returns to Admin Team with revision task; new approval email resent on resubmission
- Seller receives DealBuilder portal invite to view/approve ad once Marketing Manager has approved
- Toolkit Manager oversees timeline and seller questions (does not own final ad approval)

## 3. Seller Interview & Business Summary (Video + SIM)

- Seller books interview via Toolkit Manager calendar link
- Toolkit Manager fills short Interview Prep Form (stored on the Opportunity)
- After the Zoom call, automation:
  - Emails raw recording to Rich
  - Creates a task for Rich: "Edit Toolkit Interview Video"
  - Sends Rich an email notification
  - If not completed in 7 days: reminder email + task bump fires
- Rich uploads final video via Upload Form or directly in DealBuilder
- DealBuilder embeds video into Business Summary (CIM) when available

> ⚠️ **Note:** SIM/CIM Builder feature set still rolling out; exact embed timing/fields may be adjusted.

## 4. Seller Portal & Data Room Access

- Sellers can view ad/SIM and upload documents via DealBuilder seller portal
- Every seller upload creates an internal review task for the Toolkit Manager (publication paused until approved)
- **Data Room Release:** Recommended field gate — "Seller Approved Data Room Access" (default = FALSE). When TRUE, automation sends Data Room access email to qualified buyers.

> ⚠️ **Pending Confirmation:** Confirm DealBuilder seller portal permissions and behaviors at go-live.

## 5. Buyer Flow & Qualification

- Buyers go through Buyer Profile + NDA and are qualified by the Buyer Manager
- When Buyer Qualified = TRUE, Deal Studio notifies the Toolkit Manager
- Toolkit Manager triggers Buyer ↔ Seller introduction email (includes buyer profile/NDA + SIM)
- From that point, seller owns communication

## 6. Buyer–Seller Handoff & Internal Follow-Up

On sending the intro email, automation:

- Updates stage to **Toolkit Handoff Complete**
- Transfers ownership of the listing to the seller in their portal
- Creates two internal follow-ups:
  - Toolkit Manager: Next-day "Did you connect?" call task
  - Admin Team: 30-day marketing check-in task to review ad performance/refresh

## 7. Listing Maintenance & Marketing Coordination

- Monthly check-in workflow emails sellers to confirm: ad accuracy, updates, price changes, selling intent
- Seller replies or portal edits create Toolkit Manager review tasks
- Any price/ad copy change request pings Admin Team and Marketing Manager for action/approval

## 8. Reporting & Oversight

- Central dashboards show Toolkit vs. Full-Service via Listing Type filter
- Weekly exec summary and monthly management report generated automatically
- Reports include: active listings, buyer intros, ad health

## Pending Confirmations

- Seller Portal (DealBuilder) behavior at launch: what sellers can edit vs. only upload
- Data Room release logic: recommended field gate (FALSE → TRUE triggers access email)
- SIM/CIM Builder rollout: adjust embed/fields as features go live
- Routing safeguard: if Listing Type is blank at creation, pause downstream automations and notify Admin Team
