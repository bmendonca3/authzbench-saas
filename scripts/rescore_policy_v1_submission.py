from __future__ import annotations

import argparse
import json
from pathlib import Path

from authzbench.evidence_migration import build_rescore_artifact, validate_rescore_artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Create one digest-bound score-policy-v2 re-score artifact.")
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--source-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    artifact = build_rescore_artifact(
        task_path=args.task,
        submission_path=args.submission,
        source_summary_path=args.source_summary,
    )
    errors = validate_rescore_artifact(artifact)
    if errors:
        raise SystemExit("invalid re-score artifact: " + "; ".join(errors))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
