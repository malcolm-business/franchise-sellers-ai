# 📥 Updates from Ted — integrated log

**How to use this file:** when Ted sends deploy/repo info, add a dated entry here with the
message **distilled into concrete rules**, update [`README.md`](README.md) and/or the repo doc
if a rule changed, then you're done. **Never re-paste a raw Ted message into a session to
re-read — integrate it here once; every future session reads the integrated version.**

Newest entry on top.

---

## 2026-08-04 (Ted confirmed) — box-config lane row is now IN the canonical doc

Ted **added the box-level-config lane row** to the shared `DASHBOARD-DEPLOY-RULES.md` (Ownership
lanes table, right under the shared-files row):

> Box-level config — sysctl, swap, systemd units or drop-ins on any service, nginx, kernel
> tunables, plan resizes → both owners; post in the Slack DM before changing, not after.

He left a short context note under the table referencing Malcolm's two changes (both kept), so it
reads as context not a rule from nowhere. This rule is now **official + shared**, not just in
Malcolm's hub. Ted is also curious what `memory.events` shows **warm** on listings-api later this
week — covered by the scheduled `listings-api-cap-recheck` task (fires 2026-08-04 ~2:50pm MDT);
relay the result to Ted when it runs.

---

## 2026-08-04 (later) — Ted's reply: cap sizing, box-config lane, DROPLET-OPS.md

Ted **approved** both changes (swap + `listings-api` memory cap) — keep them. The swap closed a
gap their capacity watchdog had been alarming on since the July resize. Follow-ups:

- **`MemoryHigh=1G` on `listings-api` may be too tight once the cache warms.** `load_master()`
  holds the parsed 24 MB master at ~100–300 MB/worker × `--workers 2` = **200–600 MB of cache**
  before uvicorn baseline + generation context. Above `MemoryHigh` the kernel throttles and
  **evicts that cache first** → re-slows the triage modal the cache was built to fix (and swap
  makes the re-parse slower). Re-measure **warm** (after real triage opens):
  `systemctl show listings-api -p MemoryCurrent -p MemoryPeak; cat /sys/fs/cgroup/system.slice/listings-api.service/memory.events` — non-zero `high` = cap biting. Fix = `MemoryHigh=2G` **or**
  drop to 1 worker (2.3 GB available). *Checked 2026-08-04 16:29Z: high=0, peak 102 MB — but cache still COLD (service ~1h old, no real load yet).*
- **Mental-model corrections:** **MariaDB is Ted's** (backs 6 WordPress staging sites for FS/CS
  rebuilds). **No mail server on the box** — outbound is Resend API (Ted) + Instantly (Malcolm),
  both external — so the cap/swap protect the **worker crons + MariaDB + the PUBLIC client review
  portal**, not a "mail server." **`listings-api` :8086 serves the only public unauthenticated
  route (`/listing-review/`)** — if the cap ever OOM-kills 8086 that's **client-facing**, so don't
  run it too tight.
- **NEW box-config coordination rule (Ted's ask):** box-level config — sysctl, swap, systemd
  units/drop-ins on ANY service, nginx, kernel tunables, plan resizes → both owners; **post in the
  Slack DM BEFORE changing, not after.** (Today's swap + cap were changed then notified; going
  forward, notify first.) Ted will add this lane row to the shared `DASHBOARD-DEPLOY-RULES.md` once
  Malcolm says OK.
- **New authoritative box writeup:** `crm-snapshot/docs/DROPLET-OPS.md` (every unit, port, owner,
  cron overlaps, resize runbook).

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
