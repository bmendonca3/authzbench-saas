"""Tests for Harbor adapter dataset build functionality."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench_harbor.adapter import build_dataset
from authzbench_harbor.cli import main as cli_main
from scripts.validate_harbor_dataset import validate_dataset


class TestHarborAdapterBuildDataset(unittest.TestCase):
    def _public_task_pattern(self) -> str:
        return str(ROOT / "tasks" / "**" / "*.json")

    def test_build_dataset_creates_required_root_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            manifest = build_dataset(
                [self._public_task_pattern()],
                output_dir,
                limit=3,
                overwrite=False,
            )
            self.assertTrue((output_dir / "dataset.toml").is_file())
            self.assertTrue((output_dir / "run_authzbench_saas.yaml").is_file())
            self.assertTrue((output_dir / "dataset-manifest.json").is_file())
            self.assertEqual(manifest["task_count"], 3)
            self.assertEqual(manifest["private_task_count"], 0)
            dataset_toml = (output_dir / "dataset.toml").read_text(encoding="utf-8")
            self.assertIn(
                'name = "bmendonca3/authzbench-saas-public-pilot"',
                dataset_toml,
            )
            self.assertEqual(dataset_toml.count("[[tasks]]"), 3)
            self.assertEqual(dataset_toml.count('digest = "sha256:'), 3)

    def test_build_dataset_preserves_task_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            manifest = build_dataset(
                [self._public_task_pattern()],
                output_dir,
                limit=4,
            )
            returned_ids = [t["id"] for t in manifest["tasks"]]
            self.assertEqual(len(returned_ids), 4)
            self.assertEqual(len(set(returned_ids)), 4, "task IDs must be unique")

    def test_build_dataset_creates_task_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            manifest = build_dataset(
                [self._public_task_pattern()],
                output_dir,
                limit=2,
            )
            for task_entry in manifest["tasks"]:
                task_dir = output_dir / task_entry["harbor_task_dir"]
                self.assertTrue((task_dir / "task.toml").is_file(), f"task.toml missing for {task_entry['id']}")
                self.assertTrue((task_dir / "instruction.md").is_file())
                self.assertTrue((task_dir / "solution" / "solve.sh").is_file())
                self.assertTrue((task_dir / "tests" / "test.sh").is_file())
                self.assertTrue((task_dir / "environment" / "Dockerfile").is_file())
                self.assertTrue((task_dir / "verifier" / "task_manifest.json").is_file())

    def test_build_dataset_single_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            manifest = build_dataset(
                [self._public_task_pattern()],
                output_dir,
                task_id="pm_same_tenant_read_control",
            )
            self.assertEqual(manifest["task_count"], 1)
            self.assertEqual(manifest["tasks"][0]["id"], "pm_same_tenant_read_control")

    def test_build_dataset_validates_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            build_dataset(
                [self._public_task_pattern()],
                output_dir,
                limit=3,
            )
            result = validate_dataset(output_dir)
            self.assertTrue(result["passed"], f"Validation errors: {result['errors']}")
            self.assertEqual(result["errors"], [])

    def test_build_dataset_rejects_planned_unsupported_live_http_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            with self.assertRaisesRegex(ValueError, "planned_unsupported"):
                build_dataset(
                    [self._public_task_pattern()],
                    output_dir,
                    harness_lane="live_http_tool_agent",
                    limit=2,
                )
            self.assertFalse(output_dir.exists())

    def test_build_dataset_rejects_private_holdout_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            private_path = str(ROOT / "tasks_private" / "holdout" / "**" / "*.json")
            with self.assertRaises(ValueError):
                build_dataset([private_path], output_dir, limit=1)

    def test_cli_build_command_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = str(Path(tmp) / "dataset")
            rc = cli_main([
                "build",
                "--tasks", self._public_task_pattern(),
                "--output-dir", output_dir,
                "--limit", "3",
                "--overwrite",
            ])
            self.assertEqual(rc, 0)
            self.assertTrue((Path(output_dir) / "dataset.toml").is_file())

    def test_cli_build_single_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = str(Path(tmp) / "dataset")
            rc = cli_main([
                "build",
                "--task-id", "pm_same_tenant_read_control",
                "--output-dir", output_dir,
                "--overwrite",
            ])
            self.assertEqual(rc, 0)

    def test_cli_rejects_planned_unsupported_live_http_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            rc = cli_main([
                "build",
                "--task-id", "pm_same_tenant_read_control",
                "--output-dir", str(output_dir),
                "--harness-lane", "live_http_tool_agent",
                "--overwrite",
            ])
            self.assertEqual(rc, 1)
            self.assertFalse(output_dir.exists())

    def test_dataset_manifest_has_no_private_task_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            build_dataset(
                [self._public_task_pattern()],
                output_dir,
                limit=2,
            )
            manifest = json.loads((output_dir / "dataset-manifest.json").read_text())
            self.assertEqual(manifest["private_task_count"], 0)


class TestValidateHarborDataset(unittest.TestCase):
    def test_validate_missing_dir_fails(self) -> None:
        result = validate_dataset(Path("/nonexistent/path"))
        self.assertFalse(result["passed"])
        self.assertTrue(any("not found" in e for e in result["errors"]))

    def test_validate_empty_dir_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_dataset(Path(tmp))
            self.assertFalse(result["passed"])

    def test_validate_good_dataset_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dataset"
            build_dataset(
                [str(ROOT / "tasks" / "**" / "*.json")],
                output_dir,
                limit=2,
            )
            result = validate_dataset(output_dir)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")


if __name__ == "__main__":
    unittest.main()
