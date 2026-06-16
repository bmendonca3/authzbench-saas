import tempfile
import unittest
from pathlib import Path
import json

from scripts.validate_kaggle_dry_run_bundle import validate_dry_run_bundle


class ValidateKaggleDryRunBundleTests(unittest.TestCase):
    def test_current_dry_run_bundle_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "platform/kaggle/dry-run-bundle"
        result = validate_dry_run_bundle(path)
        self.assertTrue(result["passed"], result)

    def test_missing_files_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            result = validate_dry_run_bundle(path)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Missing sample_submission.csv" in err for err in result["errors"]))
