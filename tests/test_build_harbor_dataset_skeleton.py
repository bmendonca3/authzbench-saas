from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_harbor_dataset_skeleton import build_harbor_dataset_skeleton


class HarborDatasetSkeletonBuilderTests(unittest.TestCase):
    def test_builds_public_task_skeleton_without_claiming_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            manifest = build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                output,
                harness_lane="no_tools",
            )

            task_dir = output / manifest["tasks"][0]["harbor_task_dir"]
            task_toml = (task_dir / "task.toml").read_text(encoding="utf-8")
            instruction = (task_dir / "instruction.md").read_text(encoding="utf-8")
            dockerfile = (task_dir / "environment" / "Dockerfile").read_text(encoding="utf-8")
            solution = (task_dir / "solution" / "solve.sh").read_text(encoding="utf-8")
            dataset_toml = (output / manifest["dataset_toml"]).read_text(encoding="utf-8")
            context = json.loads((task_dir / "environment" / "context.json").read_text(encoding="utf-8"))
            task_manifest = json.loads((task_dir / "verifier" / "task_manifest.json").read_text(encoding="utf-8"))
            run_config = (output / manifest["reference_run_config"]).read_text(encoding="utf-8")

        self.assertEqual(manifest["schema_version"], "harbor-dataset-skeleton-v1")
        self.assertEqual(manifest["task_count"], 1)
        self.assertFalse(manifest["harbor_execution_verified"])
        self.assertIn("not Harbor execution evidence", manifest["claim_boundary"])
        self.assertIn('schema_version = "1.3"', task_toml)
        self.assertIn("[metadata.authzbench]", task_toml)
        self.assertIn('skeleton_schema_version = "harbor-dataset-skeleton-v1"', task_toml)
        self.assertIn("harbor_execution_verified = false", task_toml)
        self.assertIn('environment_mode = "separate"', task_toml)
        self.assertIn("findings: []", instruction)
        self.assertIn("not Harbor execution evidence", dockerfile)
        self.assertIn("FROM python:", dockerfile)
        self.assertIn("does not include a public oracle solution", solution)
        self.assertIn("exit 64", solution)
        self.assertIn('name = "authzbench-saas-public-skeleton"', dataset_toml)
        self.assertIn('version = "public-skeleton"', dataset_toml)
        self.assertIn('tasks/pm_same_tenant_read_control', dataset_toml)
        self.assertIn("not Harbor publish evidence", dataset_toml)
        self.assertIn("harbor_publish_verified = false", dataset_toml)
        self.assertEqual(context["task_id"], "pm_same_tenant_read_control")
        self.assertEqual(task_manifest["id"], "pm_same_tenant_read_control")
        self.assertIn("datasets:", run_config)
        self.assertIn("  - path: .", run_config)
        self.assertIn("not evidence that Harbor execution has been verified", run_config)
        self.assertNotIn("private_pack_fingerprint_sha256", json.dumps(manifest))

    def test_live_http_lane_records_service_orchestration_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            manifest = build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"],
                output,
                harness_lane="live_http_tool_agent",
            )
            task_dir = output / manifest["tasks"][0]["harbor_task_dir"]
            task_toml = (task_dir / "task.toml").read_text(encoding="utf-8")

        self.assertEqual(manifest["harness_lane"], "live_http_tool_agent")
        self.assertIn("preserve AUTHZBENCH_AGENT_ID-equivalent request correlation", task_toml)

    def test_rejects_private_holdout_manifest_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_task = Path(tmp) / "private.json"
            private_task.write_text(
                json.dumps(
                    {
                        "id": "private-task",
                        "app": "project_mgmt",
                        "split": "private_holdout",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "private holdout manifests"):
                build_harbor_dataset_skeleton([str(private_task)], Path(tmp) / "out")

    def test_filters_by_task_id_and_overwrites_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            output.mkdir()
            (output / "stale.txt").write_text("old", encoding="utf-8")

            manifest = build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/*.json"],
                output,
                task_ids=["pm_same_tenant_read_control"],
                clean=True,
            )

            self.assertFalse((output / "stale.txt").exists())

        self.assertEqual([task["id"] for task in manifest["tasks"]], ["pm_same_tenant_read_control"])

    def test_filters_by_task_ids_before_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            manifest = build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/*.json"],
                output,
                task_ids=["pm_bola_read_alpha_from_beta"],
                limit=1,
            )

        self.assertEqual([task["id"] for task in manifest["tasks"]], ["pm_bola_read_alpha_from_beta"])

    def test_rejects_empty_task_selection_without_cleaning_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            output.mkdir()
            (output / "stale.txt").write_text("old", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "at least one public task"):
                build_harbor_dataset_skeleton(
                    ["tasks/project_mgmt/*.json"],
                    output,
                    task_ids=["does-not-exist"],
                    clean=True,
                )

            self.assertTrue((output / "stale.txt").exists())

    def test_cli_accepts_task_ids_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_harbor_dataset_skeleton.py",
                    "--task",
                    "tasks/project_mgmt/*.json",
                    "--output-dir",
                    str(output),
                    "--task-ids",
                    "pm_bola_read_alpha_from_beta",
                    "--limit",
                    "1",
                    "--overwrite",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            )

        manifest = json.loads(result.stdout)
        self.assertEqual([task["id"] for task in manifest["tasks"]], ["pm_bola_read_alpha_from_beta"])


if __name__ == "__main__":
    unittest.main()
