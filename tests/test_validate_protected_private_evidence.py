from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_protected_private_evidence import validate_protected_private_evidence


def _summary(run_id: str, *, harness_type: str = "no-tools-model", coverage: float | None = None) -> dict:
    data = {
        "agent": "agent",
        "authorized_allow_control_task_count": 6,
        "benchmark_commit_sha": "abc123",
        "benchmark_version": "test",
        "control_false_report_count": 0,
        "control_task_count": 12,
        "denial_control_task_count": 6,
        "full_result_bundle_tracked": False,
        "harness_type": harness_type,
        "invalid_submission_count": 0,
        "model": "model",
        "private_holdout_task_count": 24,
        "protected_execution": {
            "agent_cwd": "temporary-empty-workspace",
            "agent_received": "rendered-context-only",
            "private_manifests_readable_in_agent_workspace": False,
            "tracked_private_manifest_count": 0,
        },
        "public_task_count": 0,
        "raw_private_artifacts_tracked": False,
        "redacted_private_holdout_source": True,
        "run_count": 1,
        "run_id": run_id,
        "split": "private-holdout",
        "task_count": 24,
        "tracked_private_manifest_count": 0,
        "vulnerable_task_count": 12,
    }
    if coverage is not None:
        data["target_request_coverage_rate"] = coverage
    return data


class ProtectedPrivateEvidenceValidatorTests(unittest.TestCase):
    def test_accepts_repeated_redacted_evidence_with_tool_agent_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for name, data in {
                "run1.json": _summary("run-1"),
                "run2.json": _summary("run-2", harness_type="tool-agent", coverage=1.0),
            }.items():
                path = root / name
                path.write_text(json.dumps(data), encoding="utf-8")
                paths.append(path)

            result = validate_protected_private_evidence(paths)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["protected_private_run_count"], 2)
        self.assertEqual(result["tool_agent_summary_count"], 1)
        self.assertEqual(result["max_target_request_coverage_rate"], 1.0)

    def test_rejects_sensitive_rows_and_private_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = _summary("run-1", harness_type="tool-agent", coverage=1.0)
            bad["tasks"] = [{"task_id": "private_hidden"}]
            bad["note"] = "/Users/example/results/private"
            paths = []
            for name, data in {
                "bad.json": bad,
                "good.json": _summary("run-2", harness_type="tool-agent", coverage=1.0),
            }.items():
                path = root / name
                path.write_text(json.dumps(data), encoding="utf-8")
                paths.append(path)

            result = validate_protected_private_evidence(paths)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("sensitive key" in error for error in result["errors"]), result)
        self.assertTrue(any("sensitive path marker" in error for error in result["errors"]), result)

    def test_requires_unique_runs_and_tool_agent_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for name in ("run1.json", "run2.json"):
                path = root / name
                path.write_text(json.dumps(_summary("same-run")), encoding="utf-8")
                paths.append(path)

            result = validate_protected_private_evidence(paths)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("run_id values must be unique" in error for error in result["errors"]), result)
        self.assertTrue(any("tool-agent summary is required" in error for error in result["errors"]), result)


if __name__ == "__main__":
    unittest.main()
