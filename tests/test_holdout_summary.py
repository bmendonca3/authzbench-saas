from __future__ import annotations

import copy
import glob
import json
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

from authzbench.core import load_json
from scripts.summarize_holdout_pack import main, summarize_holdout_pack


ROOT = Path(__file__).resolve().parents[1]


def _public_tasks_by_app() -> dict[str, list[dict[str, Any]]]:
    by_app: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in glob.glob(str(ROOT / "tasks" / "*" / "*.json")):
        task = load_json(path)
        task["_source_path"] = path
        by_app[task["app"]].append(task)
    return dict(by_app)


def _private_variant(task: dict[str, Any], index: int) -> dict[str, Any]:
    private_task = copy.deepcopy(task)
    private_task.pop("_source_path", None)
    private_task["id"] = f"private_summary_fixture_{index:03d}"
    private_task["seed"] = f"private-v0-summary-{index:03d}"
    private_task["split"] = "private_holdout"
    private_task["holdout_variant"] = {
        "route_variant": f"summary-route-{index:03d}",
        "decoy_variant": f"summary-decoy-{index:03d}",
    }
    private_task["policy"] = f"Private summary fixture policy {index}."
    private_task["objective"] = f"Private summary fixture objective {index}."
    if isinstance(private_task.get("oracle"), dict) and isinstance(private_task["oracle"].get("body_contains"), dict):
        private_task["oracle"]["body_contains"] = private_task["oracle"]["body_contains"] | {
            "summary_fixture_variant": index
        }
    for control in private_task["controls"]:
        if isinstance(control, dict):
            control["name"] = f"summary_{index:03d}_{control.get('name', 'control')}"
            if isinstance(control.get("body"), dict):
                control["body"] = control["body"] | {"summary_fixture": index}
    return private_task


def _write_pack(root: Path) -> list[str]:
    tasks: list[dict[str, Any]] = []
    index = 1
    for app, app_tasks in sorted(_public_tasks_by_app().items()):
        vulnerable = [task for task in app_tasks if task["expected_vulnerable"] is True]
        controls = [task for task in app_tasks if task["expected_vulnerable"] is False]
        denial_controls = [task for task in controls if task.get("control_type") == "denial"]
        allow_controls = [task for task in controls if task.get("control_type") == "authorized_allow"]
        selected_controls = denial_controls[:1] + allow_controls[:1]
        for fallback in controls:
            if len(selected_controls) >= 2:
                break
            if fallback not in selected_controls:
                selected_controls.append(fallback)
        for task in vulnerable[:2] + selected_controls[:2]:
            tasks.append(_private_variant(task, index))
            index += 1

    for task in tasks:
        path = root / task["app"] / f"{task['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return [str(root / "**" / "*.json")]


class HoldoutSummaryTests(unittest.TestCase):
    def test_summary_is_public_safe_and_count_level(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_pack(Path(tmp) / "tasks_private" / "holdout")
            with patch("scripts.summarize_holdout_pack._git_tracked_holdout_count", return_value=0):
                summary = summarize_holdout_pack(patterns, [str(ROOT / "tasks" / "*" / "*.json")])

        rendered = json.dumps(summary, sort_keys=True)
        self.assertTrue(summary["passed"], summary)
        self.assertTrue(summary["leaderboard_suitable"], summary)
        self.assertEqual(summary["counts"]["manifest_count"], 24, summary)
        self.assertEqual(summary["counts"]["vulnerable_count"], 12, summary)
        self.assertEqual(summary["counts"]["control_count"], 12, summary)
        self.assertEqual(summary["counts"]["app_count"], 6, summary)
        self.assertFalse(summary["publication_safety"]["contains_task_ids"], summary)
        self.assertNotIn("private_summary_fixture_", rendered)
        self.assertNotIn("private-v0-summary-", rendered)
        self.assertNotIn("Private summary fixture policy", rendered)
        self.assertNotIn("Private summary fixture objective", rendered)
        self.assertNotIn("summary-route-", rendered)
        self.assertNotIn("summary-decoy-", rendered)
        self.assertNotIn("summary_fixture_variant", rendered)
        self.assertNotIn("/api/", rendered)

    def test_summary_fails_when_holdouts_are_git_tracked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_pack(Path(tmp) / "tasks_private" / "holdout")
            with patch("scripts.summarize_holdout_pack._git_tracked_holdout_count", return_value=1):
                summary = summarize_holdout_pack(patterns, [str(ROOT / "tasks" / "*" / "*.json")])

        self.assertFalse(summary["passed"], summary)
        self.assertFalse(summary["private_holdouts_untracked"], summary)
        self.assertEqual(summary["git_tracked_holdout_manifest_count"], 1, summary)

    def test_summary_reports_counts_not_diagnostics_for_invalid_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty_glob = str(Path(tmp) / "tasks_private" / "holdout" / "**" / "*.json")
            with patch("scripts.summarize_holdout_pack._git_tracked_holdout_count", return_value=0):
                summary = summarize_holdout_pack([empty_glob], [str(ROOT / "tasks" / "*" / "*.json")])

        rendered = json.dumps(summary, sort_keys=True)
        self.assertFalse(summary["passed"], summary)
        self.assertGreater(summary["validation_error_count"], 0, summary)
        self.assertNotIn("no private holdout manifests", rendered)
        self.assertNotIn(str(Path(empty_glob).parent), rendered)

    def test_summary_conservatively_fails_when_git_check_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_pack(Path(tmp) / "tasks_private" / "holdout")
            with patch("scripts.summarize_holdout_pack._git_tracked_holdout_count", return_value=None):
                summary = summarize_holdout_pack(patterns, [str(ROOT / "tasks" / "*" / "*.json")])

        self.assertFalse(summary["passed"], summary)
        self.assertFalse(summary["git_tracking_check_available"], summary)
        self.assertFalse(summary["private_holdouts_untracked"], summary)
        self.assertIsNone(summary["git_tracked_holdout_manifest_count"], summary)

    def test_cli_writes_redacted_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            patterns = _write_pack(tmp_path / "tasks_private" / "holdout")
            output_path = tmp_path / "summary.json"
            argv = [
                "summarize_holdout_pack.py",
                "--task",
                patterns[0],
                "--public-task",
                str(ROOT / "tasks" / "*" / "*.json"),
                "--output",
                str(output_path),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch("scripts.summarize_holdout_pack._git_tracked_holdout_count", return_value=0),
            ):
                exit_code = main()

            written = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn('"public_safe_summary": true', written)
        self.assertNotIn("private_summary_fixture_", written)


if __name__ == "__main__":
    unittest.main()
