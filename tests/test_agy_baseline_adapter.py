from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from authzbench.run import run_benchmark
from scripts.agy_baseline_agent import _effective_model_label, _extract_json, main, run_agy


ROOT = Path(__file__).resolve().parents[1]
MODEL = "Gemini 3.1 Pro (High)"


class AgyBaselineAdapterTests(unittest.TestCase):
    def test_extracts_fenced_findings_json(self) -> None:
        self.assertEqual(_extract_json('```json\n{"findings":[]}\n```'), {"findings": []})

    def test_effective_model_label_uses_last_propagated_label(self) -> None:
        log = (
            'Propagating selected model override to backend: label="Gemini 3.5 Flash (High)"\n'
            'Propagating selected model override to backend: label="Gemini 3.1 Pro (High)"\n'
        )
        self.assertEqual(_effective_model_label(log), MODEL)

    def test_command_failure_has_no_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "agy.log"
            with patch(
                "scripts.agy_baseline_agent.subprocess.run",
                return_value=subprocess.CompletedProcess(["agy"], 1, stdout="", stderr="failure"),
            ):
                submission, metadata = run_agy({}, MODEL, 1, log_path)

        self.assertIsNone(submission)
        self.assertTrue(metadata["adapter_failed"])
        self.assertEqual(metadata["parse_error"], "agy command failed")

    def test_unverified_model_label_has_no_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "agy.log"
            log_path.write_text(
                'Propagating selected model override to backend: label="other-model"\n',
                encoding="utf-8",
            )
            with patch(
                "scripts.agy_baseline_agent.subprocess.run",
                return_value=subprocess.CompletedProcess(["agy"], 0, stdout='{"findings": []}', stderr=""),
            ):
                submission, metadata = run_agy({}, MODEL, 1, log_path)

        self.assertIsNone(submission)
        self.assertTrue(metadata["adapter_failed"])
        self.assertEqual(metadata["parse_error"], "agy model label was not verified")

    def test_malformed_output_has_no_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "agy.log"
            log_path.write_text(
                f'Propagating selected model override to backend: label="{MODEL}"\n',
                encoding="utf-8",
            )
            with patch(
                "scripts.agy_baseline_agent.subprocess.run",
                return_value=subprocess.CompletedProcess(["agy"], 0, stdout="not JSON", stderr=""),
            ):
                submission, metadata = run_agy({}, MODEL, 1, log_path)

        self.assertIsNone(submission)
        self.assertTrue(metadata["adapter_failed"])
        self.assertIn("did not contain", metadata["parse_error"])

    def test_timeout_has_no_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "agy.log"
            with patch(
                "scripts.agy_baseline_agent.subprocess.run",
                side_effect=subprocess.TimeoutExpired(["agy"], 31, output="partial", stderr="late"),
            ):
                submission, metadata = run_agy({}, MODEL, 1, log_path)

        self.assertIsNone(submission)
        self.assertTrue(metadata["adapter_failed"])
        self.assertEqual(metadata["parse_error"], "agy command timed out")
        self.assertEqual(metadata["stdout"], "partial")

    def test_launch_failure_has_no_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "agy.log"
            with patch(
                "scripts.agy_baseline_agent.subprocess.run",
                side_effect=FileNotFoundError("agy"),
            ):
                submission, metadata = run_agy({}, MODEL, 1, log_path)

        self.assertIsNone(submission)
        self.assertTrue(metadata["adapter_failed"])
        self.assertEqual(metadata["parse_error"], "agy command could not start")

    def test_non_list_findings_has_no_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "agy.log"
            log_path.write_text(
                f'Propagating selected model override to backend: label="{MODEL}"\n',
                encoding="utf-8",
            )
            with patch(
                "scripts.agy_baseline_agent.subprocess.run",
                return_value=subprocess.CompletedProcess(["agy"], 0, stdout='{"findings": {}}', stderr=""),
            ):
                submission, metadata = run_agy({}, MODEL, 1, log_path)

        self.assertIsNone(submission)
        self.assertTrue(metadata["adapter_failed"])
        self.assertEqual(metadata["parse_error"], "model output findings must be a list")

    def test_main_failure_writes_metadata_but_not_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            context_path = tmp_path / "context.json"
            submission_path = tmp_path / "submission.json"
            context_path.write_text(json.dumps({}), encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    "AUTHZBENCH_CONTEXT": str(context_path),
                    "AUTHZBENCH_SUBMISSION": str(submission_path),
                },
                clear=False,
            ):
                with patch(
                    "scripts.agy_baseline_agent.subprocess.run",
                    return_value=subprocess.CompletedProcess(["agy"], 1, stdout="", stderr="failure"),
                ):
                    result = main(["--model", MODEL, "--timeout-seconds", "1"])

            metadata = json.loads((tmp_path / "model-output.json").read_text(encoding="utf-8"))
            self.assertEqual(result, 1)
            self.assertFalse(submission_path.exists())
            self.assertTrue(metadata["adapter_failed"])

    def test_command_failure_is_invalid_not_secure_control_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_agy = tmp_path / "agy"
            fake_agy.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            fake_agy.chmod(0o755)
            with patch.dict(
                os.environ,
                {"PATH": f"{tmp}{os.pathsep}{os.environ.get('PATH', '')}"},
                clear=False,
            ):
                summary = run_benchmark(
                    [str(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")],
                    f'{sys.executable} scripts/agy_baseline_agent.py --model "{MODEL}" --timeout-seconds 1',
                    tmp_path / "results",
                    timeout_seconds=5,
                )

        task = summary["tasks"][0]
        self.assertEqual(task["agent_returncode"], 1, task)
        self.assertTrue(task["invalid_submission"], task)
        self.assertFalse(task["passed"], task)
        self.assertTrue(task["model_output_artifact"], task)
        self.assertTrue(task["adapter_failed"], task)
        self.assertEqual(task["adapter_parse_error"], "agy command failed", task)
        self.assertFalse(task["model_label_verified"], task)
        self.assertEqual(summary["model_output_artifact_count"], 1, summary)
        self.assertEqual(summary["adapter_failure_count"], 1, summary)
        self.assertEqual(summary["adapter_failure_rate"], 1.0, summary)
        self.assertEqual(summary["model_label_unverified_count"], 1, summary)
        self.assertEqual(summary["passed_count"], 0, summary)


if __name__ == "__main__":
    unittest.main()
