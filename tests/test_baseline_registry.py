from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import load_json
from scripts.validate_baseline_registry import ROOT, validate_registry


REGISTRY = ROOT / "baselines" / "baseline-registry.json"
LEGACY_CLAUDE_ID = "kiro-claude-sonnet-4-6-legacy-15"
CURRENT_QWEN_ID = "kiro-qwen3-coder-next-current-public-44"


def _copy_registry_workspace(tmp_path: Path) -> Path:
    source = load_json(REGISTRY)
    baseline_dir = tmp_path / "baselines"
    baseline_dir.mkdir(parents=True)
    copied_paths: set[str] = set()
    for entry in source["baselines"]:
        artifact_paths = [entry["summary_path"]]
        artifact_paths.extend(entry.get("run_artifacts", []))
        for artifact_path in artifact_paths:
            if artifact_path in copied_paths:
                continue
            source_summary = REGISTRY.parent / artifact_path
            target_summary = baseline_dir / artifact_path
            target_summary.parent.mkdir(parents=True, exist_ok=True)
            target_summary.write_text(source_summary.read_text(encoding="utf-8"), encoding="utf-8")
            copied_paths.add(artifact_path)
    registry_path = baseline_dir / "baseline-registry.json"
    registry_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry_path


def _baseline_by_id(registry: dict, baseline_id: str) -> dict:
    for entry in registry["baselines"]:
        if entry["id"] == baseline_id:
            return entry
    raise AssertionError(f"missing baseline fixture: {baseline_id}")


class BaselineRegistryTests(unittest.TestCase):
    def test_current_registry_is_honest_but_not_v0_ready(self) -> None:
        result = validate_registry(REGISTRY)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["baseline_count"], 9, result)
        self.assertEqual(result["public_split"]["task_count"], 44, result)
        self.assertEqual(result["current_public_model_family_count"], 4, result)
        self.assertEqual(result["repeated_model_baseline_count"], 4, result)
        self.assertFalse(result["v0_baseline_ready"], result)
        self.assertTrue(any("current public model families" in item for item in result["unmet_v0_requirements"]), result)
        self.assertTrue(any("missing current public tool-agent baseline" in item for item in result["unmet_v0_requirements"]), result)
        self.assertFalse(result["has_current_public_tool_agent_baseline"], result)

    def test_rejects_harness_check_mislabeled_as_current_public_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            registry["baselines"][1]["release_suitability"] = "current_public_split"
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any("harness checks must use current_public_harness_check" in error for error in result["errors"]),
            result,
        )

    def test_rejects_one_off_model_baseline_marked_leaderboard_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = copy.deepcopy(_baseline_by_id(registry, LEGACY_CLAUDE_ID))
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
            model_entry = copy.deepcopy(_baseline_by_id(registry, LEGACY_CLAUDE_ID))
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
            model_entry = copy.deepcopy(_baseline_by_id(registry, LEGACY_CLAUDE_ID))
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

    def test_rejects_run_artifact_that_does_not_match_registry_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = _baseline_by_id(registry, CURRENT_QWEN_ID)
            run2_path = registry_path.parent / model_entry["run_artifacts"][1]
            run2_summary = load_json(run2_path)
            run2_summary["model"] = "wrong-model"
            run2_summary["task_count"] = 43
            run2_path.write_text(json.dumps(run2_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("run artifact" in error and "model" in error for error in result["errors"]), result)
        self.assertTrue(any("run artifact" in error and "task_count" in error for error in result["errors"]), result)

    def test_rejects_model_baseline_labeled_as_harness_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = copy.deepcopy(_baseline_by_id(registry, LEGACY_CLAUDE_ID))
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
