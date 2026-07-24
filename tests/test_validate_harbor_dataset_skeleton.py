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

    def test_accepts_generated_billing_route_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/billing/bill_bfla_member_plan_change.json"],
                dataset_dir,
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertTrue(result["passed"], result)

    def test_requires_task_specific_app_module_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/billing/bill_bfla_member_plan_change.json"],
                dataset_dir,
            )
            manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
            task_dir = dataset_dir / manifest["tasks"][0]["harbor_task_dir"]
            (task_dir / "tests" / "apps" / "billing" / "app.py").unlink()

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("tests/apps/billing/app.py" in error for error in result["errors"]), result)

    def test_rejects_stale_copied_verifier_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
            task_dir = dataset_dir / manifest["tasks"][0]["harbor_task_dir"]
            copied_core = task_dir / "tests" / "authzbench" / "core.py"
            copied_core.write_text(copied_core.read_text(encoding="utf-8") + "\n# stale copy\n", encoding="utf-8")

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("copied verifier source tree" in error for error in result["errors"]), result)

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

    def test_rejects_missing_dataset_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            (dataset_dir / "dataset.toml").unlink()

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertIn("dataset_toml file is missing", result["errors"])

    def test_rejects_empty_manifest_task_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            manifest_path = dataset_dir / "dataset-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["tasks"] = []
            manifest["task_count"] = 0
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (dataset_dir / "dataset.toml").write_text(
                "\n".join(
                    [
                        'name = "authzbench-saas-public-skeleton"',
                        'version = "public-skeleton"',
                        'description = "Public-safe AuthZBench-SaaS Harbor-compatible skeleton dataset."',
                        "tasks = []",
                        "",
                        "[metadata.authzbench]",
                        'skeleton_schema_version = "harbor-dataset-skeleton-v1"',
                        'evidence_status = "generated_public_skeleton"',
                        'harness_lane = "no_tools"',
                        "private_task_count = 0",
                        "harbor_execution_verified = false",
                        "harbor_publish_verified = false",
                        'claim_boundary = "Generated public dataset skeleton only; not Harbor publish evidence, not Harbor execution evidence, and not v1 readiness."',
                    ]
                ),
                encoding="utf-8",
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertIn("tasks must contain at least one public task", result["errors"])

    def test_rejects_dataset_toml_overclaim_and_task_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            (dataset_dir / "dataset.toml").write_text(
                "\n".join(
                    [
                        'name = "authzbench-saas-public-skeleton"',
                        'version = "public-skeleton"',
                        'tasks = ["tasks/other"]',
                        "",
                        "[metadata.authzbench]",
                        f'skeleton_schema_version = "harbor-dataset-skeleton-v1"',
                        'evidence_status = "generated_public_skeleton"',
                        "private_task_count = 0",
                        "harbor_execution_verified = true",
                        "harbor_publish_verified = true",
                    ]
                ),
                encoding="utf-8",
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("tasks must match dataset-manifest" in error for error in result["errors"]), result)
        self.assertTrue(any("harbor_execution_verified must be false" in error for error in result["errors"]), result)
        self.assertTrue(any("harbor_publish_verified must be false" in error for error in result["errors"]), result)

    def test_rejects_missing_harbor_shape_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
            task_dir = dataset_dir / manifest["tasks"][0]["harbor_task_dir"]
            (task_dir / "environment" / "Dockerfile").unlink()
            (task_dir / "tests" / "Dockerfile").unlink()
            (task_dir / "solution" / "solve.sh").unlink()

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("missing environment/Dockerfile" in error for error in result["errors"]), result)
        self.assertTrue(any("missing tests/Dockerfile" in error for error in result["errors"]), result)
        self.assertTrue(any("missing solution/solve.sh" in error for error in result["errors"]), result)

    def test_rejects_environment_without_context_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
            task_dir = dataset_dir / manifest["tasks"][0]["harbor_task_dir"]
            dockerfile = task_dir / "environment" / "Dockerfile"
            dockerfile.write_text(
                dockerfile.read_text(encoding="utf-8").replace(
                    "COPY context.json environment/context.json\n",
                    "",
                ),
                encoding="utf-8",
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("copy rendered context" in error for error in result["errors"]), result)

    def test_rejects_overclaiming_solution_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
            task_dir = dataset_dir / manifest["tasks"][0]["harbor_task_dir"]
            (task_dir / "solution" / "solve.sh").write_text(
                "#!/usr/bin/env bash\necho solved\nexit 0\n",
                encoding="utf-8",
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("placeholder oracle boundary" in error for error in result["errors"]), result)
        self.assertTrue(any("fail closed" in error for error in result["errors"]), result)

    def test_rejects_private_markers_in_test_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                dataset_dir,
            )
            manifest = json.loads((dataset_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
            task_dir = dataset_dir / manifest["tasks"][0]["harbor_task_dir"]
            test_script = task_dir / "tests" / "test.sh"
            test_script.write_text(
                test_script.read_text(encoding="utf-8") + "\necho 'raw private output at /tmp/private.json'\n",
                encoding="utf-8",
            )

            result = validate_harbor_dataset_skeleton(dataset_dir)

        self.assertFalse(result["passed"], result)
        self.assertTrue(any("tests/test.sh" in error and "private detail marker" in error for error in result["errors"]), result)


if __name__ == "__main__":
    unittest.main()
