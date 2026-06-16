import tempfile
import unittest
from pathlib import Path

from scripts.build_host_review_bundle import is_allowed_file, check_private_markers


class BuildHostReviewBundleTests(unittest.TestCase):
    def test_is_allowed_file_valid(self) -> None:
        self.assertTrue(is_allowed_file("README.md"))
        self.assertTrue(is_allowed_file("docs/host/host-review-package.md"))
        self.assertTrue(is_allowed_file("platform/kaggle/sample_submission.csv"))
        self.assertTrue(is_allowed_file("authzbench/score.py"))

    def test_is_allowed_file_denied_prefixes(self) -> None:
        self.assertFalse(is_allowed_file("tasks_private/holdout/fake.json"))
        self.assertFalse(is_allowed_file("captures/request.log"))
        self.assertFalse(is_allowed_file("results/raw.json"))
        self.assertFalse(is_allowed_file(".handoff/notes.md"))
        self.assertFalse(is_allowed_file("docs/reviews/panel-logs/raw.md"))
        self.assertFalse(is_allowed_file("artifact/harbor-dataset-public-smoke/harbor-jobs/job-1/log.txt"))
        self.assertFalse(is_allowed_file("harbor-jobs/job-1/log.txt"))

    def test_is_allowed_file_denied_extensions(self) -> None:
        self.assertFalse(is_allowed_file("authzbench/key.pem"))
        self.assertFalse(is_allowed_file("authzbench/cert.pfx"))

    def test_is_allowed_file_env_files(self) -> None:
        self.assertFalse(is_allowed_file(".env"))
        self.assertFalse(is_allowed_file(".env.production"))
        self.assertFalse(is_allowed_file("sub/.env"))

    def test_check_private_markers_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "clean.py"
            f.write_text("print('hello')", encoding="utf-8")
            errors = check_private_markers(f)
            self.assertEqual(errors, [])

    def test_check_private_markers_openai_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "dirty.py"
            f.write_text("API_KEY = 'sk-" + "12345678901234567890123456789012'", encoding="utf-8")
            errors = check_private_markers(f)
            self.assertTrue(any("OpenAI API key" in err for err in errors))

    def test_check_private_markers_github_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "dirty.py"
            f.write_text("TOKEN = 'ghp_" + "abcdefghijklmnopqrstuvwxyz0123456789'", encoding="utf-8")
            errors = check_private_markers(f)
            self.assertTrue(any("GitHub token" in err for err in errors))

    def test_check_private_markers_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "dirty.py"
            f.write_text("PATH = '/Users/" + "brianmendonca/Documents'", encoding="utf-8")
            errors = check_private_markers(f)
            self.assertTrue(any("absolute local path" in err for err in errors))
