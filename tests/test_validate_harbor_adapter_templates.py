from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_harbor_adapter_templates import (
    ADAPTER_METADATA_TEMPLATE_PATH,
    PARITY_EXPERIMENT_TEMPLATE_PATH,
    validate_harbor_adapter_templates,
)


class HarborAdapterTemplateValidatorTests(unittest.TestCase):
    def test_current_templates_pass(self) -> None:
        result = validate_harbor_adapter_templates()

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["adapter_metadata_template"], "artifact/harbor-adapter-metadata.template.json")
        self.assertEqual(result["parity_experiment_template"], "artifact/harbor-parity-experiment.template.json")

    def test_rejects_metadata_template_overclaim_and_missing_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_path = root / "metadata.json"
            parity_path = root / "parity.json"
            metadata = json.loads(ADAPTER_METADATA_TEMPLATE_PATH.read_text(encoding="utf-8"))
            parity = json.loads(PARITY_EXPERIMENT_TEMPLATE_PATH.read_text(encoding="utf-8"))
            metadata["template_only"] = False
            metadata["public_claim_boundary"] = "Complete adapter metadata evidence."
            metadata["required_cli_flags"] = ["--output-dir"]
            metadata["dataset_root_files"] = []
            metadata["task_directory_files"] = ["instruction.md"]
            metadata["supported_lanes"] = ["no_tools", "live_http_tool_agent"]
            metadata["planned_unsupported_lanes"] = []
            metadata["artifact_policy"]["private_manifests_tracked"] = True
            metadata["debug_note"] = "raw private " + "output at /tmp/authzbench/private.json"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            parity_path.write_text(json.dumps(parity), encoding="utf-8")

            result = validate_harbor_adapter_templates(metadata_path, parity_path)

        self.assertFalse(result["passed"], result)
        self.assertIn("adapter metadata template must set template_only true", result["errors"])
        self.assertIn(
            "adapter metadata template claim boundary must reject metadata and execution evidence claims",
            result["errors"],
        )
        self.assertTrue(any("required_cli_flags missing:" in error for error in result["errors"]), result)
        self.assertTrue(any("dataset_root_files missing:" in error for error in result["errors"]), result)
        self.assertTrue(any("task_directory_files missing:" in error and "verifier/task_manifest.json" in error for error in result["errors"]), result)
        self.assertIn(
            "adapter metadata template supported_lanes must contain only no_tools",
            result["errors"],
        )
        self.assertIn(
            "adapter metadata template planned_unsupported_lanes must contain exactly live_http_tool_agent",
            result["errors"],
        )
        self.assertIn(
            "adapter metadata template artifact_policy.private_manifests_tracked must be false",
            result["errors"],
        )
        self.assertTrue(any("local absolute path is not allowed" in error for error in result["errors"]), result)

    def test_rejects_parity_template_with_fake_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_path = root / "metadata.json"
            parity_path = root / "parity.json"
            metadata = json.loads(ADAPTER_METADATA_TEMPLATE_PATH.read_text(encoding="utf-8"))
            parity = json.loads(PARITY_EXPERIMENT_TEMPLATE_PATH.read_text(encoding="utf-8"))
            parity["template_only"] = False
            parity["public_claim_boundary"] = "Complete Harbor parity evidence."
            parity["parity_verified"] = True
            parity["harbor_execution_verified"] = True
            parity["comparison_scope"] = "current"
            parity["required_inputs"] = ["real Harbor runs from the packaged adapter"]
            parity["result_fields_required_before_parity_claim"] = ["harbor_run_ids"]
            parity["result_rows"] = [{"metric_name": "score", "harbor_mean": 1.0}]
            parity["debug_note"] = "private " + "route: /api/private"
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
            parity_path.write_text(json.dumps(parity), encoding="utf-8")

            result = validate_harbor_adapter_templates(metadata_path, parity_path)

        self.assertFalse(result["passed"], result)
        self.assertIn("parity experiment template must set template_only true", result["errors"])
        self.assertIn(
            "parity experiment template claim boundary must reject parity and execution evidence claims",
            result["errors"],
        )
        self.assertIn("parity experiment template parity_verified must be false", result["errors"])
        self.assertIn("parity experiment template harbor_execution_verified must be false", result["errors"])
        self.assertIn("parity experiment template comparison_scope must be future_verified_runs_only", result["errors"])
        self.assertTrue(any("required_inputs missing:" in error for error in result["errors"]), result)
        self.assertTrue(any("result_fields_required_before_parity_claim missing:" in error for error in result["errors"]), result)
        self.assertIn("parity experiment template result_rows must be empty", result["errors"])
        self.assertTrue(any("private detail marker is not allowed" in error for error in result["errors"]), result)

    def test_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata_path = Path(tmp) / "metadata.json"
            metadata_path.write_text(
                '{"schema_version":"harbor-adapter-metadata-template-v1",'
                '"schema_version":"harbor-adapter-metadata-template-v1"}',
                encoding="utf-8",
            )

            result = validate_harbor_adapter_templates(
                metadata_path,
                PARITY_EXPERIMENT_TEMPLATE_PATH,
            )

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any("duplicate JSON key: schema_version" in error for error in result["errors"]),
            result,
        )


if __name__ == "__main__":
    unittest.main()
