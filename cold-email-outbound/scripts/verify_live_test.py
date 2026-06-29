"""Live verification diagnostic — confirm LeadMagic + ZeroBounce keys/endpoints work.

Run with dry-run OFF for THIS PROCESS ONLY (env override; .env stays true):
    CEO_DRY_RUN=false python3 cold-email-outbound/scripts/verify_live_test.py diag
    CEO_DRY_RUN=false python3 cold-email-outbound/scripts/verify_live_test.py batch 20

  diag       — 1 LeadMagic + 1 ZeroBounce call, prints RAW responses (2 credits)
  batch N    — verify N real Tier A contacts through the waterfall

Spends real credits. Prints raw JSON so we can fix verdict-normalization if a
provider's response shape differs from what engine/verification.py assumes.
"""
import sys
import json

# Import after a hard check that we're intentionally live
sys.path.insert(0, "C:/Users/theod/OneDrive/Desktop/Claude MASTER/Claude CODE/.claude/worktrees/practical-wozniak-2c8c43/cold-email-outbound")

from engine import config, data_layer, verification


def diag():
    print(config.status_banner())
    assert not config.DRY_RUN, "Run with CEO_DRY_RUN=false to test live."
    # Pick 2 real emails from CS Tier A
    contacts = data_layer.load_tier_a("CS", limit=2)
    e1 = contacts[0].email_norm
    e2 = contacts[1].email_norm if len(contacts) > 1 else e1

    print(f"\n--- LeadMagic raw (email={e1}) ---")
    try:
        raw = verification._verify_leadmagic_live(e1)
        print(json.dumps(raw, indent=2)[:1500])
        print("normalized verdict:", verification._normalize_verdict("leadmagic", raw))
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

    print(f"\n--- ZeroBounce raw (email={e2}) ---")
    try:
        raw = verification._verify_zerobounce_live(e2)
        print(json.dumps(raw, indent=2)[:1500])
        print("normalized verdict:", verification._normalize_verdict("zerobounce", raw))
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")


def batch(n: int):
    print(config.status_banner())
    assert not config.DRY_RUN, "Run with CEO_DRY_RUN=false to test live."
    contacts = data_layer.load_tier_a("CS", limit=n)
    v = verification.Verifier()
    v.verify_batch(contacts)
    print(f"\n{'EMAIL':<45} {'VERDICT':<16}")
    print("-" * 62)
    from collections import Counter
    verdicts = Counter()
    for c in contacts:
        verdicts[c.verification_status] += 1
        print(f"{c.email_norm[:43]:<45} {c.verification_status:<16}")
    print("-" * 62)
    print("verdict distribution:", dict(verdicts))
    print("provider usage:", v.stats())
    deliv, dead = verification.split_deliverable(contacts)
    print(f"deliverable={len(deliv)} dead={len(dead)} ({len(deliv)/max(len(contacts),1)*100:.0f}% deliverable)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "diag"
    if mode == "diag":
        diag()
    elif mode == "batch":
        batch(int(sys.argv[2]) if len(sys.argv) > 2 else 20)
