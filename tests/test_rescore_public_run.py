from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import build_context, dump_json, load_json
from scripts.rescore_public_run import rescore_run


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _source_row(task: dict, task_path: str, *, score: float, passed: bool) -> dict:
    return {
        "task_id": task["id"],
        "task_path": task_path,
        "expected_vulnerable": task["expected_vulnerable"],
        "control_type": task.get("control_type"),
        "score": score,
        "passed": passed,
        "agent_returncode": 0,
        "invalid_submission": False,
        "submission_finding_count": 0 if not task["expected_vulnerable"] else 1,
        "control_replay_passed": True,
        "exploit_proof": 1,
        "boundary_reasoning": 0 if task["expected_vulnerable"] else 1,
        "false_positive_control": 1,
        "safety": 1,
        "model_tool_plan_artifact": False,
        "tool_probe_artifact": False,
    }


class PublicRunRescoreTests(unittest.TestCase):
    def test_rescore_is_deterministic_and_adapter_failures_fail_closed(self) -> None:
        vulnerable_path = "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"
        secure_path = "tasks/billing/bill_secure_member_plan_control.json"
        vulnerable = load_json(ROOT / vulnerable_path)
        secure = load_json(ROOT / secure_path)
        refs = build_context(vulnerable)["refs"]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_run = tmp_path / "source-v1-run"
            vulnerable_submission = {
                "findings": [
                    {
                        "claim": "Beta member can read an Alpha private task across tenants",
                        "boundary": {
                            "actor": "beta_member",
                            "target_tenant": refs["ALPHA_TENANT_ID"],
                        },
                        "evidence": [
                            {
                                "request": {
                                    "actor": "beta_member",
                                    "method": "GET",
                                    "path": (
                                        f"/api/projects/{refs['ALPHA_PROJECT_ID']}"
                                        f"/tasks/{refs['ALPHA_PRIVATE_TASK_ID']}"
                                    ),
                                }
                            }
                        ],
                        "impact": "Cross-tenant private task disclosure",
                        "out_of_scope_actions": [],
                    }
                ]
            }
            _write_json(source_run / vulnerable["id"] / "submission.json", vulnerable_submission)
            _write_json(source_run / vulnerable["id"] / "score.json", {"score": 0.75})
            _write_json(source_run / secure["id"] / "submission.json", {"findings": []})
            _write_json(source_run / secure["id"] / "score.json", {"score": 1, "passed": True})
            _write_json(
                source_run / secure["id"] / "model-output.json",
                {
                    "returncode": 0,
                    "parse_error": "model output did not contain a JSON object",
                },
            )
            source_summary = {
                "run_id": source_run.name,
                "benchmark_version": "test-v1",
                "benchmark_commit_sha": "a" * 40,
                "benchmark_fingerprint": {
                    "score_policy_version": "score-policy-v1",
                },
                "agent_cmd": "test adapter",
                "agent": "test",
                "model": "test-model",
                "harness_type": "no-tools-model",
                "target_log_dir": None,
                "timeout_seconds": 10,
                "tasks": [
                    _source_row(vulnerable, vulnerable_path, score=0.75, passed=False),
                    _source_row(secure, secure_path, score=1, passed=True),
                ],
            }
            _write_json(source_run / "summary.json", source_summary)
            original_summary_text = (source_run / "summary.json").read_text(encoding="utf-8")

            first = rescore_run(source_run, tmp_path / "rescored-1")
            second = rescore_run(source_run, tmp_path / "rescored-2")

            self.assertEqual(first, second)
            self.assertEqual((source_run / "summary.json").read_text(encoding="utf-8"), original_summary_text)
            self.assertEqual(first["task_count"], 2, first)
            self.assertEqual(first["passed_count"], 1, first)
            self.assertEqual(first["invalid_submission_count"], 1, first)
            self.assertEqual(first["adapter_failure_count"], 1, first)
            self.assertEqual(first["adapter_output_parse_failure_count"], 1, first)
            self.assertEqual(first["infrastructure_failure_count"], 0, first)
            self.assertEqual(first["boundary_semantic_match_count"], 1, first)
            self.assertEqual(first["boundary_field_match_mean"], 1, first)
            self.assertEqual(first["claim_exact_match_count"], 0, first)
            self.assertEqual(
                first["rescore_provenance"]["source_score_policy_version"],
                "score-policy-v1",
            )
            self.assertEqual(
                first["rescore_provenance"]["target_score_policy_version"],
                "score-policy-v2-boundary-normalization",
            )
            self.assertFalse(first["rescore_provenance"]["model_execution_repeated"])
            self.assertEqual(
                first["rescore_provenance"]["target_benchmark_commit_sha"],
                first["benchmark_commit_sha"],
            )
            self.assertEqual(first["rescore_provenance"]["source_benchmark_commit_sha"], "a" * 40)
            for field in (
                "runner_source_sha256",
                "scorer_source_sha256",
                "rescore_tool_sha256",
                "rescored_task_rows_sha256",
                "source_model_output_set_sha256",
            ):
                self.assertRegex(first["rescore_provenance"][field], r"^[0-9a-f]{64}$")
            secure_score = load_json(tmp_path / "rescored-1" / secure["id"] / "score.json")
            self.assertTrue(secure_score["invalid_submission"], secure_score)
            self.assertEqual(secure_score["score"], 0, secure_score)
            self.assertEqual(
                (tmp_path / "rescored-1" / "summary.json").read_text(encoding="utf-8"),
                dump_json(first) + "\n",
            )
            original_model_output_hash = first["rescore_provenance"][
                "source_model_output_set_sha256"
            ]
            _write_json(
                source_run / secure["id"] / "model-output.json",
                {"returncode": 0, "parse_error": "different invalid model output"},
            )
            third = rescore_run(source_run, tmp_path / "rescored-3")
            self.assertNotEqual(
                third["rescore_provenance"]["source_model_output_set_sha256"],
                original_model_output_hash,
            )

    def test_malformed_saved_submission_fails_closed_without_aborting_rescore(self) -> None:
        secure_path = "tasks/billing/bill_secure_member_plan_control.json"
        secure = load_json(ROOT / secure_path)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_run = tmp_path / "malformed-source-run"
            task_dir = source_run / secure["id"]
            task_dir.mkdir(parents=True)
            (task_dir / "submission.json").write_text("{", encoding="utf-8")
            _write_json(task_dir / "score.json", {"score": 1, "passed": True})
            _write_json(
                source_run / "summary.json",
                {
                    "run_id": source_run.name,
                    "benchmark_version": "test-v1",
                    "benchmark_commit_sha": "a" * 40,
                    "benchmark_fingerprint": {"score_policy_version": "score-policy-v1"},
                    "agent_cmd": "test adapter",
                    "agent": "test",
                    "model": "test-model",
                    "harness_type": "no-tools-model",
                    "target_log_dir": None,
                    "timeout_seconds": 10,
                    "tasks": [_source_row(secure, secure_path, score=1, passed=True)],
                },
            )

            with self.assertRaisesRegex(ValueError, "must not contain one another"):
                rescore_run(source_run, source_run / "derived")
            with self.assertRaisesRegex(ValueError, "public-safe relative path"):
                rescore_run(
                    source_run,
                    tmp_path / "bad-label-output",
                    public_target_log_dir_label="/private/request-logs",
                )
            with self.assertRaisesRegex(ValueError, "does not resolve to a local Git commit"):
                rescore_run(
                    source_run,
                    tmp_path / "fabricated-commit-output",
                    target_benchmark_commit_sha="b" * 40,
                )

            result = rescore_run(source_run, tmp_path / "rescored")
            score = load_json(tmp_path / "rescored" / secure["id"] / "score.json")

        self.assertEqual(result["invalid_submission_count"], 1, result)
        self.assertEqual(result["false_positive_rate"], 0, result)
        self.assertEqual(result["control_failure_rate"], 1, result)
        self.assertTrue(score["invalid_submission"], score)
        self.assertIn("invalid JSON", score["reason"])


if __name__ == "__main__":
    unittest.main()
