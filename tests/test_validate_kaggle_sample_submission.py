import tempfile
import unittest
from pathlib import Path
import json

from scripts.validate_kaggle_sample_submission import validate_sample_csv

ROOT = Path(__file__).resolve().parents[1]
ACTUAL_CSV = ROOT / "platform/kaggle/sample_submission.csv"
TASKS_DIR = ROOT / "tasks"


class ValidateKaggleSampleSubmissionTests(unittest.TestCase):
    def test_current_sample_csv_passes(self) -> None:
        result = validate_sample_csv(ACTUAL_CSV, TASKS_DIR)
        self.assertTrue(result["passed"], result)

    def test_invalid_headers_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.csv"
            path.write_text("Id,path,notes\ntok_cross_tenant_secret_read,submissions/tok_cross_tenant_secret_read/submission.json,note\n", encoding="utf-8")
            result = validate_sample_csv(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Invalid headers" in err for err in result["errors"]))

    def test_unknown_public_task_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            # Use a non-existent task ID
            path.write_text(
                "Id,finding_path,notes\n"
                "non_existent_task_id,submissions/non_existent_task_id/submission.json,note\n"
                "tok_secure_cross_tenant_secret_control,submissions/tok_secure_cross_tenant_secret_control/submission.json,note\n"
                "sup_admin_reassignment_control,submissions/sup_admin_reassignment_control/submission.json,note\n",
                encoding="utf-8"
            )
            result = validate_sample_csv(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Id not found in public tasks" in err for err in result["errors"]))

    def test_duplicate_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            # Duplicate ID
            path.write_text(
                "Id,finding_path,notes\n"
                "tok_cross_tenant_secret_read,submissions/tok_cross_tenant_secret_read/submission.json,note\n"
                "tok_cross_tenant_secret_read,submissions/tok_cross_tenant_secret_read/submission.json,note2\n"
                "sup_admin_reassignment_control,submissions/sup_admin_reassignment_control/submission.json,note\n",
                encoding="utf-8"
            )
            result = validate_sample_csv(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Duplicate task Id" in err for err in result["errors"]))

    def test_path_traversal_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            path.write_text(
                "Id,finding_path,notes\n"
                "tok_cross_tenant_secret_read,submissions/../../tok_cross_tenant_secret_read/submission.json,note\n"
                "tok_secure_cross_tenant_secret_control,submissions/tok_secure_cross_tenant_secret_control/submission.json,note\n"
                "sup_admin_reassignment_control,submissions/sup_admin_reassignment_control/submission.json,note\n",
                encoding="utf-8"
            )
            result = validate_sample_csv(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("must not contain '..'" in err or "escapes expected base directory" in err for err in result["errors"]))

    def test_absolute_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            path.write_text(
                "Id,finding_path,notes\n"
                "tok_cross_tenant_secret_read,/tmp/submissions/tok_cross_tenant_secret_read/submission.json,note\n"
                "tok_secure_cross_tenant_secret_control,submissions/tok_secure_cross_tenant_secret_control/submission.json,note\n"
                "sup_admin_reassignment_control,submissions/sup_admin_reassignment_control/submission.json,note\n",
                encoding="utf-8"
            )
            result = validate_sample_csv(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("must be relative" in err for err in result["errors"]))

    def test_require_existing_findings_missing_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            path.write_text(
                "Id,finding_path,notes\n"
                "tok_cross_tenant_secret_read,submissions/tok_cross_tenant_secret_read/submission.json,note\n"
                "tok_secure_cross_tenant_secret_control,submissions/tok_secure_cross_tenant_secret_control/submission.json,note\n"
                "sup_admin_reassignment_control,submissions/sup_admin_reassignment_control/submission.json,note\n",
                encoding="utf-8"
            )
            # require-existing-findings set, but findings do not exist in the temp directory
            result = validate_sample_csv(path, TASKS_DIR, require_existing_findings=True)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Finding file does not exist" in err for err in result["errors"]))

    def test_require_existing_findings_malformed_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "test.csv"
            csv_path.write_text(
                "Id,finding_path,notes\n"
                "tok_cross_tenant_secret_read,submissions/tok_cross_tenant_secret_read/submission.json,note\n"
                "tok_secure_cross_tenant_secret_control,submissions/tok_secure_cross_tenant_secret_control/submission.json,note\n"
                "sup_admin_reassignment_control,submissions/sup_admin_reassignment_control/submission.json,note\n",
                encoding="utf-8"
            )

            # Create a malformed json finding file
            sub_dir = tmp_path / "submissions/tok_cross_tenant_secret_read"
            sub_dir.mkdir(parents=True)
            (sub_dir / "submission.json").write_text("malformed json content", encoding="utf-8")

            # Write empty/dummy JSONs for other tasks to avoid missing file errors
            for task in ["tok_secure_cross_tenant_secret_control", "sup_admin_reassignment_control"]:
                d = tmp_path / f"submissions/{task}"
                d.mkdir(parents=True)
                (d / "submission.json").write_text("{}", encoding="utf-8")

            result = validate_sample_csv(csv_path, TASKS_DIR, require_existing_findings=True)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Finding file is not valid JSON" in err for err in result["errors"]))

    def test_extra_columns_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            path.write_text(
                "Id,finding_path,notes,extra\n"
                "tok_cross_tenant_secret_read,submissions/tok_cross_tenant_secret_read/submission.json,note,extra_value\n",
                encoding="utf-8"
            )
            result = validate_sample_csv(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)

    def test_whitespace_trimmed_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            path.write_text(
                "Id,finding_path,notes\n"
                " tok_cross_tenant_secret_read ,submissions/tok_cross_tenant_secret_read/submission.json,note\n"
                "tok_secure_cross_tenant_secret_control,submissions/tok_secure_cross_tenant_secret_control/submission.json,note\n"
                "sup_admin_reassignment_control,submissions/sup_admin_reassignment_control/submission.json,note\n",
                encoding="utf-8"
            )
            result = validate_sample_csv(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Id has leading/trailing whitespace" in err for err in result["errors"]))
