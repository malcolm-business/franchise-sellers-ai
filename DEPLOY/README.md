# 🚀 DEPLOY — START HERE

> **OWNER: Malcolm (Director of Marketing).** This is **Malcolm's personal deploy runbook** for his
> marketing-dashboard lane (`cold-email-outbound/**` on `fs-cs-internal-tools`). Malcolm created and
> maintains it. **Ted may operate differently on his side — this is not Ted's process and is not
> binding on him.** The only shared, cross-owner authority is the repo doc
> `cold-email-outbound/docs/DASHBOARD-DEPLOY-RULES.md` (see §1).

**Read this before ANY change to the droplet or ANY `git push` to the dashboard repo.**
This is the operational runbook Malcolm + Claude follow every time. It is meant to be
**stable** — change it deliberately, log the change, never silently rewrite it.

---

## 0. The one rule that prevents every incident

> **Nothing reaches the droplet except through git.**
> - **Frontend dashboard `*.html`** ships **ONLY** via `git push` → the GitHub Action. **Never scp/hand-edit a `.html` on the droplet.**
> - **Backend `*.py`** is the **one manual exception** (it has no CI) — always with a **droplet backup first**.

Every drift incident (2026-07-09, 2026-07-23, 2026-08-04) came from breaking this: a stale file, a hand-scp, or work that lived somewhere git didn't know about.

---

## 1. Canonical sources (precedence order — higher wins on conflict)

1. **The binding shared doc (Ted + Malcolm):** `fs-cs-internal-tools/cold-email-outbound/docs/DASHBOARD-DEPLOY-RULES.md`. `git pull` and read the repo copy — it wins.
2. **The CI itself (ground truth of behavior):** `.github/workflows/deploy.yml` + `cold-email-outbound/deploy/deploy-from-git.sh`.
3. **This runbook** = the operational how-to, kept in sync with #1/#2. If this ever disagrees with the repo doc, **the repo doc wins — fix this file.**
4. **Ted's updates:** folded into [`TED-UPDATES.md`](TED-UPDATES.md) (dated). Never act on a raw pasted message — integrate it here once, then every session reads the integrated version.

---

## 2. The two deploy paths

### 🅰️ Frontend — dashboard `*.html` — **GIT ONLY**
Files: `cold-email-outbound/dashboard/*.html` (`listings.html`, `meta-ads.html`, `social-media.html`, `index.html`, `usage.html`, `simulator.html`).

1. Work on a branch → merge to `master` → **`git push`**.
2. The **"Deploy dashboards"** Action auto-deploys the changed `.html` with: **drift guard** (live md5 vs `/root/.deploy-markers/marketing-<name>.md5`), **shrink guard** (refuses if >8% smaller than live), backup, md5 verify.
3. **Never scp a `.html`.** (That caused the 2026-08-04 drift-guard failure + CRLF drift.)
4. **If the drift guard refuses** ("live changed out-of-band"): that's the guard *working*. Verify git content == live content (normalized md5), get **Ted's Slack ack**, then force:
   ```bash
   gh workflow run deploy.yml --repo theodorebaird/fs-cs-internal-tools \
     -f target=marketing -f files="cold-email-outbound/dashboard/<file>.html" -f force=true
   ```
   (Note: Claude cannot run `gh workflow run` or `git push` — the safety layer blocks deploy triggers. **Malcolm runs those.**)

### 🅱️ Backend — `listings_api.py`, `listings_ai.py`, `engine/*.py` — **MANUAL (no CI)**
There is **no drift guard** on `.py` — an scp silently overwrites live. So:

1. **Back up on the droplet first:**
   `sudo cp -a <target> /home/malcolm/marketing-deploy-backups/<name>.bak-$(date +%Y%m%d-%H%M%S)`
2. scp → staging → `sudo cp` to `/root/cold-email-outbound/{dashboard,engine}/…`
3. `sudo python3 -m py_compile <file>` → `sudo systemctl restart listings-api` (:8086) or `marketing-api` (:8083)
4. Verify `/ping` 200, no errors in `/var/log/listings-api.log`.
5. **Commit the same content to git** so repo == live.

---

## 3. Pre-flight — every deploy, every session

- [ ] `git fetch origin` + `git pull --rebase` — **never work from a stale base** (this burned us 2026-07-23 and 2026-08-04). A conflict here is the system catching a problem: **read + merge, never steamroll.**
- [ ] Working tree is **committed** — never deploy from uncommitted / hand-edited state.
- [ ] **Frontend:** confirm the drift marker matches (or expect the guard to refuse and follow §2🅰️4).
- [ ] **Verify AFTER:** live == git (normalized `tr -d '\r' | md5sum`), landing-hub title still `Dashboards · Franchise Sellers`.

---

## 4. Session roles (why this folder exists)

- **Build sessions** (Social tab, Listings tab, …): work on a **feature branch or git worktree**, commit early + often, **never push or deploy**. Their output = committed commits. *That's the queue.*
- **Deploy session** (this hub): the **only** place that pulls Ted's changes, merges, pushes (pipeline deploys `.html`), and does the manual backend deploys. **Always re-derive state from git + the droplet at deploy time — never trust a session's memory of "what's deployed."**

---

## 5. When Ted sends an update

Do **not** just paste it into a session and act on it. Instead:
1. Add a dated entry to [`TED-UPDATES.md`](TED-UPDATES.md) with the message distilled into concrete rule changes.
2. If it changes a shared rule, update the repo doc (§1.1) too — coordinate with Ted.
3. Update this runbook if the operational steps change.

Now it's persistent: every future session reads the integrated rules, never the raw message again.

---

## 6. Never

- ❌ Never scp / hand-edit a dashboard `.html` on the droplet (git push only).
- ❌ Never deploy from uncommitted or unpulled state.
- ❌ Never `--force` a deploy without Ted's Slack ack.
- ❌ Never write to `/var/www/dashboard/index.html` (the **landing hub**) or any bare file at `/var/www/dashboard/`, or any sibling dashboard folder. All marketing deploys live under `/var/www/dashboard/marketing/` only.
- ❌ Never trust a session's memory of deploy state — verify against git + droplet live.
- ❌ If the landing hub title ever changes: **STOP, tell Ted, do not self-fix.**

---

*Last verified against reality: 2026-08-04 (full listings/social reconcile — git == droplet across all files, markers current).*
