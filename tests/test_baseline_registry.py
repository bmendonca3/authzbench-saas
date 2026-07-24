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
CURRENT_GLM_54_ID = "kiro-glm-5-current-public-54"
CURRENT_OPUS_54_ID = "kiro-claude-opus-4-6-current-public-54"
CURRENT_SONNET_ID = "kiro-claude-sonnet-4-6-current-public-46"
STALE_TOOL_AGENT_49_ID = "kiro-live-tool-agent-sonnet-current-public-49"
CURRENT_TOOL_AGENT_54_ID = "kiro-live-tool-agent-sonnet-current-public-54"
CURRENT_SCRIPTED_60_ID = "scripted-sanity-public-60"
CURRENT_QWEN_60_ID = "kiro-qwen3-coder-next-current-public-60"
CURRENT_HAIKU_60_ID = "kiro-claude-haiku-4-5-current-public-60"
CURRENT_SONNET_60_ID = "kiro-claude-sonnet-4-6-current-public-60"
CURRENT_GLM_60_ID = "kiro-glm-5-current-public-60"
CURRENT_OPUS_60_ID = "kiro-claude-opus-4-6-current-public-60"
CURRENT_TOOL_AGENT_60_ID = "kiro-live-tool-agent-sonnet-current-public-60"
CURRENT_SCRIPTED_63_ID = "scripted-sanity-public-63"


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


def _add_synthetic_promoted_composite_entry(registry_path: Path) -> tuple[dict, dict]:
    registry = load_json(registry_path)
    base_entry = _baseline_by_id(registry, CURRENT_QWEN_60_ID)
    entry = copy.deepcopy(base_entry)
    entry.update(
        {
            "id": "synthetic-qwen-current-public-63-composite",
            "release_suitability": "current_public_split",
            "leaderboard_eligible": False,
            "expected_task_count": 63,
            "requires_rerun_before_current_comparison": False,
            "summary_path": "synthetic-qwen-current-public-63-composite-run1-summary.json",
            "run_artifacts": [
                "synthetic-qwen-current-public-63-composite-run1-summary.json",
                "synthetic-qwen-current-public-63-composite-run2-summary.json",
            ],
            "run_date": "2026-06-20",
            "evidence_status": "current_promoted_composite",
            "baseline_construction": "promoted_cohort_delta_merge",
            "base_public_task_count": 60,
            "delta_public_task_count": 3,
            "merged_public_task_count": 63,
            "base_summary_path": base_entry["summary_path"],
            "delta_summary_paths": ["synthetic-qwen-current-public-63-delta-summary.json"],
            "promotion_annotation": (
                "Current 63-task promoted-composite baseline built from the immutable "
                "60-task public baseline plus fresh reruns on the three promoted public tasks; "
                "not a full 63-task rerun."
            ),
            "not_full_rerun": True,
        }
    )

    scripted_summary = load_json(registry_path.parent / "scripted-baseline-public-63-summary.json")
    summary = copy.deepcopy(scripted_summary)
    summary.update(
        {
            "agent": entry["expected_agent"],
            "model": entry["expected_model"],
            "harness_type": entry["expected_harness_type"],
            "baseline_construction": "promoted_cohort_delta_merge",
            "public_split_freshness": "current_promoted_composite_not_full_rerun",
            "rerun_scope": "delta_public_tasks_only",
            "not_full_rerun": True,
            "base_public_task_count": 60,
            "delta_public_task_count": 3,
            "merged_public_task_count": 63,
            "delta_task_ids": [
                "bill_bfla_member_disables_export_entitlement_discovery",
                "fs_team_membership_cross_workspace_discovery",
                "sup_bfla_viewer_updates_assigned_ticket_status_discovery",
            ],
            "promotion_annotation": entry["promotion_annotation"],
            "promotion_sources": {
                "base_summary": entry["base_summary_path"],
                "delta_summary": entry["delta_summary_paths"][0],
                "base_task_count": 60,
                "delta_task_count": 3,
                "base_run_id": "synthetic-base",
                "delta_run_id": "synthetic-delta",
            },
        }
    )
    for index, artifact_path in enumerate(entry["run_artifacts"], start=1):
        artifact = copy.deepcopy(summary)
        artifact["run_id"] = f"synthetic-qwen-current-public-63-composite-run{index}"
        (registry_path.parent / artifact_path).write_text(
            json.dumps(artifact, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    delta_summary = {
        **summary,
        "run_id": "synthetic-qwen-current-public-63-delta",
        "task_count": 3,
        "tasks": [
            task for task in summary["tasks"] if task["task_id"] in set(summary["delta_task_ids"])
        ],
    }
    (registry_path.parent / entry["delta_summary_paths"][0]).write_text(
        json.dumps(delta_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    registry["baselines"].append(entry)
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry, entry


class BaselineRegistryTests(unittest.TestCase):
    def test_rejects_registry_summary_score_policy_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            entry = next(item for item in registry["baselines"] if item.get("run_artifacts"))
            entry["expected_score_policy_version"] = "score-policy-v2"
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
            result = validate_registry(registry_path)
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("score_policy_version" in error for error in result["errors"]), result)

    def test_current_registry_keeps_60_task_rows_stale_and_63_task_rows_current(self) -> None:
        result = validate_registry(REGISTRY)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["baseline_count"], 46, result)
        self.assertEqual(result["public_split"]["task_count"], 63, result)
        self.assertEqual(result["current_public_model_family_count"], 7, result)
        self.assertEqual(result["repeated_model_baseline_count"], 7, result)
        self.assertTrue(result["has_current_public_tool_agent_baseline"], result)
        self.assertTrue(result["has_current_public_scripted_sanity_baseline"], result)
        self.assertTrue(result["has_current_public_model_or_tool_agent_baseline"], result)
        self.assertTrue(result["v0_baseline_ready"], result)
        self.assertTrue(result["v0_release_snapshot_ready"], result)
        self.assertEqual(len(result["release_snapshots"]), 1, result)
        self.assertEqual(result["release_snapshots"][0]["id"], "v0.0", result)
        self.assertEqual(result["release_snapshots"][0]["public_split"]["task_count"], 46, result)
        self.assertEqual(result["release_snapshots"][0]["model_family_count"], 5, result)
        self.assertEqual(result["release_snapshots"][0]["repeated_model_baseline_count"], 5, result)
        self.assertEqual(result["unmet_v0_requirements"], [])

        registry = load_json(REGISTRY)
        current_scripted_63 = _baseline_by_id(registry, CURRENT_SCRIPTED_63_ID)
        self.assertEqual(current_scripted_63["expected_task_count"], 63)
        self.assertEqual(current_scripted_63["run_count"], 1)
        self.assertEqual(current_scripted_63["release_suitability"], "current_public_harness_check")
        self.assertFalse(current_scripted_63["requires_rerun_before_current_comparison"])

        current_scripted = _baseline_by_id(registry, CURRENT_SCRIPTED_60_ID)
        self.assertEqual(current_scripted["expected_task_count"], 60)
        self.assertEqual(current_scripted["run_count"], 1)
        self.assertEqual(current_scripted["release_suitability"], "current_public_stale")
        self.assertTrue(current_scripted["requires_rerun_before_current_comparison"])
        current_qwen_60 = _baseline_by_id(registry, CURRENT_QWEN_60_ID)
        self.assertEqual(current_qwen_60["expected_task_count"], 60)
        self.assertEqual(current_qwen_60["run_count"], 2)
        self.assertEqual(current_qwen_60["release_suitability"], "current_public_stale")
        self.assertTrue(current_qwen_60["requires_rerun_before_current_comparison"])
        current_haiku_60 = _baseline_by_id(registry, CURRENT_HAIKU_60_ID)
        self.assertEqual(current_haiku_60["expected_model"], "claude-haiku-4.5")
        self.assertEqual(current_haiku_60["release_suitability"], "current_public_stale")
        self.assertTrue(current_haiku_60["requires_rerun_before_current_comparison"])
        current_sonnet_60 = _baseline_by_id(registry, CURRENT_SONNET_60_ID)
        self.assertEqual(current_sonnet_60["expected_model"], "claude-sonnet-4.6")
        self.assertEqual(current_sonnet_60["release_suitability"], "current_public_stale")
        self.assertTrue(current_sonnet_60["requires_rerun_before_current_comparison"])
        current_glm_60 = _baseline_by_id(registry, CURRENT_GLM_60_ID)
        self.assertEqual(current_glm_60["expected_model"], "glm-5")
        self.assertEqual(current_glm_60["release_suitability"], "current_public_stale")
        self.assertTrue(current_glm_60["requires_rerun_before_current_comparison"])
        current_opus_60 = _baseline_by_id(registry, CURRENT_OPUS_60_ID)
        self.assertEqual(current_opus_60["expected_model"], "claude-opus-4.6")
        self.assertEqual(current_opus_60["release_suitability"], "current_public_stale")
        self.assertTrue(current_opus_60["requires_rerun_before_current_comparison"])
        current_tool_agent_60 = _baseline_by_id(registry, CURRENT_TOOL_AGENT_60_ID)
        self.assertEqual(current_tool_agent_60["expected_harness_type"], "tool-agent")
        self.assertEqual(current_tool_agent_60["expected_task_count"], 60)
        self.assertEqual(current_tool_agent_60["release_suitability"], "current_public_stale")
        self.assertTrue(current_tool_agent_60["requires_rerun_before_current_comparison"])
        current_qwen = _baseline_by_id(registry, CURRENT_QWEN_54_ID)
        self.assertEqual(current_qwen["expected_task_count"], 54)
        self.assertEqual(current_qwen["run_count"], 2)
        self.assertEqual(current_qwen["release_suitability"], "current_public_stale")
        self.assertTrue(current_qwen["requires_rerun_before_current_comparison"])
        current_haiku = _baseline_by_id(registry, CURRENT_HAIKU_54_ID)
        self.assertEqual(current_haiku["expected_task_count"], 54)
        self.assertEqual(current_haiku["run_count"], 2)
        self.assertEqual(current_haiku["expected_model"], "claude-haiku-4.5")
        self.assertEqual(current_haiku["release_suitability"], "current_public_stale")
        self.assertTrue(current_haiku["requires_rerun_before_current_comparison"])
        current_sonnet = _baseline_by_id(registry, CURRENT_SONNET_54_ID)
        self.assertEqual(current_sonnet["expected_task_count"], 54)
        self.assertEqual(current_sonnet["run_count"], 2)
        self.assertEqual(current_sonnet["expected_model"], "claude-sonnet-4.6")
        self.assertEqual(current_sonnet["release_suitability"], "current_public_stale")
        self.assertTrue(current_sonnet["requires_rerun_before_current_comparison"])
        current_glm = _baseline_by_id(registry, CURRENT_GLM_54_ID)
        self.assertEqual(current_glm["expected_task_count"], 54)
        self.assertEqual(current_glm["run_count"], 2)
        self.assertEqual(current_glm["expected_model"], "glm-5")
        self.assertEqual(current_glm["release_suitability"], "current_public_stale")
        self.assertTrue(current_glm["requires_rerun_before_current_comparison"])
        current_opus = _baseline_by_id(registry, CURRENT_OPUS_54_ID)
        self.assertEqual(current_opus["expected_task_count"], 54)
        self.assertEqual(current_opus["run_count"], 2)
        self.assertEqual(current_opus["expected_model"], "claude-opus-4.6")
        self.assertEqual(current_opus["release_suitability"], "current_public_stale")
        self.assertTrue(current_opus["requires_rerun_before_current_comparison"])
        current_tool_agent = _baseline_by_id(registry, CURRENT_TOOL_AGENT_54_ID)
        self.assertEqual(current_tool_agent["expected_task_count"], 54)
        self.assertEqual(current_tool_agent["run_count"], 2)
        self.assertEqual(current_tool_agent["expected_model"], "claude-sonnet-4.6")
        self.assertEqual(current_tool_agent["expected_harness_type"], "tool-agent")
        self.assertEqual(current_tool_agent["release_suitability"], "current_public_stale")
        self.assertTrue(current_tool_agent["requires_rerun_before_current_comparison"])

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

    def test_current_glm_pair_preserves_runner_failure_and_clean_retry_diagnostics(self) -> None:
        registry = load_json(REGISTRY)
        entry = _baseline_by_id(registry, CURRENT_GLM_54_ID)
        summaries = [load_json(REGISTRY.parent / path) for path in entry["run_artifacts"]]

        self.assertEqual(
            {summary["run_id"] for summary in summaries},
            {
                "20260607T201255153205Z-5de7a354",
                "20260608T002053809050Z-e50a764c",
            },
        )
        self.assertEqual(
            {summary["benchmark_commit_sha"] for summary in summaries},
            {"73d7b111360cc2439ae5ff418e8b5171e96bb395"},
        )
        self.assertEqual(
            {summary["benchmark_fingerprint"]["task_set_sha256"] for summary in summaries},
            {"f8d19cb89d347d1397f85bf978e6b7b232e8a2f1307fc2ac6ba02674e5c23c9f"},
        )
        self.assertEqual({summary["passed_count"] for summary in summaries}, {33})
        self.assertEqual({summary["false_positive_rate"] for summary in summaries}, {0.0})
        self.assertEqual({summary["boundary_reasoning_pass_rate"] for summary in summaries}, {0.0})
        self.assertEqual({summary["vulnerable_full_pass_count"] for summary in summaries}, {0})
        self.assertEqual({summary["exploit_proven_task_count"] for summary in summaries}, {2, 3})
        self.assertEqual({summary["scored_submission_finding_total"] for summary in summaries}, {2, 4})
        self.assertEqual(
            {
                summary["run_id"]: summary["invalid_submission_count"]
                for summary in summaries
            },
            {
                "20260607T201255153205Z-5de7a354": 1,
                "20260608T002053809050Z-e50a764c": 0,
            },
        )
        self.assertEqual(
            {
                summary["run_id"]: summary["model_output_failure_count"]
                for summary in summaries
            },
            {
                "20260607T201255153205Z-5de7a354": 1,
                "20260608T002053809050Z-e50a764c": 0,
            },
        )
        run1 = next(summary for summary in summaries if summary["run_id"] == "20260607T201255153205Z-5de7a354")
        self.assertEqual(run1["missing_submission_json_count"], 1)
        self.assertEqual(run1["runner_agent_failure_count"], 1)
        self.assertEqual(run1["kiro_command_failure_count"], 0)
        self.assertEqual(
            run1["model_output_failures"],
            [
                {
                    "task_id": "sup_multistep_agent_status_then_admin_reassignment",
                    "failure_type": "runner agent failed before writing submission/model-output",
                }
            ],
        )
        run2 = next(summary for summary in summaries if summary["run_id"] == "20260608T002053809050Z-e50a764c")
        self.assertEqual(run2["missing_submission_json_count"], 0)
        self.assertEqual(run2["runner_agent_failure_count"], 0)
        self.assertEqual(run2["kiro_command_failure_count"], 0)
        self.assertEqual(run2["model_output_failures"], [])

    def test_current_opus_pair_preserves_promoted_diagnostics_and_metrics(self) -> None:
        registry = load_json(REGISTRY)
        entry = _baseline_by_id(registry, CURRENT_OPUS_54_ID)
        summaries = [load_json(REGISTRY.parent / path) for path in entry["run_artifacts"]]

        self.assertEqual(
            {summary["run_id"] for summary in summaries},
            {
                "20260608T010424615768Z-6ce73f0b",
                "20260608T011105635536Z-ae586ffd",
            },
        )
        self.assertEqual(
            {summary["benchmark_commit_sha"] for summary in summaries},
            {"56fcbde7b54d05f3bc4da3813c5ecffb14320a35"},
        )
        self.assertEqual(
            {summary["benchmark_fingerprint"]["task_set_sha256"] for summary in summaries},
            {"f8d19cb89d347d1397f85bf978e6b7b232e8a2f1307fc2ac6ba02674e5c23c9f"},
        )
        for summary in summaries:
            self.assertEqual(summary["task_count"], 54)
            self.assertEqual(summary["model"], "claude-opus-4.6")
            self.assertEqual(summary["harness_type"], "no-tools-model")
            self.assertEqual(summary["passed_count"], 33)
            self.assertEqual(summary["mean_score"], 0.8444)
            self.assertEqual(summary["exploit_proven_task_count"], 14)
            self.assertEqual(summary["exploit_proven_success_rate"], 0.6667)
            self.assertEqual(summary["boundary_reasoning_pass_rate"], 0.0)
            self.assertEqual(summary["vulnerable_full_pass_count"], 0)
            self.assertEqual(summary["false_positive_rate"], 0.0)
            self.assertEqual(summary["invalid_submission_count"], 0)
            self.assertEqual(summary["scored_submission_finding_total"], 21)
            self.assertEqual(summary["model_output_failure_count"], 0)
            self.assertEqual(summary["kiro_command_failure_count"], 0)
            self.assertEqual(summary["missing_submission_json_count"], 0)
            self.assertEqual(summary["runner_agent_failure_count"], 0)
            self.assertEqual(summary["model_output_failures"], [])

    def test_current_tool_agent_pair_preserves_live_correlation_and_planner_diagnostics(self) -> None:
        registry = load_json(REGISTRY)
        entry = _baseline_by_id(registry, CURRENT_TOOL_AGENT_54_ID)
        summaries = [load_json(REGISTRY.parent / path) for path in entry["run_artifacts"]]

        self.assertEqual(
            {summary["run_id"] for summary in summaries},
            {
                "20260608T013814005961Z-9c4b9351",
                "20260608T014504973620Z-1a19b7fb",
            },
        )
        self.assertEqual(
            {summary["benchmark_commit_sha"] for summary in summaries},
            {"60322f319a8492aa0feb78f77b9eef5a098f35bd"},
        )
        self.assertEqual(
            {summary["benchmark_fingerprint"]["task_set_sha256"] for summary in summaries},
            {"f8d19cb89d347d1397f85bf978e6b7b232e8a2f1307fc2ac6ba02674e5c23c9f"},
        )
        self.assertEqual(
            {
                summary["run_id"]: summary["executed_tool_probe_total"]
                for summary in summaries
            },
            {
                "20260608T013814005961Z-9c4b9351": 123,
                "20260608T014504973620Z-1a19b7fb": 126,
            },
        )
        for summary in summaries:
            self.assertEqual(summary["task_count"], 54)
            self.assertEqual(summary["model"], "claude-sonnet-4.6")
            self.assertEqual(summary["agent"], "kiro_live_tool_agent")
            self.assertEqual(summary["harness_type"], "tool-agent")
            self.assertEqual(summary["passed_count"], 33)
            self.assertEqual(summary["mean_score"], 0.8472)
            self.assertEqual(summary["exploit_proven_task_count"], 15)
            self.assertEqual(summary["exploit_proven_success_rate"], 0.7143)
            self.assertEqual(summary["boundary_reasoning_pass_rate"], 0.0)
            self.assertEqual(summary["vulnerable_full_pass_count"], 0)
            self.assertEqual(summary["false_positive_rate"], 0.0)
            self.assertEqual(summary["invalid_submission_count"], 0)
            self.assertEqual(summary["model_tool_plan_artifact_count"], 54)
            self.assertEqual(summary["per_task_tool_probe_artifact_count"], 54)
            self.assertEqual(summary["target_request_correlated_task_count"], 54)
            self.assertEqual(summary["target_request_coverage_rate"], 1.0)
            self.assertEqual(summary["planner_failure_count"], 0)
            self.assertEqual(summary["planner_parse_error_count"], 0)
            self.assertEqual(summary["scored_submission_finding_total"], 20)
            self.assertEqual(summary["submitted_finding_total"], 20)
            self.assertEqual(summary["fallback_probe_total"], 0)
            self.assertEqual(summary["target_log_dir"], "captures/request-logs-tool-agent-current-54")

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
            tool_entry = _baseline_by_id(registry, CURRENT_TOOL_AGENT_54_ID)
            tool_entry["release_suitability"] = "current_public_split"
            tool_entry["expected_task_count"] = 54
            summary_path = registry_path.parent / tool_entry["summary_path"]
            summary = load_json(summary_path)
            summary["model_tool_plan_artifact_count"] = 54
            summary["per_task_tool_probe_artifact_count"] = 54
            summary["target_request_correlated_task_count"] = 53
            summary["target_request_coverage_rate"] = 0.9815
            summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("correlate target requests for all 54 tasks" in error for error in result["errors"]), result)
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

    def test_current_entry_without_provenance_fields_fails_hard(self) -> None:
        """A current_public_split entry that lacks any of the required
        provenance fields (model_name, model_version, scaffold_name,
        run_date, evidence_status) must be rejected with a hard
        error, not just a warning. This is the
        goal-external-validation-coverage.md objective-1 hard CI
        gate.
        """
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            current = _baseline_by_id(registry, CURRENT_SCRIPTED_63_ID)
            for field in (
                "model_name",
                "model_version",
                "scaffold_name",
                "run_date",
                "evidence_status",
            ):
                current.pop(field, None)
            registry_path.write_text(
                json.dumps(registry, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any(
                "missing required provenance fields" in error
                and CURRENT_SCRIPTED_63_ID in error
                for error in result["errors"]
            ),
            result,
        )

    def test_current_adapter_promotion_guard_requires_complete_zero_failure_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            entry = _baseline_by_id(registry, "kiro-qwen3-coder-next-current-public-63")
            entry["requires_zero_adapter_failures"] = True
            summary_paths = {entry["summary_path"], *entry["run_artifacts"]}
            for summary_path in summary_paths:
                path = registry_path.parent / summary_path
                summary = load_json(path)
                summary.update(
                    {
                        "model_output_artifact_count": entry["expected_task_count"],
                        "adapter_failure_count": 0,
                        "model_label_unverified_count": 0,
                        "invalid_submission_count": 0,
                    }
                )
                path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            accepted = validate_registry(registry_path)

            primary_path = registry_path.parent / entry["summary_path"]
            failing_primary = load_json(primary_path)
            failing_primary["adapter_failure_count"] = 1
            primary_path.write_text(
                json.dumps(failing_primary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            primary_rejected = validate_registry(registry_path)

            failing_primary["adapter_failure_count"] = 0
            primary_path.write_text(
                json.dumps(failing_primary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            failing_summary = load_json(registry_path.parent / entry["run_artifacts"][1])
            failing_summary["adapter_failure_count"] = 1
            (registry_path.parent / entry["run_artifacts"][1]).write_text(
                json.dumps(failing_summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            repeated_rejected = validate_registry(registry_path)

        self.assertTrue(accepted["passed"], accepted)
        for rejected in (primary_rejected, repeated_rejected):
            self.assertFalse(rejected["passed"], rejected)
            self.assertTrue(
                any(
                    "adapter_failure_count 1 does not satisfy requires_zero_adapter_failures=0" in error
                    for error in rejected["errors"]
                ),
                rejected,
            )

    def test_accepts_current_promoted_composite_with_explicit_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            _add_synthetic_promoted_composite_entry(registry_path)

            result = validate_registry(registry_path)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["current_public_model_family_count"], 7, result)
        self.assertEqual(result["repeated_model_baseline_count"], 8, result)

    def test_rejects_current_promoted_composite_without_explicit_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry, entry = _add_synthetic_promoted_composite_entry(registry_path)
            promoted = _baseline_by_id(registry, entry["id"])
            promoted.pop("delta_summary_paths")
            promoted["not_full_rerun"] = False
            registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            result = validate_registry(registry_path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("promoted composite entry missing fields" in error for error in result["errors"]), result)
        self.assertTrue(any("not_full_rerun=true" in error for error in result["errors"]), result)

    def test_stale_entry_missing_provenance_emits_warning_only(self) -> None:
        """A stale entry (current_public_stale or legacy_snapshot)
        is allowed to use the legacy field set. Missing provenance
        fields on a stale entry must surface as a warning, not a
        hard error, so legacy evidence rows still validate.
        """
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = _copy_registry_workspace(Path(tmp))
            registry = load_json(registry_path)
            stale = _baseline_by_id(registry, STALE_QWEN_ID)
            for field in (
                "model_name",
                "model_version",
                "scaffold_name",
                "run_date",
                "evidence_status",
            ):
                stale.pop(field, None)
            registry_path.write_text(
                json.dumps(registry, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            result = validate_registry(registry_path)

        self.assertTrue(
            any(
                "historical entry missing provenance fields" in warning
                and STALE_QWEN_ID in warning
                for warning in result["warnings"]
            ),
            result,
        )
        self.assertFalse(
            any(
                "missing required provenance fields" in error
                and STALE_QWEN_ID in error
                for error in result["errors"]
            ),
            result,
        )


if __name__ == "__main__":
    unittest.main()
