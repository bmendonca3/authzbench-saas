from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT_PATH = SCRIPTS / "validate_saas_product_security_review.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_saas_product_security_review",
    SCRIPT_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _pending_registry() -> dict[str, object]:
    return {
        "schema_version": "saas-product-security-review-registry-v1",
        "claim_boundary": (
            "This pending registry is public-safe intake, not SaaS-provider "
            "validation or product-security endorsement."
        ),
        "packet": MODULE.PACKET_PATH,
        "schema": MODULE.SCHEMA_PATH,
        "review_status": "pending",
        "reviewer_id": None,
        "review_date": None,
        "reviewed_commit_sha": None,
        "overall_disposition": None,
        "blocking_issues": [],
        "nonblocking_issues": [],
        "records": [],
        "blocker": "An independent SaaS product-security reviewer has not responded.",
        "next_action": "Freeze a commit and obtain public-safe app and family records.",
    }


def _complete_registry(reviewed_commit_sha: str) -> dict[str, object]:
    registry = _pending_registry()
    registry.update(
        {
            "review_status": "complete",
            "reviewer_id": "independent-product-security-reviewer",
            "review_date": date.today().isoformat(),
            "reviewed_commit_sha": reviewed_commit_sha,
            "overall_disposition": "accept",
            "blocker": None,
            "next_action": None,
        }
    )
    apps = sorted(MODULE.REQUIRED_APPS)
    families = sorted(MODULE.REQUIRED_FAMILIES)
    registry["records"] = [
        {
            "reviewer_role": "SaaS product-security reviewer",
            "review_date": date.today().isoformat(),
            "reviewed_commit_sha": reviewed_commit_sha,
            "app_id": apps[index % len(apps)],
            "vulnerability_family": family,
            "auth_model_fidelity": 4,
            "control_realism": 4,
            "scoring_validity": 4,
            "coverage_adequacy": 4,
            "synthetic_gap_severity": 2,
            "blocking_issue": False,
            "comments_public_safe": "Public-safe realism review record.",
        }
        for index, family in enumerate(families)
    ]
    return registry


class SaasProductSecurityReviewValidatorTests(unittest.TestCase):
    def test_registry_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            schema = temp_root / MODULE.SCHEMA_PATH
            schema.parent.mkdir(parents=True, exist_ok=True)
            schema.write_bytes((ROOT / MODULE.SCHEMA_PATH).read_bytes())
            registry_path = temp_root / "registry.json"
            registry_path.write_text(
                '{"schema_version":"saas-product-security-review-registry-v1",'
                '"schema_version":"saas-product-security-review-registry-v1"}',
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

    def _validate(
        self,
        registry_factory,
        *,
        require_complete: bool = False,
        mutate=None,
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for relative in (MODULE.PACKET_PATH, MODULE.SCHEMA_PATH):
                source = ROOT / relative
                destination = temp_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read_bytes())
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
            registry = registry_factory(reviewed_commit_sha)
            if mutate is not None:
                mutate(registry)
            registry_path = (
                temp_root / "docs/reviews/saas-product-security-review-registry.json"
            )
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text(json.dumps(registry), encoding="utf-8")
            with patch.object(MODULE, "ROOT", temp_root), patch.object(
                MODULE,
                "REGISTRY_PATH",
                registry_path,
            ):
                return MODULE.validate(require_complete=require_complete)

    def test_pending_registry_is_valid_without_claiming_completion(self) -> None:
        result = self._validate(lambda _sha: _pending_registry())
        self.assertTrue(result["passed"])
        self.assertFalse(result["saas_product_security_validation_complete"])

    def test_pending_registry_fails_strict_completion_gate(self) -> None:
        result = self._validate(
            lambda _sha: _pending_registry(),
            require_complete=True,
        )
        self.assertFalse(result["passed"])
        self.assertIn(
            "review_status is not 'complete' under --require-complete",
            result["findings"],
        )

    def test_complete_registry_with_app_and_family_coverage_passes(self) -> None:
        result = self._validate(_complete_registry, require_complete=True)
        self.assertTrue(result["passed"], result["findings"])
        self.assertTrue(result["saas_product_security_validation_complete"])
        self.assertEqual(set(result["observed_apps"]), MODULE.REQUIRED_APPS)
        self.assertEqual(
            set(result["observed_vulnerability_families"]),
            MODULE.REQUIRED_FAMILIES,
        )

    def test_rejected_review_never_yields_saas_validation_completion(self) -> None:
        def mutate(registry):
            registry["overall_disposition"] = "reject"

        structural = self._validate(_complete_registry, mutate=mutate)
        strict = self._validate(
            _complete_registry,
            require_complete=True,
            mutate=mutate,
        )

        self.assertTrue(structural["passed"])
        self.assertFalse(structural["saas_product_security_validation_complete"])
        self.assertFalse(strict["passed"])
        self.assertFalse(strict["saas_product_security_validation_complete"])
        self.assertIn(
            "overall_disposition must be accepted under --require-complete",
            strict["findings"],
        )

    def test_complete_registry_rejects_missing_app_coverage(self) -> None:
        def mutate(registry):
            for record in registry["records"]:
                record["app_id"] = "billing"

        result = self._validate(_complete_registry, require_complete=True, mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("missing app coverage" in item for item in result["findings"]),
            result["findings"],
        )

    def test_complete_registry_rejects_missing_family_coverage(self) -> None:
        def mutate(registry):
            registry["records"] = registry["records"][:-1]

        result = self._validate(_complete_registry, require_complete=True, mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("missing vulnerability-family coverage" in item for item in result["findings"]),
            result["findings"],
        )

    def test_complete_registry_rejects_nonexistent_review_commit(self) -> None:
        def mutate(registry):
            registry["reviewed_commit_sha"] = "0" * 40
            for record in registry["records"]:
                record["reviewed_commit_sha"] = "0" * 40

        result = self._validate(_complete_registry, require_complete=True, mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertIn(
            "reviewed_commit_sha must reference an existing commit",
            result["findings"],
        )

    def test_complete_registry_rejects_blocking_record(self) -> None:
        def mutate(registry):
            registry["records"][0]["blocking_issue"] = True

        result = self._validate(_complete_registry, require_complete=True, mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("unresolved blocking issue" in item for item in result["findings"]),
            result["findings"],
        )

    def test_complete_registry_rejects_schema_extra_field(self) -> None:
        def mutate(registry):
            registry["records"][0]["private_notes"] = "not allowed"

        result = self._validate(_complete_registry, require_complete=True, mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("unexpected fields" in item for item in result["findings"]),
            result["findings"],
        )

    def test_complete_registry_rejects_duplicate_app_family_record(self) -> None:
        def mutate(registry):
            registry["records"].append(copy.deepcopy(registry["records"][0]))

        result = self._validate(_complete_registry, require_complete=True, mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("duplicate app/family review record" in item for item in result["findings"]),
            result["findings"],
        )

    def test_registry_rejects_unknown_top_level_fields(self) -> None:
        def mutate(registry):
            registry["private_route"] = "redacted"

        result = self._validate(lambda _sha: _pending_registry(), mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertIn("unexpected registry fields: private_route", result["findings"])

    def test_registry_rejects_non_string_issue_records(self) -> None:
        def mutate(registry):
            registry["nonblocking_issues"] = [{"task_id": "private-example-id"}]

        result = self._validate(lambda _sha: _pending_registry(), mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertIn(
            "nonblocking_issues must contain concrete public-safe strings",
            result["findings"],
        )

    def test_registry_rejects_private_markers_at_any_depth(self) -> None:
        def mutate(registry):
            registry["nonblocking_issues"] = [
                "Raw response is under tasks_private/holdout."
            ]

        result = self._validate(lambda _sha: _pending_registry(), mutate=mutate)
        self.assertFalse(result["passed"])
        self.assertIn("registry contains a private-detail marker", result["findings"])


if __name__ == "__main__":
    unittest.main()
