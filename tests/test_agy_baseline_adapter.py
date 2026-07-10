from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.agy_baseline_agent import _effective_model_label, _extract_json, _write_adapter_result, run_agy


class AgyBaselineAdapterTests(unittest.TestCase):
    def test_extracts_fenced_findings_json(self) -> None:
        self.assertEqual(_extract_json('```json\n{"findings":[]}\n```'), {"findings": []})

    def test_effective_model_label_uses_last_propagated_label(self) -> None:
        log = (
            'Propagating selected model override to backend: label="Gemini 3.5 Flash (High)"\n'
            'Propagating selected model override to backend: label="Gemini 3.1 Pro (High)"\n'
        )
        self.assertEqual(_effective_model_label(log), "Gemini 3.1 Pro (High)")

    def test_malformed_model_output_does_not_become_empty_findings(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["agy"],
            returncode=0,
            stdout='{"findings": []"findings": []}',
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "antigravity-cli.log"
            log_path.write_text(
                'Propagating selected model override to backend: label="Gemini 3.1 Pro (High)"\n',
                encoding="utf-8",
            )
            with patch("scripts.agy_baseline_agent.subprocess.run", return_value=completed):
                submission, metadata = run_agy({}, "Gemini 3.1 Pro (High)", 5, log_path)

        self.assertIsNone(submission)
        self.assertEqual(metadata["returncode"], 0)
        self.assertEqual(metadata["parse_error"], "model output did not contain a JSON object")

    def test_timeout_bytes_are_normalized_for_json_metadata(self) -> None:
        timeout = subprocess.TimeoutExpired(
            cmd=["agy"],
            timeout=5,
            output=b"partial output",
            stderr=b"timeout error",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with patch("scripts.agy_baseline_agent.subprocess.run", side_effect=timeout):
                submission, metadata = run_agy(
                    {},
                    "Gemini 3.1 Pro (High)",
                    5,
                    Path(tmp) / "antigravity-cli.log",
                )

        self.assertIsNone(submission)
        self.assertEqual(metadata["stdout"], "partial output")
        self.assertEqual(metadata["stderr"], "timeout error")
        json.dumps(metadata)

    def test_adapter_failure_writes_metadata_but_no_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            submission_path = Path(tmp) / "submission.json"
            submission_path.write_text('{"findings":[]}', encoding="utf-8")
            returncode = _write_adapter_result(
                submission_path,
                None,
                {"returncode": 0, "parse_error": "model output did not contain a JSON object"},
            )

            self.assertEqual(returncode, 2)
            self.assertFalse(submission_path.exists())
            metadata = json.loads((Path(tmp) / "model-output.json").read_text(encoding="utf-8"))
            self.assertIn("parse_error", metadata)


if __name__ == "__main__":
    unittest.main()
