from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.validate_harbor_local_evidence import (
    DEFAULT_EVIDENCE_PATH,
    _source_fingerprint_errors,
    validate_harbor_local_evidence,
)


def valid_evidence() -> dict:
    return {
        "schema_version": "harbor-local-execution-smoke-v1",
        "evidence_status": "local_harbor_execution_smoke",
        "public_claim_boundary": "Local smoke only; not parity evidence and not v1 readiness.",
        "benchmark_source_sha": "abc123456789",
        "benchmark_source_tree_sha": "0de5f10d307299e0c3ddb6ce1642c7061538c5d6",
        "harbor_command": "uvx harbor",
        "harbor_version": "0.13.1",
        "docker_server_version": "29.5.2",
        "run_command_template": "cd <generated-public-dataset> && harbor run -c run_authzbench_saas.yaml --yes --debug",
        "task_ids": ["pm_same_tenant_read_control"],
        "task_count": 1,
        "harness_lane": "no_tools",
        "oracle_solution_mode": "secure-control-empty-findings",
        "harbor_execution_verified": True,
        "parity_verified": False,
        "scorer_reward_parity_verified": True,
        "native_score_summary": {
            "submission_shape": "secure_control_empty_findings",
            "score": 1.0,
            "passed": True,
            "control_replay_passed": True,
        },
        "public_outputs_redacted": True,
        "private_artifacts_tracked": False,
        "raw_harbor_jobs_tracked": False,
        "expected_reward_reason": "Secure-control empty-findings smoke; not full adapter parity.",
        "blocked_until": [
            "adapter writes valid submissions",
            "parity experiment is computed",
        ],
        "harbor_run_id": "00000000-0000-0000-0000-000000000000",
        "n_total_trials": 1,
        "n_completed_trials": 1,
        "n_errored_trials": 0,
        "reward_mean": 1.0,
        "verifier_reward_files": ["reward.json", "reward.txt"],
    }


class HarborLocalEvidenceTests(unittest.TestCase):
    def write_and_validate(self, payload: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return validate_harbor_local_evidence(path)

    def test_accepts_public_safe_smoke_evidence(self) -> None:
        result = self.write_and_validate(valid_evidence())
        self.assertTrue(result["passed"], result)

    def test_checked_in_smoke_is_source_bound_historical(self) -> None:
        result = validate_harbor_local_evidence(DEFAULT_EVIDENCE_PATH)

        self.assertTrue(result["passed"], result)
        payload = json.loads(DEFAULT_EVIDENCE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["evidence_status"],
            "historical_source_bound_smoke",
        )
        self.assertFalse(payload["current_claim_eligible"])
        self.assertTrue(payload["requires_rerun_before_current_claim"])

    def test_rejects_parity_overclaim(self) -> None:
        payload = valid_evidence()
        payload["parity_verified"] = True
        result = self.write_and_validate(payload)
        self.assertFalse(result["passed"])
        self.assertIn("parity_verified must be false", result["errors"])

    def test_rejects_local_absolute_path(self) -> None:
        payload = valid_evidence()
        payload["run_command_template"] = "/tmp/private/path/run"
        result = self.write_and_validate(payload)
        self.assertFalse(result["passed"])
        self.assertTrue(any("local absolute path" in error for error in result["errors"]), result)

    def test_rejects_missing_run_identity(self) -> None:
        payload = valid_evidence()
        del payload["harbor_run_id"]
        result = self.write_and_validate(payload)
        self.assertFalse(result["passed"])
        self.assertIn("harbor_run_id is required", result["errors"])

    def test_rejects_missing_total_trial_count(self) -> None:
        payload = valid_evidence()
        payload["n_total_trials"] = None
        result = self.write_and_validate(payload)
        self.assertFalse(result["passed"])
        self.assertIn("n_total_trials must be 1", result["errors"])

    def test_rejects_missing_scorer_reward_parity(self) -> None:
        payload = valid_evidence()
        payload["scorer_reward_parity_verified"] = False
        result = self.write_and_validate(payload)
        self.assertFalse(result["passed"])
        self.assertIn("scorer_reward_parity_verified must be true for the secure-control smoke", result["errors"])

    def test_rejects_missing_checked_in_source_tree(self) -> None:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        errors = _source_fingerprint_errors(DEFAULT_EVIDENCE_PATH, head, "f" * 40)
        self.assertIn("benchmark_source_tree_sha must exist in this repository for checked-in smoke evidence", errors)

    def test_rejects_checked_in_source_tree_mismatch(self) -> None:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        head_tree = subprocess.check_output(["git", "rev-parse", f"{head}^{{tree}}"], text=True).strip()
        log_output = subprocess.check_output(["git", "rev-list", "--max-count=50", "HEAD"], text=True)
        mismatched_tree = None
        for commit in log_output.splitlines():
            candidate_tree = subprocess.check_output(["git", "rev-parse", f"{commit}^{{tree}}"], text=True).strip()
            if candidate_tree != head_tree:
                mismatched_tree = candidate_tree
                break
        if mismatched_tree is None:
            self.skipTest("repository history does not contain a tree distinct from HEAD")

        errors = _source_fingerprint_errors(DEFAULT_EVIDENCE_PATH, head, mismatched_tree)

        self.assertIn("benchmark_source_tree_sha must match benchmark_source_sha tree for checked-in smoke evidence", errors)


if __name__ == "__main__":
    unittest.main()
