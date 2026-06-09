from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_harbor_dataset_skeleton import build_harbor_dataset_skeleton
from scripts.validate_harbor_dataset_skeleton import validate_harbor_dataset_skeleton


class HarborDatasetSkeletonValidatorTests(unittest.TestCase):
    def test_accepts_generated_public_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["task_count"], 1)
        self.assertEqual(result["harness_lane"], "no_tools")

    def test_accepts_generated_live_http_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"],
                dataset_dir,
                harness_lane="live_http_tool_agent",
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["harness_lane"], "live_http_tool_agent")

    def test_rejects_overclaim_and_private_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            manifest_path = dataset_dir / "dataset-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["harbor_execution_verified"] = True
            manifest["private_task_count"] = 1
            manifest["claim_boundary"] = "Harbor execution evidence accepted" + " by platform"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            task_dir = dataset_dir / manifest["tasks"][0]["harbor_task_dir"]
            private_manifest = json.loads((task_dir / "verifier" / "task_manifest.json").read_text(encoding="utf-8"))
            private_manifest["split"] = "private_holdout"
            private_manifest["debug_note"] = "raw private output at /tmp/private.json"
            (task_dir / "verifier" / "task_manifest.json").write_text(json.dumps(private_manifest), encoding="utf-8")

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertIn("harbor_execution_verified must be false", result["errors"])
        self.assertIn("private_task_count must be 0", result["errors"])
        self.assertTrue(any("private holdout manifests are not allowed" in error for error in result["errors"]), result)
        self.assertTrue(any("disallowed private/overclaim marker" in error for error in result["errors"]), result)
        self.assertTrue(any("local absolute path is not allowed" in error for error in result["errors"]), result)

    def test_rejects_non_harbor_task_toml_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
            task_dir = dataset_dir / manifest["tasks"][0]["harbor_task_dir"]
            (task_dir / "task.toml").write_text(
                "\n".join(
                    [
                        'schema_version = "harbor-dataset-skeleton-v1"',
                        'private_execution = false',
                        'harbor_execution_verified = false',
                    ]
                ),
                encoding="utf-8",
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("task.toml schema_version must be 1.3" in error for error in result["errors"]), result)
        self.assertTrue(any("[metadata.authzbench]" in error for error in result["errors"]), result)

    def test_rejects_missing_reference_run_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            (dataset_dir / "run_authzbench_saas.yaml").unlink()

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertIn("reference_run_config file is missing", result["errors"])


if __name__ == "__main__":
    unittest.main()
