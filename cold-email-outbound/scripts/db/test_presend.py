"""Test the CAN-SPAM footer render + domain allow-list + pre-send gate.

    .venv/bin/python scripts/db/test_presend.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine import config, data_layer, presend  # noqa: E402
from engine.copy_gen import parse_template, render  # noqa: E402


def main() -> int:
    c = data_layer.load_tier_a("FS", limit=1)[0]
    tpl = parse_template(config.TEMPLATES_DIR / "seller_cold_fs_niche.md")
    body, _ = render(tpl["steps"][0]["body"], c, "FS")
    print("=== rendered email 1 (tail) ===")
    print(body[-260:])
    print("address present:", config.COMPLIANCE["mailing_address"] in body)

    print("\n=== cold-sending domain allow-list ===")
    for e in ["jay@companysellergroup.com", "david@franchisesellers.com",
              "theo@companysellers.co", "info@reply.franchisesellers.com",
              "sales@companysellers.com", "madison@thecompaniesseller.com"]:
        print(f"  {e:40s} cold_approved={presend.is_cold_approved(e)}")

    print("\n=== pre-send gate ===")
    g = presend.check_gate(stream="seller_cold_fs_niche", sample_body=body,
                           copy_approved=True, icp_confirmed=True)
    print("ok:", g["ok"], "| skipped:", g["skipped"])
    for ch in g["checks"]:
        mark = "OK  " if ch["pass"] else ("SKIP" if ch["pass"] is None else "FAIL")
        print(f"  [{mark}] {ch['check']:24s} {('· ' + ch['detail']) if ch['detail'] else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
