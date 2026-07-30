from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_external_review_summary.py"
SPEC = importlib.util.spec_from_file_location("validate_external_review_summary", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _lane(lane_id: str, status: str = "pending") -> dict[str, object]:
    complete = status == "complete"
    contract = MODULE.LANE_CONTRACTS.get(
        lane_id,
        {
            "reviewer_role": f"{lane_id} reviewer",
            "packet": f"docs/reviews/{lane_id}.md",
            "schema": f"docs/reviews/schemas/{lane_id}.schema.json",
        },
    )
    reviewed_commit_sha = "a" * 40
    review_date = date.today().isoformat()
    records: list[dict[str, object]] = []
    if complete and lane_id == "appsec":
        records = [
            {
                "reviewer_role": contract["reviewer_role"],
                "review_date": review_date,
                "reviewed_commit_sha": reviewed_commit_sha,
                "pack_id": "public",
                "task_id": task_id,
                "realistic": 4,
                "oracle_clear": 4,
                "boundary_valid": 4,
                "false_positive_control_meaningful": 4,
                "unsafe_ambiguity": 4,
                "difficulty_estimate": "single-step-with-decoy",
                "blocking_issue": False,
                "comments_public_safe": "Public task review completed.",
            }
            for task_id in sorted(
                json.loads(path.read_text(encoding="utf-8"))["id"]
                for path in (ROOT / "tasks").glob("*/*.json")
            )
        ]
    elif complete and lane_id == "benchmark_evals":
        records = [
            {
                "reviewer_role": contract["reviewer_role"],
                "review_date": review_date,
                "reviewed_commit_sha": reviewed_commit_sha,
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
        ]
    elif complete and lane_id == "agent_tooling":
        records = [
            {
                "reviewer_role": contract["reviewer_role"],
                "review_date": review_date,
                "reviewed_commit_sha": reviewed_commit_sha,
                "harness_contract_clear": 4,
                "tool_access_requirements_enforceable": 4,
                "transcript_schema_replayable": 4,
                "target_request_correlation_enforced": 4,
                "submission_bundle_validator_acceptable": 4,
                "harbor_status_table_consistent": 4,
                "tool_agent_comparability_keys_acceptable": 4,
                "blocking_issues": [],
                "nonblocking_issues": [],
                "comments_public_safe": "Agent tooling review completed.",
            }
        ]
    return {
        "lane": lane_id,
        "reviewer_role": contract["reviewer_role"],
        "packet": contract["packet"],
        "schema": contract["schema"],
        "review_status": status,
        "reviewer_id": "independent-reviewer" if complete else None,
        "review_date": review_date if complete else None,
        "reviewed_commit_sha": reviewed_commit_sha if complete else None,
        "overall_disposition": "accept" if complete else None,
        "blocking_issues": [],
        "nonblocking_issues": [],
        "per_task_records": records,
    }


def _registry() -> dict[str, object]:
    return {
        "schema_version": "external-review-registry-v1",
        "description": (
            "Public-safe registry for the three independent external review lanes."
        ),
        "lanes": [_lane(lane_id) for lane_id in MODULE.REQUIRED_LANE_IDS],
    }


class ExternalReviewSummaryValidatorTests(unittest.TestCase):
    def test_registry_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            registry_path = temp_root / "registry.json"
            registry_path.write_text(
                '{"schema_version":"external-review-registry-v1",'
                '"schema_version":"external-review-registry-v1","lanes":[]}',
                encoding="utf-8",
            )
            with (
                patch.object(MODULE, "ROOT", temp_root),
                patch.object(MODULE, "REGISTRY_PATH", registry_path),
            ):
                result = MODULE.validate()
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("duplicate JSON key" in finding for finding in result["findings"]),
            result["findings"],
        )

    def test_registry_rejects_nonfinite_json_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            registry_path = temp_root / "registry.json"
            registry_path.write_text(
                '{"schema_version":"external-review-registry-v1",'
                '"description":NaN,"lanes":[]}',
                encoding="utf-8",
            )
            with (
                patch.object(MODULE, "ROOT", temp_root),
                patch.object(MODULE, "REGISTRY_PATH", registry_path),
            ):
                result = MODULE.validate()
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("non-finite JSON number" in finding for finding in result["findings"]),
            result["findings"],
        )

    def _validate(
        self,
        registry: dict[str, object],
        require_complete: bool = False,
        mutate_root=None,
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            registry_path = temp_root / "registry.json"
            summary_path = temp_root / "summary.md"
            shutil.copytree(ROOT / "tasks", temp_root / "tasks")
            for contract in MODULE.LANE_CONTRACTS.values():
                for field in ("packet", "schema"):
                    source = ROOT / contract[field]
                    destination = temp_root / contract[field]
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(source.read_bytes())
            if mutate_root is not None:
                mutate_root(temp_root)
            subprocess.run(["git", "init", "-q"], cwd=temp_root, check=True)
            subprocess.run(["git", "config", "user.name", "bmendonca3"], cwd=temp_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "bmendonca3@example.com"],
                cwd=temp_root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=temp_root, check=True)
            subprocess.run(["git", "commit", "-qm", "seed review contract"], cwd=temp_root, check=True)
            reviewed_commit_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=temp_root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            registry_copy = copy.deepcopy(registry)
            for lane in registry_copy.get("lanes", []):
                if not isinstance(lane, dict):
                    continue
                if lane.get("reviewed_commit_sha") == "a" * 40:
                    lane["reviewed_commit_sha"] = reviewed_commit_sha
                for record in lane.get("per_task_records", []):
                    if isinstance(record, dict) and record.get("reviewed_commit_sha") == "a" * 40:
                        record["reviewed_commit_sha"] = reviewed_commit_sha
            registry_path.write_text(json.dumps(registry_copy), encoding="utf-8")
            with patch.object(MODULE, "ROOT", temp_root), patch.object(
                MODULE, "REGISTRY_PATH", registry_path
            ), patch.object(MODULE, "SUMMARY_PATH", summary_path):
                return MODULE.validate(require_v2_complete=require_complete)

    def test_canonical_pending_lanes_pass_without_v2_completion(self) -> None:
        result = self._validate(_registry())
        self.assertTrue(result["passed"])
        self.assertFalse(result["v2_external_validation_complete"])

    def test_exact_canonical_complete_lanes_are_required_for_v2_completion(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]
        result = self._validate(registry, require_complete=True)
        self.assertTrue(result["passed"])
        self.assertTrue(result["v2_external_validation_complete"])

    def test_rejected_lane_never_yields_v2_validation_completion(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]
        registry["lanes"][0]["overall_disposition"] = "reject"

        structural = self._validate(registry)
        strict = self._validate(registry, require_complete=True)

        self.assertTrue(structural["passed"])
        self.assertFalse(structural["v2_external_validation_complete"])
        self.assertFalse(strict["passed"])
        self.assertFalse(strict["v2_external_validation_complete"])
        self.assertIn(
            "appsec: overall_disposition must be accepted under --require-v2-complete",
            strict["findings"],
        )

    def test_missing_lane_fails_closed(self) -> None:
        registry = _registry()
        registry["lanes"] = copy.deepcopy(registry["lanes"][:-1])
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertFalse(result["v2_external_validation_complete"])
        self.assertIn("missing required review lanes: agent_tooling", result["findings"])

    def test_duplicate_lane_fails_closed(self) -> None:
        registry = _registry()
        registry["lanes"] = copy.deepcopy(registry["lanes"])
        registry["lanes"][-1] = copy.deepcopy(registry["lanes"][0])
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertFalse(result["v2_external_validation_complete"])
        self.assertIn("duplicate review lanes: appsec", result["findings"])
        self.assertIn("missing required review lanes: agent_tooling", result["findings"])

    def test_unexpected_lane_fails_closed(self) -> None:
        registry = _registry()
        registry["lanes"] = copy.deepcopy(registry["lanes"])
        registry["lanes"].append(_lane("saas_provider"))
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertFalse(result["v2_external_validation_complete"])
        self.assertIn("unexpected review lanes: saas_provider", result["findings"])

    def test_complete_lane_requires_review_records(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]
        registry["lanes"][1]["per_task_records"] = []
        result = self._validate(registry, require_complete=True)
        self.assertFalse(result["passed"])
        self.assertIn(
            "benchmark_evals: complete review requires non-empty per_task_records",
            result["findings"],
        )

    def test_complete_lane_record_must_match_schema(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]
        del registry["lanes"][2]["per_task_records"][0]["harness_contract_clear"]
        result = self._validate(registry, require_complete=True)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("missing schema-required field 'harness_contract_clear'" in item for item in result["findings"]),
            result["findings"],
        )

    def test_complete_lane_record_must_match_reviewed_commit(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]
        registry["lanes"][1]["per_task_records"][0]["reviewed_commit_sha"] = "b" * 40
        result = self._validate(registry, require_complete=True)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("reviewed_commit_sha: must match the lane-level value" in item for item in result["findings"]),
            result["findings"],
        )

    def test_complete_lane_reviewed_commit_must_exist(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]
        registry["lanes"][0]["reviewed_commit_sha"] = "0" * 40
        registry["lanes"][0]["per_task_records"][0]["reviewed_commit_sha"] = "0" * 40
        result = self._validate(registry, require_complete=True)
        self.assertFalse(result["passed"])
        self.assertIn(
            "appsec: reviewed_commit_sha must reference an existing commit",
            result["findings"],
        )

    def test_complete_lane_rejects_record_blocking_issue(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]
        registry["lanes"][0]["per_task_records"][0]["blocking_issue"] = True
        result = self._validate(registry, require_complete=True)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("unresolved blocking issue" in item for item in result["findings"]),
            result["findings"],
        )

    def test_pending_lane_rejects_premature_records(self) -> None:
        registry = _registry()
        registry["lanes"][0]["per_task_records"] = _lane("appsec", "complete")["per_task_records"]
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertIn("appsec: pending lane must not contain review records", result["findings"])

    def test_registry_rejects_unknown_top_level_fields(self) -> None:
        registry = _registry()
        registry["private_route"] = "redacted"
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertIn("unexpected registry fields: private_route", result["findings"])

    def test_registry_rejects_unknown_lane_fields(self) -> None:
        registry = _registry()
        registry["lanes"][0]["private_route"] = "redacted"
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertIn(
            "appsec: unexpected lane fields: private_route",
            result["findings"],
        )

    def test_registry_rejects_non_string_issue_records(self) -> None:
        registry = _registry()
        registry["lanes"][0]["nonblocking_issues"] = [
            {"task_id": "private-example-id"}
        ]
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertIn(
            "appsec: nonblocking_issues must contain concrete public-safe strings",
            result["findings"],
        )

    def test_registry_rejects_private_markers_at_any_depth(self) -> None:
        registry = _registry()
        registry["lanes"][0]["nonblocking_issues"] = [
            "Raw follow-up is under tasks_private/holdout."
        ]
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertIn("registry contains a private-detail marker", result["findings"])

    def test_complete_appsec_lane_requires_public_task_inventory(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]

        def remove_tasks(temp_root):
            shutil.rmtree(temp_root / "tasks")

        result = self._validate(
            registry,
            require_complete=True,
            mutate_root=remove_tasks,
        )
        self.assertFalse(result["passed"])
        self.assertIn("appsec: public task inventory is missing or empty", result["findings"])

    def test_complete_appsec_lane_rejects_malformed_public_manifest(self) -> None:
        registry = _registry()
        registry["lanes"] = [_lane(lane_id, "complete") for lane_id in MODULE.REQUIRED_LANE_IDS]

        def corrupt_task(temp_root):
            first = sorted((temp_root / "tasks").glob("*/*.json"))[0]
            first.write_text("{not json", encoding="utf-8")

        result = self._validate(
            registry,
            require_complete=True,
            mutate_root=corrupt_task,
        )
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("public task manifest is unreadable" in item for item in result["findings"]),
            result["findings"],
        )

    def test_in_progress_records_are_schema_validated(self) -> None:
        registry = _registry()
        lane = registry["lanes"][0]
        lane["review_status"] = "in_progress"
        lane["per_task_records"] = [{"unexpected": "record"}]
        result = self._validate(registry)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("missing schema-required field" in item for item in result["findings"]),
            result["findings"],
        )


if __name__ == "__main__":
    unittest.main()
