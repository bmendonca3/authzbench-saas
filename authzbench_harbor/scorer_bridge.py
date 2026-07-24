"""Scorer bridge: runs AuthZBench scoring and emits Harbor-compatible reward output.

Wraps authzbench.score.score_submission to translate AuthZBench scorer results
into Harbor verifier reward format.

Usage as module:
    python3 -m authzbench_harbor.scorer_bridge \\
        --task-file <path> \\
        --submission-file <path> \\
        --output <path>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json  # noqa: E402
from authzbench.score import score_submission  # noqa: E402
from authzbench_harbor.schemas import (  # noqa: E402
    SCORER_BRIDGE_OUTPUT_SCHEMA_VERSION,
    check_public_safety,
    validate_submission,
    validate_submission_against_task,
)


def run_scorer_bridge(
    task: dict[str, Any],
    submission: dict[str, Any],
) -> dict[str, Any]:
    """Score a submission against a task and return Harbor reward output.

    Returns a dict with:
      - reward: float (0.0 or 1.0)
      - score: float
      - passed: bool
      - authzbench: dict with scoring detail
      - schema_version: str
    """
    submission_errors = validate_submission(submission)
    if submission_errors:
        return {
            "schema_version": SCORER_BRIDGE_OUTPUT_SCHEMA_VERSION,
            "reward": 0.0,
            "score": 0.0,
            "passed": False,
            "invalid_submission": True,
            "authzbench": {
                "task_id": task.get("id"),
                "errors": submission_errors,
            },
        }

    task_id_errors = validate_submission_against_task(submission, task)
    if task_id_errors:
        return {
            "schema_version": SCORER_BRIDGE_OUTPUT_SCHEMA_VERSION,
            "reward": 0.0,
            "score": 0.0,
            "passed": False,
            "invalid_submission": True,
            "authzbench": {
                "task_id": task.get("id"),
                "errors": task_id_errors,
            },
        }

    try:
        score = score_submission(task, submission)
    except Exception as exc:
        return {
            "schema_version": SCORER_BRIDGE_OUTPUT_SCHEMA_VERSION,
            "reward": 0.0,
            "score": 0.0,
            "passed": False,
            "invalid_submission": True,
            "authzbench": {
                "task_id": task.get("id"),
                "errors": [f"scorer raised {type(exc).__name__}"],
            },
        }

    reward = float(score.get("score") or 0.0)
    expected_vulnerable = bool(task.get("expected_vulnerable"))
    findings = submission.get("findings", [])
    false_positive = bool(not expected_vulnerable and findings)
    exploit_proof_valid = bool(
        expected_vulnerable and score.get("subscores", {}).get("exploit_proof") == 1
    )
    boundary_pass = bool(score.get("subscores", {}).get("boundary_reasoning", 0) > 0)
    control_pass = score.get("control_replay_passed")

    output = {
        "schema_version": SCORER_BRIDGE_OUTPUT_SCHEMA_VERSION,
        "reward": reward,
        "score": reward,
        "passed": bool(score.get("passed")),
        "invalid_submission": bool(score.get("invalid_submission")),
        "authzbench": {
            "task_id": task.get("id"),
            "expected_vulnerable": expected_vulnerable,
            "exploit_proof_valid": exploit_proof_valid,
            "false_positive": false_positive,
            "invalid_submission": bool(score.get("invalid_submission")),
            "boundary_reasoning_pass": boundary_pass,
            "control_execution_pass": control_pass,
        },
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AuthZBench scoring and emit Harbor-compatible reward output."
    )
    parser.add_argument("--task-file", required=True, help="Path to task manifest JSON")
    parser.add_argument("--submission-file", required=True, help="Path to agent submission JSON")
    parser.add_argument("--output", required=True, help="Path to write scorer bridge output JSON")
    args = parser.parse_args()

    task_path = Path(args.task_file)
    submission_path = Path(args.submission_file)
    output_path = Path(args.output)

    if not task_path.is_file():
        print(f"ERROR: task file not found: {task_path}", file=sys.stderr)
        return 1
    if not submission_path.is_file():
        print(f"ERROR: submission file not found: {submission_path}", file=sys.stderr)
        return 1

    try:
        task = load_json(task_path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: failed to load task file: {exc}", file=sys.stderr)
        return 1

    try:
        submission = load_json(submission_path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: failed to load submission file (invalid JSON fails closed): {exc}", file=sys.stderr)
        return 1

    submission_text = json.dumps(submission)
    privacy_violations = check_public_safety(submission_text)
    if privacy_violations:
        print(f"ERROR: submission failed public-safety check: {privacy_violations}", file=sys.stderr)
        return 1

    result = run_scorer_bridge(task, submission)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dump_json(result) + "\n", encoding="utf-8")
    print(dump_json(result))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
