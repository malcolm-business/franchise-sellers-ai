# Listings Tool — Change Queue

Running backlog of changes/fixes Malcolm finds while testing the Listings tool.
**Capture only — nothing gets built until Malcolm says "go."** When we build, we work
top-to-bottom (or by priority) and check items off.

- Repo/lane: `fs-cs-internal-tools` → `cold-email-outbound/**` (Malcolm's lane).
- Authoritative tool doc: `fs-cs-internal-tools/cold-email-outbound/dashboard/LISTINGS-TOOL.md`.
- Deploy per `DEPLOY/README.md` (frontend .html = git push; backend .py = manual + backup).

**Status legend:** `QUEUED` · `READY` (spec'd, awaiting go) · `BUILDING` · `DONE`

---

## Queue

### Q1 — Submit button not locked during background regeneration → submits stale copy
- **Status:** ✅ DONE — deployed + verified live 2026-08-05 (commit `8f5a86b`)
- **Where:** Support wizard, Step 3 "Review & handoff" (during the client-feedback **Regenerate** flow). Effect also shows on the Marketing "Copy approval" screen's "Compare new vs old" view.
- **Issue:** When support regenerates copy (e.g. from client feedback), the regen runs in the background (the "Regenerating: … 25% ~64s left" corner widget). But **"Submit copy for approval →" stays active/clickable while the regen is still running.** Clicking it before the regen finishes submits the **OLD, pre-regen copy** — the regenerated version never lands. Confirmed on **10037**: submitted mid-regen, the output was byte-identical to the existing copy, and the marketing manager's "Compare new vs old" showed **NEW == OLD** (identical title + description).
- **Desired change:** While a regeneration is in progress, **lock/disable "Submit copy for approval →"** (and likely "Save as draft" / "Next") until the regenerated copy has actually landed in the wizard. Show the button in a clear disabled/"generating…" state so it's obvious why. Then submit always sends the latest applied copy, never the stale pre-regen version.
- **Details:** Listing **10037** (SC-1-800-Striper-Greenville). Background gen = `GENQ` / the corner "Regenerating…" widget. Related code: LISTINGS-TOOL.md §5 (`_wizHasCopy` / `gotoStep` guards lock the step tabs until copy exists, but **not** against an in-flight regen) and §10 (support client-changes regenerate opens the new copy in the wizard). Likely a two-part fix: (a) guard submit/next/save against an active `GENQ` job; (b) ensure submit reads the freshly-applied copy.

### Q2 — Same listing shows up multiple times in CM view; must consolidate to ONE entry with full history
- **Status:** ✅ DONE — deployed + verified live 2026-08-05 (commit `8f5a86b`)
- **Where:** CM "[CM] All Listings" section (and the per-listing detail window).
- **Issue:** The same listing appears as **multiple duplicate rows**. On **10165** (TX-Class 101-Frisco-Stacy Cook), it shows **twice** — one row tagged "New listing," one tagged "Revamp / refresh," both "Live" — because a new-listing flow and a revamp were both run for it. It's one listing, so it should not render as two.
- **Desired change:** **One listing = one entry / one window**, deduped by listing identity. Under that single entry, roll up **everything done for the listing, past and present**, so the CM sees the whole picture in one place:
  - all **copy versions** (original onboarding + every revamp/refresh + price-drops),
  - all **marketing requests** (past and present),
  - anything **currently being worked on** (in-progress status),
  - any **scoped marketing plan** for a request,
  - completed marketing work / tracking.
  The point: the CM opens one listing and can see exactly where marketing stands, then submit further requests based on that current state.
- **Details:** The draft store keeps one file per listing/request, and marketing requests + revamps spawn **separate draft records**; the CM "All listings" renders each draft as its own row → duplicates. Fix = **group/dedupe by listing identity** in the CM view, and make the listing detail **aggregate all related drafts** (onboarding, revamps, marketing-request children, ad/social production) into one timeline/history. Note on identity: grouping by `internal_id` handles the common case (both 10165 rows share the ID); but a revamp that changes the ID (BizBuySell re-list) would need the stable anchor (opportunity/contact, or the planned permanent code) to still group correctly — tie this to the permalink/stable-ID work.

### Q3 — After a client-feedback regeneration, the wizard lands on Step 3 (Submit) instead of Step 2 (Listing copy)
- **Status:** ✅ DONE — deployed + verified live 2026-08-05 (commit `49e2f8b`)
- **Where:** Support wizard, after "Regenerate from feedback" (client-changes flow). Seen on 10165.
- **Issue:** When support regenerates from client feedback and it finishes, the wizard shows **Step 3 "Review & handoff"** (the Submit step) instead of **Step 2 "Listing copy."** Support doesn't see the copy that was just written without manually clicking back to Step 2.
- **Desired change:** After a client-feedback regeneration, **automatically land on Step 2 (Listing copy)** so support reviews the new copy first, then moves to Submit.
- **Root cause (diagnosed):** `submitCopyClientChanges` opens the wizard via `resumeDraft(id)`, which jumps to the draft's STORED `step` = 3 (set when the draft was previously submitted for approval). The scoped-section regen path lands there with no correction; the whole-listing path only corrects to Step 2 via `_onGenForegroundDone` when the wizard is open at completion, and reopening via the corner "Review →" chip lands on stored step 3.
- **Fix plan (listings.html, frontend only):** land on Step 2 in all cases — (a) `gotoStep(2)` right after `resumeDraft` in BOTH the scoped (~line 2942) and whole-listing (~line 2947) client-feedback regen paths; (b) set the draft's stored `step` to 2 on generation completion (~line 878, currently `d.step=Math.max(2,d.step||1)`) so a reopen via the corner chip also opens on the copy step.

### Q4 — Listing image (and full info) doesn't transfer to the spawned social post on the Social Media tab
- **Status:** ✅ DONE (Pass 1) — deployed + verified live 2026-08-05 (commit `51e22fa`). build_social inherits the parent photo; spawns carry main_image; Meta ad card shows the image.
- **Where:** Listings → Social Media tab handoff. A social-post child draft is spawned into the Social Media production queue when a NEW listing's copy is approved (auto), and via a marketing request.
- **Issue:** The spawned social child draft carries the **listing copy** + basic intake (brand, level, `listing_id`, `parent_id`, flags) but **NOT the image**. Confirmed in both spawn paths — backend `_spawn_new_listing_social` (listings_api.py ~1341) and frontend `approveClientCopy` (listings.html ~2641): neither copies `intake.main_image` / `intake.images`, and neither copies the image FILE from the parent's image dir (`data/listings-images/<parent_id>/`) to the child's dir. → When the Social Media tab runs "Build the posts," `build_social` fails its guard: *"This listing has no photo yet — add a listing image before building social posts."* The carousel can't render without the photo.
- **Desired change:** The listing's image (the main photo) must travel to the social post so the Social Media tab can build the carousel without re-uploading — and all other needed info should come over so the social post is build-ready.
- **Fix plan (backend + frontend):**
  1. On spawn, copy `parent.intake.main_image` (+ `intake.images`) into the child intake — both `_spawn_new_listing_social` (backend) and `approveClientCopy` (frontend).
  2. Make the image FILE available to the child: EITHER (recommended, no duplication) have `build_social` resolve the photo from the PARENT's image dir via `parent_id` when the child has no image of its own, OR copy the parent's image file(s) into the child's image dir at spawn time.
  - Note: the listing copy + facts already transfer (copy on `child.listing`; facts resolve via `listing_id` from the snapshot). The confirmed break is the **image** — verify the rest is complete when building.
  - **Scope:** this image-transfer fix must cover BOTH handoffs — the **social** spawn AND the **Meta Ads** production queue ([[Q8]] point 5). The ad builder needs the listing photos too.

### Q5 — A CM's submitted marketing request doesn't immediately show (pending) in the open listing window
- **Status:** ✅ DONE — deployed + verified live 2026-08-05 (commit `49e2f8b`)
- **Where:** CM listing-detail window → "📣 Marketing Request" section, right after the CM submits a Marketing Request.
- **Issue:** The request IS created correctly — `submitMarketingRequest` (listings.html ~2586) sets status `mkt_triage` ("To scope"), `parent_id`, and carries the copy — and it DOES appear in the listing's Marketing Request section **on reopen**. But the OPEN detail window is not re-rendered after submit: `submitMarketingRequest` calls `loadDrafts()` (refreshes the queues) and closes the request modal, leaving the underlying listing-detail modal on its pre-request render. So the CM gets **no immediate confirmation** that their request landed and is waiting to be scoped.
- **Desired change:** Right after the CM submits, the listing window's Marketing Request section should show the new request with a clear **PENDING / "waiting for the marketing manager to scope"** status — confirmation it was submitted — even before the plan is scoped. Once scoped, show the plan (already handled).
- **Fix plan (frontend, listings.html):** after `submitMarketingRequest` succeeds, re-render the open listing detail for the parent (re-run `openListingDetail(parentId)` / refresh `renderCmExpandHtml`) once the child index (`CHILD_BY_PARENT`) is rebuilt, so the request shows instantly. Optionally make the pending label clearer for the CM (e.g. "Waiting for marketing to scope" vs just "To scope"). The status/plain-language + plan-on-scope are already handled (`_mktStatusPlain` "Marketing is reviewing your request and setting the plan"; `openMarketingRequestDetail`); the gap is the immediate refresh + clear pending confirmation.

### Q6 — "Scope the marketing plan" costs sit too far right → hard to tell which cost goes with which option
- **Status:** ✅ DONE — deployed + verified live 2026-08-05 (commit `49e2f8b`)
- **Where:** "Scope the marketing plan" modal (marketing triage) → "The plan we'll run" tactic checklist. listings.html `_renderMarketingTriage` (~line 2452-2456).
- **Issue:** Each tactic's cost is rendered with `margin-left:auto`, pushing it to the far right edge of the wide modal, leaving a big empty gap between the option label and its price. Only some rows have a cost, so it's easy to misread which price belongs to which option.
- **Desired change:** Make it obvious which cost belongs to which option (Malcolm's suggestions: lines across + close the empty space between label and cost).
- **Fix plan (frontend, purely presentational):** switch each row to a menu-style **dotted leader** layout — `[✓] Label ·········· $price` — with a light `border-bottom` divider per row (the "lines across"). Rows with no cost show no leader/price. Groups each option + cost as one readable unit and removes the confusing gap. Change is in the `checks` row template (~line 2455-2456), plus optionally a small CSS helper class.

### Q7 — Marketing request with social doesn't reach the Social Media tab; and the request type (price reduction / new listing / revamp) must be clearly carried + shown
- **Status:** ✅ DONE (Pass 2) — deployed + verified live 2026-08-05 (commit `1e12c00`). Marketing-request social/ad now spawn to the tabs (copy+photo+mode); "assets done → client approval" advance restored (was a regression from removing the production sections). **NEEDS Malcolm's end-to-end test.**
- **Where:** Marketing request → "Scope the plan" (`saveMarketingPlan`, listings.html ~2521-2556) → Social Media tab.
- **Issue (a) — social not sent:** A request scoped with a **copy revamp AND social** routes to the copy rebuild first — `saveMarketingPlan` sets `d.status='requested'` whenever `wantCopy`, deferring the social (`want_social=true`, `social_status='todo'`). Malcolm saw the copy revamp happen fine, but the **social post never reached the Social Media tab.** The assets-only path works (`else if(wantAd||wantSocial){ d.status='production'; }` → the social queue picks it up); the **copy+social path is missing the follow-on hop to `production` after the copy is rebuilt/approved**, so the social is stranded. VERIFY on build: the copy-approval/publish path for a `want_social` request must route it to `production`.
- **Issue (b) — request type must be clearly carried + shown:** Anything sent to the Social Media tab must clearly note whether it's a **Price reduction**, **New listing**, or **Revamp/refresh**. `saveMarketingPlan` sets `ink.mode` ('Price reduction' / 'Revamp / refresh'); the new-listing auto-spawn sets 'New listing'. Ensure: (1) `mode` reliably travels with whatever the social tab picks up, (2) the **Social Media tab displays the mode/request-type prominently**, and (3) `build_social` uses the right carousel variant by mode (new-listing orange vs price-drop red) — and decide what a "Revamp / refresh" maps to (new-listing styling?).
- **Fix plan:** (a) wire the post-copy-rebuild → `production` transition for `want_social`/`want_ad` marketing requests so the social reaches the tab; (b) carry `mode` onto the social production item, surface it clearly on the Social Media tab, and confirm `build_social` picks the carousel variant by mode. Do alongside **Q4** (image transfer) — same handoff path.

### Q8 — Meta Ads production queue: already exists; needs the handoff to fire + placement + clear request-type/copy (mirror social)
- **Status:** ✅ DONE (Pass 2) — deployed + verified live 2026-08-05 (commit `1e12c00`). Ad production queue repositioned between the KPIs and By brand; mode/request-type shows on the ad card; image shows (Q4); `ad-done` advances the item. **NEEDS Malcolm's end-to-end test.**
- **Where:** Meta Ads tab (meta-ads.html) + the marketing-request routing.
- **Current state (good news):** meta-ads.html ALREADY has a per-listing ad production queue — **"🎬 Ad production queue"** (`loadProduction` / `renderAdQueue`, ~line 176-232). It pulls drafts with `status==='production'` + `want_ad` + `ad_status!=='done'`, renders "Build the ad" with the draft's copy attached (comment ~line 189: the approved copy travels on the draft). So the infra mirrors the social side — this is NOT build-from-scratch.
- **What's actually needed:**
  1. **Make the handoff fire (root cause).** Malcolm's ad request never appeared because it had copy + ad → routed to copy-rebuild first and never hopped to `production`. **Same fix as Q7(a).** Once that's fixed, `want_ad` requests reach `production` and this queue populates.
  2. **Placement:** position the "🎬 Ad production queue" **between the top META ADS (KPI) section and the BY BRAND section** on meta-ads.html (Malcolm's requested spot — verify/move current placement).
  3. **Clear request type:** show New listing / Price reduction / Revamp prominently on each ad-queue row (same as Q7(b)).
  4. **Full handoff:** confirm the approved listing copy + all details Malcolm needs to build the ad travel on the draft the queue reads (line 189 intends this — verify).
  5. **Images:** the listing's photos must travel to the ad queue too, so they can be used in the Meta ad — **same image-transfer fix as Q4, applied to the ad side.** (Q4's fix should cover BOTH the social and the ad handoff.)
- **Fix plan:** build alongside Q4 + Q7 as one Listings→Social/Ads handoff piece — (a) Q7(a) routing fix populates this queue; (b) reposition the ad queue between META ADS and BY BRAND; (c) show mode/request-type per row; (d) verify copy + details on the draft; (e) carry the listing images to the ad queue (Q4 fix, ad side).

<!--
Template for each item:

### Q1 — <short title>
- **Status:** QUEUED
- **Where:** <role/screen — support wizard | marketing approval | client portal | publish | production tab | backend>
- **Issue:** <what's wrong / what's happening now>
- **Desired change:** <what it should do instead>
- **Details:** <listing ID / exact field / repro steps / screenshot notes, if any>
-->
