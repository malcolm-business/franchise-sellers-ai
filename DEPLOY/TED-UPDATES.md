# 📥 Updates from Ted — integrated log

**How to use this file:** when Ted sends deploy/repo info, add a dated entry here with the
message **distilled into concrete rules**, update [`README.md`](README.md) and/or the repo doc
if a rule changed, then you're done. **Never re-paste a raw Ted message into a session to
re-read — integrate it here once; every future session reads the integrated version.**

Newest entry on top.

---

## 2026-08-04 — listings.html drift + backend CI gap + social overlap

Ted's message (relayed by Malcolm) distilled into rules:

- **Backend `.py` is NOT covered by CI.** An scp silently overwrites whatever's live (no drift
  guard). → **Back up on the droplet before deploying any `.py`.** *(now in README §2🅱️)*
- **`listings.html` had open drift** — live was bigger than git; do **not** `--force` git over it
  blindly. The marketing marker had advanced via a chart `index.html` `workflow_dispatch`, so a
  plain push would **not** auto-retry `listings.html` — it must be deployed explicitly via
  `workflow_dispatch`. → README §2🅰️4. **[RESOLVED 2026-08-04:** reconciled git↔droplet, forced
  the dispatch, live == git, marker current.**]**
- **`social-media.html` already exists as a real page** (~16.7 KB) — a rewrite that comes out
  smaller will trip the **8% shrink guard**. *(README §2🅰️2)*
- **Ted's side was clean** at the time ("origin/master + local HEAD both `c58a389`, nothing
  unpushed") and he cleared Malcolm to **"pull and push away."**
- Playwright + a `listings-api` restart for the social carousel: **Ted greenlit.**

---

## 2026-07-24/25 — auto-deploy pipeline went live (from memory / repo doc)

- The **"Deploy dashboards" GitHub Action** now auto-deploys `cold-email-outbound/dashboard/*.html`
  on push to `master`, from a fresh `origin/master` checkout, with shrink-guard + backup + md5.
  → **Manual `.html` scp deploys are OFF.** (Backend `.py` is still manual.)
- Malcolm's own lane (`cold-email-outbound/**`): Malcolm merges his own branch to master and
  pushes — no Ted gate. Shared files (`ai_consensus.py`, nginx vhost, deploy scripts): **Slack DM
  Ted before pushing.**

---

*Older history lives in the repo doc `cold-email-outbound/docs/DASHBOARD-DEPLOY-RULES.md` and the
2026-07-09 / 2026-07-23 incident write-ups in `MALCOLM-MARKETING-DASHBOARD-DEPLOY-RULES.md`.*
