# Facebook Group Sharing — Playbook (SOP)

> **New here / handing this off?** Start with **`SOCIAL-GROUP-SHARING-OVERVIEW.md`** (the master index) — it has the current status, the file map, the guardrails, and the posting-gate taxonomy. This playbook is the process detail it points to.

The rules and criteria for finding, vetting, and joining Facebook groups where we share business listings, and (later) how we post to them. State-agnostic: this governs the process; each state has its own working directory of actual groups.

- **Working group lists (all in this `AI Folders/Facebook-Group-Sharing/` folder):** `SOCIAL-GROUP-SHARING-TX-DIRECTORY.md` (Texas, 32 joined), `SOCIAL-GROUP-SHARING-CA-DIRECTORY.md` (California, 41 joined), `SOCIAL-GROUP-SHARING-GA-DIRECTORY.md` (Georgia, 44 joined — COMPLETE), `SOCIAL-GROUP-SHARING-FL-DIRECTORY.md` (Florida, 44 — COMPLETE), `SOCIAL-GROUP-SHARING-IN-DIRECTORY.md` (Indiana, 18 — target met), `SOCIAL-GROUP-SHARING-CO-DIRECTORY.md` (Colorado, 17 — target met), `SOCIAL-GROUP-SHARING-OH-DIRECTORY.md` (Ohio, 16 — target met), and `SOCIAL-GROUP-SHARING-TN-DIRECTORY.md` (Tennessee, 9 — in progress). Each new state gets its own directory here. Next: finish Tennessee, then the 2-listing states. Page total ≈234 groups.
- **Related:** Meta paid ads playbook, social caption/carousel SOPs, buyer-blast playbook.

---

## 1. Purpose
Get FS business-for-sale listings in front of entrepreneurial, business-minded audiences at low cost, as a **supplemental reach channel**. Honest expectation: Facebook groups are a top-of-funnel awareness play, not a primary source of serious buyers (those cluster on BizBuySell, brokers, our own funnel). We do it because it's cheap and each post takes minutes. Prioritize conversion over raw volume.

**This is a living, ongoing project.** We keep adding new groups to the system over time and keep the state directories updated in the repo as we go. The plan and rules below stay the same; the set of groups grows. See the overview's "Ongoing maintenance & ownership" section for how the repo is kept current on handoff.

## 2. Hard guardrails (never break)
- **Join and post AS the Franchise Sellers Page** (verify the account before any action: the composer should read "What's on your mind, Franchise Sellers?").
- **No automation.** Meta killed the Facebook Groups API (April 2024). No API / Zapier / Make can join or post to groups. All joining + posting is human-in-the-loop through a logged-in browser. Bulk/scraped joining gets the Page banned.
- **Never misrepresent to pass a gate.** If a group asks "Are you a [state] business owner?", we are a brokerage and cannot answer yes. Skip it, don't lie.
- **Respect listing confidentiality.** Confidential listings hide city/brand. Never post details a listing's confidentiality level conceals.
- **CTA routes to the website**, never "DM us / message us" (the site has phone + all contact options).
- **Posts are CM-approved**, not client-facing. Social is a promised service; a human/CM greenlights before posting.
- **No em dashes** in any drafted copy. Use commas, colons, periods.

## 3. Groups we LOOK FOR (join)
Target audience = people who might buy, or know someone who'd buy, a business: owners, entrepreneurs, investors, franchise-minded people.

Join when the group is:
- **Public** (so the Page can join without owner-gating), AND
- **Active** — ideally 20+ posts/day (dead groups = no eyeballs), AND
- **Business/promo-friendly in purpose** — "business owners", "entrepreneurs", "networking", "promote your business", "business for sale", "small business community".

Group categories, in priority order:
1. **Business-for-sale boards** ("[State] Business for Sale", "business sale by owner") — closest to buyer intent.
2. **Owner / entrepreneur / networking groups** (statewide + each major metro) — the reach backbone.
3. **Metro-specific** business groups (one+ per major metro).
4. **Industry-specific** groups that match a particular listing (fitness, food, franchise, salon, home services, auto, retail) — join situationally when a listing fits; often converts better because intent is aligned.

### Per-group record schema (what we log for EVERY group — this is what makes listing→group filtering work)
Two fields do the matching; the rest rank and qualify:
- **Geo scope** (matching key 1): `national` / `statewide-[ST]` / `metro-[name]` / `subregion-[name]`. A listing filters to groups whose geo covers its location (e.g. a San Diego business → San Diego + SoCal + CA-statewide + national).
- **Audience/industry tag** (matching key 2): `general-business` / `business-for-sale` / `industry-[fitness|food|retail|franchise|home-services|salon-beauty|auto|...]` / `niche-[identity]`. A listing filters to `general-business` + `business-for-sale` + its own industry tag.
- **Members** and **Activity** (posts/day) — prioritization (skip dead groups, favor big + active).
- **Privacy** (public/private) and **Page-OK** (Y/N) — eligibility.
- **Post status**: `open` / `approval-needed` (+ note what the participation questions ask) — so Rosie knows if the first post needs the gate cleared.
- **Content/promo fit**: welcomes business-for-sale / promo posts, or local-services-only? Flags poor posting fits even where we're a member.
- **Fit tier** A/B/C and any special rule to respect.
- **Group profile / angle (1-2 sentences)** — the character of THIS group: who's in it, the tone, what content lands, any local flavor or quirk. This is the field the tailored-message generator draws on so each share ties directly to the group and reads native, never a copy-paste. Examples:
  - *Small Business Owners of Austin/Central Texas* — "Austin owners who actively cross-promote; About literally says 'post your business.' Warm, supportive, promo-welcome. Angle: frame the listing as an opportunity for a fellow Central TX owner/buyer."
  - *Business For Sale by Owner (267K, national)* — "Active acquisition-minded audience explicitly there to buy/sell businesses. Angle: lead with the numbers/opportunity, this room has real buyer intent."
  - *SAN DIEGO SMALL BUSINESS AND SERVICES* — "Big, busy SD local room, services-and-shops flavor. Angle: local hook ('a San Diego business is on the market'), keep it neighborly."
  - Capture a cheap one-liner at join time (from the group's About + a glance at posts); enrich it for the specific groups a listing targets at share-time (that's when the rich, tailored copy gets written anyway).

With those fields the weekly step is a clean filter: `geo covers listing location` AND (`audience = general-business` OR `business-for-sale` OR `industry matches`), then rank by members × activity, drop poor content-fit.

Status: current directories capture name/geo/members/activity/privacy/post-status/notes (enough for GEO matching now). The **audience/industry tag** is the field to apply consistently — it mostly activates once we start joining industry-specific groups per listing.

## 4. Groups we AVOID (skip, and log why so we don't re-consider)
- **Owner-gated private groups** ("Are you a [state] business owner?") — can't pass honestly as a brokerage.
- **Buy / Sell / Trade & marketplace groups** — bargain hunters wanting a used couch, not a $400K business. Posting there = spam.
- **Real estate networks** — wrong audience, unless the listing is itself real-estate-tied.
- **Generic "advertising / promote anything" dump groups** — high volume, near-zero quality; members are all promoters, no buyers.
- **Off-topic identity/community groups** (faith, ethnic, women-owned, etc.) — real audiences, but only relevant if the specific seller/listing genuinely fits. Don't blanket-target.
- **"By owner, no broker" boards for posting listings** — our brokered listings aren't welcome. BUT note: these rooms are full of owners trying to sell = potential SELLER leads (our #1 goal). Flag for a possible separate seller-outreach play, don't spam listings there.

## 5. Daily join process
- **Pace:** Facebook throttles at ~30 join requests / 12 hrs (temporary "action blocked" risk). Keep each day to **~20 max**, spaced out.
- **Geo note:** the Page's account reads as Colorado-based, so plain searches return CO/UT groups. **Always include the state/metro in the search** ("Houston business owners", "Texas business for sale").
- **Mechanics:** join from the group-search results. The FIRST click on a fresh target often misses — **verify the button flips to "Visit"/"Joined" and re-click if not.** Some groups pop a "Participant questions" dialog on join (that's a posting-gate, see below) — click "Not now" for now.
- **Verify** the day's joins at `facebook.com/groups/joins/` ("last visited: a few seconds ago" = joined today).
- **Log** every result in the state directory, including posting-gate status.

## 6. Joining is NOT posting (the posting-gate)
Many public groups let the Page join instantly but require a **one-time, admin-reviewed participation request** with questions before the first post, and explicitly decline promo/spam. Some questions assume you're a local business ("what's your business / do you live here?"). Handle these **at first-post time**, not at join:
- Answer honestly as Franchise Sellers.
- Never enter an email/phone into a group's entry questions.
- If the group is clearly local-owner-only, it may be a weak posting fit even though we joined — note it.

## 6B. What a post physically looks like — "share a listing" vs. original post
Verified live in a joined group as the FS Page (2026-08-26): the Page composes a normal post (composer opens as "Franchise Sellers"; options = text, Photo/video, tag, location, feeling). **There is no separate "share this external listing" button.** Sharing a Facebook *post* between groups exists, but our listings live on our website, so a listing always goes in as a **new post we compose**, in one of two formats:

- **A. Link post (the closest thing to "just sharing the listing").** Paste the listing's **public `.com` URL** into the composer. Facebook auto-fetches a preview card (image + title + `franchisesellers.com`); delete the raw URL text and keep the card, then write the tailored message above it. Fast. Trade-offs: some groups down-rank external-link posts, and the auto-card pulls whatever image/title the public page carries (so it's only as confidential as that page — see below).
- **B. Original creative post (the recommended default).** Click **Photo/video**, upload our carousel slides (the ones we already build for the listing), write the tailored caption, and put the website link **in the caption or the first comment.** This looks native, we control the image and the framing, and it dodges the link-post down-ranking. It reuses the carousel + caption system we already have, so it's the primary format for group shares. (Bare "here's who Franchise Sellers is" general posts are a distant secondary — occasional, not the point.)

**Which to use:** default to **B** in most groups (better reach, we control image + confidentiality); **A** is fine in the promo-tolerant open rooms when speed matters. Either way, one post per group with its own tailored copy — never the same text pasted across groups (FB throttles duplicates).

**Does it go live immediately or wait for an admin?** Depends on the group, and it's already tracked per-group as **Post status** in each state directory: `open` = publishes instantly (confirmed: open groups show members' promo/link posts live with no gate); `approval-needed` = the first post clears a one-time participation gate and/or admin review (see §6). Match effort to that flag.

**Confidentiality is inherited from the URL/creative, automatically:** always use the public `.com` listing page (never the `.co` NDA microsite). A link card can't reveal more than the public page shows, and our own slides only show what we put on them, so a brand-hidden (Level A) listing stays safe by construction. Fully-confidential or seller-opted-out listings get **no group post at all** (they fall out of the pool, §8).

**Geo-match is the whole point (your primary use case):** a listing only goes to groups whose **Geo scope** covers its city (a Savannah business → Savannah + GA-statewide groups, not Atlanta-only rooms). That filter is exactly what the directory's Geo field is for.

## 7. Geographic rollout — driven by where our listings come from
Prioritize states by our **actual listing volume (trailing ~12 months)**, and **match group-coverage effort to volume.** Don't overdo the low-volume states. Work straight down the list; each state gets its own directory file built with these same rules.

**Coverage tiers (listing counts from the source table):**
- **Deep coverage** — top states where we do real business. Saturate: statewide + every major metro + national business-for-sale (the ~30-40-group treatment we gave TX/CA).
  - Texas (11) ✅ done · California (10) ✅ done · **Georgia (9)** ← next · Florida (6)
- **Moderate coverage** — solid but not exhaustive: statewide + the main 2-3 metros (~15-20 groups).
  - Indiana (4) · Colorado (3) · Ohio (3) · Tennessee (3)
- **Light coverage** — low-volume states (~2 or fewer listings/yr). Quick pass, **~10 groups each**, statewide + the top 1-2 metros, then move on.
  - New Jersey (2) · Massachusetts, Kansas, Idaho, Washington, Virginia (2 each) · Michigan (2) · Alabama (2) · South Carolina (2) · Minnesota (2) · Iowa (2) · Maryland (2)
  - 1-listing states (lightest touch, statewide + maybe one metro): Kentucky, PA, IL, NC, WI, NY, LA, NM, OK, DE
- **Skip:** "no state on file" (2) — unknown location, nothing to geo-target.

**Order of operations:** TX ✅ → CA ✅ → **Georgia** → Florida → Indiana → Colorado → Ohio → Tennessee → the 2-listing states → the 1-listing states. Revisit/refresh the top-tier states periodically as new groups appear.

## 8. Sharing process — WEEKLY EMAIL TO ROSIE (design locked, generator TO BUILD)
Cadence: **once a week**. Deliverable: **one email to Rosie** (she does the actual posting). The email is organized per listing/post and contains everything she needs to post without further instruction.

**Each email contains, per listing:**
1. **The post** — the creative/image + the base caption (the social content being shared).
2. **The target group list** — which of our joined groups this listing should go to (matched by `[industry] + [metro]` from the state directory; only groups we're actually in).
3. **A unique, group-tailored message for EACH group** — this is the core requirement:
   - Every group gets its **own** message. No identical copy-paste across groups.
   - Each message is built from **that group's profile/angle note** (see the record schema) — its locale, audience, tone, and quirk — so it reads as native to that room, not a broadcast.
   - Why it must be unique: identical cross-posts read as spam to members AND get throttled by Facebook's duplicate-content detection. Tailoring is both better reach and required by our "value, not an ad" rule.
   - Every message still: routes CTA to the website (never "DM us"), respects the listing's confidentiality, no em dashes.

**Format (per group in the email):**
> **Group:** [name] — [metro] ([members])
> **Note:** [posting-gate status / any group-specific rule Rosie should respect]
> **Message to post:**
> [the unique, tailored copy for this group]

**Posting cadence (keep it minimal — event-driven, not calendar-driven):**
- **No "stay active" posting.** Groups don't penalize silence; there's no reach decay. Never post filler just to stay visible — it's wasted effort and raises spam risk.
- **Trigger = a new listing**, not the calendar. New listing in a state/metro → it goes to that state's matched groups in that week's batch. No new listings that week → post nothing.
- **Two ceilings, don't confuse them:**
  - *Same listing → same group:* **once a month max**, always with a fresh angle/copy (never identical — FB throttles duplicates, members tune out repeats).
  - *All listings → any single group (total):* **~1 post/week, ~4/month max.** When several listings land in one month for a state, **stagger them across weeks AND distribute listings across the group set** (each listing → its best-fit groups) — never dump every listing into every group at once. That's what prevents overposting.
- **Optional monthly refresh** for a priority/aging still-active listing: re-share with a new hook (price drop, "still available," different selling point) to catch members who are new since last time. Monthly is plenty; that's the only reason to re-touch a group.
- Net rhythm: new listings weekly in the batch; any one listing hits any one group at most monthly; light weeks and empty weeks are fine and expected.

**Engagement (don't post-and-ghost):**
- Pure drive-by posting (only dropping listings, never engaging) is what admins dislike most and the fastest way to get removed from stricter groups.
- **Do this (high value, low effort):** reply to comments/questions on our OWN listing posts — that's where buyer conversations start. Rosie checks her posted listings for comments ~weekly and replies (as the Page).
- **Optional, light:** an occasional like/comment on others' posts keeps the Page looking human and admins friendly. Nice-to-have, not required.
- No need to be a community regular; just never ghost our own posts.

**Confidentiality drop-out:** highly confidential listings usually get NO group post (either identifying details can't be shown, or the seller opted out of social entirely). They fall out of the sharing pool automatically — CM/confidentiality level decides, no extra step.

**Build notes:**
- AI generates the match list + the per-group tailored copy. A human/CM approves.
- The weekly email itself is **drafted, not sent, by Claude** (Outlook = draft-only; Malcolm reviews and sends to Rosie).
- First time posting in a gated group: Rosie (or a human) completes its participation request honestly first.
- Timing: a few days' lag from the original post costs nothing — the group sees it fresh whenever posted.

## 9. Roles
- **Claude / AI:** research + vet + join groups, maintain the directory, match listings to groups, draft the unique per-group copy, and draft the weekly email to Rosie.
- **Malcolm:** reviews/approves and sends the weekly email; clicks Join where he prefers to.
- **Rosie:** receives the weekly email and does the actual posting into each group (one tailored message per group).
- **CM:** approves the social post before it goes out.
