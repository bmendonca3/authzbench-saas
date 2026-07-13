from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from authzbench.run import _adapter_failure_type, run_benchmark


ROOT = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def test_adapter_failure_classification_does_not_require_parse_error_text(self) -> None:
        cases = (
            ({"returncode": 9}, "command_failure"),
            ({"adapter_metadata_invalid": True}, "adapter_metadata_failure"),
            ({}, "adapter_metadata_failure"),
            ({"returncode": None}, "adapter_metadata_failure"),
            ({"returncode": False}, "adapter_metadata_failure"),
            ({"returncode": 0, "model_label_verified": False}, "model_label_failure"),
            ({"returncode": 0, "parse_error": "invalid JSON"}, "output_parse_failure"),
            ({"returncode": 0}, None),
        )
        for model_output, expected in cases:
            with self.subTest(model_output=model_output):
                self.assertEqual(_adapter_failure_type(model_output), expected)

    def test_scripted_baseline_scores_all_public_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_benchmark(
                [str(ROOT / "tasks" / "*" / "*.json")],
                "python3 scripts/scripted_baseline_agent.py",
                Path(tmp),
                timeout_seconds=10,
            )
            self.assertEqual(summary["task_count"], 63, summary)
            self.assertEqual(summary["benchmark_version"], "alpha-0.0.1-public-scaffold-local", summary)
            self.assertEqual(summary["benchmark_fingerprint"]["schema_version"], "benchmark-fingerprint-v1", summary)
            self.assertEqual(
                summary["benchmark_fingerprint"]["score_policy_version"],
                "score-policy-v2-boundary-normalization",
                summary,
            )
            self.assertEqual(summary["benchmark_fingerprint"]["scorer_contract"], "v0-candidate-authz-evidence", summary)
            self.assertEqual(summary["benchmark_fingerprint"]["task_count"], 63, summary)
            self.assertEqual(summary["benchmark_fingerprint"]["vulnerable_task_count"], 27, summary)
            self.assertEqual(summary["benchmark_fingerprint"]["control_task_count"], 36, summary)
            self.assertRegex(summary["benchmark_fingerprint"]["task_set_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(summary["benchmark_fingerprint"]["task_path_set_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(summary["passed_count"], 63, summary)
            self.assertEqual(summary["mean_score"], 1.0, summary)
            self.assertEqual(summary["v0_metric_profile"], "v0-candidate-authz-evidence", summary)
            self.assertEqual(summary["v0_passed_count"], 63, summary)
            self.assertEqual(summary["v0_mean_score"], 1.0, summary)
            self.assertEqual(summary["invalid_submission_count"], 0, summary)
            self.assertEqual(summary["invalid_submission_rate"], 0.0, summary)
            self.assertEqual(summary["vulnerable_task_count"], 27, summary)
            self.assertEqual(summary["control_task_count"], 36, summary)
            self.assertEqual(summary["denial_control_task_count"], 21, summary)
            self.assertEqual(summary["authorized_allow_control_task_count"], 15, summary)
            self.assertEqual(summary["exploit_proven_task_count"], 27, summary)
            self.assertEqual(summary["exploit_proven_success_rate"], 1.0, summary)
            self.assertEqual(summary["vulnerable_full_pass_count"], 27, summary)
            self.assertEqual(summary["boundary_reasoning_pass_rate"], 1.0, summary)
            self.assertEqual(summary["vulnerable_safety_pass_rate"], 1.0, summary)
            self.assertEqual(summary["control_false_report_count"], 0, summary)
            self.assertEqual(summary["control_false_report_rate"], 0.0, summary)
            self.assertEqual(summary["scored_submission_finding_total"], 27, summary)
            self.assertIsNone(summary["submitted_finding_total"], summary)
            self.assertEqual(summary["tool_probe_telemetry_status"], "unobserved", summary)
            self.assertEqual(summary["tool_probe_telemetry_complete_task_count"], 0, summary)
            self.assertEqual(summary["tool_probe_telemetry_coverage_rate"], 0.0, summary)
            self.assertIsNone(summary["executed_tool_probe_total"], summary)
            self.assertEqual(summary["control_execution_pass_rate"], 1.0, summary)
            self.assertEqual(summary["false_positive_rate"], 0.0, summary)
            self.assertEqual(summary["control_failure_rate"], 0.0, summary)
            self.assertEqual(summary["authorized_allow_pass_rate"], 1.0, summary)
            self.assertIsNone(summary["target_request_correlated_task_count"], summary)
            self.assertIsNone(summary["target_request_coverage_rate"], summary)
            self.assertEqual(summary["tasks"][0]["invalid_submission"], False, summary["tasks"][0])
            self.assertEqual(summary["tasks"][0]["submission_finding_count"], 1, summary["tasks"][0])
            self.assertEqual(summary["tasks"][0]["control_replay_passed"], True, summary["tasks"][0])
            self.assertIn("exploit_proof", summary["tasks"][0])
            self.assertTrue(Path(summary["run_dir"], "summary.json").exists())
            transcript = Path(summary["run_dir"], "pm_bola_read_alpha_from_beta", "transcript.json")
            self.assertTrue(transcript.exists())
            self.assertIn('"name": "proof"', transcript.read_text(encoding="utf-8"))

    def test_secure_control_execution_failure_is_separate_from_false_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_task = ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json"
            task = json.loads(source_task.read_text(encoding="utf-8"))
            task["id"] = "bill_secure_member_plan_control_broken_replay_unit"
            for control in task["controls"]:
                control["status"] = 418
            task_path = tmp_path / "broken_control.json"
            task_path.write_text(json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            summary = run_benchmark(
                [str(task_path)],
                "python3 scripts/scripted_baseline_agent.py",
                tmp_path / "results",
                timeout_seconds=10,
            )

            self.assertEqual(summary["passed_count"], 0, summary)
            self.assertEqual(summary["control_false_report_count"], 0, summary)
            self.assertEqual(summary["control_false_report_rate"], 0.0, summary)
            self.assertEqual(summary["control_execution_pass_rate"], 0.0, summary)
            self.assertEqual(summary["false_positive_rate"], 0.0, summary)
            self.assertEqual(summary["control_failure_rate"], 1.0, summary)
            self.assertEqual(summary["v0_mean_score"], 0.0, summary)
            self.assertEqual(summary["tasks"][0]["submission_finding_count"], 0, summary["tasks"][0])
            self.assertEqual(summary["tasks"][0]["control_replay_passed"], False, summary["tasks"][0])

    def test_vulnerable_control_replay_failure_blocks_v0_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_task = ROOT / "tasks" / "project_mgmt" / "pm_bola_read_alpha_from_beta.json"
            task = json.loads(source_task.read_text(encoding="utf-8"))
            for control in task["controls"]:
                control["status"] = 418
            task_path = tmp_path / "broken_vulnerable_control.json"
            task_path.write_text(json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            summary = run_benchmark(
                [str(task_path)],
                "python3 scripts/scripted_baseline_agent.py",
                tmp_path / "results",
                timeout_seconds=10,
            )

            self.assertEqual(summary["passed_count"], 0, summary)
            self.assertEqual(summary["exploit_proven_success_rate"], 1.0, summary)
            self.assertEqual(summary["boundary_reasoning_pass_rate"], 1.0, summary)
            self.assertEqual(summary["v0_passed_count"], 0, summary)
            self.assertEqual(summary["v0_mean_score"], 0.0, summary)
            self.assertEqual(summary["tasks"][0]["control_replay_passed"], False, summary["tasks"][0])

    def test_secure_control_false_report_is_separate_from_control_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "false_report_agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    from __future__ import annotations

                    import json
                    import os
                    from pathlib import Path

                    submission = {
                        "findings": [
                            {
                                "claim": "incorrect_secure_control_report",
                                "boundary": {},
                                "evidence": [],
                                "out_of_scope_actions": [],
                            }
                        ]
                    }
                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps(submission, indent=2, sort_keys=True) + "\\n",
                        encoding="utf-8",
                    )
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                timeout_seconds=10,
            )

            self.assertEqual(summary["passed_count"], 0, summary)
            self.assertEqual(summary["control_false_report_count"], 1, summary)
            self.assertEqual(summary["control_false_report_rate"], 1.0, summary)
            self.assertEqual(summary["scored_submission_finding_total"], 1, summary)
            self.assertIsNone(summary["submitted_finding_total"], summary)
            self.assertEqual(summary["control_execution_pass_rate"], 1.0, summary)
            self.assertEqual(summary["false_positive_rate"], 1.0, summary)
            self.assertEqual(summary["control_failure_rate"], 1.0, summary)
            self.assertEqual(summary["v0_mean_score"], 0.0, summary)
            self.assertEqual(summary["tasks"][0]["submission_finding_count"], 1, summary["tasks"][0])
            self.assertEqual(summary["tasks"][0]["control_replay_passed"], True, summary["tasks"][0])

    def test_invalid_submission_has_own_summary_metric(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "invalid_submission_agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    from __future__ import annotations

                    import json
                    import os
                    from pathlib import Path

                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps({"findings": "not-a-list"}, indent=2, sort_keys=True) + "\\n",
                        encoding="utf-8",
                    )
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                timeout_seconds=10,
            )

            self.assertEqual(summary["passed_count"], 0, summary)
            self.assertEqual(summary["invalid_submission_count"], 1, summary)
            self.assertEqual(summary["invalid_submission_rate"], 1.0, summary)
            self.assertEqual(summary["control_false_report_count"], 0, summary)
            self.assertEqual(summary["control_false_report_rate"], 0.0, summary)
            self.assertEqual(summary["tasks"][0]["invalid_submission"], True, summary["tasks"][0])

    def test_nonzero_agent_exit_cannot_score_a_written_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "write_then_fail_agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    from __future__ import annotations

                    import json
                    import os
                    from pathlib import Path

                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps({"findings": []}),
                        encoding="utf-8",
                    )
                    raise SystemExit(7)
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                timeout_seconds=10,
            )
            score = json.loads(
                Path(summary["run_dir"], "bill_secure_member_plan_control", "score.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(summary["passed_count"], 0, summary)
        self.assertEqual(summary["invalid_submission_count"], 1, summary)
        self.assertEqual(summary["false_positive_rate"], 0.0, summary)
        self.assertEqual(summary["control_failure_rate"], 1.0, summary)
        self.assertEqual(summary["tasks"][0]["agent_returncode"], 7, summary)
        self.assertEqual(score["score"], 0, score)
        self.assertIn("return code 7", score["reason"])

    def test_agent_timeout_bytes_are_preserved_as_text_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            timeout = subprocess.TimeoutExpired(
                cmd=["agent"],
                timeout=1,
                output=b"partial output",
                stderr=b"timeout error",
            )
            with patch("authzbench.run._run_agent", side_effect=timeout):
                summary = run_benchmark(
                    [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                    "unused-agent",
                    Path(tmp),
                    timeout_seconds=1,
                )
            agent = json.loads(
                Path(summary["run_dir"], "bill_secure_member_plan_control", "agent.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(summary["passed_count"], 0, summary)
        self.assertEqual(summary["runner_agent_failure_count"], 1, summary)
        self.assertEqual(agent["stdout"], "partial output")
        self.assertIn("timeout error", agent["stderr"])

    def test_adapter_failure_metadata_cannot_score_empty_findings_as_abstention(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "fail_open_adapter.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    from __future__ import annotations

                    import json
                    import os
                    from pathlib import Path

                    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission_path.write_text(json.dumps({"findings": []}), encoding="utf-8")
                    (submission_path.parent / "model-output.json").write_text(
                        json.dumps(
                            {
                                "returncode": 0,
                                "parse_error": "model output did not contain a JSON object",
                            }
                        ),
                        encoding="utf-8",
                    )
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                timeout_seconds=10,
            )

        self.assertEqual(summary["passed_count"], 0, summary)
        self.assertEqual(summary["invalid_submission_count"], 1, summary)
        self.assertEqual(summary["adapter_failure_count"], 1, summary)
        self.assertEqual(summary["adapter_output_parse_failure_count"], 1, summary)
        self.assertEqual(summary["infrastructure_failure_count"], 0, summary)
        self.assertEqual(summary["false_positive_rate"], 0.0, summary)
        self.assertEqual(summary["control_failure_rate"], 1.0, summary)
        self.assertEqual(summary["tasks"][0]["adapter_failure_type"], "output_parse_failure", summary)

    def test_malformed_model_output_metadata_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "malformed_adapter_metadata.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    submission = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission.write_text(json.dumps({"findings": []}), encoding="utf-8")
                    (submission.parent / "model-output.json").write_text("{", encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                timeout_seconds=10,
            )

        self.assertEqual(summary["passed_count"], 0, summary)
        self.assertEqual(summary["adapter_output_parse_failure_count"], 0, summary)
        self.assertEqual(summary["adapter_metadata_failure_count"], 1, summary)
        self.assertEqual(summary["infrastructure_failure_count"], 1, summary)
        self.assertEqual(summary["false_positive_rate"], 0.0, summary)

    def test_incomplete_model_output_metadata_fails_closed(self) -> None:
        for label, metadata in (("empty", {}), ("null-returncode", {"returncode": None})):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                agent_path = tmp_path / "incomplete_adapter_metadata.py"
                agent_path.write_text(
                    textwrap.dedent(
                        f"""
                        import json
                        import os
                        from pathlib import Path

                        submission = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                        submission.write_text(json.dumps({{"findings": []}}), encoding="utf-8")
                        (submission.parent / "model-output.json").write_text(
                            json.dumps({metadata!r}), encoding="utf-8"
                        )
                        """
                    ),
                    encoding="utf-8",
                )

                summary = run_benchmark(
                    [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                    f"python3 {agent_path}",
                    tmp_path / "results",
                    timeout_seconds=10,
                )

            self.assertEqual(summary["passed_count"], 0, summary)
            self.assertEqual(summary["invalid_submission_count"], 1, summary)
            self.assertEqual(summary["adapter_failure_count"], 1, summary)
            self.assertEqual(summary["adapter_metadata_failure_count"], 1, summary)
            self.assertEqual(summary["infrastructure_failure_count"], 1, summary)
            self.assertEqual(
                summary["tasks"][0]["adapter_failure_type"],
                "adapter_metadata_failure",
                summary,
            )

    def test_malformed_submission_json_uses_stable_result_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "malformed_submission.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import os
                    from pathlib import Path

                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text("{", encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                timeout_seconds=10,
            )
            score = json.loads(
                Path(summary["run_dir"], "bill_secure_member_plan_control", "score.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertTrue(score["invalid_submission"], score)
        self.assertIn("claim_present", score)
        self.assertIn("transcript", score)
        self.assertIn("scoring failed", score["reason"])

    def test_runner_records_leaderboard_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_benchmark(
                [str(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")],
                "python3 scripts/scripted_baseline_agent.py",
                Path(tmp),
                timeout_seconds=10,
                benchmark_version="alpha-test",
                benchmark_commit_sha="abc123",
                agent="scripted_baseline_agent",
                model="deterministic-script",
                harness_type="scripted",
            )
            self.assertEqual(summary["benchmark_version"], "alpha-test")
            self.assertEqual(summary["benchmark_commit_sha"], "abc123")
            self.assertEqual(summary["agent"], "scripted_baseline_agent")
            self.assertEqual(summary["model"], "deterministic-script")
            self.assertEqual(summary["harness_type"], "scripted")
            written = Path(summary["run_dir"], "summary.json").read_text(encoding="utf-8")
            self.assertIn('"benchmark_version": "alpha-test"', written)
            self.assertIn('"benchmark_commit_sha": "abc123"', written)
            self.assertIn('"benchmark_fingerprint"', written)

    def test_runner_rejects_unsafe_task_or_run_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json"
            task = json.loads(source.read_text(encoding="utf-8"))
            task["id"] = "../escaped-task"
            task_path = tmp_path / "unsafe-task.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "task id must be a safe single path component"):
                run_benchmark([str(task_path)], "unused", tmp_path / "results", timeout_seconds=1)
            with self.assertRaisesRegex(ValueError, "run_id must be a safe single path component"):
                run_benchmark(
                    [str(source)],
                    "unused",
                    tmp_path / "results",
                    timeout_seconds=1,
                    run_id="../escaped-run",
                )

    def test_runner_rejects_duplicate_tasks_and_nonempty_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json"
            task = source.read_text(encoding="utf-8")
            first = tmp_path / "first.json"
            second = tmp_path / "second.json"
            first.write_text(task, encoding="utf-8")
            second.write_text(task, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate task id"):
                run_benchmark(
                    [str(first), str(second)],
                    "unused",
                    tmp_path / "results",
                    timeout_seconds=1,
                )

            existing = tmp_path / "results" / "existing-run"
            existing.mkdir(parents=True)
            (existing / "evidence.txt").write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                run_benchmark(
                    [str(source)],
                    "unused",
                    tmp_path / "results",
                    timeout_seconds=1,
                    run_id="existing-run",
                )

    def test_fingerprint_is_stable_when_called_from_another_cwd(self) -> None:
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root_summary = run_benchmark(
                [str(ROOT / "tasks" / "project_mgmt" / "pm_bola_read_alpha_from_beta.json")],
                "python3 scripts/scripted_baseline_agent.py",
                tmp_path / "root-results",
                timeout_seconds=10,
            )
            try:
                os.chdir(tmp_path)
                summary = run_benchmark(
                    [str(ROOT / "tasks" / "project_mgmt" / "pm_bola_read_alpha_from_beta.json")],
                    "python3 scripts/scripted_baseline_agent.py",
                    tmp_path / "results",
                    timeout_seconds=10,
                )
            finally:
                os.chdir(original_cwd)

        self.assertEqual(summary["passed_count"], 1, summary)
        self.assertEqual(summary["benchmark_fingerprint"], root_summary["benchmark_fingerprint"])
        self.assertEqual(summary["tasks"][0]["agent_returncode"], 0, summary["tasks"][0])

    def test_runner_summarizes_tool_agent_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "tool_agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    from __future__ import annotations

                    import json
                    import os
                    from pathlib import Path

                    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    submission_path.write_text(json.dumps({"findings": []}))
                    (submission_path.parent / "model-tool-plan.json").write_text(
                        json.dumps({"metadata": {"returncode": 7, "parse_error": "bad planner json"}, "plan": {"probes": []}})
                    )
                    (submission_path.parent / "tool-probes.json").write_text(
                        json.dumps(
                            {
                                "probe_count": 2,
                                "fallback_probe_count": 1,
                                "submitted_finding_count": 1,
                            }
                        )
                    )
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                timeout_seconds=10,
                agent="test_tool_agent",
                model="test-model",
                harness_type="tool-agent",
            )

        self.assertEqual(summary["model_tool_plan_artifact_count"], 1, summary)
        self.assertEqual(summary["per_task_tool_probe_artifact_count"], 1, summary)
        self.assertEqual(summary["executed_tool_probe_total"], 2, summary)
        self.assertEqual(summary["fallback_probe_total"], 1, summary)
        self.assertEqual(summary["submitted_finding_total"], 1, summary)
        self.assertEqual(summary["tool_probe_telemetry_status"], "complete", summary)
        self.assertEqual(summary["tool_probe_telemetry_complete_task_count"], 1, summary)
        self.assertEqual(summary["tool_probe_telemetry_coverage_rate"], 1.0, summary)
        self.assertEqual(summary["scored_submission_finding_total"], 0, summary)
        self.assertEqual(summary["planner_failure_count"], 1, summary)
        self.assertEqual(summary["planner_parse_error_count"], 1, summary)
        self.assertTrue(summary["tasks"][0]["model_tool_plan_artifact"], summary["tasks"][0])
        self.assertTrue(summary["tasks"][0]["tool_probe_artifact"], summary["tasks"][0])
        self.assertEqual(summary["tasks"][0]["executed_probe_count"], 2, summary["tasks"][0])
        self.assertEqual(summary["tasks"][0]["planner_returncode"], 7, summary["tasks"][0])
        self.assertEqual(summary["tasks"][0]["planner_parse_error"], "bad planner json", summary["tasks"][0])

    def test_runner_ignores_malformed_optional_tool_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "tool_agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    from __future__ import annotations

                    import json
                    import os
                    from pathlib import Path

                    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    submission_path.write_text(json.dumps({"findings": []}))
                    (submission_path.parent / "model-tool-plan.json").write_text("{not-json")
                    (submission_path.parent / "tool-probes.json").write_text("{also-not-json")
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                timeout_seconds=10,
                agent="test_tool_agent",
                model="test-model",
                harness_type="tool-agent",
            )

        self.assertEqual(summary["model_tool_plan_artifact_count"], 0, summary)
        self.assertEqual(summary["per_task_tool_probe_artifact_count"], 0, summary)
        self.assertIsNone(summary["executed_tool_probe_total"], summary)
        self.assertEqual(summary["tool_probe_telemetry_status"], "unobserved", summary)
        self.assertEqual(summary["planner_failure_count"], 0, summary)


if __name__ == "__main__":
    unittest.main()
