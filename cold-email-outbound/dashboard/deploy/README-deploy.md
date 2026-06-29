# Marketing Dashboard — Deploy Runbook

Deploys the operator dashboard to **dashboard.franchisesellers.com/marketing**,
protected by a login for Malcolm. Follows the same nginx + static-file + snapshot-cron
pattern as the other dashboards.

## Files
- `dashboard/index.html` — the operator UI (static, reads marketing-snapshot.json)
- `dashboard/simulator.html` — interactive campaign SANDBOX (self-contained, baked mock data, NO live connection / NO data written). Linked from index.html (topbar "🎮 Simulator" + the Send & monitor card). Deploy = a plain `scp` into the same dir; no nginx change (the `/marketing/` location already serves it under the same auth). Deep-link a step: `?step=3&brand=CS&seg=manufacturing&offer=comparable_sales`. **Deployed 2026-06-28.**
- `dashboard/snapshot.py` — generates marketing-snapshot.json from the engine
- `dashboard/marketing-snapshot.json` — aggregate data (no PII)

## Droplet layout
```
/var/www/dashboard/marketing/index.html
/var/www/dashboard/marketing/marketing-snapshot.json
/root/cold-email-outbound/                      # engine + dashboard/snapshot.py
/etc/nginx/.htpasswd-marketing                  # Malcolm's login (NOT in git)
```

## 1. Login (HTTP Basic Auth) — who can access

Auth file `/etc/nginx/.htpasswd-marketing` (passwords set on the droplet, NEVER committed).
Authorized users (set 2026-06-08):

| Username | Who | Credential source |
|---|---|---|
| `malcolm` | Malcolm (marketing) | set on droplet |
| `david` | David | set on droplet |
| `leadership` | Eric + Theodore | reuses the existing leadership login (hash copied from `.htpasswd-leadership`) |

```bash
# on the droplet — create/rotate individual logins
apt-get install -y apache2-utils                                  # if htpasswd missing
htpasswd -bc /etc/nginx/.htpasswd-marketing malcolm '<password>'  # -c only for the FIRST user
htpasswd -b  /etc/nginx/.htpasswd-marketing david   '<password>'  # add more (no -c)
# leadership reuses their existing login:
grep '^leadership:' /etc/nginx/.htpasswd-leadership >> /etc/nginx/.htpasswd-marketing
```
> Passwords are set directly on the droplet, never in any committed file. To add a
> person: `htpasswd -b /etc/nginx/.htpasswd-marketing <user> '<password>'` (no `-c`).

## 2. nginx location block

Add under the existing `dashboard.franchisesellers.com` server block
(see `dashboard.franchisesellers.com.nginx` in dashboard-api/ for the full vhost):
```nginx
location /marketing/ {
    alias /var/www/dashboard/marketing/;
    index index.html;
    auth_basic "Marketing Platform";
    auth_basic_user_file /etc/nginx/.htpasswd-marketing;
    add_header Cache-Control "no-store";   # always fresh snapshot
}
# redirect /marketing -> /marketing/
location = /marketing { return 301 /marketing/; }
```
Then: `nginx -t && systemctl reload nginx`

## 3. Deploy the files
```bash
# from local (or git pull on droplet)
scp cold-email-outbound/dashboard/index.html root@165.227.206.190:/var/www/dashboard/marketing/
scp cold-email-outbound/dashboard/marketing-snapshot.json root@165.227.206.190:/var/www/dashboard/marketing/
```

## 4. Snapshot cron (hourly, business hours — matches the GHL-touching cadence)
```bash
# crontab -e on the droplet (times in UTC per the droplet-cron-TZ note)
0 14-23 * * 1-5  cd /root/cold-email-outbound && /usr/bin/python3 dashboard/snapshot.py && cp dashboard/marketing-snapshot.json /var/www/dashboard/marketing/
```
The snapshot is aggregate-only (no GHL calls beyond what the engine already does),
so it's light. Regenerate after building new segments so they appear for Malcolm.

## 5. Verify
- Visit https://dashboard.franchisesellers.com/marketing → browser prompts for login
- Log in as malcolm → dashboard loads, pool/channels/sequences/segments render
- Mode badge shows DRY-RUN (until the engine's CEO_DRY_RUN is flipped)

## ✅ DEPLOYED 2026-06-08 — live at https://dashboard.franchisesellers.com/marketing (login: malcolm)

Verified: no-auth→401, malcolm→200, snapshot→200, /marketing→301, wrong-pass→401,
existing dashboards unaffected. Live vhost snapshotted to
`dashboard.franchisesellers.com.nginx` in this folder.

### Deploy gotchas hit (read before re-deploying)
1. **`sites-enabled/dashboard.franchisesellers.com` is a REAL FILE, not a symlink to
   `sites-available/`.** nginx loads the *enabled* file — edit that one. (Editing
   sites-available had no effect.)
2. **Backups must NOT live in `sites-enabled/`** — nginx includes `sites-enabled/*`,
   so a `.bak` copy there causes "duplicate listen options" and `nginx -t` fails.
   Keep backups in `/root/nginx-backups/`.
3. Always `nginx -t` before `systemctl reload nginx`.

## Access matrix (RBAC, rolled out 2026-06-08)

Three auth tiers (all under `/etc/nginx/`, perms **640 root:www-data** so nginx can
read them but hashes aren't world-readable — a `cp` that drops the www-data group
causes a 500 "Permission denied", watch for it):

| Tier file | Users | Dashboards |
|---|---|---|
| `.htpasswd-leadership` | `leadership` (Eric, Theodore) | `/report`, `/staff-report` |
| `.htpasswd-internal` | leadership + `david` + `malcolm` | `/marketing`, `/sales` |
| `.htpasswd-ops` | internal + `team` + `rich`,`templa`,`alicea`,`yvonne`,`laura` | `/toolkit`, `/buyer-manager`, `/full-service`, `/shared`, `/api` |

Existing shared `leadership`/`team` logins preserved in the tiers → no one locked out.
Every dashboard location is `^~` (beats regex) with inline no-cache, so HTML +
snapshot.json get the right tier + freshness. The old shared no-cache regex blocks
were removed (they overrode per-path auth — a precedence trap).

Verified live (curl, every user×dashboard): report blocks all non-leadership;
marketing/sales allow david+malcolm, block rich; toolkit/buyers/full-service allow
everyone. New individual passwords default to `Franchise#1` (set on droplet only).

## Operator API (FastAPI) — DEPLOYED 2026-06-07

The dashboard's interactive backend (audience builder + campaign dry-run).

**On the droplet:**
```
/root/cold-email-outbound/            # engine + dashboard + config + .env + pool data
  .venv/                              # fastapi + uvicorn + pydantic
  data/dedup-output/*.csv             # the tier files the API scores (~136MB)
/etc/systemd/system/marketing-api.service   # uvicorn dashboard.api:app :8083, 2 workers
/var/log/marketing-api.log
```

**Endpoints** (proxied at `/marketing/api/`, auth `.htpasswd-internal`):
`/ping /health /segments /sequences /preview /save /dryrun`

**Deploy / update the API:**
```bash
# copy changed engine/dashboard files to /root/cold-email-outbound/...
systemctl restart marketing-api && tail -f /var/log/marketing-api.log
```

**nginx proxy** (already in the vhost, before the /marketing/ location):
```nginx
location ^~ /marketing/api/ {
    auth_basic "Marketing Platform"; auth_basic_user_file /etc/nginx/.htpasswd-internal;
    proxy_pass http://127.0.0.1:8083/api/marketing/;
    proxy_set_header Host $host; proxy_read_timeout 60s;
}
```

**Gotchas hit:**
- uvicorn takes a few seconds to boot (loads the engine) — `systemctl is-active` shows active before the port answers; `sleep 4` before smoke-testing.
- The dry-run must run on a CAPPED sample (`build_segment_capped`, 600) — a full-segment orchestration logs tens of thousands of touch lines and times out nginx.
- Pool data is gitignored PII; it's on the droplet but NOT in git. Re-copy from local `data/dedup-output/` if the droplet is rebuilt.

**Data refresh:** when the pool changes (re-run dedup), re-copy the tier CSVs to
`/root/cold-email-outbound/data/dedup-output/` and `systemctl restart marketing-api`.

## Notes
- The dashboard is **read-rich + interactive** (v2): pool analytics, sequence timelines,
  readiness simulator, channel health, plus the live Audience Builder + Campaign Dry-Run.
  Launching campaigns is done via the engine (`run_multichannel_campaign`) — a future
  version can add a "launch" button wired to the dashboard-api FastAPI service.
- Add `/marketing` to the landing page's card grid when ready.
