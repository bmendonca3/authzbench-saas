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
            self.assertEqual(summary["task_count"], 15, summary)
            self.assertEqual(summary["passed_count"], 15, summary)
            self.assertEqual(summary["mean_score"], 1.0, summary)
            self.assertEqual(summary["vulnerable_task_count"], 6, summary)
            self.assertEqual(summary["control_task_count"], 9, summary)
            self.assertEqual(summary["exploit_proven_success_rate"], 1.0, summary)
            self.assertEqual(summary["false_positive_rate"], 0.0, summary)
            self.assertTrue(Path(summary["run_dir"], "summary.json").exists())
            transcript = Path(summary["run_dir"], "pm_bola_read_alpha_from_beta", "transcript.json")
            self.assertTrue(transcript.exists())
            self.assertIn('"name": "proof"', transcript.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
