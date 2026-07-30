from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from authzbench.run import run_benchmark


ROOT = Path(__file__).resolve().parents[1]


class RunnerRequestLogTests(unittest.TestCase):
    def test_runner_correlates_target_logs_per_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target_log_dir = tmp_path / "request-logs"
            target_log_dir.mkdir(parents=True, exist_ok=True)
            stale_entry = {
                "app": "project_mgmt",
                "run_id": "unit-run",
                "task_id": "pm_bola_read_alpha_from_beta",
                "agent_id": "target_logging_agent",
                "seed": "public-v0-001",
                "actor": "beta_member",
                "method": "GET",
                "path": "/stale-matching-entry",
                "status": 200,
                "response_body_sha256": "0" * 64,
            }
            (target_log_dir / "project_mgmt.jsonl").write_text(
                json.dumps(stale_entry, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            agent_path = tmp_path / "target_logging_agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    f"""
                    from __future__ import annotations

                    import json
                    import os
                    import sys
                    from pathlib import Path

                    sys.path.insert(0, os.getcwd())
                    target_log_dir = Path({str(target_log_dir)!r})

                    from scripts.scripted_baseline_agent import solve

                    assert "AUTHZBENCH_TARGET_LOG_DIR" not in os.environ
                    context = json.loads(Path(os.environ["AUTHZBENCH_CONTEXT"]).read_text(encoding="utf-8"))
                    submission = solve(context)
                    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    submission_path.write_text(
                        json.dumps(submission, indent=2, sort_keys=True) + "\\n",
                        encoding="utf-8",
                    )

                    target_log_dir.mkdir(parents=True, exist_ok=True)
                    log_path = target_log_dir / f"{{context['app']}}.jsonl"
                    entries = [
                        {{
                            "app": context["app"],
                            "run_id": "different-run",
                            "task_id": context["task_id"],
                            "agent_id": os.environ["AUTHZBENCH_AGENT_ID"],
                            "seed": context["seed"],
                            "actor": "beta_member",
                            "method": "GET",
                            "path": "/ignored",
                            "status": 200,
                            "response_body_sha256": "0" * 64,
                        }},
                        {{
                            "app": context["app"],
                            "run_id": os.environ["AUTHZBENCH_RUN_ID"],
                            "task_id": os.environ["AUTHZBENCH_TASK_ID"],
                            "agent_id": os.environ["AUTHZBENCH_AGENT_ID"],
                            "seed": context["seed"],
                            "actor": "beta_member",
                            "method": "GET",
                            "path": "/api/projects/proof/tasks/proof",
                            "status": 200,
                            "response_body_sha256": "1" * 64,
                        }},
                        {{
                            "app": "billing",
                            "run_id": os.environ["AUTHZBENCH_RUN_ID"],
                            "task_id": os.environ["AUTHZBENCH_TASK_ID"],
                            "agent_id": os.environ["AUTHZBENCH_AGENT_ID"],
                            "seed": context["seed"],
                            "actor": "beta_member",
                            "method": "GET",
                            "path": "/wrong-app",
                            "status": 200,
                            "response_body_sha256": "3" * 64,
                        }},
                    ]
                    with log_path.open("a", encoding="utf-8") as fh:
                        for entry in entries:
                            fh.write(json.dumps(entry, sort_keys=True) + "\\n")
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                10,
                benchmark_commit_sha=None,
                agent="target_logging_agent",
                model="unit-test",
                harness_type="unit",
                target_log_dir=target_log_dir,
                run_id="unit-run",
            )

            self.assertEqual(summary["passed_count"], 1)
            self.assertEqual(summary["target_log_dir"], str(target_log_dir))
            self.assertEqual(summary["target_request_correlated_task_count"], 1)
            self.assertEqual(summary["target_request_coverage_rate"], 1.0)
            self.assertEqual(summary["tasks"][0]["target_request_count"], 1)
            self.assertNotIn("target_request_warning", summary["tasks"][0])

            artifact = Path(summary["run_dir"]) / "pm_bola_read_alpha_from_beta" / "target-requests.jsonl"
            entries = [json.loads(line) for line in artifact.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["run_id"], "unit-run")
            self.assertEqual(entries[0]["task_id"], "pm_bola_read_alpha_from_beta")
            self.assertEqual(entries[0]["agent_id"], "target_logging_agent")
            self.assertEqual(entries[0]["path"], "/api/projects/proof/tasks/proof")
            self.assertEqual(entries[0]["correlation"]["matched_on"], ["run_id", "task_id", "agent_id"])

    def test_runner_warns_when_target_log_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "submission_only_agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    from __future__ import annotations

                    import json
                    import os
                    import sys
                    from pathlib import Path

                    sys.path.insert(0, os.getcwd())

                    from scripts.scripted_baseline_agent import solve

                    assert "AUTHZBENCH_TARGET_LOG_DIR" not in os.environ
                    context = json.loads(Path(os.environ["AUTHZBENCH_CONTEXT"]).read_text(encoding="utf-8"))
                    submission = solve(context)
                    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission_path.parent.mkdir(parents=True, exist_ok=True)
                    submission_path.write_text(
                        json.dumps(submission, indent=2, sort_keys=True) + "\\n",
                        encoding="utf-8",
                    )
                    """
                ),
                encoding="utf-8",
            )

            summary = run_benchmark(
                [str(ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json")],
                f"python3 {agent_path}",
                tmp_path / "results",
                10,
                benchmark_commit_sha=None,
                agent="submission_only_agent",
                model="unit-test",
                harness_type="unit",
                target_log_dir=tmp_path / "missing-request-logs",
                run_id="missing-log-run",
            )

            self.assertEqual(summary["passed_count"], 1)
            self.assertEqual(summary["target_request_correlated_task_count"], 0)
            self.assertEqual(summary["target_request_coverage_rate"], 0.0)
            self.assertEqual(summary["tasks"][0]["target_request_count"], 0)
            self.assertEqual(summary["tasks"][0]["target_request_warning"], "target_log_missing")

            artifact = Path(summary["run_dir"]) / "pm_bola_read_alpha_from_beta" / "target-requests.jsonl"
            self.assertEqual(artifact.read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
