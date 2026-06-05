from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import load_json
from scripts.validate_baseline_registry import ROOT, validate_registry


REGISTRY = ROOT / "baselines" / "baseline-registry.json"


def _copy_registry_workspace(tmp_path: Path) -> Path:
    source = load_json(REGISTRY)
    baseline_dir = tmp_path / "baselines"
    baseline_dir.mkdir(parents=True)
    for entry in source["baselines"]:
        source_summary = REGISTRY.parent / entry["summary_path"]
        target_summary = baseline_dir / entry["summary_path"]
        target_summary.write_text(source_summary.read_text(encoding="utf-8"), encoding="utf-8")
    registry_path = baseline_dir / "baseline-registry.json"
    registry_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry_path


class BaselineRegistryTests(unittest.TestCase):
    def test_current_registry_is_honest_but_not_v0_ready(self) -> None:
        result = validate_registry(REGISTRY)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["baseline_count"], 4, result)
        self.assertEqual(result["public_split"]["task_count"], 44, result)
        self.assertFalse(result["v0_baseline_ready"], result)
        self.assertTrue(any("current public model families" in item for item in result["unmet_v0_requirements"]), result)
        self.assertTrue(any("missing current public tool-agent baseline" in item for item in result["unmet_v0_requirements"]), result)

    def test_rejects_legacy_snapshot_mislabeled_as_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            registry["baselines"][1]["release_suitability"] = "current_public_split"
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("current_public_split must use current public task count" in error for error in result["errors"]), result)

    def test_rejects_one_off_model_baseline_marked_leaderboard_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = copy.deepcopy(registry["baselines"][2])
            model_entry["id"] = "bad-one-off-current-model"
            model_entry["release_suitability"] = "current_public_split"
            model_entry["expected_task_count"] = 44
            model_entry["leaderboard_eligible"] = True
            model_entry["run_count"] = 1
            summary_path = registry_path.parent / model_entry["summary_path"]
            summary = load_json(summary_path)
            summary["task_count"] = 44
            summary["vulnerable_task_count"] = 18
            summary["control_task_count"] = 26
            summary["denial_control_task_count"] = 16
            summary["authorized_allow_control_task_count"] = 10
            summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry["baselines"].append(model_entry)
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("leaderboard_eligible model baselines" in error for error in result["errors"]), result)

    def test_rejects_inflated_run_count_without_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = copy.deepcopy(registry["baselines"][2])
            model_entry["id"] = "bad-inflated-repeated-model"
            model_entry["release_suitability"] = "current_public_split"
            model_entry["expected_task_count"] = 44
            model_entry["leaderboard_eligible"] = True
            model_entry["run_count"] = 2
            summary_path = registry_path.parent / model_entry["summary_path"]
            summary = load_json(summary_path)
            summary["task_count"] = 44
            summary["vulnerable_task_count"] = 18
            summary["control_task_count"] = 26
            summary["denial_control_task_count"] = 16
            summary["authorized_allow_control_task_count"] = 10
            summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry["baselines"].append(model_entry)
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("run_artifacts list" in error for error in result["errors"]), result)
        self.assertTrue(any("validated run_artifacts" in error for error in result["errors"]), result)

    def test_rejects_duplicated_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = copy.deepcopy(registry["baselines"][2])
            model_entry["id"] = "bad-duplicated-run-artifacts"
            model_entry["release_suitability"] = "current_public_split"
            model_entry["expected_task_count"] = 44
            model_entry["leaderboard_eligible"] = True
            model_entry["run_count"] = 2
            model_entry["run_artifacts"] = [
                "kiro-claude-sonnet-4.6-full-summary.json",
                "kiro-claude-sonnet-4.6-full-summary.json",
            ]
            summary_path = registry_path.parent / model_entry["summary_path"]
            summary = load_json(summary_path)
            summary["task_count"] = 44
            summary["vulnerable_task_count"] = 18
            summary["control_task_count"] = 26
            summary["denial_control_task_count"] = 16
            summary["authorized_allow_control_task_count"] = 10
            summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry["baselines"].append(model_entry)
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("unique files" in error for error in result["errors"]), result)
        self.assertTrue(any("distinct run_id" in error for error in result["errors"]), result)

    def test_rejects_model_baseline_labeled_as_harness_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = copy.deepcopy(registry["baselines"][2])
            model_entry["id"] = "bad-model-as-harness-check"
            model_entry["release_suitability"] = "current_public_harness_check"
            model_entry["expected_task_count"] = 44
            summary_path = registry_path.parent / model_entry["summary_path"]
            summary = load_json(summary_path)
            summary["task_count"] = 44
            summary["vulnerable_task_count"] = 18
            summary["control_task_count"] = 26
            summary["denial_control_task_count"] = 16
            summary["authorized_allow_control_task_count"] = 10
            summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry["baselines"].append(model_entry)
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("current_public_harness_check is only valid" in error for error in result["errors"]), result)


if __name__ == "__main__":
    unittest.main()
