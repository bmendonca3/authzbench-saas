"""Tests for baseline variance reporting helpers."""

from __future__ import annotations

import unittest

from scripts.analyze_baseline_variance import _agreement_rate, _per_task_verdicts


class BaselineVarianceAnalysisTests(unittest.TestCase):
    def test_per_task_verdicts_reads_passed_field(self) -> None:
        summary = {
            "tasks": [
                {"task_id": "task_a", "passed": True},
                {"task_id": "task_b", "passed": False},
                {"task_id": "missing_verdict"},
                {"task_id": "", "passed": True},
            ]
        }

        self.assertEqual(_per_task_verdicts(summary), {"task_a": True, "task_b": False})

    def test_agreement_rate_counts_changed_verdicts(self) -> None:
        agreement = _agreement_rate(
            [
                {"task_a": True, "task_b": False, "task_c": True},
                {"task_a": True, "task_b": True, "task_c": True},
            ]
        )

        self.assertEqual(
            agreement,
            {
                "task_count": 3,
                "agreement_rate": 0.6667,
                "changed_verdict_count": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
