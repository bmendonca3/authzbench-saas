from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from datetime import date
from pathlib import Path
from unittest.mock import patch

from scripts import validate_v2_external_validation as MODULE


ROOT = Path(__file__).resolve().parents[1]


class _ReviewFixture:
    def __init__(self, root: Path, *, complete: bool) -> None:
        self.root = root
        self.registry_path = root / "docs/reviews/external-review-registry.json"
        self.summary_json_path = root / "docs/reviews/external-review-summary.json"
        self.summary_md_path = root / "docs/reviews/external-review-summary.md"
        self.saas_registry_path = (
            root / "docs/reviews/saas-product-security-review-registry.json"
        )
        self.reviewed_artifact = root / "docs/review-evidence.md"
        self._seed_review_candidate()
        self.reviewed_sha = self._git("rev-parse", "HEAD")
        if complete:
            self.registry = self._complete_registry()
            self.summary = self._complete_summary()
            self.saas_registry = self._complete_saas_registry()
        else:
            self.registry = self._pending_registry()
            self.summary = self._pending_summary()
            self.saas_registry = self._pending_saas_registry()
        self.write()

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

    def _seed_review_candidate(self) -> None:
        schema_paths = {
            contract["schema"]
            for contract in MODULE.registry_validator.LANE_CONTRACTS.values()
        } | {MODULE.saas_validator.SCHEMA_PATH}
        packet_paths = {
            contract["packet"]
            for contract in MODULE.registry_validator.LANE_CONTRACTS.values()
        } | {MODULE.saas_validator.PACKET_PATH}
        for relative in sorted(schema_paths):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())
        for relative in sorted(packet_paths):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(f"# {Path(relative).stem}\n", encoding="utf-8")
        for relative in sorted(MODULE.MANDATORY_REVIEW_SOURCE_FILES):
            destination = self.root / relative
            if destination.exists():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                f"Frozen review source: {relative}\n",
                encoding="utf-8",
            )
        task = self.root / "tasks/example/task-1.json"
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_text('{"id": "task-1"}\n', encoding="utf-8")
        self.reviewed_artifact.parent.mkdir(parents=True, exist_ok=True)
        self.reviewed_artifact.write_text(
            "# Frozen external-review evidence\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.name", "bmendonca3"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "bmendonca3@example.com"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "freeze external-review candidate"],
            cwd=self.root,
            check=True,
        )

    @staticmethod
    def _lane_metadata(lane_id: str) -> dict[str, object]:
        contract = MODULE.registry_validator.LANE_CONTRACTS[lane_id]
        return {
            "lane": lane_id,
            "reviewer_role": contract["reviewer_role"],
            "packet": contract["packet"],
            "schema": contract["schema"],
        }

    def _complete_registry(self) -> dict[str, object]:
        review_date = date.today().isoformat()
        appsec_record = {
            "reviewer_role": "AppSec reviewer",
            "review_date": review_date,
            "reviewed_commit_sha": self.reviewed_sha,
            "pack_id": "public",
            "task_id": "task-1",
            "realistic": 4,
            "oracle_clear": 4,
            "boundary_valid": 4,
            "false_positive_control_meaningful": 4,
            "unsafe_ambiguity": 4,
            "difficulty_estimate": "single-step-with-decoy",
            "blocking_issue": False,
            "comments_public_safe": "Public task review completed.",
        }
        evals_record = {
            "reviewer_role": "Benchmark / evals reviewer",
            "review_date": review_date,
            "reviewed_commit_sha": self.reviewed_sha,
            "split_design_acceptable": 4,
            "scoring_semantics_clear": 4,
            "determinism_contract_holds": 4,
            "variance_framing_acceptable": 4,
            "stale_current_separation_clear": 4,
            "leaderboard_tiers_acceptable": 4,
            "anti_gaming_policy_acceptable": 4,
            "claim_boundary_enforcement_acceptable": 4,
            "private_cluster_assignment_reviewed": True,
            "public_private_cluster_disjointness_verified": True,
            "minimum_analysis_artifact": "docs/review-evidence.md",
            "minimum_scored_task_count": 24,
            "minimum_semantic_cluster_count": 8,
            "cohort_methodology_decision": "accept",
            "blocking_issues": [],
            "nonblocking_issues": [],
            "comments_public_safe": "Methodology review completed.",
        }
        tooling_record = {
            "reviewer_role": "AI-agent / tooling reviewer",
            "review_date": review_date,
            "reviewed_commit_sha": self.reviewed_sha,
            "harness_contract_clear": 4,
            "tool_access_requirements_enforceable": 4,
            "transcript_schema_replayable": 4,
            "target_request_correlation_enforced": 4,
            "submission_bundle_validator_acceptable": 4,
            "harbor_status_table_consistent": 4,
            "tool_agent_comparability_keys_acceptable": 4,
            "blocking_issues": [],
            "nonblocking_issues": [],
            "comments_public_safe": "Tooling review completed.",
        }
        records = {
            "appsec": [appsec_record],
            "benchmark_evals": [evals_record],
            "agent_tooling": [tooling_record],
        }
        lanes: list[dict[str, object]] = []
        for lane_id in MODULE.registry_validator.REQUIRED_LANE_IDS:
            lanes.append(
                {
                    **self._lane_metadata(lane_id),
                    "review_status": "complete",
                    "reviewer_id": f"independent-{lane_id}-reviewer",
                    "review_date": review_date,
                    "reviewed_commit_sha": self.reviewed_sha,
                    "overall_disposition": "accept",
                    "blocking_issues": [],
                    "nonblocking_issues": [],
                    "per_task_records": records[lane_id],
                }
            )
        return {
            "schema_version": "external-review-registry-v1",
            "description": "Public-safe independent external-review registry.",
            "lanes": lanes,
        }

    def _pending_registry(self) -> dict[str, object]:
        lanes = []
        for lane_id in MODULE.registry_validator.REQUIRED_LANE_IDS:
            lanes.append(
                {
                    **self._lane_metadata(lane_id),
                    "review_status": "pending",
                    "reviewer_id": None,
                    "review_date": None,
                    "reviewed_commit_sha": None,
                    "overall_disposition": None,
                    "blocking_issues": [],
                    "nonblocking_issues": [],
                    "per_task_records": [],
                }
            )
        return {
            "schema_version": "external-review-registry-v1",
            "description": "Public-safe independent external-review registry.",
            "lanes": lanes,
        }

    @staticmethod
    def _no_finding_decision() -> dict[str, str]:
        return {
            "finding": "No finding.",
            "decision": "rejected",
            "summary": "No change is needed.",
            "claim_boundary_impact": "No claim-boundary change.",
        }

    def _complete_summary(self) -> dict[str, object]:
        review_date = date.today().isoformat()
        lanes = []
        for lane_name, lane_id in MODULE.REVIEW_LANE_IDS.items():
            lanes.append(
                {
                    "lane": lane_name,
                    "registry_lane_id": lane_id,
                    "review_status": "complete",
                    "review_date": review_date,
                    "reviewed_commit_sha": self.reviewed_sha,
                    "reviewer_role_scope": f"Independent reviewer for {lane_name}.",
                    "overall_disposition": "accept",
                    "claim_boundary_impact": "No claim-boundary expansion.",
                    "questions_reviewed": ["Is the bounded review contract acceptable?"],
                    "artifacts_reviewed": ["docs/review-evidence.md"],
                    "disposition": "no_findings",
                    "decisions": [self._no_finding_decision()],
                }
            )
        return {
            "schema_version": "external-review-summary-v1",
            "claim_boundary": "All recorded reviews remain bounded to the frozen candidate.",
            "review_lanes": lanes,
        }

    @staticmethod
    def _pending_summary() -> dict[str, object]:
        lanes = []
        for lane_name in MODULE.REQUIRED_REVIEW_LANES:
            lanes.append(
                {
                    "lane": lane_name,
                    "review_status": "pending",
                    "requested_artifacts": ["docs/review-evidence.md"],
                    "requested_questions": ["Is the bounded review contract acceptable?"],
                    "blocker": "An independent reviewer has not returned a disposition.",
                    "next_action": "Recruit the independent reviewer.",
                }
            )
        return {
            "schema_version": "external-review-summary-v1",
            "claim_boundary": "No independent external validation is claimed.",
            "review_lanes": lanes,
        }

    def _complete_saas_registry(self) -> dict[str, object]:
        review_date = date.today().isoformat()
        apps = sorted(MODULE.saas_validator.REQUIRED_APPS)
        families = sorted(MODULE.saas_validator.REQUIRED_FAMILIES)
        records = [
            {
                "reviewer_role": "SaaS product-security reviewer",
                "review_date": review_date,
                "reviewed_commit_sha": self.reviewed_sha,
                "app_id": apps[index % len(apps)],
                "vulnerability_family": family,
                "auth_model_fidelity": 4,
                "control_realism": 4,
                "scoring_validity": 4,
                "coverage_adequacy": 4,
                "synthetic_gap_severity": 2,
                "blocking_issue": False,
                "comments_public_safe": "Public-safe product-security review.",
            }
            for index, family in enumerate(families)
        ]
        return {
            "schema_version": "saas-product-security-review-registry-v1",
            "claim_boundary": "A distinct product-security review of the frozen candidate.",
            "packet": MODULE.saas_validator.PACKET_PATH,
            "schema": MODULE.saas_validator.SCHEMA_PATH,
            "review_status": "complete",
            "reviewer_id": "independent-saas-product-security-reviewer",
            "review_date": review_date,
            "reviewed_commit_sha": self.reviewed_sha,
            "overall_disposition": "accept",
            "blocking_issues": [],
            "nonblocking_issues": [],
            "records": records,
            "blocker": None,
            "next_action": None,
        }

    @staticmethod
    def _pending_saas_registry() -> dict[str, object]:
        return {
            "schema_version": "saas-product-security-review-registry-v1",
            "claim_boundary": "This pending record does not claim product-security validation.",
            "packet": MODULE.saas_validator.PACKET_PATH,
            "schema": MODULE.saas_validator.SCHEMA_PATH,
            "review_status": "pending",
            "reviewer_id": None,
            "review_date": None,
            "reviewed_commit_sha": None,
            "overall_disposition": None,
            "blocking_issues": [],
            "nonblocking_issues": [],
            "records": [],
            "blocker": "An independent product-security review has not completed.",
            "next_action": "Recruit a distinct product-security reviewer.",
        }

    def write(self) -> None:
        for path, payload in (
            (self.registry_path, self.registry),
            (self.summary_json_path, self.summary),
            (self.saas_registry_path, self.saas_registry),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.summary_md_path.write_text(
            "\n".join(
                [
                    "# External Review Summary",
                    *MODULE.REQUIRED_REVIEW_LANES,
                    f"Reviewed commit: {self.reviewed_sha}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def commit_unbound_file(self, relative_path: str, content: str) -> str:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "--", relative_path], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", f"add {relative_path}"],
            cwd=self.root,
            check=True,
        )
        return self._git("rev-parse", "HEAD")


class V2ExternalValidationTests(unittest.TestCase):
    @contextmanager
    def _fixture(self, *, complete: bool):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = _ReviewFixture(Path(temp_dir), complete=complete)
            with ExitStack() as stack:
                stack.enter_context(patch.object(MODULE, "ROOT", fixture.root))
                stack.enter_context(
                    patch.object(MODULE, "REGISTRY_PATH", fixture.registry_path)
                )
                stack.enter_context(
                    patch.object(MODULE, "SUMMARY_JSON_PATH", fixture.summary_json_path)
                )
                stack.enter_context(
                    patch.object(MODULE, "SUMMARY_MD_PATH", fixture.summary_md_path)
                )
                stack.enter_context(
                    patch.object(MODULE.registry_validator, "ROOT", fixture.root)
                )
                stack.enter_context(
                    patch.object(
                        MODULE.registry_validator,
                        "REGISTRY_PATH",
                        fixture.registry_path,
                    )
                )
                stack.enter_context(
                    patch.object(
                        MODULE.registry_validator,
                        "SUMMARY_PATH",
                        fixture.summary_md_path,
                    )
                )
                stack.enter_context(
                    patch.object(
                        MODULE.registry_validator,
                        "EXPECTED_PUBLIC_TASK_COUNT",
                        1,
                    )
                )
                stack.enter_context(
                    patch.object(MODULE.saas_validator, "ROOT", fixture.root)
                )
                stack.enter_context(
                    patch.object(
                        MODULE.saas_validator,
                        "REGISTRY_PATH",
                        fixture.saas_registry_path,
                    )
                )
                stack.enter_context(
                    patch.object(
                        MODULE.cohort_validator,
                        "validate",
                        return_value={
                            "passed": True,
                            "methodology_complete": complete,
                            "errors": [],
                        },
                    )
                )
                yield fixture

    def test_pending_default_passes_without_claiming_completion_and_strict_fails(self) -> None:
        with self._fixture(complete=False):
            default = MODULE.validate()
            strict = MODULE.validate(require_complete=True)

        self.assertTrue(default["passed"], default["findings"])
        self.assertFalse(default["external_validation_complete"])
        self.assertFalse(default["three_lane_validation_complete"])
        self.assertFalse(default["saas_product_security_validation_complete"])
        self.assertFalse(default["cohort_methodology_complete"])
        self.assertFalse(strict["passed"])
        self.assertFalse(strict["external_validation_complete"])

    def test_strict_complete_coherent_review_surfaces_pass(self) -> None:
        with self._fixture(complete=True):
            result = MODULE.validate(require_complete=True)

        self.assertTrue(result["passed"], result["findings"])
        self.assertTrue(result["external_validation_complete"])

    def test_cross_surface_disposition_or_date_divergence_fails(self) -> None:
        with self._fixture(complete=True) as fixture:
            fixture.summary["review_lanes"][0]["review_date"] = "2025-01-02"
            fixture.write()
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertIn(
            "appsec: review_date differs between registry and summary",
            result["findings"],
        )

    def test_rejected_lane_cannot_complete_external_validation(self) -> None:
        with self._fixture(complete=True) as fixture:
            fixture.registry["lanes"][0]["overall_disposition"] = "reject"
            fixture.summary["review_lanes"][0]["overall_disposition"] = "reject"
            fixture.write()
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertTrue(
            any("overall_disposition must be accepted" in item for item in result["findings"]),
            result["findings"],
        )

    def test_unresolved_decision_cannot_complete_external_validation(self) -> None:
        with self._fixture(complete=True) as fixture:
            fixture.summary["review_lanes"][0]["disposition"] = "findings"
            fixture.summary["review_lanes"][0]["decisions"] = [
                {
                    "finding": "One reviewer concern remains.",
                    "decision": "unresolved",
                    "summary": "The concern has not been resolved.",
                    "claim_boundary_impact": "External validation remains blocked.",
                    "follow_up_artifact": "docs/review-evidence.md",
                }
            ]
            fixture.write()
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertTrue(
            any("must be resolved for external validation" in item for item in result["findings"]),
            result["findings"],
        )

    def test_accepted_finding_requires_post_review_remediation(self) -> None:
        with self._fixture(complete=True) as fixture:
            fixture.summary["review_lanes"][0]["disposition"] = "findings"
            fixture.summary["review_lanes"][0]["decisions"] = [
                {
                    "finding": "Clarify the reviewed evidence.",
                    "decision": "accepted",
                    "summary": "The clarification is accepted.",
                    "claim_boundary_impact": "Validation depends on the clarification.",
                    "follow_up_artifact": "docs/review-evidence.md",
                }
            ]
            fixture.write()
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertTrue(
            any(
                "accepted decisions require committed post-review remediation"
                in item
                for item in result["findings"]
            ),
            result["findings"],
        )

    def test_committed_post_review_remediation_can_satisfy_accepted_finding(self) -> None:
        with self._fixture(complete=True) as fixture:
            fixture.commit_unbound_file(
                "docs/review-follow-up.md",
                "# Committed remediation after the frozen review candidate\n",
            )
            fixture.summary["review_lanes"][0]["disposition"] = "findings"
            fixture.summary["review_lanes"][0]["overall_disposition"] = (
                "accept_with_minor_changes"
            )
            fixture.registry["lanes"][0]["overall_disposition"] = (
                "accept_with_minor_changes"
            )
            fixture.summary["review_lanes"][0]["decisions"] = [
                {
                    "finding": "Add a bounded remediation note.",
                    "decision": "accepted",
                    "summary": "The committed follow-up resolves the finding.",
                    "claim_boundary_impact": "No claim expansion.",
                    "follow_up_artifact": "docs/review-follow-up.md",
                }
            ]
            fixture.write()
            result = MODULE.validate(require_complete=True)

        self.assertTrue(result["passed"], result["findings"])
        self.assertTrue(result["external_validation_complete"])

    def test_mixed_reviewed_shas_across_saas_and_three_lanes_fail(self) -> None:
        with self._fixture(complete=True) as fixture:
            second_sha = fixture.commit_unbound_file(
                "docs/post-review-administration.md",
                "# Administrative evidence only\n",
            )
            fixture.saas_registry["reviewed_commit_sha"] = second_sha
            for record in fixture.saas_registry["records"]:
                record["reviewed_commit_sha"] = second_sha
            fixture.write()
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertIn(
            "strict external validation requires all three lanes and the SaaS lane to review one frozen commit",
            result["findings"],
        )

    def test_reviewed_artifact_drift_after_frozen_sha_fails(self) -> None:
        with self._fixture(complete=True) as fixture:
            fixture.reviewed_artifact.write_text(
                "# Changed after independent review\n",
                encoding="utf-8",
            )
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertIn(
            "review artifact changed after reviewed commit: docs/review-evidence.md",
            result["findings"],
        )

    def test_mandatory_app_source_drift_fails_even_when_reviewer_omits_it(self) -> None:
        with self._fixture(complete=True) as fixture:
            source = fixture.root / "apps/example/authorization.py"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("ALLOW_ALL = True\n", encoding="utf-8")
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertIn(
            "reviewed commit does not contain declared review artifact: "
            "apps/example/authorization.py",
            result["findings"],
        )

    def test_mandatory_scorer_source_drift_fails_without_summary_declaration(self) -> None:
        with self._fixture(complete=True) as fixture:
            source = fixture.root / "authzbench/score.py"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("SCORE_POLICY = 'changed-after-review'\n", encoding="utf-8")
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertIn(
            "reviewed commit does not contain declared review artifact: "
            "authzbench/score.py",
            result["findings"],
        )

    def test_strict_gate_requires_distinct_saas_product_security_lane(self) -> None:
        with self._fixture(complete=True) as fixture:
            fixture.saas_registry = fixture._pending_saas_registry()
            fixture.write()
            result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertTrue(
            any(
                "SaaS product-security lane: review_status is not 'complete'"
                in item
                for item in result["findings"]
            ),
            result["findings"],
        )

    def test_strict_gate_requires_completed_cohort_methodology(self) -> None:
        with self._fixture(complete=True):
            with patch.object(
                MODULE.cohort_validator,
                "validate",
                return_value={
                    "passed": False,
                    "methodology_complete": False,
                    "errors": ["cohort methodology decision is pending"],
                },
            ):
                result = MODULE.validate(require_complete=True)

        self.assertFalse(result["passed"])
        self.assertFalse(result["external_validation_complete"])
        self.assertIn(
            "cohort methodology: cohort methodology decision is pending",
            result["findings"],
        )


if __name__ == "__main__":
    unittest.main()
