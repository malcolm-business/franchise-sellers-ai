"""Disambiguate the AMBIGUOUS-brand Tier A records into FS / CS.

Non-destructive: reads tier-a-ambiguous.csv, assigns a resolved_brand + reason,
writes tier-a-ambiguous-resolved.csv. Does NOT overwrite the dedup output.

Resolution rules (in order):
  1. Source-brand signal: record's sources are FS-only -> FS; CS-only -> CS.
  2. Tiebreak (both FS+CS sources, or neither):
     - franchise-system keyword in company name -> FS
     - else -> CS (independent business is the default; CS is the larger, more
       reliable bucket and most content-ambiguous records are independents)

Run:  python3 cold-email-outbound/scripts/dedup/disambiguate.py
"""
import csv
import json
import os
from collections import Counter

csv.field_size_limit(10_000_000)

DEDUP = "C:/Users/theod/OneDrive/Desktop/Claude MASTER/Claude CODE/.claude/worktrees/practical-wozniak-2c8c43/cold-email-outbound/data/dedup-output"
SRC = os.path.join(DEDUP, "tier-a-ambiguous.csv")
OUT = os.path.join(DEDUP, "tier-a-ambiguous-resolved.csv")

def _is_fs_family(fam: str) -> bool:
    return (
        "franchise" in fam            # dropbox_master_franchise_list
        or fam.startswith("clay_fs")  # clay_fs_owner_linkedin, _storage_*
        or fam.startswith("fs_save_fs")  # fs_save_fs_master
        or "zoominfo_fs" in fam       # dropbox_zoominfo_fs
        or "mufc" in fam              # dropbox_mufc_2025
    )


def _is_cs_family(fam: str) -> bool:
    return (
        fam.startswith("clay_cs")     # clay_cs_archived, clay_cs_live
        or fam.startswith("fs_save_cs")  # fs_save_cs_master
        or "master_cs_data" in fam    # dropbox_master_cs_data
        or "zoominfo_master" in fam   # dropbox_zoominfo_master (the CS zoominfo export)
    )

FRANCHISE_SYSTEMS = [
    "snap-on", "great clips", "comfort keepers", "firstlight", "home instead",
    "visiting angels", "caring transitions", "comforcare", "honor", "brightstar",
    "right at home", "senior helpers", "homewatch", "code ninja", "kumon", "mathnasium",
    "goldfish swim", "primrose", "kiddie academy", "maaco", "1-800 radiator", "meineke",
    "midas", "jiffy lube", "valvoline", "take 5", "ace hardware", "true value",
    "ben & jerry", "nekter", "tropical smoothie", "smoothie king", "jersey mike", "subway",
    "jimmy john", "firehouse subs", "wingstop", "jet's pizza", "anytime fitness",
    "orangetheory", "pure barre", "club pilates", "f45", "9round", "servpro",
    "servicemaster", "puroclean", "stanley steemer", "chem-dry", "two men and a truck",
    "college hunks", "junk king", "the ups store", "fastsigns", "minuteman press",
    "house doctors", "mr. handyman", "molly maid", "merry maids", "elements massage",
    "massage envy", "hand and stone", "drybar", "sport clips", "del taco", "dunkin",
    "baskin", "dairy queen", "express employment", "fitness together", "bricks 4 kidz",
    "sylvan", "cruise planners", "rhea lana", "apricot lane", "schooley mitchell",
    "homevestors", "exit realty", "the entrepreneur's source", "hommati",
    "national property inspections", "sculpture hospitality",
]


def source_families(srcs_json):
    out = set()
    for s in json.loads(srcs_json or "[]"):
        out.add(s.split("__")[0])
    return out


def is_franchise_company(company):
    cl = (company or "").lower()
    return any(sysname in cl for sysname in FRANCHISE_SYSTEMS)


def resolve(row):
    fams = source_families(row["source_categories"])
    has_fs = any(_is_fs_family(f) for f in fams)
    has_cs = any(_is_cs_family(f) for f in fams)

    if has_fs and not has_cs:
        return "FS", "fs_only_source"
    if has_cs and not has_fs:
        return "CS", "cs_only_source"
    # both or neither -> content tiebreak
    if is_franchise_company(row.get("company", "")):
        return "FS", "franchise_system_in_company"
    return "CS", "default_independent"


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    print(f"Ambiguous Tier A: {len(rows):,}")

    reason_counter = Counter()
    brand_counter = Counter()
    fieldnames = list(rows[0].keys()) + ["resolved_brand", "resolution_reason"]
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            brand, reason = resolve(r)
            r["resolved_brand"] = brand
            r["resolution_reason"] = reason
            reason_counter[reason] += 1
            brand_counter[brand] += 1
            w.writerow(r)

    print(f"\nResolved -> FS: {brand_counter['FS']:,} | CS: {brand_counter['CS']:,}")
    print("\nBy reason:")
    for reason, n in reason_counter.most_common():
        print(f"  {n:6,}  {reason}")

    print(f"\nWrote {OUT}")
    print("\n=== New effective Tier A (after disambiguation) ===")
    # Original Tier A: FS 10,206 / CS 160,699 (from DEDUP-REPORT)
    print(f"  FS: 10,206 + {brand_counter['FS']:,} = {10206 + brand_counter['FS']:,}")
    print(f"  CS: 160,699 + {brand_counter['CS']:,} = {160699 + brand_counter['CS']:,}")
    print(f"  TOTAL Tier A: {10206 + 160699 + len(rows):,} (unchanged — just cleanly split now)")


if __name__ == "__main__":
    main()
