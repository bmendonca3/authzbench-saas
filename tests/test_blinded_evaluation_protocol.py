from __future__ import annotations

import json
import shlex
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from authzbench.core import build_context, load_json, replay_request
from authzbench.evaluate import (
    _evaluate_control_verification,
    _exit_code,
    _protocol_manifest,
    _protocol_source_paths,
    _summarize_model_tool_attempt_telemetry,
    _verified_benchmark_commit_sha,
    _wilson_interval,
    run_evaluation,
)
from authzbench.score import score_submission


ROOT = Path(__file__).resolve().parents[1]


class BlindedEvaluationProtocolTests(unittest.TestCase):
    def test_legacy_context_shape_remains_unchanged(self) -> None:
        task = load_json(
            ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"
        )
        context = build_context(task)

        self.assertEqual(
            set(context),
            {
                "task_id",
                "app",
                "seed",
                "policy",
                "objective",
                "allowed_hosts",
                "target",
                "actors",
                "refs",
                "api_docs",
                "output_schema",
            },
        )
        self.assertEqual(context["task_id"], task["id"])
        self.assertEqual(context["seed"], task["seed"])
        self.assertEqual(context["target"]["seed"], task["seed"])
        self.assertNotIn("case_id", context)
        self.assertNotIn("context_profile", context)

    def test_completed_evaluation_exit_is_separate_from_model_performance(self) -> None:
        summary = {
            "task_count": 63,
            "passed_count": 35,
            "infrastructure_failure_count": 0,
        }
        self.assertEqual(_exit_code(summary), 0)
        self.assertEqual(_exit_code(summary, require_all_pass=True), 1)
        self.assertEqual(_exit_code(summary | {"infrastructure_failure_count": 1}), 2)

    def test_wilson_interval_is_bounded_and_explicit(self) -> None:
        interval = _wilson_interval(27, 27)
        self.assertIsNotNone(interval)
        assert interval is not None
        self.assertEqual(interval["method"], "wilson")
        self.assertEqual(interval["confidence_level"], 0.95)
        self.assertGreaterEqual(interval["lower"], 0)
        self.assertLessEqual(interval["upper"], 1)
        self.assertIsNone(_wilson_interval(0, 0))

    def test_model_tool_attempt_totals_require_complete_per_task_telemetry(self) -> None:
        complete = _summarize_model_tool_attempt_telemetry(
            [
                {
                    "adapter_tool_attempt_telemetry_status": "complete",
                    "adapter_tool_attempt_count": 0,
                    "adapter_tool_attempt_types": [],
                },
                {
                    "adapter_tool_attempt_telemetry_status": "complete",
                    "adapter_tool_attempt_count": 1,
                    "adapter_tool_attempt_types": ["command_execution"],
                },
            ]
        )
        partial = _summarize_model_tool_attempt_telemetry(
            [
                {
                    "adapter_tool_attempt_telemetry_status": "complete",
                    "adapter_tool_attempt_count": 0,
                },
                {"adapter_tool_attempt_telemetry_status": "unobserved"},
            ]
        )

        self.assertEqual(complete["model_tool_attempt_telemetry_status"], "complete")
        self.assertEqual(complete["model_tool_attempt_total"], 1)
        self.assertEqual(
            complete["model_tool_attempt_type_counts"],
            {"command_execution": 1},
        )
        self.assertEqual(partial["model_tool_attempt_telemetry_status"], "partial")
        self.assertIsNone(partial["model_tool_attempt_total"])

    def test_protocol_manifest_hashes_explicit_agent_and_all_replay_apps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent_source = Path(tmp) / "custom_adapter.py"
            agent_source.write_text("print('first')\n", encoding="utf-8")
            first = _protocol_manifest(_protocol_source_paths([agent_source]))
            agent_source.write_text("print('second')\n", encoding="utf-8")
            second = _protocol_manifest(_protocol_source_paths([agent_source]))

        self.assertIn("agent_source_1", first["source_sha256"])
        self.assertIn("app:apps/project_mgmt/app.py", first["source_sha256"])
        self.assertIn("app:apps/request_logging.py", first["source_sha256"])
        self.assertNotIn("kiro_adapter", first["source_sha256"])
        self.assertNotEqual(first["source_set_sha256"], second["source_set_sha256"])
        with self.assertRaisesRegex(ValueError, "agent source path"):
            _protocol_source_paths([])

    def test_evaluation_commit_label_must_match_observed_head(self) -> None:
        git_provenance = {"git_commit_sha": "a" * 40}

        self.assertEqual(
            _verified_benchmark_commit_sha(git_provenance, "a" * 40),
            "a" * 40,
        )
        with self.assertRaisesRegex(ValueError, "exactly match"):
            _verified_benchmark_commit_sha(git_provenance, "b" * 40)
        with self.assertRaisesRegex(ValueError, "unable to resolve Git HEAD"):
            _verified_benchmark_commit_sha({}, None)

    def test_blinded_context_removes_authored_outcome_and_canonical_id(self) -> None:
        vulnerable = load_json(
            ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"
        )
        secure = load_json(
            ROOT / "tasks/project_mgmt/pm_secure_cross_tenant_read_control.json"
        )
        vulnerable_context = build_context(
            vulnerable,
            participant_task_id="case-vulnerable",
            profile="blinded-evaluation-v1",
        )
        secure_context = build_context(
            secure,
            participant_task_id="case-secure",
            profile="blinded-evaluation-v1",
        )

        rendered = json.dumps(vulnerable_context, sort_keys=True)
        self.assertNotIn(vulnerable["id"], rendered)
        self.assertNotIn(vulnerable["objective"], rendered)
        self.assertNotIn(vulnerable["policy"], rendered)
        self.assertNotIn("expected_vulnerable", rendered)
        self.assertNotIn('"oracle"', rendered)
        self.assertEqual(vulnerable_context["task_id"], "case-vulnerable")
        self.assertEqual(vulnerable_context["context_profile"], "blinded-evaluation-v1")
        self.assertTrue(vulnerable_context["candidate_requests"])
        for request in vulnerable_context["candidate_requests"]:
            self.assertNotIn("status", request)
            self.assertNotIn("body_contains", request)
        self.assertEqual(vulnerable_context["objective"], secure_context["objective"])
        self.assertEqual(vulnerable_context["output_schema"], secure_context["output_schema"])
        self.assertIn('verification: [{"request": {...}, "expected": {"status": <integer>}}]', vulnerable_context["output_schema"])
        self.assertIn("selected from candidate_requests", vulnerable_context["output_schema"])
        self.assertEqual(vulnerable_context["policy"], secure_context["policy"])

    def test_blinded_context_withholds_raw_seed_without_breaking_host_replay(self) -> None:
        task = load_json(
            ROOT / "tasks/project_mgmt/pm_secure_cross_tenant_read_control.json"
        )
        raw_seed = task["seed"]
        context = build_context(
            task,
            participant_task_id="case-seed-canary",
            profile="blinded-evaluation-v1",
        )

        self.assertNotIn("seed", context)
        self.assertNotIn("seed", context["target"])
        self.assertNotIn(raw_seed, json.dumps(context, sort_keys=True))

        request = context["candidate_requests"][0]
        response = replay_request(task, request)
        self.assertEqual(response["status"], 403, response)
        self.assertEqual(response["body"], {"error": "forbidden"}, response)

    def test_runner_uses_opaque_case_id_and_isolated_task_workdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            agent_path = tmp_path / "control_agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    context = json.loads(Path(os.environ["AUTHZBENCH_CONTEXT"]).read_text())
                    submission = {
                        "findings": [],
                        "verification": [
                            {
                                "request": context["candidate_requests"][0],
                                "expected": {"status": 403},
                            }
                        ],
                    }
                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(json.dumps(submission))
                    (Path(os.environ["AUTHZBENCH_SUBMISSION"]).parent / "model-output.json").write_text(json.dumps({
                        "returncode": 0,
                        "model_label_verified": None,
                        "model_identity_status": "requested_only_unverified",
                        "prompt_sha256": "0" * 64,
                        "prompt_hash_scope": "host_supplied_user_prompt_only",
                        "profile_skill_loading_status": "not_disabled_by_current_codex_cli_surface",
                        "output_schema_sha256": "1" * 64,
                        "tool_attempt_telemetry_status": "complete",
                        "tool_attempt_count": 0,
                        "tool_attempt_types": [],
                    }))
                    print(json.dumps({
                        "cwd": os.getcwd(),
                        "context_path": os.environ["AUTHZBENCH_CONTEXT"],
                        "submission_path": os.environ["AUTHZBENCH_SUBMISSION"],
                        "env_task_id": os.environ["AUTHZBENCH_TASK_ID"],
                        "context_task_id": context["task_id"],
                    }))
                    """
                ),
                encoding="utf-8",
            )
            summary = run_evaluation(
                [str(ROOT / "tasks/project_mgmt/pm_secure_cross_tenant_read_control.json")],
                f"{shlex.quote(sys.executable)} {shlex.quote(str(agent_path))}",
                tmp_path / "results",
                timeout_seconds=10,
                run_id="blinded-unit-run",
                agent_source_paths=[agent_path],
            )
            participant_case_id = summary["tasks"][0]["participant_case_id"]
            task_dir = Path(summary["run_dir"]) / participant_case_id
            agent = json.loads((task_dir / "agent.json").read_text(encoding="utf-8"))
            emitted = json.loads(agent["stdout"])
            stored_context = json.loads((task_dir / "context.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["passed_count"], 1, summary)
        self.assertEqual(summary["control_verification_required_count"], 1, summary)
        self.assertEqual(summary["control_verification_passed_count"], 1, summary)
        self.assertEqual(summary["model_identity_status"], "requested_only_unverified")
        self.assertEqual(summary["model_label_verified_task_count"], 0)
        self.assertEqual(
            summary["tasks"][0]["adapter_prompt_hash_scope"],
            "host_supplied_user_prompt_only",
        )
        self.assertEqual(
            summary["tasks"][0]["adapter_profile_skill_loading_status"],
            "not_disabled_by_current_codex_cli_surface",
        )
        self.assertEqual(Path(emitted["cwd"]).resolve(), task_dir.resolve())
        self.assertEqual(emitted["env_task_id"], emitted["context_task_id"])
        self.assertRegex(emitted["env_task_id"], r"^case-[0-9a-f]{16}$")
        self.assertNotEqual(
            emitted["env_task_id"],
            "pm_secure_cross_tenant_read_control",
        )
        participant_paths = "\n".join(
            [emitted["cwd"], emitted["context_path"], emitted["submission_path"]]
        )
        self.assertNotIn("pm_secure_cross_tenant_read_control", participant_paths)
        self.assertIn(participant_case_id, participant_paths)
        self.assertEqual(
            stored_context["candidate_observations"][0]["request"],
            stored_context["candidate_requests"][0],
        )
        self.assertNotIn("seed", stored_context)
        self.assertNotIn("seed", stored_context["target"])
        self.assertNotIn(
            "public-v0-004",
            json.dumps(stored_context, sort_keys=True),
        )
        self.assertEqual(
            stored_context["candidate_observations"][0]["response"]["status"],
            403,
        )
        protocol = summary["evaluation_protocol"]
        self.assertEqual(protocol["participant_context_profile"], "blinded-evaluation-v1")
        self.assertEqual(protocol["participant_task_id_mode"], "opaque-per-run")
        self.assertEqual(
            protocol["agent_workdir_mode"],
            "isolated-per-task-artifact-directory",
        )
        self.assertRegex(protocol["manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(protocol["source_set_sha256"], r"^[0-9a-f]{64}$")

    def test_empty_only_agent_does_not_receive_verified_control_credit(self) -> None:
        secure = load_json(
            ROOT / "tasks/project_mgmt/pm_secure_cross_tenant_read_control.json"
        )
        submission = {"findings": []}
        legacy_score = score_submission(secure, submission)
        self.assertTrue(legacy_score["passed"], legacy_score)

        protocol_score = _evaluate_control_verification(
            secure,
            submission,
            legacy_score,
        )
        self.assertFalse(protocol_score["passed"], protocol_score)
        self.assertTrue(protocol_score["control_replay_passed"], protocol_score)
        self.assertTrue(protocol_score["control_verification_required"], protocol_score)
        self.assertFalse(protocol_score["control_verification_present"], protocol_score)
        self.assertFalse(protocol_score["control_verification_passed"], protocol_score)

    def test_unmatched_control_verification_is_rejected_before_replay(self) -> None:
        secure = load_json(
            ROOT / "tasks/project_mgmt/pm_secure_cross_tenant_read_control.json"
        )
        submission = {
            "findings": [],
            "verification": [
                {
                    "request": {
                        "actor": "alpha_owner",
                        "method": "PATCH",
                        "path": "/api/projects/not-a-declared-control",
                        "body": {"name": "unexpected"},
                    },
                    "expected": {"status": 200},
                }
            ],
        }
        legacy_score = score_submission(secure, submission)

        with patch("authzbench.evaluate.replay_request") as replay:
            protocol_score = _evaluate_control_verification(
                secure,
                submission,
                legacy_score,
            )

        replay.assert_not_called()
        self.assertFalse(protocol_score["passed"], protocol_score)
        self.assertTrue(protocol_score["control_verification_present"], protocol_score)
        self.assertFalse(protocol_score["control_verification_passed"], protocol_score)
        self.assertIn(
            "did not match a declared control",
            "\n".join(str(item) for item in protocol_score["observations"]),
        )

    def test_control_verification_requires_correct_predicted_status(self) -> None:
        secure = load_json(
            ROOT / "tasks/project_mgmt/pm_secure_cross_tenant_read_control.json"
        )
        context = build_context(
            secure,
            participant_task_id="case-control",
            profile="blinded-evaluation-v1",
        )
        submission = {
            "findings": [],
            "verification": [
                {
                    "request": context["candidate_requests"][0],
                    "expected": {"status": 200},
                }
            ],
        }
        legacy_score = score_submission(secure, submission)
        protocol_score = _evaluate_control_verification(
            secure,
            submission,
            legacy_score,
        )

        self.assertFalse(protocol_score["passed"], protocol_score)
        self.assertFalse(protocol_score["control_verification_passed"], protocol_score)
        self.assertIn(
            "did not match replayed status",
            "\n".join(str(item) for item in protocol_score["observations"]),
        )


if __name__ == "__main__":
    unittest.main()
