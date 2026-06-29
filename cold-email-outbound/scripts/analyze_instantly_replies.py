"""Process all paginated `list_emails` dumps; classify cold replies; report patterns.

Reads every list_emails-*.txt file from the Claude tool-results dump dir,
dedupes, filters to from==lead (actual prospect emails), keeps first email
per lead chronologically, classifies into intent categories, produces
per-campaign breakdown.

Output: /tmp/instantly-retro/classified_replies.json + stdout report.
"""
import json, os, re
from collections import Counter, defaultdict

TOOL_DUMPS = (
    "C:/Users/theod/.claude/projects/"
    "C--Users-theod-OneDrive-Desktop-Claude-MASTER-Claude-CODE--claude-worktrees-practical-wozniak-2c8c43/"
    "8c61ea94-4c0c-4978-8331-2180c91d80f3/tool-results"
)

CAMPAIGN_NAMES = {
    "6528d2e0-b9d2-4a82-bfdd-aee7c3a82872": "Buyer: UT & CO Breweries",
    "5c0fb714-af96-41b1-b50a-5f85b893c68d": "FLHC Pre Event 2025",
    "1015a124-5ea6-49c8-8dc7-2029d143539c": "FLHC Post Event 2025",
    "40f4218d-2e16-4395-b339-c523e3783619": "FS-Education-Code Ninja",
    "a4b1b9bd-ff69-4a7c-aa33-f6f4bc635157": "FS-New Franchise-Existing-NO",
    "a5c23725-2754-4062-a5c1-91331ccfb248": "FS-Senior Care-FirstLight",
    "3dc0e983-4cdf-4b0d-9143-da8e137cde03": "FS-New Franchise-Existing-YES",
    "5e4e9495-9fff-4ab6-a4e2-83610474eaab": "Buyer: FL Wind Mitigation",
    "2b72ae98-b265-4474-a37a-c21a051691ae": "FS-Senior Care-Comfort Keepers",
    "32595744-5686-4362-a01d-7cb50a0373aa": "FS-F&B-Ben & Jerry",
    "2f79025f-2876-48a7-bbfe-791defd74cab": "CS: Home Health (Weekly)",
    "5212c819-c15c-4435-a87d-11527f44ee95": "FS-F&B-Nekter",
    "39769b9f-7321-4e41-ae28-5c7cf3ce063c": "CS: Automotive 2-10",
    "5513fa48-759e-4f2d-a6e7-f84b08801500": "CS: Auto Weekly",
    "30726ceb-4b94-49a9-8f56-0a25ba8d42b9": "CS: Consumer Services",
    "75521278-3138-420f-ac3a-824b85df6298": "Post MUFC 2025 - Zor",
    "0ca03a86-f310-486f-8ce1-2a5afe6f4358": "CS: Automotive 11-50",
    "9baf39b6-7ba2-4422-be0b-919417df2ed5": "Post MUFC 2025 - Zee",
    "f8e7baac-da1e-41a2-84f2-43a6680d395f": "Franchise Testing",
    "feda211d-8f47-473c-9565-1f0b1c90b5d5": "Biz Advisor Testing",
    "fcb652ae-f009-44db-811d-54ca3078d9a2": "FS-Auto-1-800 Radiator",
    "565adc42-8d2a-4312-9642-d5791c3d8f7d": "HCAOA Blast - Franchise",
    "7bebafac-88a7-46cc-ad9c-b5238ece9620": "CS: H&W&F 2-10",
    "a739b74b-e95c-4394-83ea-8a91074660cb": "Exit Summit Pre 2025",
    "f0e0060b-04c4-4721-871d-ac353bf41f44": "CS: H&W&F 11-50",
    "4c826ebd-e48a-4ee0-99e8-b13bff920f13": "HCAOA Oct Franchise",
    "c009dc73-fa57-4052-98ca-56bcac1da9e3": "CS: F&B 1-50",
    "1cd637f1-680c-49b3-a0f9-5e41ff5ad727": "HCAOA Oct Private",
    "f8baee1f-ce50-451e-b093-d9e67a756f9d": "FS-Auto-Maaco",
    "8b9a7694-5878-44c8-9d99-8579a045e742": "HCAOA Blast - Private",
}


def classify(it):
    subj = (it.get("subject", "") or "").lower().strip()
    prev = (it.get("content_preview", "") or "").lower().strip()
    text = subj + " " + prev

    if "out of office" in text or "on vacation" in text or "on leave" in text or "returning" in subj or "i'll be out" in text:
        return "out_of_office"
    if "undeliverable" in text or "delivery failed" in text or "delivery has failed" in text:
        return "bounce_notice"
    if "unsubscribe" in text or "remove me" in text or "take me off" in text or "opt me out" in text:
        return "unsubscribe"
    if (
        re.search(r"\bno (thanks?|thank you)\b", text)
        or "not interested" in text
        or "no interest" in text
        or "not at this time" in text
        or "not for sale" in text
        or re.search(r"^no\b\.?$", prev[:30])
        or re.search(r"^not\b", prev[:20])
        or subj in ("no", "no.", "no thanks", "no thank you")
    ):
        return "objection_not_interested"
    if "not the right" in text or "wrong person" in text or "no longer with" in text or "don't own" in text or "don't work" in text:
        return "wrong_person"
    if "not right now" in text or "maybe later" in text or "in a few years" in text or "not ready" in text or "down the road" in text or "too early" in text or "end of 2026" in text or "touch base with me" in text:
        return "objection_not_now"
    if "accepted" in subj and ("meeting" in subj or "call" in subj or "discovery" in subj or "discussion" in subj):
        return "meeting_accepted"
    if (
        "would like to learn" in text
        or "tell me more" in text
        or "interested in selling" in text
        or "i would be interested" in text
        or "send me" in text
        or "sounds good" in text
        or "let's talk" in text
        or "let's chat" in text
        or "love to" in text
        or "happy to" in text
        or "curious" in text
        or re.search(r"\byes\b", prev[:30])
        or "absolutely" in text
    ):
        return "positive"
    if "how much" in text or "what does it cost" in text or "what is your" in text or "what does this" in text or "tell me about" in text or "what does all this mean" in text:
        return "information_request"
    return "other"


def main():
    list_files = sorted([f for f in os.listdir(TOOL_DUMPS) if "list_emails" in f])
    all_items = []
    for fn in list_files:
        with open(os.path.join(TOOL_DUMPS, fn), "r", encoding="utf-8") as f:
            try:
                data = json.loads(json.load(f)["result"])
                all_items.extend(data["items"])
            except Exception as e:
                print(f"  err {fn}: {e}")
    print(f"Loaded {len(all_items)} email records from {len(list_files)} pagination dumps")

    seen_ids = set()
    deduped = []
    for it in all_items:
        eid = it.get("id")
        if eid not in seen_ids:
            seen_ids.add(eid)
            deduped.append(it)
    print(f"After id-dedup: {len(deduped)}")

    from_lead = [it for it in deduped if it.get("from_address_email") == it.get("lead")]
    print(f"From-lead (actual prospect emails): {len(from_lead)}")

    by_lead = defaultdict(list)
    for it in from_lead:
        by_lead[it.get("lead")].append(it)

    first_replies = []
    for lead, msgs in by_lead.items():
        msgs.sort(key=lambda m: m.get("timestamp_email", ""))
        first_replies.append(msgs[0])
    print(f"Unique replying prospects (deduped to first email per lead): {len(first_replies)}")

    for it in first_replies:
        it["_class"] = classify(it)
        it["_campaign_name"] = CAMPAIGN_NAMES.get(it.get("campaign_id"), "OTHER/" + (it.get("campaign_id") or "none")[:8])

    cats = Counter(it["_class"] for it in first_replies)
    total = sum(cats.values())
    print()
    print(f"=== Classification — {total} unique prospect replies ===")
    for cat, n in cats.most_common():
        print(f"  {n:4} ({n / total * 100:5.1f}%) {cat}")

    print()
    print("=== Reply mix by campaign (top 20) ===")
    camp_classes = defaultdict(Counter)
    for it in first_replies:
        camp_classes[it["_campaign_name"]][it["_class"]] += 1
    camp_totals = {n: sum(c.values()) for n, c in camp_classes.items()}

    cols = ["positive", "objection_not_interested", "objection_not_now", "unsubscribe", "meeting_accepted", "out_of_office", "wrong_person", "information_request", "other"]
    print(f"{'CAMPAIGN':<32} {'TOT':>4} " + " ".join(f"{c[:5]:>5}" for c in cols))
    for cname, ctotal in sorted(camp_totals.items(), key=lambda x: -x[1])[:20]:
        classes = camp_classes[cname]
        row = f"{cname[:30]:<32} {ctotal:>4} "
        for c in cols:
            row += f"{classes.get(c, 0):>5} "
        print(row)

    out_dir = "/tmp/instantly-retro"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "classified_replies.json"), "w", encoding="utf-8") as f:
        json.dump(first_replies, f, indent=2)


if __name__ == "__main__":
    main()
