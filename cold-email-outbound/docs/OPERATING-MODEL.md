# Cold Email — Day-to-Day Operating Model

**Who this is for:** Theodore and Malcolm. The one-page answer to "how does this thing actually run, and who does what, where."

**The short version:** there are two surfaces. **Claude Code is the engine room** (where the work runs), and the **Marketing dashboard is the cockpit** (where you watch it and approve). You almost never touch raw code. You ask Claude to run a step, then you check the result on the dashboard. Want to feel the whole loop first? Open the dashboard → **Send & monitor** → **"Try a campaign (sandbox)"** and walk the simulator end to end. Nothing there is live.

---

## 1. The two surfaces

| | **Claude Code** (the engine room) | **Marketing dashboard** (the cockpit) |
|---|---|---|
| What it is | The orchestration brain. Runs every real action: pull leads, qualify, verify, build copy, stage, send, classify replies. | The read-and-approve view at `dashboard.franchisesellers.com/marketing`. Shows the state of the pool, the pipeline, deliverability health, and the safety gate. |
| Who drives it | Theodore or Claude (you ask, Claude runs the command). | Malcolm, daily. Theodore, when he wants a glance. |
| What you do here | Say what you want ("pull 1,000 qualified CS leads and stage them"); Claude runs it and reports back. | Watch the numbers, approve the copy, confirm the gate is green, decide the maintenance move. |
| Can it send email? | Only when `CEO_DRY_RUN=false`, and only Theodore flips that. | No. The dashboard can never send. The master switch is shown there but only **changed in the engine**, by Theodore. That separation is deliberate. |

**Rule of thumb:** if it *does* something (spends money, moves data, sends), it happens in Claude Code. If it *shows* something or asks for a human yes/no, that's the dashboard.

---

## 2. Who does what

| Person | Owns | Touches |
|---|---|---|
| **Theodore** | The go-live switch. Final approval before any live send. Flips `CEO_DRY_RUN` on a small batch, watches it, then ramps. | Claude Code + dashboard. |
| **Malcolm** | The campaigns: copy, offers, segments, the weekly read-and-adjust. Approves copy. Runs the weekly cadence (below). | Dashboard daily; asks Claude to run pulls/sends. |
| **Claude** | Runs every engine command so nobody logs into LeadMagic / MillionVerifier / Instantly by hand. Qualifies, verifies, stages, reports. | Claude Code. |
| **Lelia** | Schedules positive replies into a call. (Per the sender-identity decision: reply → Lelia books → David takes the first call → Eric does the valuation.) | CRM. |
| **Eric** | The ICP (ideal-customer profile) per brand. Feeds the targeting + the strategy. | The fillable ICP PDF. |

---

## 3. The weekly rhythm

This is the loop Malcolm runs once it is live. Each line says **where** it happens.

1. **Pull a fresh batch** of qualified leads for one brand/segment. *(Claude Code — `pull-leads`.)*
2. **Verify them fresh** through MillionVerifier right before sending, because the list is aged. *(Claude Code — `verify-pool`.)*
3. **Stage the campaign in dry-run:** build the sequence, render the copy, run the pre-send gate. Nothing sends yet. *(Claude Code — `run-campaign`, default analysis-only.)*
4. **Review on the dashboard:** open the Copy Preview Pack, confirm the gate is green, check deliverability health. *(Dashboard.)*
5. **Go live on a small batch:** Theodore flips the switch for ~200-300 on one brand. *(Claude Code, Theodore only.)*
6. **Monitor for 48 hours:** bounce under 3%, unsub under 2%, replies sane. *(Dashboard — Send & monitor + Replies.)*
7. **Read the weekly report:** sends, replies, positive-reply %, bounce, unsub, per campaign. *(Claude Code — `campaign-report`; numbers surface on the dashboard.)*
8. **Adjust or scale:** hold a clean campaign, promote a winning offer, or raise volume (never over 2% bounce). *(Decision; Claude re-runs.)*
9. **Cooldown + re-engage:** non-repliers rest 60 days, then re-enter a fresh sequence. *(Automatic — `cooldown-reactivation`.)*

Then repeat with next week's batch. The simulator walks exactly these steps.

---

## 4. Claude Code cheat-sheet (the commands behind each step)

You do not type these; you ask Claude for the outcome and it runs them. They are here so the mapping is transparent.

| Want to… | Skill / command |
|---|---|
| Qualify a fresh batch (paid: free filters → LeadMagic lookup → AI judge) | `qualification.qualify_batch(batch, live_enrich=True, save=True)` — run with the `.venv` python |
| Pull qualified, verified leads for a campaign | `db.pull_qualified(brand, limit, min_confidence=0.5)` · skill `pull-leads.md` |
| Re-verify a list before sending | skill `verify-pool.md` (MillionVerifier) |
| Build + dry-run a campaign (analysis only) | `pipeline.run_campaign(stream, limit, do_verify=True)` · skill `run-campaign.md` |
| Build with an A/B challenger offer | `pipeline.run_campaign(stream, test_offer='comparable_sales')` |
| Go live (Theodore only) | set `CEO_DRY_RUN=false`, then `run_campaign(..., do_push=True, activate=True)` |
| Weekly analytics | skill `campaign-report.md` |
| Quick safety probe, no push | skill `dry-run-probe.md` |
| Check sending-domain health | skill `mailbox-health.md` (also runs daily as a cron) |

**Always-true safety facts:** `CEO_DRY_RUN=true` today (nothing sends). Cold only ever sends from approved lookalike domains, never `franchisesellers.com` / `companysellers.com` or staff inboxes (hard-blocked in the engine). Open + link tracking are off. Every email carries the mailing address + opt-out automatically.

---

## 5. Dashboard cheat-sheet (the cockpit)

`dashboard.franchisesellers.com/marketing` → **Email Marketing** tab, in process order:

- **Performance snapshot** — the scoreboard (sample data until live).
- **① Leads & qualifying** — the funnel and qualification pass rate.
- **② Verify emails** — bounce target + re-verify window.
- **③ Campaign copy** — open the Copy Preview Pack, approve copy.
- **④ Pre-send gate** — the must-be-green checklist.
- **⑤ Send & monitor** — the master switch state + the **Try a campaign (sandbox)** button.
- **⑥ Replies & routing** — where replies go.
- **Deliverability health** — the silent daily monitor.

---

## 6. Where the simulator fits

The **"Try a campaign (sandbox)"** button (Send & monitor card) opens an interactive walkthrough of this entire model with test inputs and realistic results. It is the fastest way to *feel* the system before going live and to spot anything you want changed. Everything in it is simulated; no emails are sent and no data is written.

---

## 7. The one gate that matters

Nothing reaches a real inbox until **Theodore** flips `CEO_DRY_RUN=false`, and even then only on a small batch he is watching. Copy approval (Malcolm) and the ICP (Eric) are the two human sign-offs still outstanding before the first live send. Everything else is built and verified in dry-run.
