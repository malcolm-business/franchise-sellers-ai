# AI Folders — workspace guide

## 🚀 DEPLOY / GIT PUSH — read the runbook FIRST
**Before ANY change to the droplet (`165.227.206.190`) or ANY `git push` to the dashboard repo
(`fs-cs-internal-tools`), open and follow [`DEPLOY/README.md`](DEPLOY/README.md).**

Non-negotiables (full detail in the runbook):
- Frontend dashboard `*.html` ships **only** via `git push` → the "Deploy dashboards" Action. **Never scp/hand-edit a `.html` on the droplet.**
- Backend `*.py` is the **only** manual deploy — always **back up on the droplet first** (no CI drift guard).
- **`git fetch` + `pull --rebase` before working** — never deploy from a stale base or uncommitted state.
- Ted's deploy updates get folded into [`DEPLOY/TED-UPDATES.md`](DEPLOY/TED-UPDATES.md) once — never act on a raw pasted message.

The binding shared rules live in the repo: `fs-cs-internal-tools/cold-email-outbound/docs/DASHBOARD-DEPLOY-RULES.md` (it wins on any conflict).

## Memory
Persistent context (deploy rules, droplet layout, project state) is in Claude memory —
`project_dashboard_deploy_rules`, `project_work_droplet`, and the `MEMORY.md` index.
