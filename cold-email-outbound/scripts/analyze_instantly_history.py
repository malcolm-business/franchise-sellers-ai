"""Analyze historical Instantly campaigns — structure + analytics + copy patterns.

Inputs:
- The on-disk list_campaigns dump (structural data with sequences/steps/variants/bodies)
- Live analytics from get_campaign_analytics (hardcoded below — paste fresh values
  by re-running get_campaign_analytics if it gets stale)

Outputs:
- /tmp/instantly-retro/analysis.json — joined records, one per campaign
- stdout: ranked table by reply rate

Run from project root:
    python3 cold-email-outbound/scripts/analyze_instantly_history.py
"""
import json, re, html, os, sys

CAMPAIGNS_DUMP = (
    "C:/Users/theod/.claude/projects/"
    "C--Users-theod-OneDrive-Desktop-Claude-MASTER-Claude-CODE--claude-worktrees-practical-wozniak-2c8c43/"
    "8c61ea94-4c0c-4978-8331-2180c91d80f3/tool-results/"
    "mcp-0369958f-f223-46b0-93c3-0b4cbcaa563b-list_campaigns-1779373018854.txt"
)

# Analytics captured 2026-05-21 from get_campaign_analytics. Re-pull if stale.
ANALYTICS = [
    {"id": "30726ceb-4b94-49a9-8f56-0a25ba8d42b9", "leads": 10508, "sent": 19559, "new": 10327, "replies": 262, "bounces": 217, "opps": 39},
    {"id": "7bebafac-88a7-46cc-ad9c-b5238ece9620", "leads": 8910, "sent": 17303, "new": 8881, "replies": 113, "bounces": 210, "opps": 13},
    {"id": "f8e7baac-da1e-41a2-84f2-43a6680d395f", "leads": 14641, "sent": 11060, "new": 11060, "replies": 192, "bounces": 176, "opps": 43},
    {"id": "c009dc73-fa57-4052-98ca-56bcac1da9e3", "leads": 8949, "sent": 9543, "new": 5148, "replies": 37, "bounces": 76, "opps": 4},
    {"id": "f0e0060b-04c4-4721-871d-ac353bf41f44", "leads": 3197, "sent": 5093, "new": 2828, "replies": 23, "bounces": 38, "opps": 5},
    {"id": "feda211d-8f47-473c-9565-1f0b1c90b5d5", "leads": 4900, "sent": 4504, "new": 4504, "replies": 71, "bounces": 17, "opps": 9},
    {"id": "a4b1b9bd-ff69-4a7c-aa33-f6f4bc635157", "leads": 1761, "sent": 3464, "new": 1761, "replies": 131, "bounces": 2, "opps": 17},
    {"id": "3dc0e983-4cdf-4b0d-9143-da8e137cde03", "leads": 1687, "sent": 3323, "new": 1687, "replies": 112, "bounces": 7, "opps": 40},
    {"id": "40f4218d-2e16-4395-b339-c523e3783619", "leads": 805, "sent": 2239, "new": 806, "replies": 61, "bounces": 63, "opps": 20},
    {"id": "32595744-5686-4362-a01d-7cb50a0373aa", "leads": 713, "sent": 2149, "new": 745, "replies": 28, "bounces": 20, "opps": 4},
    {"id": "a739b74b-e95c-4394-83ea-8a91074660cb", "leads": 5131, "sent": 2127, "new": 2127, "replies": 23, "bounces": 7, "opps": 13},
    {"id": "5212c819-c15c-4435-a87d-11527f44ee95", "leads": 687, "sent": 2088, "new": 733, "replies": 24, "bounces": 24, "opps": 3},
    {"id": "a5c23725-2754-4062-a5c1-91331ccfb248", "leads": 678, "sent": 1997, "new": 704, "replies": 51, "bounces": 46, "opps": 10},
    {"id": "2b72ae98-b265-4474-a37a-c21a051691ae", "leads": 679, "sent": 1990, "new": 694, "replies": 43, "bounces": 35, "opps": 11},
    {"id": "5e4e9495-9fff-4ab6-a4e2-83610474eaab", "leads": 619, "sent": 1766, "new": 614, "replies": 40, "bounces": 23, "opps": 14},
    {"id": "565adc42-8d2a-4312-9642-d5791c3d8f7d", "leads": 1353, "sent": 1354, "new": 1354, "replies": 19, "bounces": 32, "opps": 9},
    {"id": "4c826ebd-e48a-4ee0-99e8-b13bff920f13", "leads": 1353, "sent": 1353, "new": 1353, "replies": 10, "bounces": 50, "opps": 3},
    {"id": "fcb652ae-f009-44db-811d-54ca3078d9a2", "leads": 467, "sent": 1236, "new": 467, "replies": 7, "bounces": 76, "opps": 0},
    {"id": "f8baee1f-ce50-451e-b093-d9e67a756f9d", "leads": 469, "sent": 1213, "new": 469, "replies": 1, "bounces": 104, "opps": 0},
    {"id": "6528d2e0-b9d2-4a82-bfdd-aee7c3a82872", "leads": 373, "sent": 1031, "new": 368, "replies": 45, "bounces": 18, "opps": 12},
    {"id": "0ca03a86-f310-486f-8ce1-2a5afe6f4358", "leads": 534, "sent": 1030, "new": 530, "replies": 13, "bounces": 22, "opps": 0},
    {"id": "39769b9f-7321-4e41-ae28-5c7cf3ce063c", "leads": 472, "sent": 912, "new": 469, "replies": 14, "bounces": 25, "opps": 3},
    {"id": "5513fa48-759e-4f2d-a6e7-f84b08801500", "leads": 320, "sent": 636, "new": 320, "replies": 9, "bounces": 5, "opps": 0},
    {"id": "2f79025f-2876-48a7-bbfe-791defd74cab", "leads": 298, "sent": 584, "new": 296, "replies": 10, "bounces": 3, "opps": 1},
    {"id": "9baf39b6-7ba2-4422-be0b-919417df2ed5", "leads": 255, "sent": 255, "new": 255, "replies": 6, "bounces": 0, "opps": 6},
    {"id": "75521278-3138-420f-ac3a-824b85df6298", "leads": 163, "sent": 163, "new": 163, "replies": 4, "bounces": 3, "opps": 1},
    {"id": "1cd637f1-680c-49b3-a0f9-5e41ff5ad727", "leads": 145, "sent": 145, "new": 145, "replies": 1, "bounces": 1, "opps": 1},
    {"id": "8b9a7694-5878-44c8-9d99-8579a045e742", "leads": 145, "sent": 145, "new": 145, "replies": 0, "bounces": 1, "opps": 1},
    {"id": "1015a124-5ea6-49c8-8dc7-2029d143539c", "leads": 73, "sent": 73, "new": 73, "replies": 6, "bounces": 1, "opps": 6},
    {"id": "5c0fb714-af96-41b1-b50a-5f85b893c68d", "leads": 1, "sent": 73, "new": 73, "replies": 7, "bounces": 2, "opps": 6},
]


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def count_words(s):
    return len(re.findall(r"\w+", s or ""))


def find_vars(s):
    return sorted(set(re.findall(r"\{\{([^}]+)\}\}", s or "")))


def derive_brand(name):
    """Brand-tag a campaign from its name."""
    if name.startswith("FS-") or name.startswith("FS:"):
        return "FS"
    if name.startswith("CS:") or name.startswith("CS-"):
        return "CS"
    if name.startswith("Buyer:"):
        return "BUYER"
    if "HCAOA" in name or "FLHC" in name or "MUFC" in name or "Exit Summit" in name:
        return "EVENT"
    if "Biz Advisor" in name:
        return "ADVISOR"
    if "Franchise Testing" in name:
        return "FS"
    return "OTHER"


def main():
    with open(CAMPAIGNS_DUMP, "r", encoding="utf-8") as f:
        outer = json.load(f)
    campaigns = json.loads(outer["result"])["items"]

    by_id = {a["id"]: a for a in ANALYTICS}

    records = []
    for c in campaigns:
        cid = c["id"]
        name = c["name"]
        if cid not in by_id:
            continue
        a = by_id[cid]

        seqs = c.get("sequences") or [{}]
        steps = seqs[0].get("steps", []) if seqs else []
        n_steps = len(steps)
        delays = [s.get("delay") for s in steps]

        subjects_per_step = []
        bodies_per_step = []
        for s in steps:
            subs, bods = [], []
            for v in s.get("variants", []):
                subs.append(v.get("subject", ""))
                bods.append(strip_html(v.get("body", "")))
            subjects_per_step.append(subs)
            bodies_per_step.append(bods)

        all_bodies = [b for step in bodies_per_step for b in step]
        all_subjects = [s for step in subjects_per_step for s in step]

        avg_body_words = (
            sum(count_words(b) for b in all_bodies) / max(len(all_bodies), 1)
        )
        all_vars = set()
        for s in all_subjects + all_bodies:
            all_vars.update(find_vars(s))

        new = a["new"]
        sent = a["sent"]
        rep = a["replies"]
        bnc = a["bounces"]

        rec = {
            "name": name,
            "brand": derive_brand(name),
            "leads": a["leads"],
            "sent": sent,
            "new": new,
            "replies": rep,
            "bounces": bnc,
            "bounce_rate_pct": round((bnc / sent * 100) if sent else 0, 2),
            "reply_rate_per_contact_pct": round((rep / new * 100) if new else 0, 2),
            "reply_rate_per_send_pct": round((rep / sent * 100) if sent else 0, 2),
            "opps": a["opps"],
            "n_steps": n_steps,
            "delays": delays,
            "n_variants_step1": len(subjects_per_step[0]) if subjects_per_step else 0,
            "subjects_step1": subjects_per_step[0] if subjects_per_step else [],
            "subjects_all": all_subjects,
            "avg_body_words": round(avg_body_words, 1),
            "spin_vars": sorted(all_vars),
            "body_step1_v1": bodies_per_step[0][0] if bodies_per_step and bodies_per_step[0] else "",
            "bodies_all": all_bodies,
        }
        records.append(rec)

    records.sort(key=lambda r: -r["reply_rate_per_contact_pct"])

    out_dir = "/tmp/instantly-retro"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    # Stdout table
    print(f"Analyzed {len(records)} campaigns")
    print()
    hdr = f"{'NAME':<42} {'BR':<5} {'SENT':>6} {'NEW':>5} {'REP':>4} {'BNC%':>5} {'%CONT':>6} {'STEPS':>5} {'WORDS':>5} {'V1':>3} {'OPPS':>4}"
    print(hdr)
    print("-" * len(hdr))
    for r in records:
        if r["sent"] < 50:
            continue
        print(
            f"{r['name'][:40]:<42} {r['brand']:<5} {r['sent']:>6} {r['new']:>5} {r['replies']:>4} "
            f"{r['bounce_rate_pct']:>5} {r['reply_rate_per_contact_pct']:>5}% {r['n_steps']:>5} "
            f"{r['avg_body_words']:>5.0f} {r['n_variants_step1']:>3} {r['opps']:>4}"
        )


if __name__ == "__main__":
    main()
