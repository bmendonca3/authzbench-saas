from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.kiro_baseline_agent import (
    _extract_json,
    _extract_json_with_metadata,
    _write_adapter_result,
    run_kiro,
)


class KiroBaselineAdapterTests(unittest.TestCase):
    def test_extracts_plain_json(self) -> None:
        self.assertEqual(_extract_json('{"findings": []}')["findings"], [])
        _submission, output_format, compliant = _extract_json_with_metadata('{"findings": []}')
        self.assertEqual(output_format, "plain_json")
        self.assertTrue(compliant)

    def test_extracts_fenced_json(self) -> None:
        text = '```json\n{"findings": [{"claim": "x"}]}\n```'
        self.assertEqual(_extract_json(text)["findings"][0]["claim"], "x")
        _submission, output_format, compliant = _extract_json_with_metadata(text)
        self.assertEqual(output_format, "fenced_json")
        self.assertFalse(compliant)

    def test_records_explicit_model_effort_and_prompt_provenance(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["kiro"],
            returncode=0,
            stdout='{"findings": [], "verification": []}',
            stderr="",
        )
        with patch("scripts.kiro_baseline_agent.subprocess.run", return_value=completed) as mocked:
            submission, metadata = run_kiro(
                {"candidate_requests": [{"actor": "demo", "method": "GET", "path": "/api/x"}]},
                "claude-sonnet-5",
                5,
                effort="high",
                kiro_cli_version="kiro-cli 2.12.1",
            )

        command = mocked.call_args.args[0]
        self.assertEqual(submission["findings"], [])
        self.assertEqual(metadata["requested_model"], "claude-sonnet-5")
        self.assertEqual(metadata["requested_effort"], "high")
        self.assertIsNone(metadata["effective_model_label"])
        self.assertIsNone(metadata["model_label_verified"])
        self.assertEqual(metadata["model_identity_status"], "requested_only_unverified")
        self.assertIn("does not expose", metadata["model_identity_claim_boundary"])
        self.assertEqual(metadata["kiro_cli_version"], "kiro-cli 2.12.1")
        self.assertRegex(metadata["prompt_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(metadata["output_format"], "plain_json")
        self.assertTrue(metadata["json_only_compliant"])
        self.assertIn("--effort", command)
        self.assertIn("high", command)

    def test_extracts_final_findings_after_transcript_json(self) -> None:
        text = (
            "I considered this example shape first: "
            '{"request":{"actor":"demo","method":"GET","path":"/api/x"}}\n'
            "The final submission is:\n"
            '{"findings":[]}'
        )
        self.assertEqual(_extract_json(text)["findings"], [])

    def test_ignores_non_submission_json_prefix_when_later_finding_exists(self) -> None:
        text = '{"request":{"actor":"demo"}}\n{"findings":[{"claim":"ok"}]}'
        self.assertEqual(_extract_json(text)["findings"][0]["claim"], "ok")

    def test_malformed_fenced_json_falls_back_to_later_submission(self) -> None:
        text = "```json\n{broken\n```\nanalysis...\n{\"findings\":[]}"
        self.assertEqual(_extract_json(text)["findings"], [])

    def test_nonzero_cli_result_does_not_become_empty_findings(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["kiro"],
            returncode=101,
            stdout='{"findings":[]}',
            stderr="kiro crashed",
        )
        with patch("scripts.kiro_baseline_agent.subprocess.run", return_value=completed):
            submission, metadata = run_kiro({}, "qwen3-coder-next", 5)

        self.assertIsNone(submission)
        self.assertEqual(metadata["returncode"], 101)
        self.assertEqual(metadata["parse_error"], "kiro command failed")

    def test_timeout_bytes_are_normalized_for_json_metadata(self) -> None:
        timeout = subprocess.TimeoutExpired(
            cmd=["kiro"],
            timeout=5,
            output=b"partial output",
            stderr=b"timeout error",
        )
        with patch("scripts.kiro_baseline_agent.subprocess.run", side_effect=timeout):
            submission, metadata = run_kiro({}, "qwen3-coder-next", 5)

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
                {"returncode": 101, "parse_error": "kiro command failed"},
            )

            self.assertEqual(returncode, 2)
            self.assertFalse(submission_path.exists())
            metadata = json.loads((Path(tmp) / "model-output.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["returncode"], 101)


if __name__ == "__main__":
    unittest.main()
