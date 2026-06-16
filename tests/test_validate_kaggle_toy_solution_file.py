import tempfile
import unittest
from pathlib import Path

from scripts.validate_kaggle_toy_solution_file import validate_toy_solution

ROOT = Path(__file__).resolve().parents[1]
ACTUAL_CSV = ROOT / "platform/kaggle/toy_solution_file.csv"
TASKS_DIR = ROOT / "tasks"


class ValidateKaggleToySolutionFileTests(unittest.TestCase):
    def test_current_toy_solution_passes(self) -> None:
        result = validate_toy_solution(ACTUAL_CSV, TASKS_DIR)
        self.assertTrue(result["passed"], result)

    def test_invalid_headers_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.csv"
            path.write_text("Id,Usage,expected\n", encoding="utf-8")
            result = validate_toy_solution(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Invalid CSV headers" in err for err in result["errors"]))

    def test_missing_private_placeholder_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            # No private placeholder
            path.write_text(
                "Id,Usage,expected_vulnerable,control_type,oracle_ref,task_pack_version\n"
                "tok_cross_tenant_secret_read,Public,true,,public-oracle:tok_cross_tenant_secret_read,public-2026-06\n"
                "tok_secure_cross_tenant_secret_control,Public,false,denial,public-oracle:tok_secure_cross_tenant_secret_control,public-2026-06\n"
                "sup_admin_reassignment_control,Public,false,authorized_allow,public-oracle:sup_admin_reassignment_control,public-2026-06\n",
                encoding="utf-8"
            )
            result = validate_toy_solution(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("must contain exactly one private placeholder row" in err for err in result["errors"]))

    def test_invalid_expected_vulnerable_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            path.write_text(
                "Id,Usage,expected_vulnerable,control_type,oracle_ref,task_pack_version\n"
                "tok_cross_tenant_secret_read,Public,invalid,,public-oracle:tok_cross_tenant_secret_read,public-2026-06\n"
                "tok_secure_cross_tenant_secret_control,Public,false,denial,public-oracle:tok_secure_cross_tenant_secret_control,public-2026-06\n"
                "sup_admin_reassignment_control,Public,false,authorized_allow,public-oracle:sup_admin_reassignment_control,public-2026-06\n"
                "private-row-placeholder,Private,false,denial,host-controlled,private-pack-version-only\n",
                encoding="utf-8"
            )
            result = validate_toy_solution(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Invalid expected_vulnerable" in err for err in result["errors"]))

    def test_public_task_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            # expected_vulnerable set to false for a vulnerable task
            path.write_text(
                "Id,Usage,expected_vulnerable,control_type,oracle_ref,task_pack_version\n"
                "tok_cross_tenant_secret_read,Public,false,,public-oracle:tok_cross_tenant_secret_read,public-2026-06\n"
                "tok_secure_cross_tenant_secret_control,Public,false,denial,public-oracle:tok_secure_cross_tenant_secret_control,public-2026-06\n"
                "sup_admin_reassignment_control,Public,false,authorized_allow,public-oracle:sup_admin_reassignment_control,public-2026-06\n"
                "private-row-placeholder,Private,false,denial,host-controlled,private-pack-version-only\n",
                encoding="utf-8"
            )
            result = validate_toy_solution(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("expected_vulnerable mismatch" in err for err in result["errors"]))

    def test_invalid_oracle_ref_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.csv"
            # Public task oracle_ref missing public-oracle: prefix
            path.write_text(
                "Id,Usage,expected_vulnerable,control_type,oracle_ref,task_pack_version\n"
                "tok_cross_tenant_secret_read,Public,true,,invalid-oracle-ref,public-2026-06\n"
                "tok_secure_cross_tenant_secret_control,Public,false,denial,public-oracle:tok_secure_cross_tenant_secret_control,public-2026-06\n"
                "sup_admin_reassignment_control,Public,false,authorized_allow,public-oracle:sup_admin_reassignment_control,public-2026-06\n"
                "private-row-placeholder,Private,false,denial,host-controlled,private-pack-version-only\n",
                encoding="utf-8"
            )
            result = validate_toy_solution(path, TASKS_DIR)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("oracle_ref must start with" in err for err in result["errors"]))
