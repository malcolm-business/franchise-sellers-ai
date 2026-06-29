"""Perplexity (Sonar) web research — source-grounded context for qualification
and (later) personalization.

Uses the Search API (POST /search) for cheap, cited snippets. Zero pip deps
(urllib + stdlib). Key from PERPLEXITY_API_KEY. Every call is best-effort and
never raises — returns [] / "" on any error so the funnel degrades gracefully.
"""
from __future__ import annotations

import json
import urllib.request

from . import config

BASE = "https://api.perplexity.ai"


def available() -> bool:
    return bool(config.get_key("PERPLEXITY_API_KEY"))


def _post(path: str, body: dict, timeout: int = 30) -> dict:
    key = config.require_key("PERPLEXITY_API_KEY")
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": config.USER_AGENT}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def search(query: str, max_results: int = 3, max_tokens_per_page: int = 384) -> list[dict]:
    """Return [{title, url, snippet}] for a query. Empty list on any failure."""
    try:
        d = _post("/search", {"query": query, "max_results": max_results,
                              "max_tokens_per_page": max_tokens_per_page})
    except Exception:
        return []
    raw = d.get("results") or d.get("web_results") or []
    out = []
    for r in raw:
        snippet = (r.get("snippet") or r.get("text") or r.get("content")
                   or r.get("extract") or "")
        out.append({"title": r.get("title", ""), "url": r.get("url", ""),
                    "snippet": str(snippet).replace("\n", " ").strip()[:500]})
    return out


def context_for_contact(contact) -> str:
    """Gather a few cited web snippets to help judge owner-currency, business type,
    and ownership. Returns a markdown block (or '' if nothing/unavailable)."""
    if not available():
        return ""
    name = contact.display_name
    company = (contact.company or "").strip()
    loc = ", ".join(p for p in (contact.city, contact.state) if p)
    queries: list[str] = []
    if name and company:
        queries.append(f"{name} owner of {company} {loc} current role")
    if company:
        queries.append(f'"{company}" {loc} franchise OR independent business owner')
        queries.append(f'"{company}" private equity OR publicly traded OR acquired OR sold')
    blocks: list[str] = []
    seen = set()
    for q in queries[:3]:
        for r in search(q, max_results=3):
            key = r["url"] or r["title"]
            if not key or key in seen:
                continue
            seen.add(key)
            blocks.append(f"- {r['title']} ({r['url']}): {r['snippet']}")
            if len(blocks) >= 8:
                break
        if len(blocks) >= 8:
            break
    return "\n".join(blocks)
