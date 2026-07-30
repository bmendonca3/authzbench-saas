from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.build_leaderboard_submission import build_submission
from scripts.protected_private_eval import ROOT, redacted_summary
from scripts.validate_leaderboard_submission import (
    _load_public_private_pack_metadata,
    validate_submission,
)

SYNTHETIC_COMMIT_SHA = "a" * 40
SYNTHETIC_SOURCE_FINGERPRINT = {
    "source_path_set_sha256": "b" * 64,
    "source_set_sha256": "c" * 64,
}


def _active_private_pack_fingerprint() -> str:
    """Return the public blocker artifact's role=active fingerprint."""
    for fingerprint, pack in _load_public_private_pack_metadata().items():
        if pack.get("role") == "active":
            return fingerprint
    raise RuntimeError("public blocker metadata has no active private pack")


def _runner_summary(run_id: str) -> dict:
    fingerprint = _active_private_pack_fingerprint()
    pack = _load_public_private_pack_metadata()[fingerprint]
    return {
        "agent": "unit-agent",
        "adapter_json_only_compliant_count": 24,
        "adapter_json_only_compliance_rate": 1.0,
        "authorized_allow_control_task_count": 6,
        "authorized_allow_pass_rate": 1.0,
        "benchmark_commit_sha": SYNTHETIC_COMMIT_SHA,
        "benchmark_execution_status": "completed",
        "benchmark_fingerprint": {
            "authorized_allow_control_task_count": 6,
            "control_task_count": 12,
            "denial_control_task_count": 6,
            "evidence_contract_version": "evidence-requirements-v2-deny-then-bypass",
            "schema_version": "benchmark-fingerprint-v2",
            "score_policy_version": "score-policy-v3-evidence-chain-observed-safety",
            "scorer_contract": "authz-evidence-chain-v3-observed-mutation-safety",
            **SYNTHETIC_SOURCE_FINGERPRINT,
            "task_count": 24,
            "task_path_set_sha256": "b" * 64,
            "task_set_sha256": "c" * 64,
            "vulnerable_task_count": 12,
        },
        "benchmark_source_state": "exact-commit-clean",
        "benchmark_version": "unit-version",
        "boundary_reasoning_pass_rate": 0.25,
        "control_execution_pass_rate": 1.0,
        "control_false_report_count": 0,
        "control_false_report_rate": 0.0,
        "control_task_count": 12,
        "core_passed_count": 15,
        "denial_control_task_count": 6,
        "evidence_chain_complete_count": 12,
        "evaluation_protocol": {
            "protocol_version": "blinded-control-evidence-v1",
            "participant_context_profile": "blinded-evaluation-v1",
            "candidate_evidence_mode": "host-replayed-bounded-requests",
            "control_verification_required": True,
        },
        "exploit_proven_success_rate": 0.25,
        "exploit_proven_task_count": 3,
        "false_positive_rate": 0.0,
        "harness_type": "no-tools-model",
        "infrastructure_failure_count": 0,
        "invalid_submission_count": 0,
        "invalid_submission_rate": 0.0,
        "mean_score": 0.625,
        "model": "unit-model",
        "model_identity_status": "verified",
        "model_identity_status_counts": {"verified": 24},
        "model_label_verified_task_count": 24,
        "requested_model_labels": ["unit-model"],
        "requested_model_label_match_task_count": 24,
        "effective_model_labels": ["unit-model"],
        "effective_model_label_match_task_count": 24,
        "private_pack_id": pack["id"],
        "private_pack_version": pack["version"],
        "private_pack_fingerprint_sha256": fingerprint,
        "private_pack_loaded_fingerprint_sha256": fingerprint,
        "private_pack_fingerprint_provenance": "runner-computed-loaded-manifests",
        "promotion_eligible_count": 15,
        "promotion_eligibility_rate": 0.625,
        "protected_execution": {
            "agent_cwd": "temporary-empty-workspace",
            "agent_received": "rendered-context-only",
            "host_private_paths_denied": True,
            "isolation_backend": "unit-test",
            "private_manifests_readable_in_agent_workspace": False,
            "raw_result_bundle_tracked": False,
            "tracked_private_manifest_count": 0,
        },
        "run_id": run_id,
        "safety_observation_status_counts": {"observed_pass": 24},
        "safety_violations": 0,
        "target_request_correlated_task_count": 24,
        "target_request_coverage_rate": 1.0,
        "task_count": 24,
        "task_completion_count": 24,
        "tasks": [
            {
                "task_id": f"private-unit-task-{index:02d}",
                "adapter_model_output_sha256": hashlib.sha256(
                    f"{run_id}:private-unit-task-{index:02d}".encode("utf-8")
                ).hexdigest(),
            }
            for index in range(1, 25)
        ],
        "v0_mean_score": 0.625,
        "v0_metric_profile": "v0-candidate-authz-evidence",
        "v0_passed_count": 15,
        "vulnerable_full_pass_count": 3,
        "vulnerable_safety_observation_coverage_rate": 1.0,
        "vulnerable_safety_pass_rate": 1.0,
        "vulnerable_task_count": 12,
    }


class BuildLeaderboardSubmissionTests(unittest.TestCase):
    def test_runner_redacted_summaries_build_an_eligible_validated_row(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            paths = []
            for run_id in ("unit-run-1", "unit-run-2"):
                path = root / f"{run_id}.json"
                path.write_text(
                    json.dumps(redacted_summary(_runner_summary(run_id)), indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                paths.append(path)
            with patch(
                "scripts.validate_leaderboard_submission._benchmark_source_fingerprint_at_commit",
                return_value=(SYNTHETIC_SOURCE_FINGERPRINT, None),
            ):
                row = build_submission(
                    paths,
                    primary_run_id="unit-run-2-redacted",
                    baseline_kind="model_baseline",
                    leaderboard_eligible=True,
                )
            submission_path = root / "submission.json"
            submission_path.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with patch(
                "scripts.validate_leaderboard_submission._benchmark_source_fingerprint_at_commit",
                return_value=(SYNTHETIC_SOURCE_FINGERPRINT, None),
            ):
                result = validate_submission(submission_path, require_source_summary=True)

        self.assertTrue(result["passed"], result)
        self.assertTrue(result["leaderboard_eligible"], result)
        self.assertEqual(row["run_count"], 2)
        self.assertEqual(row["variance_or_ci"], "stddev=0.0000")

    def test_cross_commit_repeat_cannot_be_eligible(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            first = redacted_summary(_runner_summary("unit-run-1"))
            second_summary = _runner_summary("unit-run-2")
            second_summary["benchmark_commit_sha"] = "d" * 40
            second = redacted_summary(second_summary)
            paths = []
            for name, summary in (("one.json", first), ("two.json", second)):
                path = root / name
                path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                paths.append(path)
            def synthetic_source_binding(commit_sha: str):
                if commit_sha == SYNTHETIC_COMMIT_SHA:
                    return SYNTHETIC_SOURCE_FINGERPRINT, None
                return None, "benchmark_commit_sha does not match the synthetic source freeze"

            with patch(
                "scripts.validate_leaderboard_submission._benchmark_source_fingerprint_at_commit",
                side_effect=synthetic_source_binding,
            ):
                with self.assertRaisesRegex(ValueError, "benchmark_commit_sha"):
                    build_submission(
                        paths,
                        primary_run_id="unit-run-2-redacted",
                        baseline_kind="model_baseline",
                        leaderboard_eligible=True,
                    )

    def test_missing_protected_adapter_root_cannot_build_an_eligible_row(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            paths = []
            for run_id in ("unit-run-1", "unit-run-2"):
                summary = redacted_summary(_runner_summary(run_id))
                summary["runner_integrity"].pop("adapter_artifact_set_sha256")
                path = root / f"{run_id}.json"
                path.write_text(
                    json.dumps(summary, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                paths.append(path)

            with patch(
                "scripts.validate_leaderboard_submission._benchmark_source_fingerprint_at_commit",
                return_value=(SYNTHETIC_SOURCE_FINGERPRINT, None),
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "runner_integrity|adapter_artifact_set_sha256",
                ):
                    build_submission(
                        paths,
                        primary_run_id="unit-run-2-redacted",
                        baseline_kind="model_baseline",
                        leaderboard_eligible=True,
                    )

    def test_shadow_private_pack_cannot_build_an_eligible_row(self) -> None:
        packs = _load_public_private_pack_metadata()
        shadow_fingerprint, shadow_pack = next(
            (fingerprint, pack)
            for fingerprint, pack in packs.items()
            if pack.get("role") == "shadow"
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            paths = []
            for run_id in ("unit-run-1", "unit-run-2"):
                raw = _runner_summary(run_id)
                raw.update(
                    {
                        "private_pack_id": shadow_pack["id"],
                        "private_pack_version": shadow_pack["version"],
                        "private_pack_fingerprint_sha256": shadow_fingerprint,
                        "private_pack_loaded_fingerprint_sha256": shadow_fingerprint,
                    }
                )
                path = root / f"{run_id}.json"
                path.write_text(
                    json.dumps(redacted_summary(raw), indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                paths.append(path)

            with patch(
                "scripts.validate_leaderboard_submission._benchmark_source_fingerprint_at_commit",
                return_value=(SYNTHETIC_SOURCE_FINGERPRINT, None),
            ):
                with self.assertRaisesRegex(ValueError, "only role=active"):
                    build_submission(
                        paths,
                        primary_run_id="unit-run-2-redacted",
                        baseline_kind="model_baseline",
                        leaderboard_eligible=True,
                    )

    def test_legacy_score_policy_sources_cannot_build_an_eligible_row(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            summary = redacted_summary(_runner_summary("legacy-policy-run"))
            summary["benchmark_fingerprint"].update(
                {
                    "schema_version": "benchmark-fingerprint-v1",
                    "score_policy_version": "score-policy-v1",
                    "scorer_contract": "v0-candidate-authz-evidence",
                    "evidence_contract_version": "evidence-requirements-v1",
                }
            )
            summary["benchmark_fingerprint"].pop("source_set_sha256")
            summary["benchmark_fingerprint"].pop("source_path_set_sha256")
            path = root / "legacy.json"
            path.write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "score-policy-v3"):
                build_submission(
                    [path],
                    primary_run_id="legacy-policy-run-redacted",
                    baseline_kind="model_baseline",
                    leaderboard_eligible=True,
                )

    def test_unobserved_safety_cannot_build_an_eligible_row(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp)
            summary = redacted_summary(_runner_summary("unobserved-safety-run"))
            summary["safety_observation_status_counts"] = {"unobserved": 24}
            summary["vulnerable_safety_observation_coverage_rate"] = 0.0
            path = root / "unobserved.json"
            path.write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with patch(
                "scripts.validate_leaderboard_submission._benchmark_source_fingerprint_at_commit",
                return_value=(SYNTHETIC_SOURCE_FINGERPRINT, None),
            ):
                with self.assertRaisesRegex(ValueError, "safety_observation_status_counts"):
                    build_submission(
                        [path],
                        primary_run_id="unobserved-safety-run-redacted",
                        baseline_kind="model_baseline",
                        leaderboard_eligible=True,
                    )


if __name__ == "__main__":
    unittest.main()
