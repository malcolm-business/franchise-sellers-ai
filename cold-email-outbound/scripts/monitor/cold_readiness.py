#!/usr/bin/env python3
"""Cold-send readiness check — how many warmed, cold-APPROVED mailboxes are ready to
send, and confirm the main-brand / staff inboxes are correctly excluded. Read-only
(lists Instantly accounts; sends nothing). Run before go-live.

    ./.venv/bin/python scripts/monitor/cold_readiness.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine import config, presend   # noqa: E402

WARMUP_FLOOR = 90


def fetch_accounts() -> list[dict]:
    key = config.get_key("INSTANTLY_API_KEY")
    if not key:
        return []
    out, cursor = [], None
    base = config.INSTANTLY["base_url"]
    for _ in range(30):
        url = f"{base}/accounts?limit=100" + (f"&starting_after={cursor}" if cursor else "")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}",
                                                   "User-Agent": config.USER_AGENT})
        with urllib.request.urlopen(req, timeout=25) as r:
            resp = json.loads(r.read().decode())
        items = resp.get("items", resp if isinstance(resp, list) else [])
        for a in items:
            email = (a.get("email") or "").lower()
            out.append({"email": email, "domain": email.split("@")[-1] if "@" in email else "",
                        "warmup": a.get("stat_warmup_score"), "status": a.get("status")})
        cursor = resp.get("next_starting_after")
        if not cursor:
            break
    return out


def main() -> int:
    accts = fetch_accounts()
    if not accts:
        print("No Instantly accounts returned (check INSTANTLY_API_KEY).")
        return 1
    cold_ready, cold_low, warm_only = [], [], []
    for a in accts:
        if presend.is_cold_approved(a["email"]):
            ws = a["warmup"] if isinstance(a["warmup"], (int, float)) else 0
            (cold_ready if ws >= WARMUP_FLOOR else cold_low).append(a)
        else:
            warm_only.append(a)

    def doms(lst):
        return sorted({a["domain"] for a in lst})

    print(f"Total mailboxes in Instantly: {len(accts)}\n")
    print(f"COLD-READY  (approved lookalike domain + warmup >= {WARMUP_FLOOR}): "
          f"{len(cold_ready)} mailboxes across {len(doms(cold_ready))} domains")
    for d in doms(cold_ready):
        n = sum(1 for a in cold_ready if a["domain"] == d)
        print(f"   {d}: {n} mailbox(es)")
    print(f"\nCOLD-APPROVED BUT WARMUP < {WARMUP_FLOOR} (let them keep warming): {len(cold_low)}")
    for a in cold_low[:20]:
        print(f"   {a['email']}  warmup={a['warmup']}")
    print(f"\nWARM-ONLY / EXCLUDED  (main brand + staff — correctly blocked from cold): "
          f"{len(warm_only)} mailboxes across {len(doms(warm_only))} domains")
    for d in doms(warm_only):
        print(f"   {d}")

    cap = len(cold_ready) * config.SENDING["cold_per_mailbox_per_day"]
    print(f"\nApprox cold capacity at {config.SENDING['cold_per_mailbox_per_day']}/mailbox/day: "
          f"~{cap} emails/day from warmed lookalike mailboxes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
