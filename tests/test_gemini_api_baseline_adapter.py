from __future__ import annotations

import io
import json
import subprocess
import sys
import urllib.error
import unittest
from pathlib import Path

from scripts.gemini_api_baseline_agent import run_gemini


MODEL = "gemini-2.5-flash"


class _Response:
    def __init__(self, body: dict) -> None:
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return self.body


def _success(text: str = '{"findings":[]}') -> _Response:
    return _Response({
        "modelVersion": MODEL,
        "candidates": [{"content": {"parts": [{"text": text}]}}],
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 2},
    })


class GeminiApiBaselineAdapterTests(unittest.TestCase):
    def test_direct_script_execution_can_import_adapter_helpers(self) -> None:
        root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "scripts/gemini_api_baseline_agent.py", "--help"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_success_verifies_model_and_does_not_record_key(self) -> None:
        submission, metadata = run_gemini({}, model=MODEL, api_key="secret", timeout_seconds=1, urlopen=lambda *_a, **_k: _success())
        self.assertEqual(submission, {"findings": []})
        self.assertTrue(metadata["model_label_verified"])
        self.assertFalse(metadata["adapter_failed"])
        self.assertNotIn("secret", json.dumps(metadata))

    def test_missing_key_fails_closed(self) -> None:
        submission, metadata = run_gemini({}, model=MODEL, api_key=None, timeout_seconds=1)
        self.assertIsNone(submission)
        self.assertTrue(metadata["adapter_failed"])

    def test_http_error_fails_closed_without_body_or_key(self) -> None:
        error = urllib.error.HTTPError("url", 429, "quota", {}, io.BytesIO(b'{"secret":"body"}'))
        submission, metadata = run_gemini({}, model=MODEL, api_key="secret", timeout_seconds=1, urlopen=lambda *_a, **_k: (_ for _ in ()).throw(error), sleep=lambda _n: None, max_retries=0)
        self.assertIsNone(submission)
        self.assertEqual(metadata["returncode"], 429)
        self.assertNotIn("secret", json.dumps(metadata))
        self.assertNotIn("body", json.dumps(metadata))

    def test_transient_503_retries_then_succeeds(self) -> None:
        calls = 0

        def urlopen(*_args, **_kwargs):
            nonlocal calls
            calls += 1
            if calls < 3:
                raise urllib.error.HTTPError("url", 503, "busy", {}, io.BytesIO())
            return _success()

        submission, metadata = run_gemini(
            {}, model=MODEL, api_key="secret", timeout_seconds=1,
            urlopen=urlopen, sleep=lambda _n: None, max_retries=3,
        )
        self.assertEqual(submission, {"findings": []})
        self.assertEqual(metadata["attempt_count"], 3)

    def test_model_mismatch_fails_closed(self) -> None:
        response = _success()
        response = _Response({"modelVersion": "other", "candidates": [{"content": {"parts": [{"text": '{"findings":[]}'}]}}]})
        submission, metadata = run_gemini({}, model=MODEL, api_key="secret", timeout_seconds=1, urlopen=lambda *_a, **_k: response)
        self.assertIsNone(submission)
        self.assertFalse(metadata["model_label_verified"])

    def test_malformed_submission_fails_closed(self) -> None:
        submission, metadata = run_gemini({}, model=MODEL, api_key="secret", timeout_seconds=1, urlopen=lambda *_a, **_k: _success("not-json"))
        self.assertIsNone(submission)
        self.assertTrue(metadata["adapter_failed"])

    def test_non_list_findings_fails_closed(self) -> None:
        submission, metadata = run_gemini({}, model=MODEL, api_key="secret", timeout_seconds=1, urlopen=lambda *_a, **_k: _success('{"findings":{}}'))
        self.assertIsNone(submission)
        self.assertEqual(metadata["parse_error"], "model output findings must be a list")


if __name__ == "__main__":
    unittest.main()
