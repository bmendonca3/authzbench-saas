from __future__ import annotations

import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path

from authzbench.run import run_benchmark


ROOT = Path(__file__).resolve().parents[1]


class RunnerTests(unittest.TestCase):
    def test_scripted_baseline_scores_all_public_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_benchmark(
                [str(ROOT / "tasks" / "*" / "*.json")],
                "python3 scripts/scripted_baseline_agent.py",
                Path(tmp),
                timeout_seconds=10,
            )
            self.assertEqual(summary["task_count"], 54, summary)
            self.assertEqual(summary["benchmark_version"], "alpha-0.0.1-public-scaffold-local", summary)
            self.assertEqual(summary["benchmark_fingerprint"]["schema_version"], "benchmark-fingerprint-v1", summary)
            self.assertEqual(summary["benchmark_fingerprint"]["score_policy_version"], "score-policy-v1", summary)
            self.assertEqual(summary["benchmark_fingerprint"]["scorer_contract"], "v0-candidate-authz-evidence", summary)
            self.assertEqual(summary["benchmark_fingerprint"]["task_count"], 54, summary)
            self.assertEqual(summary["benchmark_fingerprint"]["vulnerable_task_count"], 21, summary)
            self.assertEqual(summary["benchmark_fingerprint"]["control_task_count"], 33, summary)
            self.assertRegex(summary["benchmark_fingerprint"]["task_set_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(summary["benchmark_fingerprint"]["task_path_set_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(summary["passed_count"], 54, summary)
            self.assertEqual(summary["mean_score"], 1.0, summary)
            self.assertEqual(summary["v0_metric_profile"], "v0-candidate-authz-evidence", summary)
            self.assertEqual(summary["v0_passed_count"], 54, summary)
            self.assertEqual(summary["v0_mean_score"], 1.0, summary)
            self.assertEqual(summary["invalid_submission_count"], 0, summary)
            self.assertEqual(summary["invalid_submission_rate"], 0.0, summary)
            self.assertEqual(summary["vulnerable_task_count"], 21, summary)
            self.assertEqual(summary["control_task_count"], 33, summary)
            self.assertEqual(summary["denial_control_task_count"], 19, summary)
            self.assertEqual(summary["authorized_allow_control_task_count"], 14, summary)
            self.assertEqual(summary["exploit_proven_task_count"], 21, summary)
            self.assertEqual(summary["exploit_proven_success_rate"], 1.0, summary)
            self.assertEqual(summary["vulnerable_full_pass_count"], 21, summary)
            self.assertEqual(summary["boundary_reasoning_pass_rate"], 1.0, summary)
            self.assertEqual(summary["vulnerable_safety_pass_rate"], 1.0, summary)
            self.assertEqual(summary["control_false_report_count"], 0, summary)
            self.assertEqual(summary["control_false_report_rate"], 0.0, summary)
            self.assertEqual(summary["scored_submission_finding_total"], 21, summary)
            self.assertEqual(summary["submitted_finding_total"], 0, summary)
            self.assertEqual(summary["control_execution_pass_rate"], 1.0, summary)
            self.assertEqual(summary["false_positive_rate"], 0.0, summary)
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
            self.assertEqual(summary["false_positive_rate"], 1.0, summary)
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
            self.assertEqual(summary["submitted_finding_total"], 0, summary)
            self.assertEqual(summary["control_execution_pass_rate"], 1.0, summary)
            self.assertEqual(summary["false_positive_rate"], 1.0, summary)
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
        self.assertEqual(summary["executed_tool_probe_total"], 0, summary)
        self.assertEqual(summary["planner_failure_count"], 0, summary)


if __name__ == "__main__":
    unittest.main()
