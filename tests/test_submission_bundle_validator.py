"""Submission bundle validator tests.

Drives ``scripts/validate_submission_bundle.py`` against three
hand-built bundles:

  * a good no-tools bundle (passes)
  * a missing-files bundle (fails)
  * a tool-agent bundle missing ``target-requests.jsonl`` (fails)
  * a no-tools bundle that contains a secret pattern (fails)

The validator runs as a subprocess so we exercise the same code path
the CI gate uses, not the in-process API.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_submission_bundle.py"


def _write_bundle(base: Path, harness_type: str, *, with_target_requests: bool, with_secret: bool) -> Path:
    bundle = base / "bundle"
    bundle.mkdir()
    (bundle / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": "test-run-1",
                "benchmark_commit_sha": "abc",
                "harness_type": harness_type,
                "split": "public",
                "agent": "test",
                "model": "test",
                "private_pack_fingerprint_sha256": "6b8b51c03492238c881b737029e7802d4127ab2a53655db2b7d5bf25032ba7c8",
            }
        )
    )
    (bundle / "score.json").write_text(json.dumps({"run_id": "test-run-1", "score": 1.0}))
    (bundle / "summary.json").write_text(json.dumps({"run_id": "test-run-1", "summary": True}))
    (bundle / "transcript.json").write_text(json.dumps({"run_id": "test-run-1", "transcript": []}))
    (bundle / "submission.json").write_text(json.dumps({"findings": []}))
    (bundle / "environment.json").write_text(
        json.dumps({"environment_hash": "abc", "python_version": "3.11"})
    )
    if with_target_requests:
        (bundle / "target-requests.jsonl").write_text(
            "\n".join(
                json.dumps({"method": "GET", "path": "/api/secure/x", "actor": "beta"})
                for _ in range(3)
            )
        )
    if with_secret:
        (bundle / "submission.json").write_text(
            json.dumps(
                {
                    "findings": [
                        {
                            "claim": "leaked",
                            "evidence": [{"request": {"actor": "evil", "method": "GET", "path": "/x", "headers": {"Authorization": "Bearer sk-abcdefghijklmnopqrstuvwxyz1234567890"}}}],
                            "impact": "secret pattern embedded",
                        }
                    ]
                }
            )
        )
    return bundle


def _run_validator(bundle: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), str(bundle), *extra],
        check=False,
        capture_output=True,
        text=True,
    )


class SubmissionBundleValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="authzbench-bundle-")

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_good_no_tools_bundle_passes(self) -> None:
        bundle = _write_bundle(Path(self._tmp), "no-tools-model", with_target_requests=False, with_secret=False)
        result = _run_validator(bundle)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_required_file_fails(self) -> None:
        bundle = _write_bundle(Path(self._tmp), "no-tools-model", with_target_requests=False, with_secret=False)
        (bundle / "score.json").unlink()
        result = _run_validator(bundle)
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing_required_file", result.stderr)

    def test_tool_agent_bundle_missing_target_requests_fails(self) -> None:
        bundle = _write_bundle(Path(self._tmp), "tool-agent", with_target_requests=False, with_secret=False)
        result = _run_validator(bundle)
        self.assertEqual(result.returncode, 1)
        self.assertIn("tool_agent_missing_target_requests", result.stderr)

    def test_tool_agent_bundle_with_target_requests_passes(self) -> None:
        bundle = _write_bundle(Path(self._tmp), "tool-agent", with_target_requests=True, with_secret=False)
        result = _run_validator(bundle)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_secret_pattern_in_submission_fails(self) -> None:
        bundle = _write_bundle(Path(self._tmp), "no-tools-model", with_target_requests=False, with_secret=True)
        result = _run_validator(bundle)
        self.assertEqual(result.returncode, 1)
        self.assertIn("secret_pattern_present", result.stderr)

    def test_run_id_mismatch_between_files_fails(self) -> None:
        bundle = _write_bundle(Path(self._tmp), "no-tools-model", with_target_requests=False, with_secret=False)
        data = json.loads((bundle / "summary.json").read_text())
        data["run_id"] = "different-run"
        (bundle / "summary.json").write_text(json.dumps(data))
        result = _run_validator(bundle)
        self.assertEqual(result.returncode, 1)
        self.assertIn("run_id_mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
