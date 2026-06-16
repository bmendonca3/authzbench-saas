from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_harbor_integration import (
    CONTRACT_PATH,
    REQUIRED_COMPONENTS,
    REQUIRED_DATASET_ROOT_FILES,
    REQUIRED_LANES,
    REQUIRED_METADATA,
    REQUIRED_PACKAGE_LAYOUT,
    RUNBOOK_PATH,
    validate_harbor_integration,
)


class HarborIntegrationValidatorTests(unittest.TestCase):
    def test_current_contract_passes(self) -> None:
        result = validate_harbor_integration()

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["adapter_component_count"], len(REQUIRED_COMPONENTS))
        self.assertEqual(result["lane_count"], len(REQUIRED_LANES))
        self.assertEqual(result["required_metadata_count"], len(REQUIRED_METADATA))

    def test_rejects_overclaims_missing_lanes_and_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "harbor-adapter-contract.json"
            runbook = root / "harbor-integration-runbook.md"
            data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
            data["public_claim_boundary"] = "Harbor " + "accepted" + " and " + "endorsed" + " this as v1-" + "ready evidence."
            data["local_run_template"] = "python run.py"
            data["dataset_shape"]["dataset_root_files"] = ["dataset-manifest.json"]
            data["lanes"] = [lane for lane in data["lanes"] if lane["name"] != "live_http_tool_agent"]
            data["required_run_metadata"] = ["benchmark_source_sha"]
            data["debug_note"] = "raw private output at /tmp/authzbench/private.json"
            contract.write_text(json.dumps(data), encoding="utf-8")
            runbook.write_text("# Harbor\n\nNo SDK mapping here.\n", encoding="utf-8")

            result = validate_harbor_integration(contract, runbook)

        self.assertFalse(result["passed"], result)
        self.assertIn("local_run_template must include harbor run -c run_authzbench_saas.yaml --yes", result["errors"])
        self.assertTrue(any("dataset_shape.dataset_root_files missing:" in error for error in result["errors"]), result)
        self.assertIn("lanes missing: live_http_tool_agent", result["errors"])
        self.assertTrue(any("required_run_metadata missing:" in error for error in result["errors"]), result)
        self.assertTrue(any("disallowed overclaim/private marker" in error for error in result["errors"]), result)
        self.assertTrue(any("local absolute path is not allowed" in error for error in result["errors"]), result)
        self.assertTrue(any("runbook missing required term:" in error for error in result["errors"]), result)

    def test_rejects_incomplete_expected_adapter_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "harbor-adapter-contract.json"
            data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
            data["expected_adapter_package"] = {
                "evidence_status": "complete",
                "claim_boundary": "Implemented SDK evidence.",
                "package_layout": ["pyproject.toml"],
                "module_entrypoint": "python main.py",
                "required_cli_flags": ["--output-dir"],
                "repo_side_compatibility_helper": "--output-dir",
                "blocked_until": [],
            }
            contract.write_text(json.dumps(data), encoding="utf-8")

            result = validate_harbor_integration(contract, RUNBOOK_PATH)

        self.assertFalse(result["passed"], result)
        self.assertIn("expected_adapter_package.evidence_status must be implementation_target", result["errors"])
        self.assertIn(
            "expected_adapter_package.claim_boundary must reject platform-acceptance claims",
            result["errors"],
        )
        self.assertTrue(any("expected_adapter_package.package_layout missing:" in error for error in result["errors"]), result)
        self.assertTrue(any("expected_adapter_package.required_cli_flags missing:" in error for error in result["errors"]), result)
        self.assertIn(
            "expected_adapter_package.module_entrypoint must name the repo-side Harbor CLI entrypoint",
            result["errors"],
        )
        self.assertIn("expected_adapter_package.blocked_until must list concrete blockers", result["errors"])

    def test_current_contract_lists_expected_adapter_package_layout(self) -> None:
        data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        package = data["expected_adapter_package"]

        self.assertEqual(set(data["dataset_shape"]["dataset_root_files"]), REQUIRED_DATASET_ROOT_FILES)
        self.assertEqual(set(package["package_layout"]), REQUIRED_PACKAGE_LAYOUT)
        self.assertEqual(set(package["required_cli_flags"]), {"--output-dir", "--limit", "--overwrite", "--task-ids"})
        self.assertIn("python3 -m authzbench_harbor.cli build", package["module_entrypoint"])

    def test_allows_public_harbor_artifact_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "harbor-adapter-contract.json"
            data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
            data["artifact_path_example"] = "/logs/artifacts/submission.json"
            contract.write_text(json.dumps(data), encoding="utf-8")

            result = validate_harbor_integration(contract, RUNBOOK_PATH)

        self.assertTrue(result["passed"], result)

    def test_rejects_invalid_adapter_blocker_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blockers = root / "harbor-adapter-readiness-blockers.json"
            blockers.write_text(
                json.dumps(
                    {
                        "schema_version": "harbor-adapter-readiness-blockers-v1",
                        "evidence_status": "complete",
                        "public_claim_boundary": "Adapter ready.",
                    }
                ),
                encoding="utf-8",
            )

            result = validate_harbor_integration(CONTRACT_PATH, RUNBOOK_PATH, blockers)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any(error.startswith("adapter_readiness_blockers:") for error in result["errors"]), result)


if __name__ == "__main__":
    unittest.main()
