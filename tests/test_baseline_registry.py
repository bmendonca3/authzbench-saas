from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from authzbench.core import load_json
from scripts.validate_baseline_registry import ROOT, validate_registry


REGISTRY = ROOT / "baselines" / "baseline-registry.json"
LIVE_SCRIPTED_ID = "live-scripted-public-44"
LEGACY_CLAUDE_ID = "kiro-claude-sonnet-4-6-legacy-15"
STALE_QWEN_ID = "kiro-qwen3-coder-next-current-public-44"
CURRENT_QWEN_ID = "kiro-qwen3-coder-next-current-public-46"
CURRENT_QWEN_54_ID = "kiro-qwen3-coder-next-current-public-54"
CURRENT_HAIKU_54_ID = "kiro-claude-haiku-4-5-current-public-54"
CURRENT_SONNET_54_ID = "kiro-claude-sonnet-4-6-current-public-54"
CURRENT_SONNET_ID = "kiro-claude-sonnet-4-6-current-public-46"
CURRENT_TOOL_AGENT_ID = "kiro-live-tool-agent-sonnet-current-public-49"


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
    def test_current_registry_tracks_three_54_task_families_and_marks_49_task_rows_stale(self) -> None:
        result = validate_registry(REGISTRY)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["baseline_count"], 27, result)
        self.assertEqual(result["public_split"]["task_count"], 54, result)
        self.assertEqual(result["current_public_model_family_count"], 3, result)
        self.assertEqual(result["repeated_model_baseline_count"], 3, result)
        self.assertFalse(result["has_current_public_tool_agent_baseline"], result)
        self.assertFalse(result["v0_baseline_ready"], result)
        self.assertTrue(result["v0_release_snapshot_ready"], result)
        self.assertEqual(len(result["release_snapshots"]), 1, result)
        self.assertEqual(result["release_snapshots"][0]["id"], "v0.0", result)
        self.assertEqual(result["release_snapshots"][0]["public_split"]["task_count"], 46, result)
        self.assertEqual(result["release_snapshots"][0]["model_family_count"], 5, result)
        self.assertEqual(result["release_snapshots"][0]["repeated_model_baseline_count"], 5, result)
        self.assertIn("current public model families: 3 of 5", result["unmet_v0_requirements"])
        self.assertIn("repeated model baselines: 3 of 5", result["unmet_v0_requirements"])
        self.assertIn("missing current public tool-agent baseline", result["unmet_v0_requirements"])

        registry = load_json(REGISTRY)
        current_qwen = _baseline_by_id(registry, CURRENT_QWEN_54_ID)
        self.assertEqual(current_qwen["expected_task_count"], 54)
        self.assertEqual(current_qwen["run_count"], 2)
        self.assertEqual(current_qwen["release_suitability"], "current_public_split")
        self.assertFalse(current_qwen["requires_rerun_before_current_comparison"])
        current_haiku = _baseline_by_id(registry, CURRENT_HAIKU_54_ID)
        self.assertEqual(current_haiku["expected_task_count"], 54)
        self.assertEqual(current_haiku["run_count"], 2)
        self.assertEqual(current_haiku["expected_model"], "claude-haiku-4.5")
        self.assertEqual(current_haiku["release_suitability"], "current_public_split")
        self.assertFalse(current_haiku["requires_rerun_before_current_comparison"])
        current_sonnet = _baseline_by_id(registry, CURRENT_SONNET_54_ID)
        self.assertEqual(current_sonnet["expected_task_count"], 54)
        self.assertEqual(current_sonnet["run_count"], 2)
        self.assertEqual(current_sonnet["expected_model"], "claude-sonnet-4.6")
        self.assertEqual(current_sonnet["release_suitability"], "current_public_split")
        self.assertFalse(current_sonnet["requires_rerun_before_current_comparison"])

    def test_stale_49_task_model_repeats_share_one_benchmark_commit(self) -> None:
        registry = load_json(REGISTRY)
        stale_49_entries = [
            entry
            for entry in registry["baselines"]
            if entry["kind"] == "model_baseline"
            and entry["release_suitability"] == "current_public_stale"
            and entry["expected_task_count"] == 49
        ]

        self.assertEqual(len(stale_49_entries), 5)
        commit_shas = {
            load_json(REGISTRY.parent / artifact_path)["benchmark_commit_sha"]
            for entry in stale_49_entries
            for artifact_path in entry["run_artifacts"]
        }

        self.assertEqual(commit_shas, {"1eaac973ffe5229dad5796b9a5b144fa3af37a3a"})

    def test_current_haiku_pair_preserves_promoted_diagnostics_and_false_report(self) -> None:
        registry = load_json(REGISTRY)
        entry = _baseline_by_id(registry, CURRENT_HAIKU_54_ID)
        summaries = [load_json(REGISTRY.parent / path) for path in entry["run_artifacts"]]

        self.assertEqual(
            {summary["run_id"] for summary in summaries},
            {
                "20260607T185502191241Z-ac053a0a",
                "20260607T190024255303Z-8f2cac6a",
            },
        )
        self.assertEqual(
            {summary["benchmark_fingerprint"]["task_set_sha256"] for summary in summaries},
            {"f8d19cb89d347d1397f85bf978e6b7b232e8a2f1307fc2ac6ba02674e5c23c9f"},
        )
        self.assertEqual({summary["scored_submission_finding_total"] for summary in summaries}, {11, 12})
        for summary in summaries:
            self.assertEqual(summary["task_count"], 54)
            self.assertEqual(summary["model"], "claude-haiku-4.5")
            self.assertEqual(summary["harness_type"], "no-tools-model")
            self.assertEqual(summary["invalid_submission_count"], 0)
            self.assertEqual(summary["model_output_failure_count"], 0)
            self.assertEqual(summary["kiro_command_failure_count"], 0)
            self.assertEqual(summary["missing_submission_json_count"], 0)
            self.assertEqual(summary["runner_agent_failure_count"], 0)
            self.assertEqual(summary["control_false_report_count"], 1)
            self.assertEqual(summary["false_positive_rate"], 0.0303)
            self.assertEqual(summary["authorized_allow_pass_rate"], 0.9286)
            false_reports = [
                task
                for task in summary["tasks"]
                if task["control_type"] == "authorized_allow"
                and task["submission_finding_count"] > 0
                and not task["passed"]
            ]
            self.assertEqual(
                [task["task_id"] for task in false_reports],
                ["sup_admin_reassignment_control"],
            )

    def test_current_sonnet_pair_preserves_promoted_diagnostics_and_false_reports(self) -> None:
        registry = load_json(REGISTRY)
        entry = _baseline_by_id(registry, CURRENT_SONNET_54_ID)
        summaries = [load_json(REGISTRY.parent / path) for path in entry["run_artifacts"]]

        self.assertEqual(
            {summary["run_id"] for summary in summaries},
            {
                "20260607T194520410841Z-23511868",
                "20260607T195114220157Z-ad7ce734",
            },
        )
        self.assertEqual(
            {summary["benchmark_fingerprint"]["task_set_sha256"] for summary in summaries},
            {"f8d19cb89d347d1397f85bf978e6b7b232e8a2f1307fc2ac6ba02674e5c23c9f"},
        )
        self.assertEqual({summary["scored_submission_finding_total"] for summary in summaries}, {21, 22})
        self.assertEqual({summary["exploit_proven_task_count"] for summary in summaries}, {14, 15})
        self.assertEqual(
            {
                summary["run_id"]: summary["authorized_allow_pass_rate"]
                for summary in summaries
            },
            {
                "20260607T194520410841Z-23511868": 0.9286,
                "20260607T195114220157Z-ad7ce734": 1.0,
            },
        )
        false_report_controls: dict[str, str] = {}
        for summary in summaries:
            self.assertEqual(summary["task_count"], 54)
            self.assertEqual(summary["model"], "claude-sonnet-4.6")
            self.assertEqual(summary["harness_type"], "no-tools-model")
            self.assertEqual(summary["passed_count"], 32)
            self.assertEqual(summary["invalid_submission_count"], 0)
            self.assertEqual(summary["model_output_failure_count"], 0)
            self.assertEqual(summary["kiro_command_failure_count"], 0)
            self.assertEqual(summary["missing_submission_json_count"], 0)
            self.assertEqual(summary["runner_agent_failure_count"], 0)
            self.assertEqual(summary["control_false_report_count"], 1)
            self.assertEqual(summary["false_positive_rate"], 0.0303)
            false_reports = [
                task
                for task in summary["tasks"]
                if not task["expected_vulnerable"]
                and task["submission_finding_count"] > 0
                and not task["passed"]
            ]
            self.assertEqual(len(false_reports), 1)
            false_report_controls[false_reports[0]["task_id"]] = false_reports[0]["control_type"]
        self.assertEqual(
            false_report_controls,
            {
                "sup_admin_reassignment_control": "authorized_allow",
                "sup_secure_viewer_status_control": "denial",
            },
        )

    def test_future_public_expansion_can_keep_v0_release_snapshot_honest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            future_counts = {
                "task_count": 50,
                "vulnerable_task_count": 21,
                "control_task_count": 29,
                "denial_control_task_count": 17,
                "authorized_allow_control_task_count": 12,
            }
            registry["public_split"] = future_counts
            for entry in registry["baselines"]:
                if entry["expected_task_count"] != future_counts["task_count"] and entry["release_suitability"] in {
                    "current_public_split",
                    "current_public_harness_check",
                }:
                    entry["release_suitability"] = "current_public_stale"
                    entry["requires_rerun_before_current_comparison"] = True
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with mock.patch(
                "scripts.validate_baseline_registry._task_counts",
                return_value=future_counts,
            ), mock.patch(
                "scripts.validate_baseline_registry.benchmark_fingerprint",
                return_value={
                    "schema_version": "benchmark-fingerprint-v1",
                    "task_set_sha256": "future",
                    "task_path_set_sha256": "future-paths",
                    "score_policy_version": "score-policy-v1",
                    "scorer_contract": "v0-candidate-authz-evidence",
                    "evidence_contract_version": "evidence-requirements-v1",
                    **future_counts,
                },
            ):
                result = validate_registry(registry_path)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["public_split"]["task_count"], 50, result)
        self.assertEqual(result["current_public_model_family_count"], 0, result)
        self.assertEqual(result["repeated_model_baseline_count"], 0, result)
        self.assertFalse(result["has_current_public_tool_agent_baseline"], result)
        self.assertFalse(result["v0_baseline_ready"], result)
        self.assertTrue(result["v0_release_snapshot_ready"], result)
        self.assertEqual(result["release_snapshots"][0]["public_split"]["task_count"], 46, result)
        self.assertIn("current public model families: 0 of 5", result["unmet_v0_requirements"])
        self.assertIn("repeated model baselines: 0 of 5", result["unmet_v0_requirements"])

    def test_rejects_release_snapshot_run_artifact_with_wrong_fingerprint_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = _baseline_by_id(registry, CURRENT_QWEN_ID)
            run2_path = registry_path.parent / model_entry["run_artifacts"][1]
            run2_summary = load_json(run2_path)
            run2_summary["benchmark_fingerprint"]["task_count"] = 45
            run2_path.write_text(json.dumps(run2_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any("run artifact" in error and "benchmark_fingerprint.task_count" in error for error in result["errors"]),
            result,
        )

    def test_rejects_harness_check_mislabeled_as_current_public_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            _baseline_by_id(registry, LIVE_SCRIPTED_ID)["release_suitability"] = "current_public_split"
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any("harness checks must use current_public_harness_check" in error for error in result["errors"]),
            result,
        )

    def test_rejects_release_snapshot_summary_with_mismatched_fingerprint_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = _baseline_by_id(registry, CURRENT_QWEN_ID)
            run1_path = registry_path.parent / model_entry["run_artifacts"][0]
            summary = load_json(run1_path)
            summary["benchmark_fingerprint"]["task_count"] = 45
            run1_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("benchmark_fingerprint.task_count" in error for error in result["errors"]), result)

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

    def test_rejects_tool_agent_without_full_live_correlation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            tool_entry = _baseline_by_id(registry, CURRENT_TOOL_AGENT_ID)
            tool_entry["release_suitability"] = "current_public_split"
            tool_entry["expected_task_count"] = 49
            summary_path = registry_path.parent / tool_entry["summary_path"]
            summary = load_json(summary_path)
            summary["model_tool_plan_artifact_count"] = 49
            summary["per_task_tool_probe_artifact_count"] = 49
            summary["target_request_correlated_task_count"] = 48
            summary["target_request_coverage_rate"] = 0.9796
            summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("correlate target requests for all 49 tasks" in error for error in result["errors"]), result)
        self.assertTrue(any("target_request_coverage_rate must be 1.0" in error for error in result["errors"]), result)

    def test_rejects_stale_public_baseline_without_rerun_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            model_entry = _baseline_by_id(registry, STALE_QWEN_ID)
            model_entry["requires_rerun_before_current_comparison"] = False
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any(
                "current_public_stale must set requires_rerun_before_current_comparison=true" in error
                for error in result["errors"]
            ),
            result,
        )


if __name__ == "__main__":
    unittest.main()
