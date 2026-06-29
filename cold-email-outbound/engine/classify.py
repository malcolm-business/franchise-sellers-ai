"""Cold Email Engine — reply classification.

Every inbound reply -> one of 11 ReplyCategory values + extracted entities
(re-engage date, referral name). This is the biggest gap-fix vs the prior engine,
which left ~70% of replies unclassified.

DRY-RUN: uses the keyword heuristic (same logic as the historical
analyze_instantly_replies.py). LIVE: calls the Claude API with a pinned model
for higher accuracy + entity extraction.

The live path imports anthropic lazily so the engine has no hard dependency
until you actually go live.
"""
from __future__ import annotations

import re
import json

from . import config, data_layer
from .models import ReplyCategory


# ────────────────────────────────────────────────────────────────────────────
# Heuristic classifier (dry-run + fast fallback)
# ────────────────────────────────────────────────────────────────────────────

def classify_heuristic(subject: str, body: str) -> ReplyCategory:
    s = (subject or "").lower().strip()
    b = (body or "").lower().strip()
    text = f"{s} {b}"

    if "out of office" in text or "on vacation" in text or "on leave" in text or "returning" in s or "auto-reply" in text:
        return ReplyCategory.OUT_OF_OFFICE
    if "unsubscribe" in text or "remove me" in text or "take me off" in text or "opt me out" in text:
        return ReplyCategory.UNSUBSCRIBE
    if "accepted" in s and any(w in s for w in ("meeting", "call", "discovery", "discussion")):
        return ReplyCategory.MEETING_ACCEPTED
    if "interested in resales" in text or "acquiring not selling" in text or "looking to buy" in text or "interested in buying" in text:
        return ReplyCategory.WRONG_INTENT_BUYER_SIDE
    if "not the right" in text or "wrong person" in text or "no longer with" in text or "don't own" in text:
        return ReplyCategory.WRONG_PERSON
    if "talk to" in text and ("my " in text or "our ") in text or "reach out to" in text or "forward" in text and "to" in text:
        # weak referral signal; refined by the LLM path
        if any(w in text for w in ("cfo", "partner", "colleague", "assistant", "team")):
            return ReplyCategory.REFERRAL
    if (re.search(r"\bno (thanks?|thank you)\b", text) or "not interested" in text or "no interest" in text
            or "not for sale" in text or s in ("no", "no.", "no thanks")):
        return ReplyCategory.OBJECTION_NOT_INTERESTED
    if ("not right now" in text or "not at this time" in text or "maybe later" in text or "in a few years" in text
            or "down the road" in text or "too early" in text or "touch base" in text or "end of 202" in text):
        return ReplyCategory.OBJECTION_NOT_NOW
    if ("but not" in text or "though we are" in text or "years away" in text) and ("interested" in text or "yes" in b[:20]):
        return ReplyCategory.POSITIVE_WITH_TIMELINE_OBJECTION
    if any(p in text for p in ("let's chat", "let's talk", "book a call", "set up a call", "schedule", "happy to chat", "give me a call")):
        return ReplyCategory.POSITIVE_MEETING_READY
    if any(p in text for p in ("tell me more", "send me", "send the", "would like to learn", "i'd be interested",
                               "i would be interested", "interested in selling", "curious", "sounds good",
                               "love to", "open to", "absolutely")) or re.search(r"\byes\b", b[:30]):
        return ReplyCategory.POSITIVE_CURIOUS

    return ReplyCategory.OTHER


# ────────────────────────────────────────────────────────────────────────────
# Entity extraction (re-engage date, referral name)
# ────────────────────────────────────────────────────────────────────────────

MONTHS = ("january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december")


def extract_entities_heuristic(body: str, category: ReplyCategory) -> dict:
    b = (body or "").lower()
    out: dict = {}
    if category in (ReplyCategory.OBJECTION_NOT_NOW, ReplyCategory.POSITIVE_WITH_TIMELINE_OBJECTION,
                    ReplyCategory.OUT_OF_OFFICE):
        # crude date hints
        m = re.search(r"\b(end of|q[1-4]|spring|summer|fall|winter|early|late)?\s*(20\d\d)\b", b)
        if m:
            out["re_engage_hint"] = m.group(0).strip()
        for mon in MONTHS:
            if mon in b:
                out["re_engage_hint"] = mon
                break
        yrs = re.search(r"(\d+)\s*year", b)
        if yrs:
            out["re_engage_hint"] = f"{yrs.group(1)} years"
    return out


# ────────────────────────────────────────────────────────────────────────────
# LLM classifier (live)
# ────────────────────────────────────────────────────────────────────────────

CLASSIFY_SYSTEM_PROMPT = """You classify replies to cold sales emails for a business brokerage \
(Franchise Sellers / Company Sellers). Return STRICT JSON only.

Categories:
- positive_meeting_ready: ready to talk/book a call now
- positive_curious: wants info/OOV/listings, soft yes
- positive_with_timeline_objection: interested but not ready (gives a future timeframe)
- objection_not_now: not now, may be later (capture any date)
- objection_not_interested: hard no / not interested / not for sale
- wrong_person: not the right contact
- wrong_intent_buyer_side: they want to BUY, not sell (route to buyer pipeline)
- unsubscribe: explicit opt-out
- out_of_office: auto-responder (capture return date)
- referral: points you to someone else (capture the name)
- meeting_accepted: calendar acceptance
- other: none of the above

Return: {"category": "<one>", "re_engage_date": "<ISO date or empty>", "referral_name": "<name or empty>", "confidence": 0.0-1.0}"""


def classify_llm(subject: str, body: str, original_subject: str = "") -> dict:
    """Live Claude-API classification. Only call when not DRY_RUN + key set."""
    import anthropic  # lazy import — no hard dependency until live

    client = anthropic.Anthropic(api_key=config.require_key(config.ANTHROPIC["key_env"]))
    user = (
        f"Original cold email subject: {original_subject}\n\n"
        f"Reply subject: {subject}\n\nReply body:\n{body}"
    )
    resp = client.messages.create(
        model=config.ANTHROPIC["classify_model"],
        max_tokens=config.ANTHROPIC["max_tokens"],
        system=CLASSIFY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text.strip()
    # tolerate code fences
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


# ────────────────────────────────────────────────────────────────────────────
# Public entry
# ────────────────────────────────────────────────────────────────────────────

def classify_reply(subject: str, body: str, original_subject: str = "") -> dict:
    """Return {category, re_engage_date, referral_name, confidence, method}."""
    if config.DRY_RUN:
        cat = classify_heuristic(subject, body)
        entities = extract_entities_heuristic(body, cat)
        result = {
            "category": cat.value,
            "re_engage_date": entities.get("re_engage_hint", ""),
            "referral_name": "",
            "confidence": 0.6,
            "method": "heuristic",
        }
        data_layer.log_dry_run("classify", f"WOULD classify reply via Claude API ({config.ANTHROPIC['classify_model']})",
                               {"subject": subject[:80], "heuristic_category": cat.value})
        return result

    try:
        out = classify_llm(subject, body, original_subject)
        out["method"] = "llm"
        return out
    except Exception as e:  # fall back to heuristic on any LLM error
        cat = classify_heuristic(subject, body)
        return {"category": cat.value, "re_engage_date": "", "referral_name": "",
                "confidence": 0.5, "method": f"heuristic_fallback:{type(e).__name__}"}
