import tempfile
import unittest
from pathlib import Path
import json

from scripts.validate_kaggle_sample_submission import validate_sample_csv


class ValidateKaggleSampleSubmissionTests(unittest.TestCase):
    def test_current_sample_csv_passes(self) -> None:
        # Test against the actual CSV in the repo.
        root = Path(__file__).resolve().parents[1]
        path = root / "platform/kaggle/sample_submission.csv"
        result = validate_sample_csv(path)
        self.assertTrue(result["passed"], result)

    def test_invalid_headers_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.csv"
            path.write_text("Id,path,notes\ntok_cross_tenant_secret_read,submissions/tok_cross_tenant_secret_read/submission.json,note\n", encoding="utf-8")
            result = validate_sample_csv(path)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Invalid headers" in err for err in result["errors"]))
