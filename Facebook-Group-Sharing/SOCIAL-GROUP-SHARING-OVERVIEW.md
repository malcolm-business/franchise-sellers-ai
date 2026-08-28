# Facebook Group Sharing — MASTER INDEX & HANDOFF

**Read this first.** If you are a new session picking up this project, this file is the single entry point. It tells you what the project is, where every file lives, the current state, the rules you must not break, and exactly what each group requires before we can post. Everything needed to continue OR to hand off again is either here or linked from here.

_Last updated: 2026-08-28._

> **This is a living project, kept on the repo.** It is never "done." We continually add new groups to the system as coverage grows and as new listings appear in new areas, and we keep the state directories and the details we hold on each group updated in this repo as we go. The team owns that ongoing maintenance (see "Ongoing maintenance & ownership" below). Everything else about the plan stays as written here.

---

## 1. The plan (what this is, why, and how it runs)

**The goal.** Get Franchise Sellers' business-for-sale listings in front of the right people at almost no cost. Facebook groups are full of business owners, entrepreneurs, investors, and people who know someone looking to buy a business. That is our audience. This is a supplemental, top-of-funnel awareness channel: it is cheap, each post takes minutes, and it widens our reach beyond paid ads, BizBuySell, and our own funnel. We stay honest about the ceiling: groups are an awareness play, not a primary source of serious buyers, so we prioritize quality and conversion over raw volume.

**Two moving parts.**
1. **Collecting the groups (joining) — the part that grows over time.** We continually find and vet Facebook groups in the states and metros where our listings actually come from, and join the good ones AS the Franchise Sellers Page. Every group we join gets logged in that state's directory with the context we will need to use it later: who is in it, how active it is, its posting rules, and the best angle for a post. We work states in order of our listing volume, and we keep coming back to add more as we grow.
2. **Sharing listings (posting).** When a new listing goes live, it is matched to the groups whose location and audience fit, and a short, group-tailored post is written for each one. A human posts them (weekly), because there is no automation. See the playbook's §6B (how a post is built) and §8 (the weekly workflow to Rosie).

**Who does what.** AI finds, vets, joins, and logs the groups, matches listings to the right groups, and drafts every post. Humans do the posting and sending. Nothing is automated: Meta shut off the Facebook Groups API in April 2024, so joining and posting are done by hand through a logged-in browser signed in as the Franchise Sellers Page.

**Where we are today** is in section 3, and the full step-by-step method for each part is in the playbook. This overview is the plan and the map; the playbook is the detailed how-to; the state directories are the live data.

---

## 2. The files (what each one is)
All live in **`AI Folders/Facebook-Group-Sharing/`** (this folder holds the entire project).

| File | What it is | Use it for |
|---|---|---|
| **SOCIAL-GROUP-SHARING-OVERVIEW.md** (this file) | Master index + handoff | Orientation, status, rules, gate taxonomy |
| **SOCIAL-GROUP-SHARING-PLAYBOOK.md** | The process SOP (state-agnostic) | HOW to find/vet/join (§3-6), the post mechanics (§6B), the weekly sharing workflow (§8), roles (§9), rollout order (§7) |
| **SOCIAL-GROUP-SHARING-TX-DIRECTORY.md** | Texas groups we're in | Which TX groups + their posting gates |
| **SOCIAL-GROUP-SHARING-CA-DIRECTORY.md** | California groups we're in | Same, CA |
| **SOCIAL-GROUP-SHARING-GA-DIRECTORY.md** | Georgia groups we're in (**COMPLETE**) | Same, GA |
| **SOCIAL-GROUP-SHARING-FL-DIRECTORY.md** | Florida groups we're in (**nearly done**) | Same, FL |
| **SOCIAL-GROUP-SHARING-MASTER-LINKS.md** | Direct FB URL for all 159 groups, bucketed by state | Jump straight to a group to post; the self-contained link source |
| Claude memory: `project_fb_group_sharing` | Condensed running state | Quick recall inside a Claude session |

**The live membership list with clickable links** is always on Facebook itself: **`facebook.com/groups/joins/`** ("All groups you've joined (N)"), signed in as the Franchise Sellers Page. That's the source of truth for what we're in.

The directories in this folder add the *context* Facebook doesn't store: geo scope, audience fit, posting-gate requirements, and the per-group angle. They're keyed by **group name + member count** (member count disambiguates same-name groups, e.g. the three different "Florida Business Networking" rooms). Each directory also carries a **"Group links (for posting / handoff)" appendix** with the direct FB URL for every group, so a session can jump straight to a group to post without opening the joined-groups page.

- **URL status: DONE — all 159 groups are linked.** `SOCIAL-GROUP-SHARING-MASTER-LINKS.md` in this folder is the complete list of every group with its direct URL, bucketed by state (TX/CA/GA/FL + franchise cluster). Florida also carries its links inline in its own directory. Every new join going forward gets logged with its URL. (The live `facebook.com/groups/joins/` page stays the source of truth if the master file ever drifts.)

---

## 3. Current status (2026-08-28)

| State | Groups joined | Status | What's left |
|---|---|---|---|
| Texas | 32 | done (baseline) | refresh only |
| California | 41 | done | refresh only |
| Georgia | 44 | **COMPLETE** | none (Macon has no dedicated FB group; covered via Middle-GA + statewide) |
| Florida | 29 | nearly done | Orlando depth, Panhandle (Pensacola/Tallahassee), Naples |
| + national + franchise cluster | ~13 | standing | national business-for-sale rooms + a dormant on-brand franchise cluster (listed in the TX/CA dirs) |
| **Page total** | **≈159** | | |

**Rollout order (by our listing volume, playbook §7):** TX ✅ -> CA ✅ -> GA ✅ -> **FL (finish)** -> Indiana -> Colorado -> Ohio -> Tennessee -> the 2-listing states -> the 1-listing states. Each new state gets its own `-DIRECTORY.md` built with the same rules.

---

## Ongoing maintenance & ownership (this is a living project)
This project is designed to keep growing. It does not stop when a state is "done"; we keep adding groups and refreshing the details over time. Here is how it stays current, and who keeps it current.

**What gets updated, and where:**
- **New groups joined:** log each one in that state's `-DIRECTORY.md` (name, geo, audience, members, activity, posting-gate status, fit, angle) and add its link to `SOCIAL-GROUP-SHARING-MASTER-LINKS.md`. Bump the running counts in this overview (section 3), the directory header, and the memory node to match.
- **New states:** when we move to the next state on the rollout list, it gets its own `-DIRECTORY.md` built with the same rules, and it is added to the file list (section 2) and the status table (section 3).
- **New info on an existing group:** anything we learn later (a posting gate we hit, a rule change, whether a post landed well) goes in that group's row or notes in its directory.
- **Refresh:** the top states are revisited periodically as new groups appear.

**Keeping it accurate:** the live membership list on Facebook (`facebook.com/groups/joins/`) is always the source of truth for what we are actually in. If the repo ever drifts from it, re-scrape the joined-groups page (method is in the memory node) and reconcile.

**Ownership on handoff:** whoever runs this keeps the repo current as the one step that must not be skipped: **if you joined it, log it.** A directory that lags behind the real memberships is the main way this project loses value, because the whole point is matching a listing to the right groups from the written record, not from memory.

**What does NOT change:** the plan, the guardrails, the vetting criteria, the posting mechanics, and the rollout approach all stay as documented. The only things that grow are the set of groups and the detail we hold on them.

---

## 4. HARD GUARDRAILS (never break these)
Condensed from playbook §2. A handoff session MUST follow these:
- **Act as the Franchise Sellers Page**, not a personal profile. Verify via the top-right profile switcher = "Franchise Sellers" (a new day/tab can revert to personal). The composer should read "What's on your mind, Franchise Sellers?"
- **Never misrepresent to pass a gate.** We are a brokerage. If a group asks "are you a local business owner / do you live here / your business phone + website," we do NOT answer to fake being local. Skip or stay a member-only, never lie.
- **Never enter phone, website, email, or residency** into a group's join/participation questions.
- **Respect listing confidentiality.** Only ever share the public `franchisesellers.com` listing page. NEVER the `.co` microsite (that's the NDA-gated SIM). Fully-confidential / opted-out listings get no group post at all.
- **CTA routes to the website**, never "DM us / message us."
- **Posts are CM-approved** before they go out; social is a promised client service.
- **No em dashes** in any drafted copy. Use commas, colons, periods.
- **Claude drafts; humans post and send.** No automation.

---

## 5. Posting requirements — the gate taxonomy ("what they require for the first post")
This is the part to watch on handoff. **Every group in the directories carries a `Post status`.** Here is what each value means and how to handle it:

- **`open`** — the Page can post immediately. It goes live, no gate. (Confirmed behavior: members' promo/link posts sit live in these with no review.)
- **`approval-needed`** — the Page joins instantly, but the **first post** is held for admin review and/or a one-time "request to participate." Common questions: "what city are you in," "what's your business," a "No Promotions / No Spam" acknowledgment. **Handle at post-time, honestly, as Franchise Sellers**, and lead with value not an ad. The per-group note says what that group asks.
- **`join-by-request`** — the group requires answering questions to become a **member at all** (the "Join" button stays "Join" until you submit answers). We generally **skip** these unless a specific listing genuinely needs that group; never submit contact/residency to get in.
- **`local-residency-required`** — a stricter `approval-needed` that asks you to **prove you live locally** (e.g. "prove you live in the CSRA"). We cannot clear this honestly, so these are **MEMBER-ONLY / likely non-postable**. They're flagged per-group; keep them for visibility but don't count on posting.

Each state directory also has a **"posting-gate reality" paragraph** summarizing that state's gates, and a **SKIPPED list** logging what we deliberately did NOT join (and why), so we don't reconsider bad-fit groups.

---

## 6. How a listing actually gets posted (mechanics — playbook §6B)
There is **no "share this listing" button**. A listing goes in as a **post we compose in the group**, one of two ways:
- **Link post** — paste the public `.com` listing URL; Facebook auto-renders a preview card. Fast. Some groups down-rank external links.
- **Original post (preferred)** — upload our carousel slides + write the caption + put the website link in the caption or first comment. Looks native, we control the image, dodges link down-ranking. Reuses our existing carousel/caption system.

**Geo-match is the rule:** a listing only goes to groups whose geo scope covers its city (a Savannah business -> Savannah + GA-statewide groups). Whether a post is live immediately vs. held is the per-group `Post status`.

---

## 7. The sharing workflow (playbook §8) — how posts get distributed
**Weekly email to Rosie** (she does the posting). Per listing the email contains: the post (creative + caption), the matched target groups (filtered by geo + audience from the directories), and a **unique, group-tailored message for each group** (never identical copy-paste; FB throttles duplicates). Claude drafts the email; Malcolm reviews and sends (Outlook is draft-only). Cadence is **event-driven** (a new listing triggers a batch), same listing -> same group **monthly max**, ~1 post/week per group. Engage on our own posts' comments; don't post-and-ghost.

---

## 8. How to continue joining (playbook §5) — quick procedure for a fresh session
1. **Browser may be disconnected on a new day.** If `list_connected_browsers` is empty, have the user reopen the Claude side panel in Chrome (signed into the FS Facebook), then `select_browser` + `tabs_context_mcp` with `createIfEmpty: true` to get a controllable tab. The prior session's tabId is dead.
2. **Confirm the active profile = "Franchise Sellers"** (top-right switcher) before joining anything.
3. Work the **next state's NEXT-UP queue** (in that state's directory), or continue the rollout order.
4. **Always include the state/metro in the search** — the account geo reads as Colorado, so unscoped searches return CO/UT/TX groups.
5. **Vet each group** against playbook §3 (look-for) / §4 (avoid): public + active (ideally 20+ posts/day) + business/owner/entrepreneur audience. Skip marketplace, real-estate, ad-dump, community/events, identity, and owner-gated-private groups.
6. **Join by clicking the ref, bottom-to-top within a batch.** A "Join"->"Visit" flip shifts the rows below it, so clicking upward avoids the ~1-in-4 first-click miss. Re-read the page for fresh coordinates after any miss.
7. Dismiss any participant-questions dialog with **"Not now"** (never submit).
8. **Pace: ~20-25 joins/day, hard cap ~30 per 12 hours.** Verify the day's count at `facebook.com/groups/joins/`.
9. **Log every join** in the state directory with the full schema (name, geo, audience, members, activity, post-status + gate note, fit, angle note), and update the memory node + this overview's status table.

---

## 9. One-line summary to paste into a handoff
> "Continue the FB group-sharing project (as the Franchise Sellers Page). Read `AI Folders/Facebook-Group-Sharing/SOCIAL-GROUP-SHARING-OVERVIEW.md` first. State of play: TX/CA/GA done, FL nearly done (finish Orlando/Panhandle/Naples), then Indiana. ~159 groups joined; live list at facebook.com/groups/joins/. Follow the hard guardrails and the gate taxonomy in the overview."
