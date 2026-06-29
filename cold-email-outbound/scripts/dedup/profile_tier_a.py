"""Profile the Tier A reactivation pool to inform Phase 1 campaign + template design.

Reads dedup-output tier files and answers:
- FS: which franchise systems have the most contacts? (drives FS niche campaign selection)
- CS: which industries are largest + cleanest? (drives CS campaign selection)
- Geographic distribution
- Verification status breakdown
- Source provenance (how many came from Clay's waterfall-enriched vs raw lists)
- Email-domain quality (personal vs business)

Output: stdout report + TIER-A-PROFILE.md
"""
import os
import re
import json
from collections import Counter

import pandas as pd

OUT_DIR = "C:/Users/theod/OneDrive/Desktop/Claude MASTER/Claude CODE/.claude/worktrees/practical-wozniak-2c8c43/cold-email-outbound/data/dedup-output"
REPORT = os.path.join(OUT_DIR, "TIER-A-PROFILE.md")

PERSONAL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "aol.com", "outlook.com",
    "icloud.com", "comcast.net", "msn.com", "live.com", "me.com",
    "sbcglobal.net", "verizon.net", "att.net", "cox.net", "bellsouth.net",
}

# Franchise system keywords to detect in company names (for FS niche campaign sizing)
FRANCHISE_SYSTEMS = [
    "snap-on", "snap on", "great clips", "comfort keepers", "firstlight", "first light",
    "home instead", "visiting angels", "caring transitions", "comforcare", "honor",
    "code ninja", "kumon", "mathnasium", "goldfish swim", "primrose", "kiddie academy",
    "maaco", "1-800 radiator", "meineke", "midas", "jiffy lube", "valvoline", "take 5",
    "ace hardware", "true value", "do it best",
    "ben & jerry", "ben and jerry", "nekter", "tropical smoothie", "smoothie king",
    "jersey mike", "subway", "jimmy john", "firehouse subs", "wingstop", "jet's pizza",
    "anytime fitness", "orangetheory", "pure barre", "club pilates", "f45", "9round",
    "servpro", "servicemaster", "puroclean", "stanley steemer", "chem-dry", "chemdry",
    "two men and a truck", "college hunks", "junk king", "1-800-got-junk",
    "the ups store", "postal annex", "fastsigns", "minuteman press", "alphagraphics",
    "house doctors", "mr. handyman", "mr handyman", "ace handyman", "handyman connection",
    "molly maid", "merry maids", "the cleaning authority", "maid brigade",
    "elements massage", "massage envy", "hand and stone", "drybar", "sport clips",
    "del taco", "taco bell", "kfc", "popeyes", "dunkin", "baskin", "dairy queen",
    "express employment", "spherion", "labor finders",
]


def load(name):
    path = os.path.join(OUT_DIR, name)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False, dtype=str).fillna("")


def domain_of(email):
    if not isinstance(email, str) or "@" not in email:
        return ""
    return email.split("@")[-1].lower().strip()


def detect_systems(company_series):
    counts = Counter()
    for c in company_series:
        cl = (c or "").lower()
        if not cl:
            continue
        for sysname in FRANCHISE_SYSTEMS:
            if sysname in cl:
                # Normalize to a canonical label
                label = sysname.replace("snap on", "snap-on").replace("first light", "firstlight")
                counts[label] += 1
                break
    return counts


def top_n_counter(series, n=25, min_len=2):
    c = Counter()
    for v in series:
        v = (v or "").strip()
        if len(v) >= min_len:
            c[v] += 1
    return c.most_common(n)


def main():
    fs = load("tier-a-fs.csv")
    cs = load("tier-a-cs.csv")
    amb = load("tier-a-ambiguous.csv")

    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    out("# Tier A Pool — Quality Profile")
    out()
    out(f"Generated from dedup-output. Tier A = sendable-today pool (valid email, no suppression).")
    out()
    out(f"| Brand | Tier A records |")
    out(f"|---|---:|")
    out(f"| FS | {len(fs):,} |")
    out(f"| CS | {len(cs):,} |")
    out(f"| Ambiguous | {len(amb):,} |")
    out(f"| **Total** | **{len(fs)+len(cs)+len(amb):,}** |")
    out()

    # ─── FS franchise systems ──────────────────────────────────────────────
    out("## FS — franchise systems by contact count")
    out()
    out("Drives `seller_cold_fs_niche` campaign selection. Systems with the most")
    out("contacts are the best candidates for system-named templates.")
    out()
    fs_systems = detect_systems(fs["company"]) if len(fs) else Counter()
    # Also check the ambiguous pool for franchise systems (they may be FS)
    amb_systems = detect_systems(amb["company"]) if len(amb) else Counter()
    combined = fs_systems + amb_systems
    if combined:
        out("| Franchise system | FS pool | Ambiguous pool | Total |")
        out("|---|---:|---:|---:|")
        for sysname, _ in combined.most_common(25):
            out(f"| {sysname} | {fs_systems.get(sysname, 0):,} | {amb_systems.get(sysname, 0):,} | {combined[sysname]:,} |")
    else:
        out("_No recognized franchise systems matched the keyword list._")
    out()
    out(f"Detected franchise-system contacts: {sum(fs_systems.values()):,} of {len(fs):,} FS Tier A "
        f"({sum(fs_systems.values())/max(len(fs),1)*100:.0f}%). The rest are franchisees of systems "
        f"not in the keyword list, or generic franchise contacts → use `seller_cold_fs_broad`.")
    out()

    # ─── FS top companies (raw) ────────────────────────────────────────────
    out("## FS — top company names (raw, top 25)")
    out()
    out("| Company | Contacts |")
    out("|---|---:|")
    for name, n in top_n_counter(fs["company"], 25):
        out(f"| {name[:50]} | {n:,} |")
    out()

    # ─── CS industries ─────────────────────────────────────────────────────
    out("## CS — industries by contact count")
    out()
    out("Drives `seller_cold_cs` campaign selection. Largest clean industries first.")
    out()
    out("| Industry | Contacts |")
    out("|---|---:|")
    for name, n in top_n_counter(cs["industry"], 25):
        out(f"| {name[:50]} | {n:,} |")
    out()

    # ─── CS sub-industries ─────────────────────────────────────────────────
    if len(cs) and cs["sub_industry"].str.strip().any():
        out("## CS — sub-industries (top 20)")
        out()
        out("| Sub-industry | Contacts |")
        out("|---|---:|")
        for name, n in top_n_counter(cs["sub_industry"], 20):
            out(f"| {name[:50]} | {n:,} |")
        out()

    # ─── Geographic ────────────────────────────────────────────────────────
    out("## Geographic distribution (state, top 20)")
    out()
    for label, df in [("FS", fs), ("CS", cs)]:
        if len(df) == 0 or not df["state"].str.strip().any():
            continue
        out(f"### {label} — top states")
        out("| State | Contacts |")
        out("|---|---:|")
        for name, n in top_n_counter(df["state"], 20):
            out(f"| {name[:40]} | {n:,} |")
        out()

    # ─── Email domain quality ──────────────────────────────────────────────
    out("## Email domain quality")
    out()
    out("| Brand | Business domains | Personal domains | Personal % |")
    out("|---|---:|---:|---:|")
    for label, df in [("FS", fs), ("CS", cs), ("Ambiguous", amb)]:
        if len(df) == 0:
            continue
        domains = df["email_original"].apply(domain_of)
        personal = domains.isin(PERSONAL_DOMAINS).sum()
        business = (domains != "").sum() - personal
        pct = personal / max((domains != "").sum(), 1) * 100
        out(f"| {label} | {business:,} | {personal:,} | {pct:.0f}% |")
    out()
    out("Personal-domain contacts (gmail/yahoo/etc) are higher-reply but worse for")
    out("deliverability + harder to verify. Consider a separate sending treatment.")
    out()

    # ─── Verification status ───────────────────────────────────────────────
    out("## Verification status (pre-LeadMagic-reverify)")
    out()
    out("All Tier A still needs re-verification before send (data is 6-18 months old).")
    out("This shows what the source data CLAIMED — not current validity.")
    out()
    out("| Brand | validated | unknown | invalid |")
    out("|---|---:|---:|---:|")
    for label, df in [("FS", fs), ("CS", cs), ("Ambiguous", amb)]:
        if len(df) == 0:
            continue
        vc = Counter(df["verification_status"])
        out(f"| {label} | {vc.get('validated', 0):,} | {vc.get('unknown', 0):,} | {vc.get('invalid', 0):,} |")
    out()

    # ─── Source richness ───────────────────────────────────────────────────
    out("## Source richness (enrichment confidence)")
    out()
    out("Records appearing in more source categories are higher-confidence (cross-verified).")
    out("Clay-sourced records carry the 6-provider waterfall enrichment.")
    out()
    for label, df in [("FS", fs), ("CS", cs)]:
        if len(df) == 0:
            continue
        clay_count = df["source_categories"].apply(lambda x: "clay_" in (x or "")).sum()
        multi = df["source_categories"].apply(lambda x: len(json.loads(x)) >= 3 if x else False).sum()
        has_li = (df["linkedin_norm"].str.strip() != "").sum()
        has_phone = (df["phone_primary"].str.strip() != "").sum()
        out(f"### {label} Tier A ({len(df):,} records)")
        out(f"- Clay-enriched (waterfall email + signals): {clay_count:,} ({clay_count/len(df)*100:.0f}%)")
        out(f"- In 3+ source categories (high confidence): {multi:,} ({multi/len(df)*100:.0f}%)")
        out(f"- Has LinkedIn URL: {has_li:,} ({has_li/len(df)*100:.0f}%)")
        out(f"- Has phone: {has_phone:,} ({has_phone/len(df)*100:.0f}%)")
        out()

    # ─── Recommendations ───────────────────────────────────────────────────
    out("## Phase 1 probe recommendations")
    out()
    out("Based on the profile above:")
    out()
    if combined:
        top_systems = [s for s, _ in combined.most_common(5)]
        out(f"**`seller_cold_fs_niche` — probe these systems first** (most contacts): "
            f"{', '.join(top_systems)}")
    cs_top_inds = [n for n, _ in top_n_counter(cs['industry'], 5)] if len(cs) else []
    if cs_top_inds:
        out(f"**`seller_cold_cs` — probe these industries first** (largest pools): "
            f"{', '.join(cs_top_inds)}")
    out()
    out("Note: 'largest' ≠ 'best'. Cross-reference with the historical retrospective —")
    out("FS niche campaigns (FirstLight, Comfort Keepers, Code Ninja) hit 6-8% reply;")
    out("CS broad campaigns underperformed. Pick systems/industries with BOTH volume")
    out("AND clean verification AND historical signal where available.")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n\nWrote {REPORT}")


if __name__ == "__main__":
    main()
