from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import SCORE_POLICY_VERSION, dump_json, load_json


LEGACY_STATUS = "stale_after_score_policy_v3"


def _is_legacy(data: dict[str, Any]) -> bool:
    fingerprint = data.get("benchmark_fingerprint")
    return (
        isinstance(fingerprint, dict)
        and fingerprint.get("score_policy_version") != SCORE_POLICY_VERSION
    )


def migrate(root: Path = ROOT, *, write: bool = False) -> dict[str, Any]:
    row_paths = sorted((root / "leaderboard_submissions").glob("*/*.leaderboard.json"))
    source_paths = sorted((root / "leaderboard_sources").glob("*.json"))
    changed_paths: list[str] = []
    legacy_row_count = 0
    legacy_source_count = 0
    for path, kind in (
        *((path, "row") for path in row_paths),
        *((path, "source") for path in source_paths),
    ):
        data = load_json(path)
        if not isinstance(data, dict) or not _is_legacy(data):
            continue
        if kind == "row":
            legacy_row_count += 1
            data["leaderboard_eligible"] = False
        else:
            legacy_source_count += 1
        data["evidence_status"] = LEGACY_STATUS
        data["requires_rerun_before_current_comparison"] = True
        rendered = dump_json(data) + "\n"
        if path.read_text(encoding="utf-8") == rendered:
            continue
        changed_paths.append(path.relative_to(root).as_posix())
        if write:
            path.write_text(rendered, encoding="utf-8")
    return {
        "passed": not changed_paths,
        "write": write,
        "legacy_row_count": legacy_row_count,
        "legacy_source_count": legacy_source_count,
        "changed_paths": changed_paths,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mark every pre-v3 leaderboard row and source summary stale."
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = migrate(write=args.write)
    print(dump_json(result))
    return 0 if args.write or result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
