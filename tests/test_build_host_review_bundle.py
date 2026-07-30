import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_host_review_bundle import (
    build_bundle,
    check_private_markers,
    is_allowed_file,
)


class BuildHostReviewBundleTests(unittest.TestCase):
    def _init_repo(self, root: Path) -> str:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(
            ["git", "config", "user.name", "bmendonca3"],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "bmendonca3@example.com"],
            cwd=root,
            check=True,
        )
        (root / "README.md").write_text("committed content\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "seed bundle source"],
            cwd=root,
            check=True,
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

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

    def test_build_bundle_materializes_exact_ref_not_dirty_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            repo = temp_root / "repo"
            repo.mkdir()
            source_commit = self._init_repo(repo)
            (repo / "README.md").write_text("dirty content\n", encoding="utf-8")
            output = temp_root / "bundle"

            result = build_bundle(
                output,
                ref_commit=source_commit,
                allow_dirty=True,
                created_at_utc="2026-06-16T00:00:00Z",
                root=repo,
            )

            self.assertTrue(result["passed"], result["errors"])
            self.assertEqual(
                (output / "README.md").read_text(encoding="utf-8"),
                "committed content\n",
            )
            manifest = json.loads(
                (output / "manifest.json").read_text(encoding="utf-8")
            )
            expected_tree = subprocess.run(
                ["git", "rev-parse", f"{source_commit}^{{tree}}"],
                cwd=repo,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            expected_blob = subprocess.run(
                ["git", "rev-parse", f"{source_commit}:README.md"],
                cwd=repo,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            readme_entry = next(
                entry for entry in manifest["files"] if entry["path"] == "README.md"
            )
            self.assertEqual(manifest["source_commit"], source_commit)
            self.assertEqual(manifest["source_tree"], expected_tree)
            self.assertEqual(manifest["source_materialization"], "git_object_database")
            self.assertFalse(manifest["working_tree_changes_included"])
            self.assertTrue(manifest["git_dirty"])
            self.assertEqual(readme_entry["git_blob_sha"], expected_blob)

    def test_build_bundle_fails_closed_for_dirty_release_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            repo = temp_root / "repo"
            repo.mkdir()
            source_commit = self._init_repo(repo)
            (repo / "README.md").write_text("dirty content\n", encoding="utf-8")
            output = temp_root / "bundle"

            result = build_bundle(
                output,
                ref_commit=source_commit,
                created_at_utc="2026-06-16T00:00:00Z",
                root=repo,
            )

            self.assertFalse(result["passed"])
            self.assertTrue(
                any("uncommitted changes" in error for error in result["errors"])
            )
            self.assertFalse(output.exists())

    def test_build_bundle_fails_closed_for_invalid_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            repo = temp_root / "repo"
            repo.mkdir()
            self._init_repo(repo)
            output = temp_root / "bundle"

            result = build_bundle(
                output,
                ref_commit="missing-ref",
                allow_dirty=True,
                created_at_utc="2026-06-16T00:00:00Z",
                root=repo,
            )

            self.assertFalse(result["passed"])
            self.assertTrue(
                any("Failed to resolve Git ref" in error for error in result["errors"])
            )
            self.assertFalse(output.exists())

    def test_build_bundle_fails_closed_when_git_inspection_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            not_a_repo = temp_root / "not-a-repo"
            not_a_repo.mkdir()
            output = temp_root / "bundle"

            result = build_bundle(
                output,
                allow_dirty=True,
                created_at_utc="2026-06-16T00:00:00Z",
                root=not_a_repo,
            )

            self.assertFalse(result["passed"])
            self.assertTrue(
                any(
                    "Failed to inspect Git working tree" in error
                    for error in result["errors"]
                )
            )
            self.assertFalse(output.exists())
