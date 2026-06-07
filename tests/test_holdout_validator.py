from __future__ import annotations

import copy
import glob
import json
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Any

from authzbench.core import load_json
from scripts.validate_holdout_pack import validate_holdout_pack


ROOT = Path(__file__).resolve().parents[1]


def _public_tasks_by_app() -> dict[str, list[dict[str, Any]]]:
    by_app: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in glob.glob(str(ROOT / "tasks" / "*" / "*.json")):
        task = load_json(path)
        task["_source_path"] = path
        by_app[task["app"]].append(task)
    return dict(by_app)


def _private_copy(task: dict[str, Any], index: int, *, keep_id: bool = False, keep_seed: bool = False) -> dict[str, Any]:
    private_task = copy.deepcopy(task)
    private_task.pop("_source_path", None)
    if not keep_id:
        private_task["id"] = f"priv_{index:03d}_{task['id']}"
    if not keep_seed:
        private_task["seed"] = f"private-v0-{index:03d}"
    private_task["split"] = "private_holdout"
    private_task["holdout_variant"] = {
        "route_variant": f"route_variant_{index:03d}",
        "decoy_variant": f"decoy_variant_{index:03d}",
    }
    private_task["policy"] = f"Private holdout policy variant {index}."
    private_task["objective"] = f"Validate private holdout task variant {index}."
    for control in private_task["controls"]:
        if isinstance(control, dict) and isinstance(control.get("path"), str):
            control["path"] = control["path"].replace("/api/", f"/api/private-variant-{index:03d}/", 1)
    return private_task


def _write_tasks(root: Path, tasks: list[dict[str, Any]]) -> list[str]:
    for task in tasks:
        path = root / task["app"] / f"{task['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return [str(root / "**" / "*.json")]


def _validate(patterns: list[str], **overrides: Any) -> dict[str, Any]:
    params = {
        "public_patterns": [str(ROOT / "tasks" / "*" / "*.json")],
        "comparison_private_patterns": None,
        "min_count": 20,
        "preferred_count": 24,
        "max_count": 30,
        "min_vulnerable": 12,
        "min_controls": 8,
        "min_apps": 6,
        "max_per_app": 8,
        "min_denial_controls": 4,
        "min_authorized_allow_controls": 4,
        "min_route_variants": 6,
        "min_decoy_variants": 6,
    }
    params.update(overrides)
    return validate_holdout_pack(patterns, **params)


class HoldoutValidatorTests(unittest.TestCase):
    def test_balanced_private_pack_passes_v0_shape_gate(self) -> None:
        by_app = _public_tasks_by_app()
        tasks: list[dict[str, Any]] = []
        index = 1
        for app in sorted(by_app):
            vulnerable = [task for task in by_app[app] if task["expected_vulnerable"] is True]
            controls = [task for task in by_app[app] if task["expected_vulnerable"] is False]
            denial_controls = [task for task in controls if task.get("control_type") == "denial"]
            allow_controls = [task for task in controls if task.get("control_type") == "authorized_allow"]
            selected_controls = (allow_controls[:1] + denial_controls[:1]) if allow_controls else controls[:2]
            for task in vulnerable[:2] + selected_controls:
                tasks.append(_private_copy(task, index))
                index += 1

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", tasks)
            result = _validate(patterns)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["manifest_count"], 24, result)
        self.assertEqual(result["private_holdout_count"], 24, result)
        self.assertEqual(result["vulnerable_count"], 12, result)
        self.assertEqual(result["control_count"], 12, result)
        self.assertGreaterEqual(result["denial_control_count"], 4, result)
        self.assertGreaterEqual(result["authorized_allow_control_count"], 4, result)
        self.assertEqual(len(result["app_counts"]), 6, result)
        self.assertEqual(result["route_variant_count"], 24, result)
        self.assertEqual(result["decoy_variant_count"], 24, result)
        self.assertTrue(result["leaderboard_suitable"], result)

    def test_rejects_holdout_pack_concentrated_in_one_app(self) -> None:
        by_app = _public_tasks_by_app()
        project_tasks = by_app["project_mgmt"]
        tasks = [_private_copy(project_tasks[index % len(project_tasks)], index + 1) for index in range(9)]

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", tasks)
            result = _validate(
                patterns,
                min_count=1,
                max_count=20,
                min_vulnerable=0,
                min_controls=0,
                min_apps=2,
                max_per_app=8,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("minimum is 2" in error for error in result["errors"]), result)
        self.assertTrue(any("more than 8 tasks" in error for error in result["errors"]), result)

    def test_rejects_public_task_id_reuse(self) -> None:
        task = next(task for tasks in _public_tasks_by_app().values() for task in tasks)
        private_task = _private_copy(task, 1, keep_id=True)

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", [private_task])
            result = _validate(
                patterns,
                min_count=1,
                max_count=5,
                min_vulnerable=0,
                min_controls=0,
                min_apps=1,
                max_per_app=5,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("reuses public task id" in error for error in result["errors"]), result)

    def test_rejects_public_seed_reuse(self) -> None:
        task = next(task for tasks in _public_tasks_by_app().values() for task in tasks)
        private_task = _private_copy(task, 1, keep_seed=True)

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", [private_task])
            result = _validate(
                patterns,
                min_count=1,
                max_count=5,
                min_vulnerable=0,
                min_controls=0,
                min_apps=1,
                max_per_app=5,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("reuses public task seed" in error for error in result["errors"]), result)

    def test_rejects_holdout_pack_missing_variant_metadata(self) -> None:
        task = next(task for tasks in _public_tasks_by_app().values() for task in tasks)
        private_task = _private_copy(task, 1)
        private_task.pop("holdout_variant")

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", [private_task])
            result = _validate(
                patterns,
                min_count=1,
                max_count=5,
                min_vulnerable=0,
                min_controls=0,
                min_apps=1,
                max_per_app=5,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("missing holdout_variant" in error for error in result["errors"]), result)

    def test_rejects_blank_holdout_variant_metadata(self) -> None:
        task = next(task for tasks in _public_tasks_by_app().values() for task in tasks)
        private_task = _private_copy(task, 1)
        private_task["holdout_variant"] = {"route_variant": " ", "decoy_variant": None}

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", [private_task])
            result = _validate(
                patterns,
                min_count=1,
                max_count=5,
                min_vulnerable=0,
                min_controls=0,
                min_apps=1,
                max_per_app=5,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("missing holdout_variant" in error for error in result["errors"]), result)

    def test_rejects_non_rehearsal_public_structure_copy(self) -> None:
        task = next(task for tasks in _public_tasks_by_app().values() for task in tasks)
        private_task = copy.deepcopy(task)
        private_task.pop("_source_path", None)
        private_task["id"] = "private_copy_of_public_structure"
        private_task["seed"] = "private-v0-copy-001"
        private_task["split"] = "private_holdout"
        private_task["holdout_variant"] = {"route_variant": "copy-route", "decoy_variant": "copy-decoy"}

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", [private_task])
            result = _validate(
                patterns,
                min_count=1,
                max_count=5,
                min_vulnerable=0,
                min_controls=0,
                min_apps=1,
                max_per_app=5,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertEqual(result["public_structure_overlap_count"], 1, result)
        self.assertFalse(result["leaderboard_suitable"], result)
        self.assertTrue(any("reuse public task structure" in error for error in result["errors"]), result)

    def test_rejects_public_structure_copy_marked_not_leaderboard_suitable(self) -> None:
        task = next(task for tasks in _public_tasks_by_app().values() for task in tasks)
        private_task = copy.deepcopy(task)
        private_task.pop("_source_path", None)
        private_task["id"] = "private_copy_flagged_false"
        private_task["seed"] = "private-v0-copy-flagged-false"
        private_task["split"] = "private_holdout"
        private_task["leaderboard_suitable"] = False
        private_task["holdout_variant"] = {"route_variant": "copy-route", "decoy_variant": "copy-decoy"}

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", [private_task])
            result = _validate(
                patterns,
                min_count=1,
                max_count=5,
                min_vulnerable=0,
                min_controls=0,
                min_apps=1,
                max_per_app=5,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertEqual(result["public_structure_overlap_count"], 1, result)
        self.assertTrue(any("reuse public task structure" in error for error in result["errors"]), result)

    def test_rejects_public_structure_copy_with_reworded_policy(self) -> None:
        task = next(task for tasks in _public_tasks_by_app().values() for task in tasks)
        private_task = copy.deepcopy(task)
        private_task.pop("_source_path", None)
        private_task["id"] = "private_copy_with_reworded_policy"
        private_task["seed"] = "private-v0-copy-reworded-policy"
        private_task["split"] = "private_holdout"
        private_task["policy"] = "Private holdout wording that changes prose only."
        private_task["objective"] = "Reworded objective with the same behavioral oracle and controls."
        private_task["holdout_variant"] = {"route_variant": "copy-route", "decoy_variant": "copy-decoy"}

        with tempfile.TemporaryDirectory() as tmp:
            patterns = _write_tasks(Path(tmp) / "tasks_private" / "holdout", [private_task])
            result = _validate(
                patterns,
                min_count=1,
                max_count=5,
                min_vulnerable=0,
                min_controls=0,
                min_apps=1,
                max_per_app=5,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertEqual(result["public_structure_overlap_count"], 1, result)
        self.assertTrue(any("reuse public task structure" in error for error in result["errors"]), result)

    def test_rejects_structure_reused_from_comparison_private_pack(self) -> None:
        task = next(task for tasks in _public_tasks_by_app().values() for task in tasks)
        source_private = _private_copy(task, 1)
        candidate_private = copy.deepcopy(source_private)
        candidate_private["id"] = "candidate_private_task"
        candidate_private["seed"] = "private-v1-candidate-seed"
        candidate_private["holdout_variant"] = {
            "route_variant": "candidate-route",
            "decoy_variant": "candidate-decoy",
        }
        duplicate_candidate_private = copy.deepcopy(candidate_private)
        duplicate_candidate_private["id"] = "candidate_private_task_duplicate"
        duplicate_candidate_private["seed"] = "private-v1-candidate-duplicate-seed"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_patterns = _write_tasks(root / "source-pack", [source_private])
            candidate_patterns = _write_tasks(
                root / "candidate-pack",
                [candidate_private, duplicate_candidate_private],
            )
            result = _validate(
                candidate_patterns,
                comparison_private_patterns=source_patterns,
                min_count=1,
                max_count=5,
                min_vulnerable=0,
                min_controls=0,
                min_apps=1,
                max_per_app=5,
                min_denial_controls=0,
                min_authorized_allow_controls=0,
                min_route_variants=1,
                min_decoy_variants=1,
            )

        self.assertFalse(result["passed"], result)
        self.assertEqual(result["private_structure_overlap_count"], 1, result)
        self.assertTrue(
            any("structural fingerprint(s) from comparison private pack" in error for error in result["errors"]),
            result,
        )


if __name__ == "__main__":
    unittest.main()
