import json
import tempfile
import unittest
from pathlib import Path
import hashlib

import scripts.validate_host_review_bundle
from scripts.validate_host_review_bundle import validate_bundle

VALID_SHA = "ef8b233565bfc1a606bf38b2e9afdd3d60bf4158"
VALID_CLAIM = "host-review only; no platform acceptance, hosted leaderboard operation, or external validation."
VALID_TIME = "2026-06-16T00:00:00Z"


class ValidateHostReviewBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orig_required = scripts.validate_host_review_bundle.REQUIRED_FILES
        # By default, clear REQUIRED_FILES to avoid missing required file errors in unit tests
        scripts.validate_host_review_bundle.REQUIRED_FILES = []

    def tearDown(self) -> None:
        scripts.validate_host_review_bundle.REQUIRED_FILES = self.orig_required

    def test_validate_bundle_valid(self) -> None:
        # Override REQUIRED_FILES for the valid path test
        scripts.validate_host_review_bundle.REQUIRED_FILES = [
            "docs/host/host-review-package.md",
            "platform/kaggle/sample_submission.csv",
        ]

        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)

            def get_sha(text: str) -> str:
                h = hashlib.sha256()
                h.update(text.encode("utf-8"))
                return h.hexdigest()

            # Create required files
            f1_text = "Hello, this is host-review package"
            f1 = bundle_dir / "docs/host/host-review-package.md"
            f1.parent.mkdir(parents=True, exist_ok=True)
            f1.write_text(f1_text, encoding="utf-8")

            f2_text = "Id,finding_path,notes"
            f2 = bundle_dir / "platform/kaggle/sample_submission.csv"
            f2.parent.mkdir(parents=True, exist_ok=True)
            f2.write_text(f2_text, encoding="utf-8")

            manifest = {
                "schema_version": "host-review-bundle-manifest-v1",
                "source_commit": VALID_SHA,
                "created_at_utc": VALID_TIME,
                "claim_boundary": VALID_CLAIM,
                "files": [
                    {
                        "path": "docs/host/host-review-package.md",
                        "sha256": get_sha(f1_text),
                        "bytes": len(f1_text),
                    },
                    {
                        "path": "platform/kaggle/sample_submission.csv",
                        "sha256": get_sha(f2_text),
                        "bytes": len(f2_text),
                    },
                ],
            }

            manifest_path = bundle_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_bundle(bundle_dir)
            self.assertTrue(result["passed"], result.get("errors"))

    def test_validate_bundle_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)
            result = validate_bundle(bundle_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("manifest.json is missing" in err for err in result["errors"]))

    def test_validate_bundle_mismatched_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)

            f1 = bundle_dir / "docs/host/host-review-package.md"
            f1.parent.mkdir(parents=True, exist_ok=True)
            f1.write_text("Hello, this is host-review package", encoding="utf-8")

            manifest = {
                "schema_version": "host-review-bundle-manifest-v1",
                "source_commit": VALID_SHA,
                "created_at_utc": VALID_TIME,
                "claim_boundary": VALID_CLAIM,
                "files": [
                    {
                        "path": "docs/host/host-review-package.md",
                        "sha256": "wrong_hash",
                        "bytes": len("Hello, this is host-review package"),
                    }
                ],
            }
            manifest_path = bundle_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_bundle(bundle_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("hash mismatch" in err for err in result["errors"]))

    def test_validate_bundle_denied_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)

            f1 = bundle_dir / "harbor-jobs/job-1/log.txt"
            f1.parent.mkdir(parents=True, exist_ok=True)
            f1.write_text("Job log", encoding="utf-8")

            manifest = {
                "schema_version": "host-review-bundle-manifest-v1",
                "source_commit": VALID_SHA,
                "created_at_utc": VALID_TIME,
                "claim_boundary": VALID_CLAIM,
                "files": [
                    {
                        "path": "harbor-jobs/job-1/log.txt",
                        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # dummy
                        "bytes": 7,
                    }
                ],
            }
            manifest_path = bundle_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_bundle(bundle_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("denied component" in err or "denied prefix" in err for err in result["errors"]))

    def test_validate_bundle_private_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)

            f1 = bundle_dir / "docs/host/host-review-package.md"
            f1.parent.mkdir(parents=True, exist_ok=True)
            f1.write_text("API key: sk-" + "12345678901234567890123456789012", encoding="utf-8")

            manifest = {
                "schema_version": "host-review-bundle-manifest-v1",
                "source_commit": VALID_SHA,
                "created_at_utc": VALID_TIME,
                "claim_boundary": VALID_CLAIM,
                "files": [
                    {
                        "path": "docs/host/host-review-package.md",
                        "sha256": "dummy_sha",
                        "bytes": len("API key: sk-" + "12345678901234567890123456789012"),
                    }
                ],
            }
            manifest_path = bundle_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            h = hashlib.sha256()
            h.update(f1.read_bytes())
            manifest["files"][0]["sha256"] = h.hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_bundle(bundle_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("Contains OpenAI API key" in err for err in result["errors"]))

    def test_validate_bundle_claim_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)

            f1 = bundle_dir / "docs/host/host-review-package.md"
            f1.parent.mkdir(parents=True, exist_ok=True)
            f1.write_text("This is an externally validated benchmark.", encoding="utf-8")

            manifest = {
                "schema_version": "host-review-bundle-manifest-v1",
                "source_commit": VALID_SHA,
                "created_at_utc": VALID_TIME,
                "claim_boundary": VALID_CLAIM,
                "files": [
                    {
                        "path": "docs/host/host-review-package.md",
                        "sha256": "dummy_sha",
                        "bytes": len("This is an externally validated benchmark."),
                    }
                ],
            }
            manifest_path = bundle_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            h = hashlib.sha256()
            h.update(f1.read_bytes())
            manifest["files"][0]["sha256"] = h.hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_bundle(bundle_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("Forbidden claim boundary phrase" in err for err in result["errors"]))

    def test_validate_bundle_unmanifested_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)

            # Create manifest with only f1
            f1 = bundle_dir / "docs/host/host-review-package.md"
            f1.parent.mkdir(parents=True, exist_ok=True)
            f1.write_text("Hello, this is host-review package", encoding="utf-8")

            # Create another untracked/unmanifested file
            f2 = bundle_dir / "docs/sneaky_file.txt"
            f2.write_text("Sneaky content", encoding="utf-8")

            manifest = {
                "schema_version": "host-review-bundle-manifest-v1",
                "source_commit": VALID_SHA,
                "created_at_utc": VALID_TIME,
                "claim_boundary": VALID_CLAIM,
                "files": [
                    {
                        "path": "docs/host/host-review-package.md",
                        "sha256": "dfcf2de72579b1df098547285c544d6db29cb9316cd9c2a13b6324db0a597a7e",
                        "bytes": len("Hello, this is host-review package"),
                    }
                ],
            }
            manifest_path = bundle_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            h = hashlib.sha256()
            h.update(f1.read_bytes())
            manifest["files"][0]["sha256"] = h.hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_bundle(bundle_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("contains files not listed in manifest" in err.lower() for err in result["errors"]))

    def test_validate_bundle_symlink_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp)

            # Create valid file docs/host/host-review-package.md
            f1 = bundle_dir / "docs/host/host-review-package.md"
            f1.parent.mkdir(parents=True, exist_ok=True)
            f1.write_text("Hello, this is host-review package", encoding="utf-8")

            # Create a symlink pointing to f1 (or any other location)
            sym = bundle_dir / "docs/symlink.md"
            try:
                sym.symlink_to(f1)
            except OSError:
                # If OS doesn't support symlinks (e.g. non-admin Windows), skip
                self.skipTest("Symlinks not supported on this environment")

            manifest = {
                "schema_version": "host-review-bundle-manifest-v1",
                "source_commit": VALID_SHA,
                "created_at_utc": VALID_TIME,
                "claim_boundary": VALID_CLAIM,
                "files": [
                    {
                        "path": "docs/host/host-review-package.md",
                        "sha256": "dfcf2de72579b1df098547285c544d6db29cb9316cd9c2a13b6324db0a597a7e",
                        "bytes": len("Hello, this is host-review package"),
                    }
                ],
            }
            manifest_path = bundle_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            h = hashlib.sha256()
            h.update(f1.read_bytes())
            manifest["files"][0]["sha256"] = h.hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = validate_bundle(bundle_dir)
            self.assertFalse(result["passed"])
            self.assertTrue(any("Symlinks are prohibited" in err for err in result["errors"]))
