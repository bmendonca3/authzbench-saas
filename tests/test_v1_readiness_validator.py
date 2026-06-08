from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts.validate_v1_readiness import (
    EXTERNAL_REVIEW_RESPONSE_TEMPLATE_PATH,
    RELEASE_VALIDATION_TEMPLATE_PATH,
    REQUIRED_RELEASE_VALIDATION_COMMANDS,
    REQUIRED_REVIEW_LANES,
    _benchmark_source_compatibility_errors,
    _private_pack_fingerprint,
    _source_summaries_have_private_denial,
    _validate_external_review_evidence,
    _validate_hosted_execution_evidence,
    _validate_paper_readiness_evidence,
    _validate_private_operation_blocker,
    _validate_private_rotation_metadata,
    _validate_release_candidate_evidence,
    _working_tree_clean,
    validate_v1_readiness,
)


class V1ReadinessValidatorTests(unittest.TestCase):
    def test_current_repo_reports_v1_prep_not_v1_ready(self) -> None:
        result = validate_v1_readiness()
        gates = {gate["id"]: gate for gate in result["gates"]}

        self.assertFalse(result["passed"])
        self.assertFalse(result["v1_ready"])
        self.assertEqual(result["gate_count"], 11)
        self.assertTrue(gates["stable_v1_prep_public_evidence"]["passed"])
        self.assertEqual(gates["stable_v1_prep_public_evidence"]["unmet"], [])
        self.assertTrue(gates["external_review_packet_ready"]["passed"])
        self.assertTrue(gates["submission_governance_spec_defined"]["passed"])
        self.assertFalse(gates["external_review_completed"]["passed"])
        self.assertFalse(gates["hosted_or_containerized_submission_execution"]["passed"])
        self.assertFalse(gates["rotating_private_holdouts_implemented"]["passed"])
        self.assertFalse(gates["repeated_private_tool_agent_evidence"]["passed"])
        self.assertFalse(gates["repeated_private_no_tools_evidence"]["passed"])
        self.assertFalse(gates["v1_task_scale"]["passed"])
        self.assertFalse(gates["paper_and_artifact_readiness"]["passed"])
        self.assertFalse(gates["final_release_candidate_validation"]["passed"])
        self.assertIn(
            "independent external review lanes are not complete",
            gates["external_review_completed"]["unmet"],
        )
        self.assertIn(
            "no repeated eligible private-holdout tool-agent leaderboard row exists",
            gates["repeated_private_tool_agent_evidence"]["unmet"],
        )
        self.assertIn(
            "no repeated eligible private-holdout no-tools model leaderboard row exists",
            gates["repeated_private_no_tools_evidence"]["unmet"],
        )

    def test_strict_cli_fails_until_v1_is_really_ready(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_v1_readiness.py"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn('"v1_ready": false', result.stdout)
        self.assertEqual(result.stderr, "")

    def test_allow_incomplete_cli_passes_for_v1_prep_validation(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_v1_readiness.py", "--allow-incomplete"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn('"v1_ready": false', result.stdout)
        self.assertEqual(result.stderr, "")

    def test_public_view_ignores_private_checkout_rotation_state(self) -> None:
        with patch(
            "scripts.validate_v1_readiness._validate_private_rotation_metadata"
        ) as rotation_validator:
            result = validate_v1_readiness(public_view=True)

        rotation_validator.assert_not_called()
        gates = {gate["id"]: gate for gate in result["gates"]}
        rotation_gate = gates["rotating_private_holdouts_implemented"]
        self.assertFalse(rotation_gate["passed"])
        self.assertIn(
            "private holdout rotation is intentionally not inspected in public view",
            rotation_gate["unmet"],
        )
        self.assertIn(
            "private holdout operation is blocked until active and shadow/candidate private packs and repeated private rows exist",
            rotation_gate["unmet"],
        )
        self.assertIn("artifact/private-holdout-operation-blocker.json", rotation_gate["evidence"])
        self.assertIn("validated_private_holdout_task_count=0", rotation_gate["evidence"])

    def test_private_operation_blocker_is_structured_but_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "private-holdout-operation-blocker.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "private-holdout-operation-blocker-v1",
                        "evidence_status": "blocked",
                        "public_claim_boundary": "Structured blocker evidence only; not v1 private operation.",
                        "blocked_gates": [
                            "rotating_private_holdouts_implemented",
                            "repeated_private_tool_agent_evidence",
                            "repeated_private_no_tools_evidence",
                            "v1_task_scale",
                        ],
                        "blocker": "Needs active and shadow private packs plus repeated private rows.",
                        "next_actions": ["Stage private packs under the maintainer-only holdout root."],
                        "required_private_inputs": ["active private pack", "shadow private pack"],
                        "current_public_view": {
                            "public_task_count": 54,
                            "validated_private_holdout_task_count": 0,
                            "total_task_count": 54,
                            "required_total_task_count": 100,
                        },
                        "last_verified_public_readiness": {
                            "commit_sha": "a" * 40,
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/1",
                            "v1_ready": False,
                            "passed_gate_count": 3,
                            "unmet_gate_count": 8,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_operation_blocker(root, expected_public_task_count=54)

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["unmet"],
            [
                "private holdout operation is blocked until active and shadow/candidate private packs and repeated private rows exist",
            ],
        )

    def test_private_operation_blocker_requires_concrete_public_safe_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "private-holdout-operation-blocker.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "wrong",
                        "evidence_status": "passed",
                        "public_claim_boundary": "TBD",
                        "blocked_gates": ["rotating_private_holdouts_implemented"],
                        "blocker": "TBD",
                        "next_actions": ["TBD"],
                        "required_private_inputs": ["TBD"],
                        "current_public_view": {
                            "public_task_count": 49,
                            "validated_private_holdout_task_count": 1,
                            "total_task_count": 50,
                            "required_total_task_count": 99,
                        },
                        "last_verified_public_readiness": {
                            "commit_sha": "not-a-sha",
                            "ci_run_url": "https://example.com/run",
                            "v1_ready": True,
                            "passed_gate_count": "3",
                            "unmet_gate_count": "8",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_operation_blocker(root, expected_public_task_count=54)

        self.assertFalse(result["passed"])
        self.assertIn("schema_version must be private-holdout-operation-blocker-v1", result["unmet"])
        self.assertIn("evidence_status must be blocked", result["unmet"])
        self.assertIn(
            "blocked_gates must include: repeated_private_tool_agent_evidence, repeated_private_no_tools_evidence, v1_task_scale",
            result["unmet"],
        )
        self.assertIn("blocker is required", result["unmet"])
        self.assertIn("public_claim_boundary is required", result["unmet"])
        self.assertIn("next_actions must list concrete non-placeholder values", result["unmet"])
        self.assertIn("required_private_inputs must list concrete non-placeholder values", result["unmet"])
        self.assertIn("current_public_view.public_task_count must match current public count 54", result["unmet"])
        self.assertIn("current_public_view.validated_private_holdout_task_count must be 0", result["unmet"])
        self.assertIn("current_public_view.total_task_count must equal public_task_count in public view", result["unmet"])
        self.assertIn("current_public_view.required_total_task_count must be 100", result["unmet"])
        self.assertIn(
            "last_verified_public_readiness.commit_sha must be a 40-character lowercase Git SHA",
            result["unmet"],
        )
        self.assertIn(
            "last_verified_public_readiness.ci_run_url must reference an AuthZBench-SaaS Actions run",
            result["unmet"],
        )
        self.assertIn("last_verified_public_readiness.v1_ready must be false", result["unmet"])

    def test_private_operation_blocker_rejects_sensitive_public_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "private-holdout-operation-blocker.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "private-holdout-operation-blocker-v1",
                        "evidence_status": "blocked",
                        "public_claim_boundary": "Structured blocker evidence only; not v1 private operation.",
                        "blocked_gates": [
                            "rotating_private_holdouts_implemented",
                            "repeated_private_tool_agent_evidence",
                            "repeated_private_no_tools_evidence",
                            "v1_task_scale",
                        ],
                        "blocker": "Needs active and shadow private packs plus repeated private rows.",
                        "next_actions": ["Stage private packs without publishing private internals."],
                        "required_private_inputs": ["active private pack", "shadow private pack"],
                        "current_public_view": {
                            "public_task_count": 54,
                            "validated_private_holdout_task_count": 0,
                            "total_task_count": 54,
                            "required_total_task_count": 100,
                        },
                        "last_verified_public_readiness": {
                            "commit_sha": "a" * 40,
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/1",
                            "v1_ready": False,
                            "passed_gate_count": 3,
                            "unmet_gate_count": 8,
                        },
                        "task_id": "private-task-001",
                        "debug_note": "raw output stored under /Users/example/tasks_private/holdout/active",
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_operation_blocker(root, expected_public_task_count=54)

        self.assertFalse(result["passed"])
        self.assertTrue(any("sensitive key is not allowed" in item for item in result["unmet"]), result)
        self.assertTrue(any("sensitive path marker is not allowed" in item for item in result["unmet"]), result)
        self.assertTrue(any("absolute path is not allowed" in item for item in result["unmet"]), result)

    def test_expected_output_fixture_mismatch_fails_even_when_incomplete_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "expected.json"
            fixture.write_text('{"v1_ready": true}\n', encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_v1_readiness.py",
                    "--allow-incomplete",
                    "--public-view",
                    "--expected-output",
                    str(fixture),
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn('"v1_ready": false', result.stdout)
        self.assertIn("does not match expected fixture", result.stderr)

    def test_hosted_smoke_requires_structured_passed_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "result": "failed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1",
                        "private_pack_version": "pack-v1",
                        "isolation_model": "container",
                        "command": "smoke failed; private isolation not passed",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("submission-runner smoke result must be passed", result["unmet"])
        self.assertIn("benchmark_source_sha must match release benchmark_source_sha", result["unmet"])
        self.assertIn("active private pack fingerprint is required for hosted smoke evidence", result["unmet"])
        self.assertIn("schema_version must be submission-runner-smoke-v1", result["unmet"])
        self.assertIn("container_constraints are incomplete", result["unmet"])

    def test_hosted_smoke_requires_active_private_pack_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "result": "passed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1",
                        "private_pack_version": "private-pack-v1",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "container",
                        "command": "run private smoke",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="c" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            "private_pack_fingerprint_sha256 must match the active private pack fingerprint",
            result["unmet"],
        )

    def test_hosted_smoke_release_candidate_evidence_can_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-v1",
                        "execution_scope": "release_candidate",
                        "result": "passed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1@sha256:example",
                        "private_pack_version": "active-pack-v1",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "container-rendered-context-only",
                        "command": "containerized submission smoke",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                        "container_constraints": [
                            "network=none",
                            "read_only_rootfs",
                            "cap_drop=ALL",
                            "no_new_privileges",
                            "non_root_user",
                            "resource_limits",
                            "rendered_context_mount_only",
                            "output_file_size_limit",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertTrue(result["passed"])
        self.assertEqual(result["unmet"], [])

    def test_hosted_smoke_blocked_evidence_is_structured_but_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-blocker-v1",
                        "evidence_status": "blocked",
                        "blocked_gate": "hosted_or_containerized_submission_execution",
                        "blocker": "Needs the active private pack and maintainer-platform release smoke.",
                        "next_action": "Run the release-candidate smoke on the maintainer platform.",
                        "required_release_inputs": [
                            "active private pack path",
                            "active private pack version",
                            "active private pack fingerprint",
                            "maintainer-platform runner image or hosted version",
                        ],
                        "last_verified_public_rehearsal": {
                            "execution_scope": "rehearsal",
                            "result": "passed",
                            "commit_sha": "a" * 40,
                            "ci_run_url": "https://github.com/bmendonca3/authzbench-saas/actions/runs/1",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(root)

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["unmet"],
            [
                "hosted/containerized release-candidate smoke is blocked until active private-pack inputs exist",
            ],
        )

    def test_hosted_smoke_blocked_evidence_requires_specific_release_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-v1",
                        "evidence_status": "blocked",
                        "blocked_gate": "wrong-gate",
                        "blocker": "TBD",
                        "next_action": "TBD",
                        "required_release_inputs": ["TBD"],
                        "last_verified_public_rehearsal": {
                            "execution_scope": "release_candidate",
                            "result": "failed",
                            "commit_sha": "not-a-sha",
                            "ci_run_url": "https://example.com/run",
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("schema_version must be submission-runner-smoke-blocker-v1", result["unmet"])
        self.assertIn("blocked_gate must be hosted_or_containerized_submission_execution", result["unmet"])
        self.assertIn("blocker is required", result["unmet"])
        self.assertIn("next_action is required", result["unmet"])
        self.assertIn("required_release_inputs must list concrete missing release inputs", result["unmet"])
        self.assertIn("last_verified_public_rehearsal.execution_scope must be rehearsal", result["unmet"])
        self.assertIn("last_verified_public_rehearsal.result must be passed", result["unmet"])
        self.assertIn(
            "last_verified_public_rehearsal.commit_sha must be a 40-character lowercase Git SHA",
            result["unmet"],
        )
        self.assertIn(
            "last_verified_public_rehearsal.ci_run_url must reference an AuthZBench-SaaS Actions run",
            result["unmet"],
        )

    def test_hosted_smoke_rejects_rehearsal_execution_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "result": "passed",
                        "execution_scope": "rehearsal",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1",
                        "private_pack_version": "ci-rehearsal",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "container",
                        "command": "run private smoke",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            "submission-runner smoke execution_scope must be release_candidate",
            result["unmet"],
        )
        self.assertIn(
            "rehearsal smoke evidence is not release-candidate evidence",
            result["unmet"],
        )

    def test_hosted_smoke_rejects_sensitive_public_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "artifact" / "submission-runner-smoke.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": "submission-runner-smoke-v1",
                        "execution_scope": "release_candidate",
                        "result": "passed",
                        "benchmark_source_sha": "a" * 40,
                        "runner_image_or_hosted_version": "runner:v1",
                        "private_pack_version": "private-pack-v1",
                        "private_pack_fingerprint_sha256": "b" * 64,
                        "isolation_model": "container",
                        "command": "read /Users/example/tasks_private/holdout",
                        "submitter_private_manifest_read_denied": True,
                        "scorer_controlled_private_eval": True,
                        "cleanup_completed": True,
                        "privacy_scan_passed": True,
                        "public_output_private_artifacts_included": False,
                        "container_constraints": [
                            "network=none",
                            "read_only_rootfs",
                            "cap_drop=ALL",
                            "no_new_privileges",
                            "non_root_user",
                            "resource_limits",
                            "rendered_context_mount_only",
                            "output_file_size_limit",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_hosted_execution_evidence(
                root,
                benchmark_source_sha="a" * 40,
                private_pack_fingerprint_sha256="b" * 64,
            )

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("sensitive path marker" in error for error in result["unmet"]),
            result["unmet"],
        )

    def test_external_review_completion_requires_structured_lane_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "TBD",
                                "reviewer_role_scope": "TBD",
                                "claim_boundary_impact": "TBD",
                                "artifacts_reviewed": ["missing.md"],
                                "disposition": "findings",
                                "decisions": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("Application security: review_date must use YYYY-MM-DD", result["unmet"])
        self.assertIn("Application security: reviewer_role_scope is required", result["unmet"])
        self.assertIn("Application security: claim_boundary_impact is required", result["unmet"])
        self.assertIn("Application security: reviewed artifact does not exist: missing.md", result["unmet"])
        self.assertIn("missing structured review lanes: AI-agent/tooling, Benchmark/evals methodology", result["unmet"])

    def test_external_review_pending_lanes_are_structured_but_not_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "reviews").mkdir(parents=True)
            (root / "docs" / "reviews" / "external-review-packet.md").write_text("# packet\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_status": "pending",
                                "requested_artifacts": ["docs/reviews/external-review-packet.md"],
                                "requested_questions": ["Are task boundaries realistic?"],
                                "blocker": "Needs an independent AppSec reviewer.",
                                "next_action": "Recruit reviewer.",
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_status": "pending",
                                "requested_artifacts": ["docs/reviews/external-review-packet.md"],
                                "requested_questions": ["Are scoring semantics valid?"],
                                "blocker": "Needs an independent evals reviewer.",
                                "next_action": "Recruit reviewer.",
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_status": "pending",
                                "requested_artifacts": ["docs/reviews/external-review-packet.md"],
                                "requested_questions": ["Are harness assumptions inspectable?"],
                                "blocker": "Needs an independent tooling reviewer.",
                                "next_action": "Recruit reviewer.",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["lanes"],
            ["AI-agent/tooling", "Application security", "Benchmark/evals methodology"],
        )
        self.assertEqual(
            result["unmet"],
            [
                "Application security: independent review is pending",
                "Benchmark/evals methodology: independent review is pending",
                "AI-agent/tooling: independent review is pending",
            ],
        )

    def test_external_review_pending_lanes_require_real_packet_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_status": "pending",
                                "requested_artifacts": ["missing.md"],
                                "requested_questions": ["TBD"],
                                "blocker": "TBD",
                                "next_action": "TBD",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("Application security: requested artifact does not exist: missing.md", result["unmet"])
        self.assertIn("Application security: pending review requires requested_questions", result["unmet"])
        self.assertIn("Application security: pending review requires blocker", result["unmet"])
        self.assertIn("Application security: pending review requires next_action", result["unmet"])
        self.assertIn("Application security: independent review is pending", result["unmet"])

    def test_external_review_response_template_lists_every_required_lane(self) -> None:
        template = json.loads(Path(EXTERNAL_REVIEW_RESPONSE_TEMPLATE_PATH).read_text(encoding="utf-8"))

        self.assertTrue(template["template_only"])
        self.assertEqual(
            {lane["lane"] for lane in template["review_lanes"]},
            set(REQUIRED_REVIEW_LANES),
        )
        for lane in template["review_lanes"]:
            self.assertEqual(lane["review_status"], "complete")
            self.assertIn("review_date", lane)
            self.assertIn("reviewer_role_scope", lane)
            self.assertIn("claim_boundary_impact", lane)
            self.assertIn("artifacts_reviewed", lane)
            self.assertIn("disposition", lane)
            self.assertIn("decisions", lane)

    def test_external_review_response_template_is_not_review_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = root / "docs" / "reviews" / "external-review-summary.json"
            summary.parent.mkdir(parents=True)
            summary.write_text(
                Path(EXTERNAL_REVIEW_RESPONSE_TEMPLATE_PATH).read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("external review response template is not external review evidence", result["unmet"])

    def test_external_review_public_evidence_rejects_sensitive_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Reviewer confirmed claim boundary.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Reviewer cited raw private output in notes.",
                                        "decision": "rejected",
                                        "claim_boundary_impact": "Private detail must stay out of public evidence.",
                                        "task_id": "private-task-id",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("sensitive key is not allowed in public external review evidence" in error for error in result["unmet"]),
            result["unmet"],
        )
        self.assertTrue(
            any(
                "sensitive path marker is not allowed in public external review evidence" in error
                for error in result["unmet"]
            ),
            result["unmet"],
        )

    def test_external_review_complete_lanes_can_pass_with_real_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reviewed_artifact = root / "docs" / "reviews" / "external-review-packet.md"
            reviewed_artifact.parent.mkdir(parents=True)
            reviewed_artifact.write_text("# packet\n", encoding="utf-8")
            follow_up = root / "docs" / "reviews" / "application-security-review-follow-up.md"
            follow_up.write_text("# follow-up\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "bmendonca3"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "bmendonca3@example.com"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "seed review artifacts"], cwd=root, check=True)
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_status": "complete",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "Independent AppSec reviewer for SaaS authorization tasks.",
                                "claim_boundary_impact": "Review accepted one task-language clarification.",
                                "artifacts_reviewed": ["docs/reviews/external-review-packet.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "decision": "accepted",
                                        "finding": "Secure-control wording could be clearer.",
                                        "summary": "Clarify secure-control wording.",
                                        "claim_boundary_impact": "No score claim change; documentation wording only.",
                                        "follow_up_artifact": "docs/reviews/application-security-review-follow-up.md",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_status": "complete",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "Independent benchmark methodology reviewer.",
                                "claim_boundary_impact": "No release-claim changes requested.",
                                "artifacts_reviewed": ["docs/reviews/external-review-packet.md"],
                                "disposition": "no_findings",
                                "decisions": [
                                    {
                                        "decision": "rejected",
                                        "finding": "No methodology finding.",
                                        "summary": "No methodology changes needed.",
                                        "claim_boundary_impact": "No release-claim change.",
                                    }
                                ],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_status": "complete",
                                "review_date": date.today().isoformat(),
                                "reviewer_role_scope": "Independent AI-agent tooling reviewer.",
                                "claim_boundary_impact": "No harness-claim changes requested.",
                                "artifacts_reviewed": ["docs/reviews/external-review-packet.md"],
                                "disposition": "no_findings",
                                "decisions": [
                                    {
                                        "decision": "rejected",
                                        "finding": "No tooling finding.",
                                        "summary": "No tooling changes needed.",
                                        "claim_boundary_impact": "No harness-claim change.",
                                    }
                                ],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "add review evidence"], cwd=root, check=True)

            result = _validate_external_review_evidence(root)

        self.assertTrue(result["passed"])
        self.assertEqual(result["unmet"], [])

    def test_external_review_decisions_reject_placeholder_follow_up_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "TBD",
                                        "decision": "accepted",
                                        "follow_up_artifact": "TBD",
                                        "claim_boundary_impact": "TBD",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("Application security: decisions[1].finding is required", result["unmet"])
        self.assertIn(
            "Application security: accepted or unresolved decisions require a real follow_up_artifact path or existing commit",
            result["unmet"],
        )
        self.assertIn("Application security: decisions[1].claim_boundary_impact is required", result["unmet"])

    def test_external_review_decisions_reject_nonexistent_commit_follow_up_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Add denied-control evidence.",
                                        "decision": "accepted",
                                        "follow_up_artifact": "deadbee",
                                        "claim_boundary_impact": "Evidence gate remains open.",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "Application security: accepted or unresolved decisions require a real follow_up_artifact path or existing commit",
            result["unmet"],
        )

    def test_external_review_decisions_reject_format_only_github_follow_up_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Add denied-control evidence.",
                                        "decision": "accepted",
                                        "follow_up_artifact": "https://github.com/bmendonca3/authzbench-saas/issues/foo",
                                        "claim_boundary_impact": "Evidence gate remains open.",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "Application security: accepted or unresolved decisions require a real follow_up_artifact path or existing commit",
            result["unmet"],
        )

    def test_external_review_decisions_reject_directory_follow_up_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# artifact\n", encoding="utf-8")
            evidence = root / "docs" / "reviews" / "external-review-summary.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "review_lanes": [
                            {
                                "lane": "Application security",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External appsec reviewer",
                                "claim_boundary_impact": "Narrowed one task-realism claim.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "findings",
                                "decisions": [
                                    {
                                        "finding": "Add denied-control evidence.",
                                        "decision": "accepted",
                                        "follow_up_artifact": ".",
                                        "claim_boundary_impact": "Evidence gate remains open.",
                                    }
                                ],
                            },
                            {
                                "lane": "Benchmark/evals methodology",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External evals reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                            {
                                "lane": "AI-agent/tooling",
                                "review_date": "2026-06-07",
                                "reviewer_role_scope": "External agent tooling reviewer",
                                "claim_boundary_impact": "No claim-boundary changes.",
                                "artifacts_reviewed": ["README.md"],
                                "disposition": "no_findings",
                                "decisions": [],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_external_review_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn(
            "Application security: accepted or unresolved decisions require a real follow_up_artifact path or existing commit",
            result["unmet"],
        )

    def test_rotation_metadata_requires_validated_active_and_candidate_packs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = root / "tasks_private" / "holdout" / "rotation-metadata.json"
            invalid_pack = root / "tasks_private" / "holdout" / "active-pack" / "billing"
            invalid_pack.mkdir(parents=True)
            (invalid_pack / "not-a-task.json").write_text('{"not": "a task manifest"}', encoding="utf-8")
            metadata.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "active-pack",
                                "role": "active",
                                "path": "tasks_private/holdout/active-pack",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_rotation_metadata(root)

        self.assertFalse(result["passed"])
        self.assertIn("active-pack: private pack manifests do not validate", result["unmet"])
        self.assertIn("rotation metadata must declare one shadow or candidate private pack", result["unmet"])

    def test_rotation_metadata_rejects_duplicate_pack_paths(self) -> None:
        manifest = {
            "id": "private_task_one",
            "app": "billing",
            "seed": "private-seed",
            "expected_vulnerable": True,
            "allowed_hosts": ["localhost"],
            "policy": "private",
            "objective": "Prove private task.",
            "output_schema": {"type": "object"},
            "oracle": {"expected": True},
            "controls": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = root / "tasks_private" / "holdout" / "shared-pack" / "billing"
            pack.mkdir(parents=True)
            (pack / "private_task_one.json").write_text(json.dumps(manifest), encoding="utf-8")
            metadata = root / "tasks_private" / "holdout" / "rotation-metadata.json"
            metadata.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "active-pack",
                                "role": "active",
                                "path": "tasks_private/holdout/shared-pack",
                            },
                            {
                                "id": "candidate-pack",
                                "role": "candidate",
                                "path": "tasks_private/holdout/shared-pack",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_private_rotation_metadata(root)

        self.assertFalse(result["passed"])
        self.assertIn("candidate-pack: pack path duplicates another declared private pack", result["unmet"])

    def test_rotation_metadata_compares_declared_private_pack_structures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            holdout = root / "tasks_private" / "holdout"
            for pack_name in ("active-pack", "candidate-pack"):
                pack = holdout / pack_name / "billing"
                pack.mkdir(parents=True)
                (pack / "task.json").write_text("{}\n", encoding="utf-8")
            metadata = holdout / "rotation-metadata.json"
            metadata.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "active-pack",
                                "role": "active",
                                "path": "tasks_private/holdout/active-pack",
                            },
                            {
                                "id": "candidate-pack",
                                "role": "candidate",
                                "path": "tasks_private/holdout/candidate-pack",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            invalid_result = {
                "passed": False,
                "leaderboard_suitable": False,
                "manifest_count": 0,
            }

            with patch(
                "scripts.validate_v1_readiness.validate_holdout_pack",
                return_value=invalid_result,
            ) as validator:
                result = _validate_private_rotation_metadata(root)

        self.assertFalse(result["passed"])
        self.assertEqual(validator.call_count, 2)
        first_comparison = validator.call_args_list[0].kwargs["comparison_private_patterns"]
        second_comparison = validator.call_args_list[1].kwargs["comparison_private_patterns"]
        self.assertEqual(first_comparison, [])
        self.assertEqual(len(second_comparison), 1)
        self.assertIn("active-pack", second_comparison[0])

    def test_clean_tree_check_rejects_untracked_inputs_except_release_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "initial",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            evidence = root / "release-evidence.json"
            evidence.write_text("{}\n", encoding="utf-8")
            self.assertTrue(_working_tree_clean(root, {evidence.resolve()}))

            (root / "untracked-task.json").write_text("{}\n", encoding="utf-8")
            self.assertFalse(_working_tree_clean(root, {evidence.resolve()}))

    def _source_and_release_with_changed_path(self, changed_path: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            path = root / changed_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "source",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            source_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            path.write_text("release\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "release",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            release_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()

            return _benchmark_source_compatibility_errors(root, source_sha, release_sha)

    def test_benchmark_source_rejects_ancestor_with_task_changes(self) -> None:
        errors = self._source_and_release_with_changed_path("tasks/billing/task.json")

        self.assertIn("release-affecting files changed after benchmark_source_sha: tasks/billing/task.json", errors)

    def test_benchmark_source_rejects_ancestor_with_docker_topology_changes(self) -> None:
        errors = self._source_and_release_with_changed_path("docker-compose.yml")

        self.assertIn("release-affecting files changed after benchmark_source_sha: docker-compose.yml", errors)

    def test_benchmark_source_rejects_ancestor_with_paper_build_changes(self) -> None:
        errors = self._source_and_release_with_changed_path("paper/ieee-sp/main.tex")

        self.assertIn("release-affecting files changed after benchmark_source_sha: paper/ieee-sp/main.tex", errors)

    def test_benchmark_source_allows_narrow_evidence_record_changes(self) -> None:
        errors = self._source_and_release_with_changed_path("artifact/submission-runner-smoke.json")

        self.assertEqual(errors, [])

    def test_paper_readiness_allows_only_narrow_post_source_evidence_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "paper" / "ieee-sp").mkdir(parents=True)
            (root / "paper" / "ieee-sp" / "main.tex").write_text("source\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "source",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            source_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "benchmark_source_sha": source_sha,
                        "claim_boundary_reviewed": True,
                        "generated_paper_tables_clean": True,
                        "charts_current_stale_legacy_labeled": True,
                        "latexmk_main_tex_passed": True,
                        "evidence_scope": "release_candidate",
                        "upstream_review_and_infrastructure_complete": True,
                    }
                ),
                encoding="utf-8",
            )
            fixture = root / "artifact" / "expected-output" / "v1-readiness-public-view.json"
            fixture.parent.mkdir(parents=True)
            fixture.write_text("{}\n", encoding="utf-8")
            (root / "docs" / "goal.md").write_text("paper evidence\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "evidence",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            release_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()

            result = _validate_paper_readiness_evidence(
                root,
                release_sha=release_sha,
                allowed_post_source_paths={
                    "docs/v1-paper-readiness.json",
                    "artifact/expected-output/v1-readiness-public-view.json",
                    "docs/goal.md",
                },
                upstream_gates_complete=True,
            )

        self.assertTrue(result["passed"])
        self.assertEqual(result["unmet"], [])

    def test_paper_readiness_rejects_release_affecting_post_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text("{}\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "source",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            source_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            evidence.write_text(
                json.dumps(
                    {
                        "benchmark_source_sha": source_sha,
                        "claim_boundary_reviewed": True,
                        "generated_paper_tables_clean": True,
                        "charts_current_stale_legacy_labeled": True,
                        "latexmk_main_tex_passed": True,
                        "evidence_scope": "release_candidate",
                        "upstream_review_and_infrastructure_complete": True,
                    }
                ),
                encoding="utf-8",
            )
            paper = root / "paper" / "ieee-sp" / "main.tex"
            paper.parent.mkdir(parents=True)
            paper.write_text("changed after source\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "release-affecting change",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            release_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()

            result = _validate_paper_readiness_evidence(
                root,
                release_sha=release_sha,
                allowed_post_source_paths={
                    "docs/v1-paper-readiness.json",
                    "artifact/expected-output/v1-readiness-public-view.json",
                    "docs/goal.md",
                },
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            "release-affecting files changed after benchmark_source_sha: paper/ieee-sp/main.tex",
            result["unmet"],
        )

    def test_paper_readiness_rejects_non_sha_benchmark_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "benchmark_source_sha": "tbd",
                        "claim_boundary_reviewed": True,
                        "generated_paper_tables_clean": True,
                        "charts_current_stale_legacy_labeled": True,
                        "latexmk_main_tex_passed": True,
                        "evidence_scope": "release_candidate",
                        "upstream_review_and_infrastructure_complete": True,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_paper_readiness_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("benchmark_source_sha must be a 40-character lowercase Git SHA", result["unmet"])

    def test_paper_readiness_rejects_self_referential_release_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
            (root / "seed.txt").write_text("seed\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=bmendonca3",
                    "-c",
                    "user.email=bmendonca3@users.noreply.github.com",
                    "commit",
                    "-m",
                    "release",
                ],
                cwd=root,
                check=True,
                stdout=subprocess.PIPE,
            )
            release_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "benchmark_source_sha": release_sha,
                        "claim_boundary_reviewed": True,
                        "generated_paper_tables_clean": True,
                        "charts_current_stale_legacy_labeled": True,
                        "latexmk_main_tex_passed": True,
                        "evidence_scope": "release_candidate",
                        "upstream_review_and_infrastructure_complete": True,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_paper_readiness_evidence(root, release_sha=release_sha)

        self.assertFalse(result["passed"])
        self.assertIn(
            "benchmark_source_sha must reference an ancestor commit, not the release commit",
            result["unmet"],
        )

    def test_paper_readiness_rejects_mismatch_with_release_evidence_sha(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "benchmark_source_sha": "a" * 40,
                        "claim_boundary_reviewed": True,
                        "generated_paper_tables_clean": True,
                        "charts_current_stale_legacy_labeled": True,
                        "latexmk_main_tex_passed": True,
                        "evidence_scope": "release_candidate",
                        "upstream_review_and_infrastructure_complete": True,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_paper_readiness_evidence(root, benchmark_source_sha="b" * 40)

        self.assertFalse(result["passed"])
        self.assertIn("benchmark_source_sha must match release benchmark_source_sha", result["unmet"])

    def test_paper_readiness_rejects_self_attested_upstream_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "docs" / "v1-paper-readiness.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps(
                    {
                        "benchmark_source_sha": "a" * 40,
                        "claim_boundary_reviewed": True,
                        "generated_paper_tables_clean": True,
                        "charts_current_stale_legacy_labeled": True,
                        "latexmk_main_tex_passed": True,
                        "evidence_scope": "release_candidate",
                        "upstream_review_and_infrastructure_complete": True,
                    }
                ),
                encoding="utf-8",
            )

            result = _validate_paper_readiness_evidence(root)

        self.assertFalse(result["passed"])
        self.assertIn("live upstream review and infrastructure gates must pass", result["unmet"])

    def test_release_candidate_template_lists_every_required_command(self) -> None:
        template = json.loads((Path(RELEASE_VALIDATION_TEMPLATE_PATH)).read_text(encoding="utf-8"))

        self.assertTrue(template["template_only"])
        self.assertEqual(
            set(template["commands"]),
            set(REQUIRED_RELEASE_VALIDATION_COMMANDS),
        )
        for command in REQUIRED_RELEASE_VALIDATION_COMMANDS:
            self.assertIn("passed", template["commands"][command])
            self.assertNotEqual(template["commands"][command]["passed"], True)

    def test_release_candidate_template_is_not_release_evidence(self) -> None:
        result = _validate_release_candidate_evidence(
            evidence_path=Path(RELEASE_VALIDATION_TEMPLATE_PATH),
            target_sha="a" * 40,
            private_pack_fingerprint_sha256="b" * 64,
        )

        self.assertFalse(result["passed"])
        self.assertIn("release validation template is not release-candidate evidence", result["unmet"])

    def test_private_pack_fingerprint_changes_when_manifest_content_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            app = pack / "billing"
            app.mkdir()
            manifest = app / "task.json"
            manifest.write_text(json.dumps({"id": "private-task", "seed": "one"}), encoding="utf-8")
            first = _private_pack_fingerprint(pack)

            manifest.write_text(json.dumps({"id": "private-task", "seed": "two"}), encoding="utf-8")
            second = _private_pack_fingerprint(pack)

        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertRegex(second, r"^[0-9a-f]{64}$")
        self.assertNotEqual(first, second)

    def test_source_summary_private_denial_rejects_stale_private_pack_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source-summary.json"
            submission = root / "submission.json"
            source.write_text(
                json.dumps(
                    {
                        "protected_execution": {"host_private_paths_denied": True},
                        "private_pack_fingerprint_sha256": "0" * 64,
                    }
                ),
                encoding="utf-8",
            )
            submission_data = {
                "source_run_summaries": [source.name],
                "private_pack_fingerprint_sha256": "0" * 64,
            }
            submission.write_text(json.dumps(submission_data), encoding="utf-8")

            matches = _source_summaries_have_private_denial(
                submission,
                submission_data,
                private_pack_fingerprint_sha256="1" * 64,
            )

        self.assertFalse(matches)


if __name__ == "__main__":
    unittest.main()
