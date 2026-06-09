from __future__ import annotations

import json
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
            context = json.loads((task_dir / "environment" / "context.json").read_text(encoding="utf-8"))
            task_manifest = json.loads((task_dir / "verifier" / "task_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema_version"], "harbor-dataset-skeleton-v1")
        self.assertEqual(manifest["task_count"], 1)
        self.assertFalse(manifest["harbor_execution_verified"])
        self.assertIn("not Harbor execution evidence", manifest["claim_boundary"])
        self.assertIn("harbor_execution_verified = false", task_toml)
        self.assertIn("findings: []", instruction)
        self.assertEqual(context["task_id"], "pm_same_tenant_read_control")
        self.assertEqual(task_manifest["id"], "pm_same_tenant_read_control")
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


if __name__ == "__main__":
    unittest.main()
