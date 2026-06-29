"""Cold Email Engine — copy generation (spintax + signal anchoring + offer rotation).

Produces the actual email text per contact from a stream template. Three jobs:

  1. Spintax expansion: {{RANDOM | a | b | c}} -> one option (rotated, not random,
     so the same canonical_id always gets the same variant = reproducible + testable).
  2. Variable slotting: {{firstName}}, {{company}}, {{franchise_system}},
     {{brand_name}}, {{sender_name}}, etc. -> values from the Contact + brand.
  3. Signal anchoring: {{signal_anchor}} -> a specific recent signal IF one exists
     in the data; otherwise the line is removed entirely (never fake a signal —
     the historical retrospective showed fake personalization underperforms).

Offer rotation (OOV control vs alternatives) is handled by selecting the CTA
block — see select_offer().

No network calls. (Phase 2 will add a Claude-API path for richer per-row signal
extraction; this module's interface stays the same.)
"""
from __future__ import annotations

import re
import hashlib

from . import config
from .models import Contact


# ────────────────────────────────────────────────────────────────────────────
# Deterministic variant selection
# ────────────────────────────────────────────────────────────────────────────

def _stable_index(seed: str, n: int) -> int:
    """Map a seed string to a stable index in [0, n). Same seed -> same index."""
    if n <= 1:
        return 0
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return h % n


SPINTAX_RE = re.compile(r"\{\{RANDOM\s*\|([^}]*)\}\}")


def expand_spintax(text: str, seed: str) -> str:
    """Replace each {{RANDOM | a | b | c}} with one option, chosen stably by seed."""
    def repl(m: re.Match) -> str:
        options = [o.strip() for o in m.group(1).split("|") if o.strip() != ""]
        if not options:
            return ""
        # Vary the choice per spin-zone by mixing the zone text into the seed
        zone_seed = f"{seed}|{m.group(1)}"
        return options[_stable_index(zone_seed, len(options))]
    # Repeat until no nested spintax remains
    prev = None
    out = text
    while prev != out:
        prev = out
        out = SPINTAX_RE.sub(repl, out)
    return out


# ────────────────────────────────────────────────────────────────────────────
# Variable slotting
# ────────────────────────────────────────────────────────────────────────────

def build_variables(c: Contact, brand: str, extra: dict | None = None) -> dict[str, str]:
    binfo = config.BRANDS.get(brand, config.BRANDS["CS"])
    first = c.first_name or (c.full_name.split(" ")[0] if c.full_name else "there")
    vars_ = {
        "firstName": first,
        "first_name": first,
        "lastName": c.last_name,
        "fullName": c.display_name,
        "company": c.company or "your business",
        "title": c.title,
        "industry": c.industry,
        "industry_lower": (c.industry or "").lower(),
        "city": c.city,
        "state": c.state,
        "brand_name": binfo["name"],
        "sender_name": binfo["sender_name"],
        "audience_descriptor": binfo["audience"],
        # franchise_system: best-effort from company name; falls back to generic
        "franchise_system": c.company or "your franchise",
    }
    if extra:
        vars_.update({k: str(v) for k, v in extra.items()})
    return vars_


VAR_RE = re.compile(r"\{\{([a-zA-Z_]+)\}\}")


def slot_variables(text: str, variables: dict[str, str]) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        return variables.get(key, m.group(0))  # leave unknown vars literally visible
    return VAR_RE.sub(repl, text)


# ────────────────────────────────────────────────────────────────────────────
# Signal anchoring — remove the line if no real signal exists
# ────────────────────────────────────────────────────────────────────────────

SIGNAL_LINE_RE = re.compile(r"^.*\{\{signal_anchor\}\}.*$\n?", re.MULTILINE)


def apply_signal_anchor(text: str, signal: str | None) -> str:
    """If `signal` is provided, slot it in. If not, delete the whole line that
    contains {{signal_anchor}} so we never ship an empty/awkward placeholder."""
    if signal:
        return text.replace("{{signal_anchor}}", signal)
    return SIGNAL_LINE_RE.sub("", text)


# ────────────────────────────────────────────────────────────────────────────
# Offer rotation
# ────────────────────────────────────────────────────────────────────────────

# CTA blocks keyed by offer id. OOV is the control (see 04-offer-concepts.md).
OFFERS = {
    "oov": "If you're curious about selling, we'd be happy to provide a complimentary, no-obligation business opinion of value.",
    "comparable_sales": "I just pulled the last several {{industry}} businesses that sold in your area — happy to send the report if it's useful.",
    "exit_readiness": "I help owners gauge how 'sale-ready' their business is before they go to market — open to a quick check?",
    "buyer_match": "We're tracking active buyers in your space right now. If you'd ever consider an offer, would it be worth a quick conversation?",
    "strategy_call": "Worth a 15-minute conversation about how owners in your industry are thinking about exits in 2026?",
    "succession": "Helping owners think through succession — whether that's selling, transitioning to family, or stepping back gradually. Open to a brief conversation?",
}


def select_offer(stream: str, contact: Contact, test_offer: str | None = None) -> tuple[str, str]:
    """Return (offer_id, cta_text). OOV is control; test_offer overrides for A/B cohorts."""
    offer_id = test_offer if (test_offer and test_offer in OFFERS) else "oov"
    return offer_id, OFFERS[offer_id]


# ────────────────────────────────────────────────────────────────────────────
# CAN-SPAM footer — physical address + opt-out on EVERY email (legal requirement)
# ────────────────────────────────────────────────────────────────────────────

def compliance_footer(brand: str) -> str:
    """Footer appended to every rendered email: brand · physical address · opt-out."""
    binfo = config.BRANDS.get(brand, config.BRANDS["CS"])
    c = config.COMPLIANCE
    return (f"\n\n{c['footer_separator']}\n"
            f"{binfo['name']} · {c['mailing_address']}\n"
            f"{c['optout_line']}")


# ────────────────────────────────────────────────────────────────────────────
# Full render
# ────────────────────────────────────────────────────────────────────────────

def render(
    template_body: str,
    contact: Contact,
    brand: str,
    signal: str | None = None,
    test_offer: str | None = None,
    extra_vars: dict | None = None,
) -> tuple[str, dict]:
    """Render one email body for one contact. Returns (text, meta).

    Order: signal-anchor (may delete a line) -> offer CTA slot -> spintax ->
    variable slotting. Deterministic per canonical_id.
    """
    seed = contact.canonical_id or contact.email_norm or contact.display_name

    offer_id, cta = select_offer("", contact, test_offer)
    extra = dict(extra_vars or {})
    extra["offer_cta"] = cta

    text = apply_signal_anchor(template_body, signal)
    text = expand_spintax(text, seed)
    variables = build_variables(contact, brand, extra)
    text = slot_variables(text, variables)
    # collapse 3+ newlines to 2 (signal-line deletion can leave gaps)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    # CAN-SPAM: physical address + opt-out on every email
    text += compliance_footer(brand) + "\n"

    meta = {
        "offer_id": offer_id,
        "brand": brand,
        "seed": seed,
        "had_signal": bool(signal),
        "word_count": len(re.findall(r"\w+", text)),
    }
    return text, meta


def variation_ratio(rendered_texts: list[str]) -> float:
    """Crude content-variation metric across a batch: unique / total. Used to
    confirm we hit config.SENDING['min_spintax_variation_pct']."""
    if not rendered_texts:
        return 0.0
    return len(set(rendered_texts)) / len(rendered_texts) * 100


# ────────────────────────────────────────────────────────────────────────────
# Template files — minimal frontmatter parser (no yaml dependency)
# ────────────────────────────────────────────────────────────────────────────

import json as _json
from pathlib import Path as _Path


def _parse_frontmatter(block: str) -> dict:
    """Parse a tiny subset of YAML: scalars, inline lists [a, b], and
    indented '- item' lists. Sufficient for template metadata."""
    meta: dict = {}
    current_key = None
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and current_key:
            meta.setdefault(current_key, [])
            if isinstance(meta[current_key], list):
                meta[current_key].append(line.lstrip()[2:].strip())
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            current_key = key
            if val == "":
                meta[key] = []          # expect '- ' items to follow
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                meta[key] = [x.strip() for x in inner.split(",")] if inner else []
            else:
                meta[key] = val
    return meta


def parse_template(path: str | _Path) -> dict:
    """Load a stream template .md file.

    Returns {meta: {...}, steps: [{n, delay_days, body}, ...]}.
    Format:
        ---
        stream: ...
        brand: FS
        subjects:
          - "Subject A"
          - "Subject B"
        delays_days: [1, 4, 6]
        ---
        ## STEP 1
        body...
        ## STEP 2
        body...
    """
    text = _Path(path).read_text(encoding="utf-8")
    meta: dict = {}
    body = text
    if text.lstrip().startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = _parse_frontmatter(parts[1])
            body = parts[2]

    # Parse ## STEP N sections
    steps = []
    delays = meta.get("delays_days", [])
    if isinstance(delays, str):
        delays = [d.strip() for d in delays.strip("[]").split(",") if d.strip()]
    step_chunks = re.split(r"^##\s*STEP\s*(\d+).*$", body, flags=re.MULTILINE)
    # step_chunks = [pre, '1', body1, '2', body2, ...]
    it = iter(step_chunks[1:])
    for n_str, chunk in zip(it, it):
        n = int(n_str)
        try:
            delay = int(delays[n - 1]) if n - 1 < len(delays) else 0
        except (ValueError, TypeError):
            delay = 0
        steps.append({"n": n, "delay_days": delay, "body": chunk.strip()})

    return {"meta": meta, "steps": steps}
