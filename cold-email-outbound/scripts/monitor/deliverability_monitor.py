#!/usr/bin/env python3
"""Deliverability & infra health monitor for the cold-email sending setup.

Runs as a daily droplet cron. Pulls every Instantly mailbox, checks DNS health
(SPF / DMARC / MX / NS) + Spamhaus DBL per sending domain, and mailbox warmup
health, compares against the last run's baseline, and EMAILS Theodore only when
something is wrong or has changed. Otherwise it's silent ("you don't worry about
it until I ping you").

Zero pip deps (urllib + subprocess `dig`). Reads keys from .env files.

    python3 scripts/monitor/deliverability_monitor.py            # check + alert
    python3 scripts/monitor/deliverability_monitor.py --quiet    # no alert, just status
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]                 # cold-email-outbound/
RUNTIME = ROOT / "data" / "runtime"
BASELINE = RUNTIME / "monitor-baseline.json"
STATUS = RUNTIME / "deliverability-status.json"
SHARED_ENV = Path("/root/crm-reporting/.env")              # holds RESEND_*
USER_AGENT = "FS-Outbound/1.0 (+franchisesellers.com)"
INSTANTLY_BASE = "https://api.instantly.ai/api/v2"
WARMUP_FLOOR = 90                                          # below this = flag

# Domains we never cold-send from (still warmed/real) — health-check but don't
# treat as cold-sending infra. Used only for labeling in the report.
NON_COLD_DOMAINS = {"franchisesellers.com", "companysellers.com"}


def load_env(path: Path) -> dict:
    out = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return out


ENV = {**load_env(SHARED_ENV), **load_env(ROOT / ".env")}


def dig(args: list[str]) -> list[str]:
    try:
        r = subprocess.run(["dig", "+short", *args], capture_output=True,
                           text=True, timeout=10)
        return [l.strip() for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def http_json(url, headers=None, method="GET"):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})}, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


# ── Instantly mailboxes ──────────────────────────────────────────────────────
def fetch_mailboxes() -> list[dict]:
    key = ENV.get("INSTANTLY_API_KEY")
    if not key:
        return []
    out, cursor = [], None
    for _ in range(20):  # safety cap on pagination
        url = f"{INSTANTLY_BASE}/accounts?limit=100" + (f"&starting_after={cursor}" if cursor else "")
        resp = http_json(url, headers={"Authorization": f"Bearer {key}"})
        items = resp.get("items", resp if isinstance(resp, list) else [])
        for a in items:
            out.append({
                "email": a.get("email", ""),
                "domain": (a.get("email", "").split("@")[-1] or "").lower(),
                "warmup_score": a.get("stat_warmup_score"),
                "status": a.get("status"),
            })
        cursor = resp.get("next_starting_after")
        if not cursor:
            break
    return out


# ── DNS health per domain ────────────────────────────────────────────────────
def check_domain(domain: str) -> dict:
    spf = next((t for t in dig(["TXT", domain]) if "v=spf1" in t.lower()), "")
    dmarc_txt = next((t for t in dig(["TXT", f"_dmarc.{domain}"]) if "v=dmarc1" in t.lower()), "")
    policy = ""
    if dmarc_txt:
        for part in dmarc_txt.replace('"', "").split(";"):
            part = part.strip()
            if part.startswith("p="):
                policy = part[2:]
    mx = sorted(dig(["MX", domain]))
    ns = sorted(dig(["NS", domain]))
    # Spamhaus DBL (domain blocklist). 127.0.1.x = listed; 127.255.x = query blocked.
    dbl_raw = dig(["A", f"{domain}.dbl.spamhaus.org"])
    if not dbl_raw:
        dbl = "clean"
    elif any(r.startswith("127.255.") for r in dbl_raw):
        dbl = "unavailable"
    elif any(r.startswith("127.0.1.") for r in dbl_raw):
        dbl = "LISTED"
    else:
        dbl = "clean"
    return {"spf": bool(spf), "dmarc": bool(dmarc_txt), "dmarc_policy": policy,
            "mx": mx, "ns": ns, "dbl": dbl}


# ── Alerting ─────────────────────────────────────────────────────────────────
# Who gets the "something is broken" email. Defaults to Theodore + Malcolm; an
# ALERT_EMAILS env (comma-separated) overrides. Silent when everything is healthy.
DEFAULT_RECIPIENTS = ["theodore@franchisesellers.com", "malcolm@franchisesellers.com"]


def recipients() -> list[str]:
    raw = os.environ.get("ALERT_EMAILS") or ENV.get("ALERT_EMAILS") or ENV.get("ALERT_EMAIL")
    if raw:
        return [e.strip() for e in raw.split(",") if e.strip()]
    return list(DEFAULT_RECIPIENTS)


def fix_for(anomaly: str) -> list[str]:
    """Plain-English 'what to do' bullets for a given problem/change line."""
    a = anomaly.lower()
    if "spf record missing" in a:
        return ["Add or restore the SPF TXT record for this domain in its DNS (Instantly's domain-setup page shows the exact record to paste).",
                "Pause cold sending from this domain until SPF passes again."]
    if "dmarc record missing" in a:
        return ["Add a DMARC TXT record at _dmarc.&lt;domain&gt; (start with p=none), then re-run Instantly's domain check.",
                "Pause sending from this domain until DMARC resolves."]
    if "spamhaus dbl" in a or "newly listed" in a:
        return ["Stop sending from this domain right now.",
                "Request delisting at spamhaus.org/dbl, and check for a recent spike in bounces or spam complaints that may have triggered it.",
                "Keep it paused until it shows clean again."]
    if "warmup score" in a:
        return ["Pause cold sends from this mailbox and let its warmup keep running.",
                "Do not include it in a campaign until its score is back above 90."]
    if "status" in a and "not active" in a:
        return ["Reconnect / re-authenticate this mailbox in Instantly (it is disconnected or errored).",
                "Exclude it from any campaign until it shows active again."]
    if "changed" in a:
        return ["A DNS or provider change was detected on this domain. Confirm it was intentional (for example, if you moved hosting).",
                "If it was NOT intentional, restore the previous value. An unexpected MX or nameserver change can break sending or signal a domain hijack."]
    return ["Review this item in the marketing dashboard's Deliverability health section."]


def build_alert_html(anomalies: list[str], n_domains: int, n_mailboxes: int,
                     now: str, test: bool = False) -> str:
    blocks = []
    for a in anomalies:
        fixes = "".join(f"<li style='margin:3px 0'>{f}</li>" for f in fix_for(a))
        blocks.append(
            "<div style='border:1px solid #e2e8f0;border-left:4px solid #ef4444;"
            "border-radius:8px;padding:12px 14px;margin-bottom:10px'>"
            f"<div style='font-weight:700;font-size:14px;color:#b91c1c'>{a}</div>"
            "<div style='font-size:13px;color:#334155;margin-top:7px'><b>What to do:</b></div>"
            f"<ul style='margin:4px 0 0;padding-left:18px;font-size:13px;color:#334155;line-height:1.5'>{fixes}</ul>"
            "</div>")
    n = len(anomalies)
    intro = "This is a TEST of the cold-email health alert (nothing is actually wrong). " if test else ""
    return (
        "<div style='font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#1a2733;max-width:580px'>"
        f"<h2 style='font-size:18px;margin:0 0 4px'>Cold email health: {n} item(s) need a look</h2>"
        f"<p style='color:#5b6b80;font-size:13px;margin:0 0 16px'>{intro}The daily check flagged {n} thing(s). "
        "Everything else is healthy. Here is what is going on and how to fix each one.</p>"
        f"{''.join(blocks)}"
        f"<p style='color:#94a3b8;font-size:12px;margin-top:14px'>Checked {n_domains} domains / {n_mailboxes} mailboxes at {now}. "
        "You only get this email when something needs attention. No email means everything is healthy.</p>"
        "</div>")


def send_alert(subject: str, html: str) -> bool:
    key = ENV.get("RESEND_API_KEY")
    sender = ENV.get("RESEND_FROM")
    to = recipients()
    if not (key and sender):
        print("  (no Resend creds — alert not emailed)")
        return False
    body = json.dumps({"from": sender, "to": to, "subject": subject, "html": html}).encode()
    req = urllib.request.Request("https://api.resend.com/emails", data=body,
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json",
                                          "User-Agent": USER_AGENT}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status in (200, 201)
    except Exception as e:
        print(f"  alert send failed: {type(e).__name__}")
        return False


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    quiet = "--quiet" in sys.argv
    RUNTIME.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    # --test-alert: send a clearly-labeled sample alert to confirm the email
    # pipeline + recipients + formatting work, then exit. Does no real checks.
    if "--test-alert" in sys.argv:
        sample = ["mail-fs-1.com: SPF record missing",
                  "jane@send-cs-2.com: warmup score 71 (below 90)",
                  "send-fs-3.com: on Spamhaus DBL blocklist"]
        html = build_alert_html(sample, 12, 86, now, test=True)
        ok = send_alert("[TEST] ⚠ Cold email health: sample alert", html)
        print(f"  test alert sent: {ok} -> {recipients()}")
        return 0

    mailboxes = fetch_mailboxes()
    domains = sorted({m["domain"] for m in mailboxes if m["domain"]})
    dns = {d: check_domain(d) for d in domains}

    # current problems (hard issues, present this run)
    problems = []
    for d in domains:
        info = dns[d]
        if not info["spf"]:
            problems.append(f"{d}: SPF record missing")
        if not info["dmarc"]:
            problems.append(f"{d}: DMARC record missing")
        if info["dbl"] == "LISTED":
            problems.append(f"{d}: on Spamhaus DBL blocklist")
    for m in mailboxes:
        ws = m["warmup_score"]
        if isinstance(ws, (int, float)) and ws < WARMUP_FLOOR:
            problems.append(f"{m['email']}: warmup score {ws} (below {WARMUP_FLOOR})")
        # Warm-only main-brand inboxes are in Instantly only to stay warm; their
        # active/inactive state does not affect COLD deliverability, so skip them.
        if m["status"] not in (1, None) and m["domain"] not in NON_COLD_DOMAINS:
            problems.append(f"{m['email']}: account status {m['status']} (not active)")

    # changes vs baseline (catches a hosting/DNS/provider change)
    changes = []
    baseline = {}
    if BASELINE.exists():
        try:
            baseline = json.loads(BASELINE.read_text())
        except Exception:
            baseline = {}
    prev_dns = baseline.get("dns", {})
    for d in domains:
        pd = prev_dns.get(d)
        if not pd:
            continue
        for field in ("spf", "dmarc", "dmarc_policy", "mx", "ns"):
            if pd.get(field) != dns[d].get(field):
                changes.append(f"{d}: {field} changed ({pd.get(field)!r} → {dns[d].get(field)!r})")
        if pd.get("dbl") != "LISTED" and dns[d]["dbl"] == "LISTED":
            changes.append(f"{d}: newly listed on Spamhaus DBL")

    prev_problems = set(baseline.get("problems", []))
    new_problems = [p for p in problems if p not in prev_problems]
    persistent = [p for p in problems if p in prev_problems]
    first_run = not baseline

    # Weekly re-reminder: an unresolved problem should not go silent forever. Ping
    # immediately on anything NEW or CHANGED, otherwise re-send at most once a week
    # while a problem persists. Healthy (no problems, no changes) stays silent.
    last_alert = baseline.get("last_alert_at")
    nag_due = False
    if problems:
        if not last_alert:
            nag_due = True
        else:
            try:
                nag_due = (datetime.fromisoformat(now) - datetime.fromisoformat(last_alert)).days >= 7
            except Exception:
                nag_due = True
    trigger = bool(new_problems or changes or nag_due)
    # When we DO email, show the COMPLETE current broken-state (every problem +
    # change), each with fix steps — not just the delta since last run.
    alert_items = problems + changes

    status = {
        "checked_at": now, "domains": len(domains), "mailboxes": len(mailboxes),
        "warmup_below_floor": sum(1 for m in mailboxes
                                  if isinstance(m["warmup_score"], (int, float)) and m["warmup_score"] < WARMUP_FLOOR),
        "problems": problems, "changes": changes, "dns": dns,
        "ok": not problems and not changes,
    }
    STATUS.write_text(json.dumps(status, indent=2))

    print(f"Checked {len(domains)} domains / {len(mailboxes)} mailboxes at {now}")
    print(f"  problems: {len(problems)} (new: {len(new_problems)}, persistent: {len(persistent)}) | "
          f"changes: {len(changes)} | first_run: {first_run} | nag_due: {nag_due}")
    for a in (new_problems + changes):
        print(f"   - NEW/CHANGED: {a}")

    sent = False
    if trigger and not first_run and not quiet:
        subj = f"⚠ Cold email health: {len(alert_items)} issue(s) need a look"
        html = build_alert_html(alert_items, len(domains), len(mailboxes), now)
        if send_alert(subj, html):
            sent = True
            print(f"  alert emailed -> {recipients()}")
    elif first_run:
        print("  baseline established (no alert on first run)")
    elif not problems and not changes:
        print("  all clear — no alert")
    else:
        print("  problems present but already alerted (weekly re-reminder not due) — no email")

    BASELINE.write_text(json.dumps({"dns": dns, "problems": problems, "checked_at": now,
                                    "last_alert_at": now if sent else last_alert}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
