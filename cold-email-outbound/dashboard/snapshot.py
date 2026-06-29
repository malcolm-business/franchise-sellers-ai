"""Marketing dashboard — snapshot generator.

Produces marketing-snapshot.json: the AGGREGATE data Malcolm's dashboard renders.
No PII — only counts, channel status, sequence definitions, segment specs, offers.
Safe to serve + (optionally) commit.

Run:  python3 cold-email-outbound/dashboard/snapshot.py
Cron: hourly business-hours, same cadence as the other dashboards.
"""
import sys
import json
import csv
from datetime import datetime
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ENGINE_DIR))

from engine import config, audiences, analytics, scoring, suppression, data_layer  # noqa: E402
from engine.sequences import DEFAULT_SEQUENCES  # noqa: E402
from engine.channels.base import CHANNEL_REGISTRY  # noqa: E402
from engine import channels as _channels        # noqa: E402,F401
from engine.copy_gen import OFFERS              # noqa: E402

import json as _json
import urllib.request as _urlreq
import urllib.error as _urlerr

csv.field_size_limit(10_000_000)

# Active Phase 1 streams (buyer_reactivation deferred — no cold source)
ACTIVE_STREAMS = [
    ("seller_cold_fs_niche", "FS", "tier_a"),
    ("seller_cold_fs_broad", "FS", "tier_a"),
    ("seller_cold_cs", "CS", "tier_a"),
    ("referral_partner_advisor", "REFERRAL", "tier_c"),
]
SELLER_STREAMS = {"seller_cold_fs_niche", "seller_cold_fs_broad", "seller_cold_cs"}


def campaign_readiness(sample=1000):
    """Per active stream: run the funnel on a sample, report % + projected sendable."""
    out = []
    for name, brand, source in ACTIVE_STREAMS:
        if source == "tier_c":
            contacts = data_layer.load_contacts(config.TIER_C, limit=sample)
        else:
            contacts = data_layer.load_tier_a(brand if brand in ("FS", "CS") else "FS", limit=sample)
        n = len(contacts) or 1
        scoring.apply_scores(contacts)
        if name in SELLER_STREAMS:
            eligible = [c for c in contacts if (c.icp_score or 0) >= config.ICP_THRESHOLD]
        else:
            eligible = contacts
        filt = suppression.SuppressionFilter(require_verified=False)
        clean, suppressed = filt.filter_batch(eligible)
        email_reach = sum(1 for c in clean if c.email_norm)
        li_reach = sum(1 for c in clean if c.linkedin_norm or c.linkedin_original)
        out.append({
            "stream": name, "brand": brand,
            "sample": n,
            "icp_eligible_pct": round(len(eligible) / n * 100),
            "after_suppression_pct": round(len(clean) / n * 100),
            "email_reach_pct": round(email_reach / n * 100),
            "linkedin_reach_pct": round(li_reach / n * 100),
        })
    return out


def _http(url, headers=None, method="GET", body=None, timeout=8):
    data = _json.dumps(body).encode() if body is not None else None
    h = dict(headers or {})
    h.setdefault("User-Agent", config.USER_AGENT)  # Instantly's Cloudflare 403s default urllib UA
    req = _urlreq.Request(url, data=data, headers=h, method=method)
    with _urlreq.urlopen(req, timeout=timeout) as r:
        return _json.loads(r.read().decode())


def channel_health():
    """Best-effort live status from Instantly + HeyReach. Never raises."""
    health = {}
    # Instantly accounts
    ik = config.get_key(config.INSTANTLY["key_env"])
    if ik:
        try:
            resp = _http(f"{config.INSTANTLY['base_url']}/accounts?limit=100",
                         headers={"Authorization": f"Bearer {ik}"})
            items = resp.get("items", resp if isinstance(resp, list) else [])
            active = sum(1 for a in items if a.get("status") == 1)
            warm = sum(1 for a in items if a.get("warmup_status") == 1 or a.get("warmup", {}).get("status") == 1)
            health["instantly"] = {"ok": True, "mailboxes": len(items), "active": active, "warming": warm}
        except _urlerr.HTTPError as e:
            # 403/1010 = the stored key is the MCP connector token, not a REST API key.
            # The engine needs a real Instantly REST API key (Settings -> Integrations ->
            # API Keys -> Create) for headless sending.
            if e.code == 403:
                health["instantly"] = {"ok": False, "http_403": True,
                                       "note": "403 from Instantly — verify the REST API key (and that the request sends a non-default User-Agent; Cloudflare blocks bare urllib)"}
            else:
                health["instantly"] = {"ok": False, "error": f"HTTP {e.code}"}
        except Exception as e:
            health["instantly"] = {"ok": False, "error": type(e).__name__}
    else:
        health["instantly"] = {"ok": False, "error": "no key"}
    # HeyReach LinkedIn accounts
    hk = config.get_key("HEYREACH_API_KEY")
    if hk:
        try:
            resp = _http("https://api.heyreach.io/api/public/li_account/GetAll",
                         headers={"X-API-KEY": hk, "Content-Type": "application/json"},
                         method="POST", body={"offset": 0, "limit": 100})
            items = resp.get("items", resp if isinstance(resp, list) else [])
            health["heyreach"] = {"ok": True, "linkedin_accounts": len(items)}
        except Exception as e:
            health["heyreach"] = {"ok": False, "error": type(e).__name__}
    else:
        health["heyreach"] = {"ok": False, "error": "no key"}
    return health


def _count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, "r", encoding="utf-8", newline="") as f:
        return max(sum(1 for _ in f) - 1, 0)  # minus header


# ── Ad performance (Google Ads via Windsor.ai) ───────────────────────────────
# Both brands run out of ONE Google Ads account, split by campaign name.
WINDSOR_AD_FIELDS = ("account_name,campaign,campaign_status,impressions,clicks,"
                     "ctr,cpc,spend,conversions,cost_per_conversion")

# Baked-in numbers pulled 2026-06-08 from Google Ads via Windsor.ai. This is the
# fallback shown until a WINDSOR_API_KEY is added to .env — once it is, snapshot.py
# pulls live each run and this constant is ignored.
STATIC_AD_CAMPAIGNS = [
    {"account": "Franchise Sellers", "campaign": "SELLERS", "status": "ENABLED",
     "impressions": 7663, "clicks": 273, "ctr": 3.56, "cpc": 3.20, "spend": 873.22,
     "conversions": 41, "cost_per_conversion": 21.30},
    {"account": "Franchise Sellers", "campaign": "Company Sellers Search Traffic", "status": "ENABLED",
     "impressions": 4721, "clicks": 243, "ctr": 5.15, "cpc": 2.21, "spend": 536.80,
     "conversions": 14, "cost_per_conversion": 38.34},
    {"account": "Franchise Sellers", "campaign": "CS RETARGETING", "status": "ENABLED",
     "impressions": 23595, "clicks": 272, "ctr": 1.15, "cpc": 0.21, "spend": 56.52,
     "conversions": 0, "cost_per_conversion": None},
]
STATIC_AD_DAILY = [
    {"date": "2026-05-09", "spend": 1.64, "clicks": 9, "impressions": 471, "conversions": 0},
    {"date": "2026-05-10", "spend": 42.01, "clicks": 19, "impressions": 602, "conversions": 1},
    {"date": "2026-05-11", "spend": 31.76, "clicks": 22, "impressions": 2245, "conversions": 0},
    {"date": "2026-05-12", "spend": 14.18, "clicks": 9, "impressions": 951, "conversions": 1},
    {"date": "2026-05-13", "spend": 19.82, "clicks": 14, "impressions": 1132, "conversions": 1},
    {"date": "2026-05-14", "spend": 17.84, "clicks": 16, "impressions": 1804, "conversions": 0},
    {"date": "2026-05-15", "spend": 10.22, "clicks": 12, "impressions": 797, "conversions": 0},
    {"date": "2026-05-16", "spend": 26.85, "clicks": 15, "impressions": 1230, "conversions": 0},
    {"date": "2026-05-17", "spend": 19.70, "clicks": 23, "impressions": 2279, "conversions": 0},
    {"date": "2026-05-18", "spend": 10.76, "clicks": 9, "impressions": 788, "conversions": 1},
    {"date": "2026-05-19", "spend": 11.76, "clicks": 24, "impressions": 2497, "conversions": 0},
    {"date": "2026-05-20", "spend": 18.55, "clicks": 5, "impressions": 364, "conversions": 1},
    {"date": "2026-05-21", "spend": 16.63, "clicks": 8, "impressions": 433, "conversions": 2},
    {"date": "2026-05-22", "spend": 8.70, "clicks": 12, "impressions": 442, "conversions": 0},
    {"date": "2026-05-23", "spend": 2.41, "clicks": 5, "impressions": 50, "conversions": 0},
    {"date": "2026-05-24", "spend": 8.88, "clicks": 6, "impressions": 171, "conversions": 0},
    {"date": "2026-05-25", "spend": 32.60, "clicks": 21, "impressions": 705, "conversions": 1},
    {"date": "2026-05-26", "spend": 29.91, "clicks": 8, "impressions": 181, "conversions": 1},
    {"date": "2026-05-27", "spend": 14.90, "clicks": 10, "impressions": 89, "conversions": 0},
    {"date": "2026-05-28", "spend": 15.57, "clicks": 10, "impressions": 191, "conversions": 1},
    {"date": "2026-05-29", "spend": 9.55, "clicks": 5, "impressions": 212, "conversions": 0},
    {"date": "2026-05-30", "spend": 25.86, "clicks": 6, "impressions": 106, "conversions": 1},
    {"date": "2026-05-31", "spend": 9.42, "clicks": 14, "impressions": 83, "conversions": 0},
    {"date": "2026-06-01", "spend": 19.35, "clicks": 13, "impressions": 109, "conversions": 1},
    {"date": "2026-06-02", "spend": 17.55, "clicks": 18, "impressions": 175, "conversions": 2},
    {"date": "2026-06-03", "spend": 2.59, "clicks": 5, "impressions": 125, "conversions": 0},
    {"date": "2026-06-04", "spend": 18.28, "clicks": 4, "impressions": 84, "conversions": 0},
    {"date": "2026-06-05", "spend": 30.68, "clicks": 19, "impressions": 239, "conversions": 0},
    {"date": "2026-06-06", "spend": 14.47, "clicks": 13, "impressions": 140, "conversions": 5},
    {"date": "2026-06-07", "spend": 16.79, "clicks": 7, "impressions": 35, "conversions": 2},
]
STATIC_ADS_PULLED_AT = "2026-06-08"


def _brand_for_campaign(name: str) -> str:
    n = (name or "").lower()
    if "company sellers" in n or n.startswith("cs ") or n.startswith("cs-") or "cs retarget" in n:
        return "CS"
    return "FS"


def _summarize_ads(campaigns, daily, source, window_days, pulled_at, accounts) -> dict:
    """Compute totals + per-brand split from a campaign list (live or static)."""
    for c in campaigns:
        c["brand"] = c.get("brand") or _brand_for_campaign(c["campaign"])
    tot_spend = sum(c["spend"] for c in campaigns)
    tot_impr = sum(c["impressions"] for c in campaigns)
    tot_clicks = sum(c["clicks"] for c in campaigns)
    tot_conv = sum(c["conversions"] for c in campaigns)
    brand = {}
    for c in campaigns:
        d = brand.setdefault(c["brand"], {"spend": 0, "impressions": 0, "clicks": 0, "conversions": 0})
        d["spend"] += c["spend"]; d["impressions"] += c["impressions"]
        d["clicks"] += c["clicks"]; d["conversions"] += c["conversions"]
    for d in brand.values():
        d["spend"] = round(d["spend"], 2)
        d["ctr"] = round(d["clicks"] / d["impressions"] * 100, 2) if d["impressions"] else 0
        d["cost_per_conversion"] = round(d["spend"] / d["conversions"], 2) if d["conversions"] else None
    return {
        "available": True, "source": source, "window_days": window_days,
        "pulled_at": pulled_at, "accounts": accounts,
        "totals": {
            "spend": round(tot_spend, 2), "impressions": tot_impr, "clicks": tot_clicks,
            "ctr": round(tot_clicks / tot_impr * 100, 2) if tot_impr else 0,
            "cpc": round(tot_spend / tot_clicks, 2) if tot_clicks else 0,
            "conversions": round(tot_conv, 1),
            "cost_per_conversion": round(tot_spend / tot_conv, 2) if tot_conv else None,
        },
        "brand_split": brand,
        "campaigns": campaigns,
        "daily": daily,
    }


def ad_performance() -> dict:
    """Google Ads performance. Prefers the DIRECT Google Ads API; falls back to
    Windsor.ai if configured; otherwise reports not-connected so the dashboard shows
    the connect scaffold (no stale baked data). Never raises."""
    # 1. Direct Google Ads API (the chosen path)
    try:
        from engine import google_ads
        if google_ads.available():
            data = google_ads.fetch()
            if data and data["campaigns"]:
                return _summarize_ads(data["campaigns"], data["daily"], "Google Ads API (live)",
                                      data.get("window_days", 30),
                                      datetime.utcnow().isoformat() + "Z", data["accounts"])
    except Exception:
        pass
    # 2. Windsor.ai connector (legacy, only if a key is present)
    key = config.get_key("WINDSOR_API_KEY")
    if key:
        try:
            url = (f"https://connectors.windsor.ai/google_ads?api_key={key}"
                   f"&date_preset=last_90d&fields={WINDSOR_AD_FIELDS}")
            resp = _http(url, timeout=25)
            rows = resp.get("data", resp if isinstance(resp, list) else [])
            campaigns = []
            for r in rows:
                campaigns.append({
                    "account": r.get("account_name", ""),
                    "campaign": r.get("campaign", ""),
                    "status": r.get("campaign_status", ""),
                    "impressions": int(float(r.get("impressions") or 0)),
                    "clicks": int(float(r.get("clicks") or 0)),
                    "ctr": round(float(r.get("ctr") or 0) * 100, 2),   # Windsor returns 0..1
                    "cpc": round(float(r.get("cpc") or 0), 2),
                    "spend": round(float(r.get("spend") or 0), 2),
                    "conversions": round(float(r.get("conversions") or 0), 1),
                    "cost_per_conversion": (round(float(r["cost_per_conversion"]), 2)
                                            if r.get("cost_per_conversion") else None),
                })
            durl = (f"https://connectors.windsor.ai/google_ads?api_key={key}"
                    f"&date_preset=last_30d&fields=date,spend,clicks,impressions,conversions")
            dresp = _http(durl, timeout=25)
            drows = dresp.get("data", dresp if isinstance(dresp, list) else [])
            daily = [{"date": d.get("date"), "spend": round(float(d.get("spend") or 0), 2),
                      "clicks": int(float(d.get("clicks") or 0)),
                      "impressions": int(float(d.get("impressions") or 0)),
                      "conversions": round(float(d.get("conversions") or 0), 1)} for d in drows]
            daily.sort(key=lambda x: x["date"] or "")
            accts = sorted({c["account"] for c in campaigns if c["account"]})
            if campaigns:
                return _summarize_ads(campaigns, daily, "Google Ads (live via Windsor.ai)",
                                      90, datetime.utcnow().isoformat() + "Z", accts)
        except Exception:
            pass  # fall back to static
    # 3. Not connected — honest scaffold (the dashboard shows what creds are needed)
    from engine import google_ads as _ga
    return {"available": False, "source": "google_ads_api", "needs": _ga.missing()}


def build_snapshot() -> dict:
    pool = {
        "tier_a_fs": _count_rows(config.TIER_A_FS),
        "tier_a_cs": _count_rows(config.TIER_A_CS),
        "tier_a_ambiguous": _count_rows(config.TIER_A_AMBIGUOUS),
        "tier_b_reverify": _count_rows(config.TIER_B),
        "tier_c_referral": _count_rows(config.TIER_C),
        "tier_d_suppression": _count_rows(config.TIER_D_SUPPRESSION),
        "canonical_total": _count_rows(config.CANONICAL_MASTER),
    }
    pool["tier_a_total"] = pool["tier_a_fs"] + pool["tier_a_cs"] + pool["tier_a_ambiguous"]

    # Per-channel setup instructions shown to Malcolm when a channel isn't live yet.
    SETUP_NOTES = {
        "email": "Live — Instantly connected.",
        "linkedin": "Live — HeyReach connected.",
        "ads": "ACTION NEEDED (Malcolm): set up Google Ads Customer Match + Meta Custom Audiences. "
               "Google: create a Customer Match user list in Google Ads, get a developer token + OAuth "
               "client + customer ID. Meta: create a Custom Audience in Ads Manager, get a Marketing API "
               "access token + audience ID. Add the keys to .env, then ads touches go live (prospects in a "
               "sequence start seeing our ads).",
        "postcard": "Later — pick a print-mail vendor (Lob or PostGrid), add POSTCARD_API_KEY.",
    }
    channels = []
    for name, ch in CHANNEL_REGISTRY.items():
        channels.append({
            "name": name,
            "available": ch.is_available(),
            "status": "live" if ch.is_available() else "needs setup",
            "setup": SETUP_NOTES.get(name, ""),
        })

    sequences = []
    for name, seq in DEFAULT_SEQUENCES.items():
        sequences.append({
            "name": name, "brand": seq.brand, "description": seq.description,
            "n_touches": len(seq.touches),
            "channels": sorted(seq.channels_used()),
            "touches": [{"day": t.delay_days, "channel": t.channel, "action": t.action}
                        for t in sorted(seq.touches, key=lambda x: x.delay_days)],
        })

    segments = []
    for seg_name in audiences.list_segments():
        spec = audiences.load_segment(seg_name)
        if spec:
            segments.append({"name": spec.name, "brand": spec.brand, "tier": spec.tier,
                             "industry": spec.industry_contains, "states": spec.states,
                             "min_icp": spec.min_icp, "limit": spec.limit})

    offers = [{"id": k, "cta": v} for k, v in OFFERS.items()]

    # Dry-run audit (how many would-be external calls have been simulated)
    dry_log = config.RUNTIME_DIR / "dry-run" / "dry-run.jsonl"
    dry_count = 0
    if dry_log.exists():
        dry_count = sum(1 for _ in open(dry_log, encoding="utf-8"))

    # Rich blocks for the v2 dashboard (best-effort; degrade gracefully)
    try:
        pool_analytics = analytics.pool_analytics()
    except Exception as e:
        pool_analytics = {"error": str(e)}
    try:
        readiness = campaign_readiness()
    except Exception as e:
        readiness = [{"error": str(e)}]
    try:
        health = channel_health()
    except Exception as e:
        health = {"error": str(e)}
    try:
        ads = ad_performance()
    except Exception as e:
        ads = {"available": False, "error": str(e)}
    try:
        from engine import db
        if db.available():
            qualification = db.qualification_stats()
            weekly_activity = db.weekly_activity()
            try:
                qualification["enrichment"] = db.enrichment_stats()
            except Exception:
                pass
        else:
            qualification, weekly_activity = {"available": False}, {}
    except Exception as e:
        qualification, weekly_activity = {"error": str(e)}, {}

    # Deliverability/infra health (from the monitor's status file) — feeds the
    # email tab's health strip + pre-send gate.
    try:
        d = json.loads((config.RUNTIME_DIR / "deliverability-status.json").read_text())
        deliverability = {
            "available": True, "checked_at": d.get("checked_at"),
            "domains": d.get("domains"), "mailboxes": d.get("mailboxes"),
            "warmup_below_floor": d.get("warmup_below_floor"),
            "ok": d.get("ok"), "problems": len(d.get("problems", [])),
        }
    except Exception:
        deliverability = {"available": False}

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "mode": "DRY-RUN" if config.DRY_RUN else "LIVE",
        "pool": pool,
        "analytics": pool_analytics,
        "qualification": qualification,
        "weekly_activity": weekly_activity,
        "deliverability": deliverability,
        "ads": ads,
        "channels": channels,
        "channel_health": health,
        "sequences": sequences,
        "campaign_readiness": readiness,
        "segments": segments,
        "offers": offers,
        "dry_run_simulated_calls": dry_count,
        "brands": {b: config.BRANDS[b]["name"] for b in config.BRANDS},
        "copy_pack_available": (config.RUNTIME_DIR / "COPY-PREVIEW-PACK.html").exists(),
    }


def main():
    snap = build_snapshot()
    out = Path(__file__).resolve().parent / "marketing-snapshot.json"
    out.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"  mode={snap['mode']}  tier_a_total={snap['pool']['tier_a_total']:,}  "
          f"channels={len(snap['channels'])}  sequences={len(snap['sequences'])}  "
          f"segments={len(snap['segments'])}")


if __name__ == "__main__":
    main()
