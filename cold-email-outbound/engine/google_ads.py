"""Direct Google Ads API connector — campaign performance for the FS + CS accounts.

No third party: talks to the official Google Ads API over the OAuth2 refresh-token
flow. Zero pip deps (urllib + stdlib). Never raises from fetch() — returns None on
any problem so the dashboard falls back to its "not connected" scaffold.

Credentials (all in cold-email-outbound/.env) — these are what Theodore provides
once, from the Google Ads side, to switch the tab live:
    GOOGLE_ADS_DEVELOPER_TOKEN     approved developer token (API Center)
    GOOGLE_ADS_CLIENT_ID           OAuth2 client id  (Google Cloud console)
    GOOGLE_ADS_CLIENT_SECRET       OAuth2 client secret
    GOOGLE_ADS_REFRESH_TOKEN       refresh token for an account with access
    GOOGLE_ADS_LOGIN_CUSTOMER_ID   manager (MCC) account id, digits only  (optional)
    GOOGLE_ADS_CUSTOMER_IDS        FS + CS customer ids, comma-separated, digits only

available() is False until those are set — until then the engine never calls Google.
NOTE: structurally complete but unverified end-to-end until real credentials land;
the first live pull is the integration test.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from . import config

API_VERSION = "v17"
TOKEN_URL = "https://oauth2.googleapis.com/token"

REQUIRED = [
    "GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN", "GOOGLE_ADS_CUSTOMER_IDS",
]

_CAMPAIGN_GAQL = (
    "SELECT campaign.name, campaign.status, metrics.impressions, metrics.clicks, "
    "metrics.cost_micros, metrics.conversions FROM campaign "
    "WHERE segments.date DURING LAST_30_DAYS"
)
_DAILY_GAQL = (
    "SELECT segments.date, metrics.cost_micros, metrics.clicks, metrics.impressions, "
    "metrics.conversions FROM customer WHERE segments.date DURING LAST_30_DAYS"
)


def missing() -> list[str]:
    return [k for k in REQUIRED if not config.get_key(k)]


def available() -> bool:
    return not missing()


def _access_token() -> str:
    data = urllib.parse.urlencode({
        "client_id": config.require_key("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": config.require_key("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": config.require_key("GOOGLE_ADS_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data,
                                 headers={"User-Agent": config.USER_AGENT}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())["access_token"]


def _search(customer_id: str, query: str, token: str, dev_token: str, login_cid: str | None) -> list[dict]:
    url = f"https://googleads.googleapis.com/{API_VERSION}/customers/{customer_id}/googleAds:searchStream"
    headers = {"Authorization": f"Bearer {token}", "developer-token": dev_token,
               "Content-Type": "application/json", "User-Agent": config.USER_AGENT}
    if login_cid:
        headers["login-customer-id"] = login_cid
    req = urllib.request.Request(url, data=json.dumps({"query": query}).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read().decode())
    batches = resp if isinstance(resp, list) else [resp]
    out: list[dict] = []
    for b in batches:
        out += b.get("results", [])
    return out


def fetch(window_days: int = 30) -> dict | None:
    """Pull campaign + daily metrics across the FS/CS customer ids. Returns a dict of
    {campaigns, daily, accounts, window_days} for _summarize_ads, or None on any error."""
    if not available():
        return None
    try:
        dev = config.require_key("GOOGLE_ADS_DEVELOPER_TOKEN")
        login = config.get_key("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        cids = [c.strip().replace("-", "") for c in config.get_key("GOOGLE_ADS_CUSTOMER_IDS").split(",") if c.strip()]
        token = _access_token()
        campaigns: list[dict] = []
        daily_map: dict[str, dict] = {}
        accounts: list[str] = []
        for cid in cids:
            for r in _search(cid, _CAMPAIGN_GAQL, token, dev, login):
                m = r.get("metrics", {}) or {}
                camp = r.get("campaign", {}) or {}
                spend = int(m.get("costMicros", 0) or 0) / 1e6
                impr = int(m.get("impressions", 0) or 0)
                clicks = int(m.get("clicks", 0) or 0)
                conv = float(m.get("conversions", 0) or 0)
                campaigns.append({
                    "account": cid, "campaign": camp.get("name", ""), "status": camp.get("status", ""),
                    "impressions": impr, "clicks": clicks,
                    "ctr": round(clicks / impr * 100, 2) if impr else 0,
                    "cpc": round(spend / clicks, 2) if clicks else 0,
                    "spend": round(spend, 2), "conversions": round(conv, 1),
                    "cost_per_conversion": round(spend / conv, 2) if conv else None,
                })
            accounts.append(cid)
            for r in _search(cid, _DAILY_GAQL, token, dev, login):
                m = r.get("metrics", {}) or {}
                date = (r.get("segments", {}) or {}).get("date")
                if not date:
                    continue
                d = daily_map.setdefault(date, {"date": date, "spend": 0.0, "clicks": 0, "impressions": 0, "conversions": 0.0})
                d["spend"] += int(m.get("costMicros", 0) or 0) / 1e6
                d["clicks"] += int(m.get("clicks", 0) or 0)
                d["impressions"] += int(m.get("impressions", 0) or 0)
                d["conversions"] += float(m.get("conversions", 0) or 0)
        daily = sorted(daily_map.values(), key=lambda x: x["date"])
        for d in daily:
            d["spend"] = round(d["spend"], 2)
            d["conversions"] = round(d["conversions"], 1)
        return {"campaigns": campaigns, "daily": daily, "accounts": accounts, "window_days": window_days}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError):
        return None
