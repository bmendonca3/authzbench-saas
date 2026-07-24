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
            verifier_root_dockerfile = (task_dir / "tests" / "Dockerfile").read_text(encoding="utf-8")
            solution = (task_dir / "solution" / "solve.sh").read_text(encoding="utf-8")
            dataset_toml = (output / manifest["dataset_toml"]).read_text(encoding="utf-8")
            context = json.loads((task_dir / "environment" / "context.json").read_text(encoding="utf-8"))
            task_manifest = json.loads((task_dir / "verifier" / "task_manifest.json").read_text(encoding="utf-8"))
            test_task_manifest = json.loads((task_dir / "tests" / "task_manifest.json").read_text(encoding="utf-8"))
            run_config = (output / manifest["reference_run_config"]).read_text(encoding="utf-8")
            test_script = (task_dir / "tests" / "test.sh").read_text(encoding="utf-8")
            has_public_score_module = (task_dir / "tests" / "authzbench" / "score.py").is_file()
            has_public_core_module = (task_dir / "tests" / "authzbench" / "core.py").is_file()
            has_public_app_module = (task_dir / "tests" / "apps" / "project_mgmt" / "app.py").is_file()
            has_unneeded_runner_module = (task_dir / "tests" / "authzbench" / "run.py").exists()

        self.assertEqual(manifest["schema_version"], "harbor-dataset-skeleton-v1")
        self.assertEqual(manifest["adapter_version"], "0.1.0")
        self.assertEqual(manifest["task_count"], 1)
        self.assertFalse(manifest["harbor_execution_verified"])
        self.assertRegex(manifest["verifier_source_set_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(manifest["oracle_solution_mode"], "none")
        self.assertIn("not Harbor execution evidence", manifest["claim_boundary"])
        self.assertIn('schema_version = "1.3"', task_toml)
        self.assertIn("[metadata.authzbench]", task_toml)
        self.assertIn('skeleton_schema_version = "harbor-dataset-skeleton-v1"', task_toml)
        self.assertIn("harbor_execution_verified = false", task_toml)
        self.assertIn('environment_mode = "separate"', task_toml)
        self.assertIn("findings: []", instruction)
        self.assertIn("This is a `no_tools` task", instruction)
        self.assertIn("Do not make network requests", instruction)
        self.assertIn("Read only `environment/context.json`", instruction)
        self.assertIn("write the submission immediately", instruction)
        self.assertIn("not Harbor execution evidence", dockerfile)
        self.assertIn("FROM python:", dockerfile)
        self.assertIn("COPY context.json environment/context.json", dockerfile)
        self.assertIn("not Harbor verifier/scorer parity evidence", verifier_root_dockerfile)
        self.assertIn("FROM python:", verifier_root_dockerfile)
        self.assertIn("ENV PYTHONPATH=/tests", verifier_root_dockerfile)
        self.assertIn("COPY authzbench /tests/authzbench", verifier_root_dockerfile)
        self.assertIn("COPY apps /tests/apps", verifier_root_dockerfile)
        self.assertFalse((task_dir / "tests" / "environment" / "Dockerfile").exists())
        self.assertTrue(has_public_score_module)
        self.assertTrue(has_public_core_module)
        self.assertTrue(has_public_app_module)
        self.assertFalse(has_unneeded_runner_module)
        self.assertIn("does not include a public oracle solution", solution)
        self.assertIn("exit 64", solution)
        self.assertIn("[dataset]", dataset_toml)
        self.assertIn('name = "bmendonca3/authzbench-saas-public-pilot"', dataset_toml)
        self.assertIn("[[dataset.authors]]", dataset_toml)
        self.assertIn('name = "authzbench-saas/pm_same_tenant_read_control"', dataset_toml)
        self.assertIn('digest = "sha256:', dataset_toml)
        self.assertIn("not Harbor publish evidence", dataset_toml)
        self.assertRegex(manifest["tasks"][0]["harbor_content_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(context["task_id"], "pm_same_tenant_read_control")
        self.assertEqual(task_manifest["id"], "pm_same_tenant_read_control")
        self.assertEqual(test_task_manifest["id"], "pm_same_tenant_read_control")
        self.assertIn("tasks:", run_config)
        self.assertIn("  - path: \"tasks/pm_same_tenant_read_control\"", run_config)
        self.assertNotIn(str(task_dir.resolve()), run_config)
        self.assertIn("not evidence that Harbor execution has been verified", run_config)
        self.assertIn("/logs/artifacts/reward.json", task_toml)
        self.assertIn("/logs/artifacts/reward.txt", task_toml)
        self.assertIn("/logs/artifacts/reward.json", test_script)
        self.assertIn("/logs/artifacts/reward.txt", test_script)
        self.assertIn("/logs/verifier/reward.json", test_script)
        self.assertIn("/logs/verifier/reward.txt", test_script)
        self.assertIn("/logs/verifier/ctrf.json", test_script)
        self.assertIn("missing agent submission", test_script)
        self.assertIn("invalid agent submission", test_script)
        self.assertIn("score_submission(task, submission)", test_script)
        self.assertIn("raise SystemExit(0)", test_script)
        self.assertNotIn("private_pack_fingerprint_sha256", json.dumps(manifest))

    def test_can_build_secure_control_empty_findings_oracle_solution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            manifest = build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                output,
                harness_lane="no_tools",
                oracle_solution_mode="secure-control-empty-findings",
            )
            task_dir = output / manifest["tasks"][0]["harbor_task_dir"]
            solution = (task_dir / "solution" / "solve.sh").read_text(encoding="utf-8")

        self.assertEqual(manifest["oracle_solution_mode"], "secure-control-empty-findings")
        self.assertEqual(manifest["tasks"][0]["oracle_solution_mode"], "secure-control-empty-findings")
        self.assertIn('/logs/artifacts/submission.json', solution)
        self.assertIn('{"findings":[]}', solution)

    def test_vulnerable_task_uses_placeholder_in_secure_control_empty_findings_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            manifest = build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"],
                output,
                oracle_solution_mode="secure-control-empty-findings",
            )
            task_dir = output / manifest["tasks"][0]["harbor_task_dir"]
            solution = (task_dir / "solution" / "solve.sh").read_text(encoding="utf-8")

        self.assertEqual(manifest["oracle_solution_mode"], "secure-control-empty-findings")
        self.assertIn("does not include a public oracle solution", solution)
        self.assertIn("exit 64", solution)

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

    def test_rejects_private_holdout_path_before_manifest_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            private_dir = Path(tmp) / "tasks_private" / "holdout"
            private_dir.mkdir(parents=True)
            private_task = private_dir / "malformed.json"
            private_task.write_text("{not json", encoding="utf-8")
            output = Path(tmp) / "harbor-public"
            output.mkdir()
            (output / "stale.txt").write_text("old", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "private holdout paths"):
                build_harbor_dataset_skeleton(
                    [str(private_task)],
                    output,
                    task_ids=["would-require-reading-json"],
                    clean=True,
                )

            self.assertTrue((output / "stale.txt").exists())

    def test_rejects_cleaning_non_generated_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            output.mkdir()
            (output / "stale.txt").write_text("old", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "without a generated Harbor skeleton manifest"):
                build_harbor_dataset_skeleton(
                    ["tasks/project_mgmt/*.json"],
                    output,
                    task_ids=["pm_same_tenant_read_control"],
                    clean=True,
                )

            self.assertTrue((output / "stale.txt").exists())

    def test_rejects_non_empty_output_directory_without_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            output.mkdir()
            (output / "stale.txt").write_text("old", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "non-empty Harbor skeleton output directory"):
                build_harbor_dataset_skeleton(
                    ["tasks/project_mgmt/*.json"],
                    output,
                    task_ids=["pm_same_tenant_read_control"],
                )

            self.assertTrue((output / "stale.txt").exists())

    def test_filters_by_task_id_and_overwrites_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "harbor-public"
            build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"],
                output,
            )
            (output / "stale-generated.txt").write_text("old", encoding="utf-8")

            manifest = build_harbor_dataset_skeleton(
                ["tasks/project_mgmt/*.json"],
                output,
                task_ids=["pm_same_tenant_read_control"],
                clean=True,
            )

            self.assertFalse((output / "stale-generated.txt").exists())
            self.assertEqual([task["id"] for task in manifest["tasks"]], ["pm_same_tenant_read_control"])

    def test_rejects_sanitized_task_directory_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = json.loads(Path("tasks/project_mgmt/pm_same_tenant_read_control.json").read_text(encoding="utf-8"))
            first = Path(tmp) / "first.json"
            second = Path(tmp) / "second.json"
            first_task = dict(base, id="collision/a")
            second_task = dict(base, id="collision:a")
            first.write_text(json.dumps(first_task), encoding="utf-8")
            second.write_text(json.dumps(second_task), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate Harbor task directory"):
                build_harbor_dataset_skeleton([str(first), str(second)], Path(tmp) / "harbor-public")

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
