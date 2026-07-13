from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.codex_baseline_agent import (
    CREDIT_BLOCKER_MESSAGE,
    CURRENT_CREDIT_BLOCKER_MESSAGE,
    DISABLED_FEATURES,
    PROFILE_SKILL_LOADING_STATUS,
    PROMPT_HASH_SCOPE,
    _global_blocker_code,
    _normalize_submission,
    _parse_event_stream,
    _write_adapter_result,
    main,
    run_codex,
)


def _event_text(*events: dict) -> str:
    return "".join(json.dumps(event) + "\n" for event in events)


def _structured_output() -> dict:
    return {
        "findings": [
            {
                "claim": "Cross-tenant read is permitted",
                "boundary": [{"field": "actor", "value": "member"}],
                "impact": "Private data disclosure",
                "evidence": [
                    {
                        "request": {
                            "actor": "member",
                            "method": "GET",
                            "path": "/api/items/one",
                            "body_json": "{}",
                        }
                    }
                ],
                "out_of_scope_actions": [],
            }
        ],
        "verification": [
            {
                "request": {
                    "actor": "member",
                    "method": "GET",
                    "path": "/api/items/one",
                    "body_json": "{}",
                },
                "expected": {"status": 200},
            }
        ],
    }


class CodexBaselineAdapterTests(unittest.TestCase):
    def test_success_uses_isolated_no_tools_structured_command_and_normalizes_output(self) -> None:
        events = _event_text(
            {"type": "thread.started", "thread_id": "thread", "model": "gpt-5.4-mini"},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "r1", "type": "reasoning", "text": "done"}},
            {
                "type": "item.completed",
                "item": {"id": "m1", "type": "agent_message", "text": "structured response"},
            },
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
        )

        def completed(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            final_path = Path(command[command.index("--output-last-message") + 1])
            final_path.write_text(json.dumps(_structured_output()), encoding="utf-8")
            self.assertEqual(kwargs["cwd"], final_path.parent)
            self.assertIn("Task context", str(kwargs["input"]))
            return subprocess.CompletedProcess(command, 0, stdout=events, stderr="warning")

        with patch("scripts.codex_baseline_agent.subprocess.run", side_effect=completed) as mocked:
            submission, metadata = run_codex(
                {"candidate_observations": []},
                "gpt-5.4-mini",
                "low",
                5,
                codex_path="codex",
                codex_cli_version="codex-cli 0.144.0-alpha.4",
            )

        command = mocked.call_args.args[0]
        self.assertEqual(submission["findings"][0]["boundary"], {"actor": "member"})
        self.assertEqual(submission["findings"][0]["evidence"][0]["request"]["body"], {})
        self.assertEqual(metadata["tool_attempt_telemetry_status"], "complete")
        self.assertEqual(metadata["tool_attempt_count"], 0)
        self.assertTrue(metadata["model_label_verified"])
        self.assertEqual(metadata["model_identity_status"], "verified")
        self.assertEqual(metadata["output_format"], "structured_json")
        self.assertRegex(metadata["prompt_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(metadata["prompt_hash_scope"], PROMPT_HASH_SCOPE)
        self.assertEqual(
            metadata["profile_skill_loading_status"],
            PROFILE_SKILL_LOADING_STATUS,
        )
        self.assertRegex(metadata["output_schema_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(command[-1], "-")
        self.assertNotIn("Task context", " ".join(command))
        self.assertIn("read-only", command)
        for feature in DISABLED_FEATURES:
            self.assertIn(feature, command)
        self.assertIn('web_search="disabled"', command)
        self.assertNotIn("web_search_cached", command)
        self.assertNotIn("web_search_request", command)

    def test_requested_only_identity_is_explicit_when_events_have_no_model_label(self) -> None:
        events = _event_text(
            {"type": "thread.started", "thread_id": "thread"},
            {"type": "turn.started"},
            {
                "type": "item.completed",
                "item": {"id": "notice", "type": "error", "message": "non-fatal CLI notice"},
            },
            {"type": "item.completed", "item": {"id": "m1", "type": "agent_message"}},
            {"type": "turn.completed", "usage": {}},
        )

        def completed(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            final_path = Path(command[command.index("--output-last-message") + 1])
            final_path.write_text(json.dumps({"findings": [], "verification": []}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout=events, stderr="")

        with patch("scripts.codex_baseline_agent.subprocess.run", side_effect=completed):
            submission, metadata = run_codex({}, "gpt-5.4-mini", "medium", 5)

        self.assertEqual(submission, {"findings": [], "verification": []})
        self.assertIsNone(metadata["model_label_verified"])
        self.assertEqual(metadata["model_identity_status"], "requested_only_unverified")
        self.assertEqual(metadata["item_error_count"], 1)
        self.assertFalse(metadata["stream_error"])

    def test_tool_events_are_deduplicated_and_fail_closed(self) -> None:
        events = _event_text(
            {"type": "thread.started", "thread_id": "thread"},
            {"type": "turn.started"},
            {"type": "item.started", "item": {"id": "tool-1", "type": "command_execution"}},
            {"type": "item.completed", "item": {"id": "tool-1", "type": "command_execution"}},
            {"type": "turn.completed", "usage": {}},
        )

        def completed(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            final_path = Path(command[command.index("--output-last-message") + 1])
            final_path.write_text(json.dumps({"findings": [], "verification": []}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout=events, stderr="")

        with patch("scripts.codex_baseline_agent.subprocess.run", side_effect=completed):
            submission, metadata = run_codex({}, "gpt-5.4-mini", "high", 5)

        self.assertIsNone(submission)
        self.assertEqual(metadata["codex_cli_returncode"], 0)
        self.assertEqual(metadata["returncode"], 3)
        self.assertEqual(metadata["tool_attempt_count"], 1)
        self.assertEqual(metadata["tool_attempt_types"], ["command_execution"])
        self.assertIn("disabled tool", metadata["parse_error"])

    def test_malformed_event_stream_fails_closed(self) -> None:
        with patch(
            "scripts.codex_baseline_agent.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout="not-json\n", stderr=""),
        ):
            submission, metadata = run_codex({}, "gpt-5.4-mini", "low", 5)

        self.assertIsNone(submission)
        self.assertEqual(metadata["returncode"], 3)
        self.assertEqual(metadata["tool_attempt_telemetry_status"], "unobserved")
        self.assertIn("incomplete", metadata["parse_error"])

    def test_event_stream_requires_ordered_single_lifecycle_and_final_terminal(self) -> None:
        valid = _parse_event_stream(
            _event_text(
                {"type": "thread.started", "thread_id": "thread"},
                {"type": "turn.started"},
                {"type": "item.completed", "item": {"id": "m1", "type": "agent_message"}},
                {"type": "turn.completed", "usage": {}},
            ),
            "gpt-5.4-mini",
        )
        post_terminal = _parse_event_stream(
            _event_text(
                {"type": "thread.started", "thread_id": "thread"},
                {"type": "turn.started"},
                {"type": "turn.completed", "usage": {}},
                {"type": "item.completed", "item": {"id": "m1", "type": "agent_message"}},
            ),
            "gpt-5.4-mini",
        )
        duplicate_start = _parse_event_stream(
            _event_text(
                {"type": "thread.started", "thread_id": "thread"},
                {"type": "turn.started"},
                {"type": "turn.started"},
                {"type": "turn.completed", "usage": {}},
            ),
            "gpt-5.4-mini",
        )
        pre_turn_item = _parse_event_stream(
            _event_text(
                {"type": "thread.started", "thread_id": "thread"},
                {
                    "type": "item.completed",
                    "item": {"id": "warning", "type": "error", "message": "CLI warning"},
                },
                {"type": "turn.started"},
                {"type": "item.completed", "item": {"id": "m1", "type": "agent_message"}},
                {"type": "turn.completed", "usage": {}},
            ),
            "gpt-5.4-mini",
        )

        self.assertTrue(valid["lifecycle_valid"])
        self.assertTrue(valid["event_stream_complete"])
        self.assertFalse(post_terminal["lifecycle_valid"])
        self.assertFalse(post_terminal["event_stream_complete"])
        self.assertIn("terminal turn event must be the final event", post_terminal["lifecycle_errors"])
        self.assertIn(
            "item events must occur between turn start and terminal",
            post_terminal["lifecycle_errors"],
        )
        self.assertFalse(duplicate_start["lifecycle_valid"])
        self.assertIn("expected exactly one turn.started event", duplicate_start["lifecycle_errors"])
        self.assertFalse(pre_turn_item["lifecycle_valid"])
        self.assertIn(
            "item events must occur between turn start and terminal",
            pre_turn_item["lifecycle_errors"],
        )

    def test_timeout_bytes_are_normalized_and_recorded(self) -> None:
        timeout = subprocess.TimeoutExpired(
            cmd=["codex"],
            timeout=5,
            output=b'{"type":"turn.started"}\n',
            stderr=b"timed out",
        )
        with patch("scripts.codex_baseline_agent.subprocess.run", side_effect=timeout):
            submission, metadata = run_codex({}, "gpt-5.4-mini", "low", 5)

        self.assertIsNone(submission)
        self.assertEqual(metadata["returncode"], 124)
        self.assertEqual(metadata["_stderr_text"], "timed out")
        json.dumps(metadata)

    def test_duplicate_boundary_fields_are_rejected(self) -> None:
        output = _structured_output()
        output["findings"][0]["boundary"].append({"field": "actor", "value": "other"})
        with self.assertRaisesRegex(ValueError, "duplicate boundary field"):
            _normalize_submission(output)

    def test_normalizer_rejects_extra_keys_invalid_methods_and_statuses(self) -> None:
        mutations = []

        extra_root = copy.deepcopy(_structured_output())
        extra_root["comment"] = "not allowed"
        mutations.append((extra_root, "model output must contain exactly"))

        extra_request = copy.deepcopy(_structured_output())
        extra_request["verification"][0]["request"]["headers"] = {}
        mutations.append((extra_request, "request must contain exactly"))

        invalid_method = copy.deepcopy(_structured_output())
        invalid_method["verification"][0]["request"]["method"] = "get"
        mutations.append((invalid_method, "request method"))

        invalid_path = copy.deepcopy(_structured_output())
        invalid_path["verification"][0]["request"]["path"] = "https://example.test/api/items"
        mutations.append((invalid_path, "request path"))

        extra_expected = copy.deepcopy(_structured_output())
        extra_expected["verification"][0]["expected"]["body"] = "ok"
        mutations.append((extra_expected, "verification expected must contain exactly"))

        for status in (99, 600, True):
            invalid_status = copy.deepcopy(_structured_output())
            invalid_status["verification"][0]["expected"]["status"] = status
            mutations.append((invalid_status, "from 100 through 599"))

        empty_claim = copy.deepcopy(_structured_output())
        empty_claim["findings"][0]["claim"] = "   "
        mutations.append((empty_claim, "non-empty strings"))

        for output, message in mutations:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                _normalize_submission(output)

    def test_run_level_credit_sentinel_skips_subsequent_remote_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            case_dir = run_dir / "case-one"
            case_dir.mkdir(parents=True)
            context_path = case_dir / "context.json"
            submission_path = case_dir / "submission.json"
            context_path.write_text("{}\n", encoding="utf-8")
            (run_dir / "codex-global-blocker.json").write_text(
                '{"code":"codex_workspace_out_of_credits"}\n',
                encoding="utf-8",
            )
            with (
                patch.dict(
                    os.environ,
                    {
                        "AUTHZBENCH_CONTEXT": str(context_path),
                        "AUTHZBENCH_SUBMISSION": str(submission_path),
                    },
                    clear=False,
                ),
                patch.object(sys, "argv", ["codex_baseline_agent.py"]),
                patch("scripts.codex_baseline_agent._codex_cli_version", return_value="codex-cli test"),
                patch("scripts.codex_baseline_agent.run_codex") as run_mock,
            ):
                code = main()

            metadata = json.loads((case_dir / "model-output.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 2)
        run_mock.assert_not_called()
        self.assertEqual(metadata["global_blocker"], "codex_workspace_out_of_credits")
        self.assertEqual(metadata["returncode"], 75)

    def test_credit_classifier_requires_exact_top_level_failure_event(self) -> None:
        for message in (CREDIT_BLOCKER_MESSAGE, CURRENT_CREDIT_BLOCKER_MESSAGE):
            with self.subTest(message=message):
                exact = _event_text(
                    {"type": "error", "message": message},
                    {"type": "turn.failed", "error": {"message": message}},
                )
                model_text = _event_text(
                    {"type": "thread.started"},
                    {"type": "turn.started"},
                    {
                        "type": "item.completed",
                        "item": {"id": "m1", "type": "agent_message", "text": message},
                    },
                    {"type": "turn.completed"},
                )

                self.assertEqual(
                    _global_blocker_code(exact, ""),
                    "codex_workspace_out_of_credits",
                )
                self.assertIsNone(_global_blocker_code(model_text, message))

    def test_writer_separates_raw_events_and_stderr_from_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            submission_path = Path(tmp) / "submission.json"
            code = _write_adapter_result(
                submission_path,
                None,
                {
                    "returncode": 1,
                    "parse_error": "codex command failed",
                    "_events_text": '{"type":"turn.failed"}\n',
                    "_stderr_text": "credit failure",
                },
            )
            metadata = json.loads((Path(tmp) / "model-output.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 2)
        self.assertNotIn("_events_text", metadata)
        self.assertNotIn("_stderr_text", metadata)
        self.assertFalse(submission_path.exists())


if __name__ == "__main__":
    unittest.main()
