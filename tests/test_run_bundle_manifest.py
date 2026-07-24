from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from authzbench.core import stable_json_sha256
from authzbench.run_bundle import (
    MANIFEST_FILENAME,
    RunBundleError,
    build_run_bundle_manifest,
    validate_run_bundle_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_run_bundle_manifest.py"
VALIDATE_SCRIPT = ROOT / "scripts" / "validate_run_bundle_manifest.py"


def _write_completed_run(root: Path) -> Path:
    bundle = root / "run"
    bundle.mkdir(parents=True)
    (bundle / "summary.json").write_text('{"run_id":"run-1"}\n', encoding="utf-8")
    task = bundle / "task-001"
    task.mkdir()
    (task / "agent.json").write_text('{"findings":[]}\n', encoding="utf-8")
    (task / "score.json").write_text('{"score":1}\n', encoding="utf-8")
    (task / "submission.json").write_text('{"findings":[]}\n', encoding="utf-8")
    (task / "transcript.json").write_text('{"events":[]}\n', encoding="utf-8")
    (bundle / "wrapper.log").write_text("complete\n", encoding="utf-8")
    return bundle


def _build(bundle: Path) -> dict[str, object]:
    return build_run_bundle_manifest(
        bundle,
        required_paths=["summary.json"],
        required_globs=[
            "*/agent.json",
            "*/score.json",
            "*/submission.json",
            "*/transcript.json",
        ],
    )


def _codes(bundle: Path) -> set[str]:
    return {finding["code"] for finding in validate_run_bundle_manifest(bundle)["findings"]}


class RunBundleManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp(prefix="authzbench-run-bundle-"))

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_manifest_is_deterministic_and_contains_metadata_only(self) -> None:
        first = _write_completed_run(self._tmp / "first")
        second = _write_completed_run(self._tmp / "second")

        first_manifest = _build(first)
        second_manifest = _build(second)

        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(
            (first / MANIFEST_FILENAME).read_bytes(),
            (second / MANIFEST_FILENAME).read_bytes(),
        )
        serialized = (first / MANIFEST_FILENAME).read_text(encoding="utf-8")
        self.assertNotIn(str(first), serialized)
        self.assertNotIn("complete", serialized)
        self.assertTrue(validate_run_bundle_manifest(first)["passed"])

    def test_refuses_to_overwrite_existing_manifest(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        before = (bundle / MANIFEST_FILENAME).read_bytes()

        with self.assertRaises(RunBundleError) as caught:
            _build(bundle)

        self.assertEqual(caught.exception.code, "manifest_already_exists")
        self.assertEqual((bundle / MANIFEST_FILENAME).read_bytes(), before)

    def test_tampered_file_fails_hash_validation(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        (bundle / "wrapper.log").write_text("tampered\n", encoding="utf-8")
        self.assertIn("bundle_file_sha256_mismatch", _codes(bundle))

    def test_missing_file_fails_completeness_and_requirement_validation(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        (bundle / "task-001" / "score.json").unlink()
        (bundle / "summary.json").unlink()
        codes = _codes(bundle)
        self.assertIn("bundle_file_missing", codes)
        self.assertIn("required_path_missing", codes)
        self.assertIn("required_glob_unmatched", codes)

    def test_file_added_after_freeze_is_unexpected(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        (bundle / "late-wrapper.log").write_text("late\n", encoding="utf-8")
        self.assertIn("unexpected_bundle_file", _codes(bundle))

    def test_symlink_is_rejected_during_build_and_validation(self) -> None:
        bundle = _write_completed_run(self._tmp)
        (bundle / "link.txt").symlink_to(bundle / "summary.json")
        with self.assertRaises(RunBundleError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "symlink_present")

        (bundle / "link.txt").unlink()
        _build(bundle)
        (bundle / "link.txt").symlink_to(bundle / "summary.json")
        self.assertIn("symlink_present", _codes(bundle))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX mkfifo")
    def test_non_regular_file_is_rejected_during_build_and_validation(self) -> None:
        bundle = _write_completed_run(self._tmp)
        os.mkfifo(bundle / "evidence.pipe")
        with self.assertRaises(RunBundleError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "non_regular_path")

        (bundle / "evidence.pipe").unlink()
        _build(bundle)
        os.mkfifo(bundle / "evidence.pipe")
        self.assertIn("non_regular_path", _codes(bundle))

    def test_build_rejects_missing_required_evidence(self) -> None:
        bundle = _write_completed_run(self._tmp)
        with self.assertRaises(RunBundleError) as caught:
            build_run_bundle_manifest(
                bundle,
                required_paths=["summary.json", "environment.json"],
                required_globs=["*/model-output.json"],
            )
        self.assertEqual(caught.exception.code, "required_evidence_missing")
        self.assertFalse((bundle / MANIFEST_FILENAME).exists())

    def test_empty_directory_fails_the_default_summary_requirement(self) -> None:
        bundle = self._tmp / "empty-run"
        bundle.mkdir()
        with self.assertRaises(RunBundleError) as caught:
            build_run_bundle_manifest(bundle)
        self.assertEqual(caught.exception.code, "required_evidence_missing")
        self.assertFalse((bundle / MANIFEST_FILENAME).exists())

    def test_forged_unsafe_paths_fail_structure(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        manifest_path = bundle / MANIFEST_FILENAME
        original = json.loads(manifest_path.read_text(encoding="utf-8"))
        unsafe_paths = (
            "../outside.json",
            "/absolute.json",
            "task//score.json",
            "task\\score.json",
            "bad\nname",
        )
        for unsafe in unsafe_paths:
            with self.subTest(path=unsafe):
                manifest = json.loads(json.dumps(original))
                manifest["files"][0]["path"] = unsafe
                manifest["bundle_sha256"] = stable_json_sha256(
                    {key: value for key, value in manifest.items() if key != "bundle_sha256"}
                )
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                self.assertIn("manifest_file_path_unsafe", _codes(bundle))

    def test_malformed_recorded_hash_fails_structure(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        manifest_path = bundle / MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][0]["sha256"] = "bad"
        manifest["bundle_sha256"] = stable_json_sha256(
            {key: value for key, value in manifest.items() if key != "bundle_sha256"}
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertIn("manifest_file_sha256_invalid", _codes(bundle))

    def test_duplicate_recorded_path_fails_structure(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        manifest_path = bundle / MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        duplicate = dict(manifest["files"][0])
        manifest["files"].append(duplicate)
        manifest["file_count"] += 1
        manifest["total_bytes"] += duplicate["size_bytes"]
        manifest["bundle_sha256"] = stable_json_sha256(
            {key: value for key, value in manifest.items() if key != "bundle_sha256"}
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertIn("manifest_file_paths_not_sorted_unique", _codes(bundle))

    def test_duplicate_json_key_is_rejected(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        manifest_path = bundle / MANIFEST_FILENAME
        text = manifest_path.read_text(encoding="utf-8")
        text = text.replace(
            '"bundle_root": ".",',
            '"bundle_root": ".",\n  "bundle_root": ".",',
            1,
        )
        manifest_path.write_text(text, encoding="utf-8")
        self.assertIn("manifest_duplicate_key", _codes(bundle))

    def test_claim_boundary_tamper_is_rejected(self) -> None:
        bundle = _write_completed_run(self._tmp)
        _build(bundle)
        manifest_path = bundle / MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["claim_boundary"] = "This is an independent attestation."
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        codes = _codes(bundle)
        self.assertIn("manifest_claim_boundary_invalid", codes)
        self.assertIn("manifest_bundle_sha256_mismatch", codes)

    def test_cli_build_and_validate_exit_contract(self) -> None:
        bundle = _write_completed_run(self._tmp)
        build = subprocess.run(
            [
                "python3",
                str(BUILD_SCRIPT),
                str(bundle),
                "--require-glob",
                "*/score.json",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        validate = subprocess.run(
            ["python3", str(VALIDATE_SCRIPT), str(bundle), "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)
        self.assertTrue(json.loads(validate.stdout)["passed"])

        missing = subprocess.run(
            ["python3", str(VALIDATE_SCRIPT), str(self._tmp / "missing")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()
