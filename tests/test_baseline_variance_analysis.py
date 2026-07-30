"""Tests for baseline variance reporting helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.analyze_baseline_variance import (
    _agreement_rate,
    _all_capability_rows_stale_pending,
    _has_current_63_scripted_sanity,
    _is_stale_pending_rerun,
    _per_task_verdicts,
    analyze_registry,
    main,
)


class BaselineVarianceAnalysisTests(unittest.TestCase):
    def test_main_accepts_repo_relative_output_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            baselines = root / "baselines"
            baselines.mkdir()
            (baselines / "baseline-registry.json").write_text(
                '{"baselines": []}', encoding="utf-8"
            )
            argv = [
                "analyze_baseline_variance.py",
                "--root",
                str(root),
                "--json-output",
                "artifact/report.json",
                "--markdown-output",
                "docs/report.md",
            ]

            with mock.patch("sys.argv", argv):
                self.assertEqual(main(), 0)

            self.assertTrue((root / "artifact" / "report.json").is_file())
            self.assertTrue((root / "docs" / "report.md").is_file())

    def test_main_accepts_absolute_output_paths_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_root = Path(tmpdir)
            root = temp_root / "repo"
            baselines = root / "baselines"
            baselines.mkdir(parents=True)
            (baselines / "baseline-registry.json").write_text(
                '{"baselines": []}', encoding="utf-8"
            )
            json_output = temp_root / "outside-report.json"
            markdown_output = temp_root / "outside-report.md"
            argv = [
                "analyze_baseline_variance.py",
                "--root",
                str(root),
                "--json-output",
                str(json_output),
                "--markdown-output",
                str(markdown_output),
            ]

            with mock.patch("sys.argv", argv):
                self.assertEqual(main(), 0)

            self.assertTrue(json_output.is_file())
            self.assertTrue(markdown_output.is_file())

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


class StalePendingRerunTests(unittest.TestCase):
    """Tests for the --allow-stale-pending-rerun pass path."""

    def test_is_stale_pending_rerun_true_for_honest_stale_row(self) -> None:
        entry = {
            "kind": "model_baseline",
            "release_suitability": "current_public_stale",
            "requires_rerun_before_current_comparison": True,
            "leaderboard_eligible": False,
            "evidence_status": "stale_after_v1_1_public_split",
            "expected_task_count": 60,
        }
        self.assertTrue(_is_stale_pending_rerun(entry))

    def test_is_stale_pending_rerun_true_without_evidence_status(self) -> None:
        entry = {
            "kind": "tool_agent_baseline",
            "release_suitability": "legacy_snapshot",
            "requires_rerun_before_current_comparison": True,
            "leaderboard_eligible": False,
            "expected_task_count": 54,
        }
        self.assertTrue(_is_stale_pending_rerun(entry))

    def test_is_stale_pending_rerun_false_for_current_row(self) -> None:
        entry = {
            "kind": "model_baseline",
            "release_suitability": "current_public_split",
            "requires_rerun_before_current_comparison": False,
            "leaderboard_eligible": False,
            "expected_task_count": 63,
        }
        self.assertFalse(_is_stale_pending_rerun(entry))

    def test_is_stale_pending_rerun_false_for_leaderboard_eligible(self) -> None:
        entry = {
            "kind": "model_baseline",
            "release_suitability": "current_public_stale",
            "requires_rerun_before_current_comparison": True,
            "leaderboard_eligible": True,
            "expected_task_count": 60,
        }
        self.assertFalse(_is_stale_pending_rerun(entry))

    def test_is_stale_pending_rerun_true_for_stale_63_task_v2_row(self) -> None:
        entry = {
            "kind": "model_baseline",
            "release_suitability": "current_public_stale",
            "requires_rerun_before_current_comparison": True,
            "leaderboard_eligible": False,
            "expected_task_count": 63,
        }
        self.assertTrue(_is_stale_pending_rerun(entry))

    def test_is_stale_pending_rerun_false_for_non_capability_kind(self) -> None:
        entry = {
            "kind": "harness_check",
            "requires_rerun_before_current_comparison": True,
            "leaderboard_eligible": False,
            "expected_task_count": 60,
        }
        self.assertFalse(_is_stale_pending_rerun(entry))

    def test_has_current_63_scripted_sanity_true(self) -> None:
        registry = {"baselines": [
            {"release_suitability": "current_public_harness_check", "kind": "harness_check", "expected_harness_type": "scripted", "expected_task_count": 63, "requires_rerun_before_current_comparison": False},
        ]}
        self.assertTrue(_has_current_63_scripted_sanity(registry))

    def test_has_current_63_scripted_sanity_false_when_stale(self) -> None:
        registry = {"baselines": [
            {"release_suitability": "current_public_harness_check", "expected_task_count": 63, "requires_rerun_before_current_comparison": True},
        ]}
        self.assertFalse(_has_current_63_scripted_sanity(registry))

    def test_all_capability_rows_stale_pending_true(self) -> None:
        registry = {"baselines": [
            {"kind": "model_baseline", "release_suitability": "current_public_stale", "requires_rerun_before_current_comparison": True, "leaderboard_eligible": False, "expected_task_count": 60},
            {"kind": "tool_agent_baseline", "release_suitability": "legacy_snapshot", "requires_rerun_before_current_comparison": True, "leaderboard_eligible": False, "expected_task_count": 60},
        ]}
        self.assertTrue(_all_capability_rows_stale_pending(registry))

    def test_all_capability_rows_stale_pending_false_when_one_current(self) -> None:
        registry = {"baselines": [
            {"kind": "model_baseline", "release_suitability": "current_public_stale", "requires_rerun_before_current_comparison": True, "leaderboard_eligible": False, "expected_task_count": 60},
            {"kind": "tool_agent_baseline", "release_suitability": "current_public_split", "requires_rerun_before_current_comparison": False, "leaderboard_eligible": False, "expected_task_count": 63},
        ]}
        self.assertFalse(_all_capability_rows_stale_pending(registry))

    def test_all_capability_rows_stale_pending_false_when_empty(self) -> None:
        registry = {"baselines": []}
        self.assertFalse(_all_capability_rows_stale_pending(registry))

    def test_strict_require_current_public_fails_without_cohorts(self) -> None:
        registry = {"baselines": [
            {"id": "sanity", "release_suitability": "current_public_harness_check", "expected_task_count": 63, "requires_rerun_before_current_comparison": False, "kind": "harness_check", "summary_path": "nonexistent.json"},
        ]}
        report = analyze_registry(registry, baselines_dir=__import__("pathlib").Path("/nonexistent"), require_current_public=True)
        self.assertTrue(any("missing required current-model cohort" in i for i in report["issues"]))
        self.assertTrue(any("missing required current-tool-agent cohort" in i for i in report["issues"]))
        self.assertEqual(report["capability_baseline_status"], "current")

    def test_stale_pending_rerun_passes_with_honest_state(self) -> None:
        from pathlib import Path
        import tempfile, json
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Create a valid summary file
            summary = {"task_count": 63, "passed_count": 63, "tasks": []}
            (tmp / "sanity63.json").write_text(json.dumps(summary))
            (tmp / "model60.json").write_text(json.dumps({"task_count": 60, "passed_count": 35, "tasks": []}))
            registry = {"baselines": [
                {"id": "sanity63", "release_suitability": "current_public_harness_check", "expected_task_count": 63, "requires_rerun_before_current_comparison": False, "kind": "harness_check", "expected_harness_type": "scripted", "summary_path": "sanity63.json"},
                {"id": "model60", "kind": "model_baseline", "requires_rerun_before_current_comparison": True, "leaderboard_eligible": False, "expected_task_count": 60, "summary_path": "model60.json", "release_suitability": "current_public_stale"},
            ]}
            report = analyze_registry(registry, baselines_dir=tmp, require_current_public=True, allow_stale_pending_rerun=True)
            self.assertEqual(report["issues"], [])
            self.assertEqual(
                report["capability_baseline_status"],
                "stale_pending_current_policy_rerun",
            )
            self.assertIsNotNone(report["capability_baseline_disclosure"])

    def test_stale_pending_rerun_fails_without_sanity_63(self) -> None:
        from pathlib import Path
        import tempfile, json
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "model60.json").write_text(json.dumps({"task_count": 60, "tasks": []}))
            registry = {"baselines": [
                {"id": "model60", "kind": "model_baseline", "requires_rerun_before_current_comparison": True, "leaderboard_eligible": False, "expected_task_count": 60, "summary_path": "model60.json", "release_suitability": "current_public_stale"},
            ]}
            report = analyze_registry(registry, baselines_dir=tmp, require_current_public=True, allow_stale_pending_rerun=True)
            self.assertTrue(any("missing current 63-task scripted sanity" in i for i in report["issues"]))


if __name__ == "__main__":
    unittest.main()
