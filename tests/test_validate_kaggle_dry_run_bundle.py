import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_kaggle_dry_run_bundle import validate_dry_run_bundle

ROOT = Path(__file__).resolve().parents[1]
ACTUAL_BUNDLE = ROOT / "platform/kaggle/dry-run-bundle"
TASKS_DIR = ROOT / "tasks"


class ValidateKaggleDryRunBundleTests(unittest.TestCase):
    def test_current_dry_run_bundle_passes(self) -> None:
        result = validate_dry_run_bundle(ACTUAL_BUNDLE, TASKS_DIR)
        self.assertTrue(result["passed"], result)

    def test_missing_files_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_dry_run_bundle(Path(tmp), TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Missing sample_submission.csv" in err for err in result["errors"]))

    def test_manifest_parity_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Copy actual dry-run bundle
            shutil.copytree(ACTUAL_BUNDLE, tmp_path, dirs_exist_ok=True)

            # Modify manifest.json to remove a task
            m_path = tmp_path / "manifest.json"
            manifest = json.loads(m_path.read_text(encoding="utf-8"))
            manifest["tasks"] = manifest["tasks"][:-1]  # remove one task
            m_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_dry_run_bundle(tmp_path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("missing from manifest.json" in err for err in result["errors"]))

    def test_leaderboard_eligible_true_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(ACTUAL_BUNDLE, tmp_path, dirs_exist_ok=True)

            # Set leaderboard_eligible to true in manifest
            m_path = tmp_path / "manifest.json"
            manifest = json.loads(m_path.read_text(encoding="utf-8"))
            manifest["leaderboard_eligible"] = True
            m_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_dry_run_bundle(tmp_path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("manifest.json must have leaderboard_eligible: false" in err for err in result["errors"]))

    def test_sub_leaderboard_eligible_true_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(ACTUAL_BUNDLE, tmp_path, dirs_exist_ok=True)

            # Set leaderboard_eligible to true in submission
            sub_json_path = tmp_path / "submissions/tok_cross_tenant_secret_read/submission.json"
            sub_data = json.loads(sub_script_content := sub_json_path.read_text(encoding="utf-8"))
            sub_data["leaderboard_eligible"] = True
            sub_json_path.write_text(json.dumps(sub_data), encoding="utf-8")

            result = validate_dry_run_bundle(tmp_path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("must have leaderboard_eligible: false" in err for err in result["errors"]))

    def test_missing_expected_shape_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(ACTUAL_BUNDLE, tmp_path, dirs_exist_ok=True)

            # Remove environment.json shape file
            shape_file = tmp_path / "expected-shape/environment.json"
            if shape_file.is_file():
                shape_file.unlink()

            result = validate_dry_run_bundle(tmp_path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Expected shape file does not exist" in err for err in result["errors"]))

    def test_manifest_task_type_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(ACTUAL_BUNDLE, tmp_path, dirs_exist_ok=True)

            # Modify manifest.json to change a task type
            m_path = tmp_path / "manifest.json"
            manifest = json.loads(m_path.read_text(encoding="utf-8"))
            for t in manifest["tasks"]:
                if t["Id"] == "tok_cross_tenant_secret_read":
                    t["expected_vulnerable"] = False  # actual is True
                    t["control_type"] = "denial"
            m_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_dry_run_bundle(tmp_path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("expected_vulnerable mismatch" in err or "control_type mismatch" in err for err in result["errors"]))
