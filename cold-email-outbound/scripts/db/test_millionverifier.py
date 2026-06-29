"""Live smoke test for the MillionVerifier provider (a few real pool emails + a
fake one). Confirms the API responds and the verdict normalization is correct.
Costs a few MillionVerifier credits.

    .venv/bin/python scripts/db/test_millionverifier.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine import verification, data_layer, config  # noqa: E402


def main() -> int:
    print("verification mode:", config.VERIFICATION["mode"])
    emails = [c.email_norm for c in data_layer.load_tier_a("CS", limit=4) if c.email_norm][:2]
    emails.append("definitely-not-real-zzz12345@gmail.com")
    for e in emails:
        raw = verification._verify_millionverifier_live(e)
        verdict = verification._normalize_verdict("millionverifier", raw)
        print(f"  {e:45s} result={raw.get('result','?'):10s} -> {verdict:14s} "
              f"(credits left: {raw.get('credits', '?')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
