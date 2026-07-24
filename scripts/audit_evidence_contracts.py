"""Audit explicit vulnerable-task evidence-contract coverage without activating v2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.protocol_contracts import audit_evidence_contracts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "patterns",
        nargs="*",
        default=None,
        help="Task manifest glob(s); defaults to tasks/**/*.json.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit 1 unless every vulnerable task has a valid explicit evidence contract.",
    )
    parser.add_argument("--json", action="store_true", help="Print the complete audit result.")
    args = parser.parse_args()

    if args.require_complete and args.patterns:
        print(
            "--require-complete audits the canonical repository task set and does not accept custom patterns",
            file=sys.stderr,
        )
        return 2

    patterns = args.patterns or [str(ROOT / "tasks/**/*.json")]
    result = audit_evidence_contracts(
        patterns,
        expected_task_count=63 if args.require_complete else None,
        expected_vulnerable_task_count=27 if args.require_complete else None,
        required_task_root=(ROOT / "tasks") if args.patterns is None else None,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "evidence contract coverage: "
            f"{result['covered_vulnerable_task_count']}/{result['vulnerable_task_count']} "
            f"({result['coverage_rate']:.4f})"
        )
        print(f"schema_bundle_sha256: {result['schema_bundle']['canonical_sha256']}")
        print(f"contract_status: {result['contract_status']}")
        if result["missing_task_ids"]:
            print("missing task ids: " + ", ".join(result["missing_task_ids"]))
        for finding in result["findings"]:
            if finding["code"] != "evidence_contract_missing":
                print(
                    f"{finding['code']}: {finding['path']}: {finding['detail']}",
                    file=sys.stderr,
                )

    if not result["valid"]:
        return 2
    if args.require_complete and not result["complete"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
