from __future__ import annotations

import tempfile
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
            self.assertEqual(summary["task_count"], 37, summary)
            self.assertEqual(summary["benchmark_version"], "alpha-0.0.1-public-scaffold-local", summary)
            self.assertEqual(summary["passed_count"], 37, summary)
            self.assertEqual(summary["mean_score"], 1.0, summary)
            self.assertEqual(summary["vulnerable_task_count"], 15, summary)
            self.assertEqual(summary["control_task_count"], 22, summary)
            self.assertEqual(summary["denial_control_task_count"], 15, summary)
            self.assertEqual(summary["authorized_allow_control_task_count"], 7, summary)
            self.assertEqual(summary["exploit_proven_success_rate"], 1.0, summary)
            self.assertEqual(summary["false_positive_rate"], 0.0, summary)
            self.assertEqual(summary["authorized_allow_pass_rate"], 1.0, summary)
            self.assertTrue(Path(summary["run_dir"], "summary.json").exists())
            transcript = Path(summary["run_dir"], "pm_bola_read_alpha_from_beta", "transcript.json")
            self.assertTrue(transcript.exists())
            self.assertIn('"name": "proof"', transcript.read_text(encoding="utf-8"))

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


if __name__ == "__main__":
    unittest.main()
