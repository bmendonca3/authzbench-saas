from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validate_v1_readiness import (
    _benchmark_source_compatibility_errors,
    _private_pack_fingerprint,
    _source_summaries_have_private_denial,
    _validate_external_review_evidence,
    _validate_hosted_execution_evidence,
    _validate_private_rotation_metadata,
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
        self.assertFalse(gates["stable_v1_prep_public_evidence"]["passed"])
        self.assertIn(
            "fewer than six current public model families are registered",
            gates["stable_v1_prep_public_evidence"]["unmet"],
        )
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
        self.assertEqual(
            rotation_gate["unmet"],
            ["private holdout rotation is intentionally not inspected in public view"],
        )
        self.assertIn("validated_private_holdout_task_count=0", rotation_gate["evidence"])

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
