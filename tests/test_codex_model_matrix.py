from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.codex_baseline_agent import PROFILE_SKILL_LOADING_STATUS, PROMPT_HASH_SCOPE
from scripts.run_codex_model_matrix import (
    DEFAULT_MATRIX,
    DEFAULT_ADMISSION_TASK,
    DEFAULT_FULL_TASK_PATTERN,
    EMPTY_DIFF_SHA256,
    EXPECTED_OUTPUT_SCHEMA_SHA256,
    _evaluator_command,
    _expected_cli_version,
    _expected_protocol_manifest,
    _expected_task_binding,
    _global_blocker,
    _matrix_exit_code,
    _require_codex_cli_version,
    _validated_admitted_configurations,
    admission_reasons,
    full_completion_reasons,
    load_matrix,
    run_matrix,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CLI_VERSION = _expected_cli_version(DEFAULT_MATRIX)


def _task_row(
    config: dict[str, str],
    index: int,
    task_id: str,
    task_path: str,
) -> dict[str, object]:
    return {
        "task_id": task_id,
        "task_path": task_path,
        "adapter_requested_model": config["model"],
        "adapter_requested_effort": config["effort"],
        "adapter_cli_version": EXPECTED_CLI_VERSION,
        "adapter_output_format": "structured_json",
        "adapter_json_only_compliant": True,
        "adapter_prompt_sha256": f"{index:064x}",
        "adapter_prompt_hash_scope": PROMPT_HASH_SCOPE,
        "adapter_profile_skill_loading_status": PROFILE_SKILL_LOADING_STATUS,
        "adapter_output_schema_sha256": EXPECTED_OUTPUT_SCHEMA_SHA256,
        "adapter_tool_attempt_telemetry_status": "complete",
        "adapter_tool_attempt_count": 0,
    }


def _summary(
    config: dict[str, str],
    *,
    task_count: int = 1,
    benchmark_commit_sha: str = "a" * 40,
) -> dict[str, object]:
    task_pattern = DEFAULT_ADMISSION_TASK if task_count == 1 else DEFAULT_FULL_TASK_PATTERN
    binding = _expected_task_binding(task_pattern)
    identities = binding["identities"]
    if len(identities) != task_count:
        raise ValueError("test summary task count does not match expected binding")
    return {
        "task_count": task_count,
        "adapter_failure_count": 0,
        "infrastructure_failure_count": 0,
        "invalid_submission_count": 0,
        "model_tool_attempt_telemetry_status": "complete",
        "model_tool_attempt_total": 0,
        "model_identity_status": "requested_only_unverified",
        "benchmark_commit_sha": benchmark_commit_sha,
        "benchmark_source_provenance": {
            "git_commit_sha": benchmark_commit_sha,
            "tracked_worktree_dirty": False,
            "tracked_diff_sha256": EMPTY_DIFF_SHA256,
        },
        "benchmark_fingerprint": binding["fingerprint"],
        "evaluation_protocol": _expected_protocol_manifest(DEFAULT_MATRIX),
        "tasks": [
            _task_row(config, index, task_id, task_path)
            for index, (task_id, task_path) in enumerate(identities)
        ],
    }


class CodexModelMatrixTests(unittest.TestCase):
    def test_matrix_exit_codes_distinguish_complete_incomplete_and_global_blocker(self) -> None:
        self.assertEqual(_matrix_exit_code({"phase_status": "completed"}), 0)
        self.assertEqual(_matrix_exit_code({"phase_status": "incomplete"}), 1)
        self.assertEqual(
            _matrix_exit_code(
                {
                    "phase_status": "blocked",
                    "global_blocker": "codex_workspace_out_of_credits",
                }
            ),
            2,
        )

    def test_public_matrix_has_27_unique_supported_non_delegating_configurations(self) -> None:
        configurations = load_matrix(DEFAULT_MATRIX)
        matrix = json.loads(DEFAULT_MATRIX.read_text(encoding="utf-8"))
        pairs = {(item["model"], item["effort"]) for item in configurations}

        self.assertEqual(len(configurations), 27)
        self.assertEqual(len(pairs), 27)
        self.assertNotIn(("gpt-5.6-sol", "ultra"), pairs)
        self.assertNotIn(("gpt-5.6-terra", "ultra"), pairs)
        self.assertNotIn(("gpt-5.4-mini", "none"), pairs)
        self.assertEqual(
            configurations[0],
            {"id": "gpt-5-4-mini-low", "model": "gpt-5.4-mini", "effort": "low"},
        )
        catalog_path = ROOT / matrix["normalized_catalog_artifact"]
        self.assertEqual(
            hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
            matrix["normalized_catalog_sha256"],
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        derived_pairs = {
            (model["slug"], row["effort"])
            for model in catalog["models"]
            if model["included_in_benchmark"]
            for row in model["reasoning_efforts"]
            if not row["automatic_delegation"]
        }
        self.assertEqual(derived_pairs, pairs)
        self.assertEqual(catalog["selected_non_delegating_configuration_count"], 27)

    def test_admission_requires_complete_zero_tool_structured_provenance(self) -> None:
        config = {"id": "gpt-5-4-mini-low", "model": "gpt-5.4-mini", "effort": "low"}
        summary = _summary(config)

        self.assertEqual(admission_reasons(summary, config), [])
        summary["model_tool_attempt_total"] = 1
        summary["tasks"][0]["adapter_output_format"] = "embedded_json"
        reasons = admission_reasons(summary, config)
        self.assertIn("model tool-attempt total must be zero", reasons)
        self.assertIn("adapter output is not structured_json", reasons)

    def test_admission_rejects_stale_schema_and_protocol_source_bindings(self) -> None:
        config = {"id": "gpt-5-4-mini-low", "model": "gpt-5.4-mini", "effort": "low"}
        summary = _summary(config)
        summary["tasks"][0]["adapter_output_schema_sha256"] = "0" * 64
        summary["evaluation_protocol"]["source_sha256"]["agent_source_1"] = "0" * 64

        reasons = admission_reasons(summary, config)

        self.assertIn("adapter output-schema hash does not match the current schema", reasons)
        self.assertIn("evaluation protocol source hashes do not match current sources", reasons)
        self.assertIn("evaluation protocol source-set hash is internally invalid", reasons)
        self.assertIn("evaluation protocol manifest hash is internally invalid", reasons)

    def test_admission_binds_exact_task_fingerprint_provenance_and_cli(self) -> None:
        config = {"id": "gpt-5-4-mini-low", "model": "gpt-5.4-mini", "effort": "low"}
        summary = _summary(config)
        summary["tasks"][0]["task_id"] = "wrong-smoke-task"
        summary["benchmark_fingerprint"] = {"forged": True}
        summary["benchmark_source_provenance"]["git_commit_sha"] = "b" * 40
        summary["benchmark_source_provenance"]["tracked_diff_sha256"] = "c" * 64
        summary["tasks"][0]["adapter_cli_version"] = "codex-cli 999.0-unrelated"

        reasons = admission_reasons(summary, config)

        self.assertIn("task ids and paths do not match the exact current task set", reasons)
        self.assertIn("benchmark fingerprint does not match the exact current task set", reasons)
        self.assertIn("benchmark source provenance commit does not match", reasons)
        self.assertIn("benchmark source provenance tracked diff is not empty", reasons)
        self.assertIn("adapter CLI version does not match the matrix", reasons)

    def test_global_credit_blocker_is_detected_from_raw_event_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            case_dir = run_dir / "case-123"
            case_dir.mkdir()
            (case_dir / "codex-events.jsonl").write_text(
                '{"type":"error","message":"Your workspace is out of credits. Ask your workspace owner to refill in order to continue."}\n',
                encoding="utf-8",
            )

            blocker = _global_blocker(run_dir)

        self.assertEqual(blocker, "codex_workspace_out_of_credits")

    def test_global_credit_blocker_is_not_spoofed_by_model_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            case_dir = run_dir / "case-123"
            case_dir.mkdir()
            (case_dir / "codex-events.jsonl").write_text(
                "\n".join(
                    [
                        '{"type":"thread.started"}',
                        '{"type":"turn.started"}',
                        '{"type":"item.completed","item":{"id":"m1","type":"agent_message","text":"Your workspace is out of credits. Ask your workspace owner to refill in order to continue."}}',
                        '{"type":"turn.completed"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            blocker = _global_blocker(run_dir)

        self.assertIsNone(blocker)

    def test_full_completion_requires_63_complete_unique_prompt_rows(self) -> None:
        config = {"id": "gpt-5-4-mini-low", "model": "gpt-5.4-mini", "effort": "low"}
        summary = _summary(config, task_count=63)

        self.assertEqual(full_completion_reasons(summary, config), [])
        summary["adapter_failure_count"] = 2
        summary["invalid_submission_count"] = 2
        self.assertEqual(
            full_completion_reasons(summary, config),
            [],
            "model parse/invalid failures remain scored results when infrastructure completed",
        )
        summary["infrastructure_failure_count"] = 1
        summary["tasks"][1]["adapter_prompt_sha256"] = summary["tasks"][0]["adapter_prompt_sha256"]
        reasons = full_completion_reasons(summary, config)
        self.assertIn("infrastructure_failure_count must be zero", reasons)
        self.assertIn("full run must preserve 63 unique prompt hashes", reasons)

    def test_full_completion_binds_all_task_identities_fingerprint_and_cli(self) -> None:
        config = {"id": "gpt-5-4-mini-low", "model": "gpt-5.4-mini", "effort": "low"}
        summary = _summary(config, task_count=63)
        summary["benchmark_fingerprint"] = {"forged": True}
        for task in summary["tasks"]:
            task.pop("task_id")
            task.pop("task_path")
        summary["tasks"][0]["adapter_cli_version"] = "codex-cli 999.0-unrelated"

        reasons = full_completion_reasons(summary, config)

        self.assertIn("task ids and paths do not match the exact current task set", reasons)
        self.assertIn("benchmark fingerprint does not match the exact current task set", reasons)
        self.assertIn("full run adapter CLI version does not match the matrix", reasons)

    def test_codex_cli_version_preflight_requires_exact_matrix_version(self) -> None:
        with patch(
            "scripts.run_codex_model_matrix.subprocess.run",
            return_value=subprocess.CompletedProcess(
                ["codex", "--version"],
                0,
                stdout=EXPECTED_CLI_VERSION + "\n",
                stderr="",
            ),
        ):
            self.assertEqual(
                _require_codex_cli_version(Path("/tmp/codex"), DEFAULT_MATRIX),
                EXPECTED_CLI_VERSION,
            )
        with patch(
            "scripts.run_codex_model_matrix.subprocess.run",
            return_value=subprocess.CompletedProcess(
                ["codex", "--version"],
                0,
                stdout="codex-cli 999.0-unrelated\n",
                stderr="",
            ),
        ):
            with self.assertRaisesRegex(ValueError, "does not match matrix"):
                _require_codex_cli_version(Path("/tmp/codex"), DEFAULT_MATRIX)

    def test_full_admission_revalidates_exact_complete_matrix_and_each_summary(self) -> None:
        configurations = load_matrix(DEFAULT_MATRIX)
        commit = "b" * 40
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            rows = []
            for config in configurations:
                summary_path = tmp_path / f"{config['id']}.json"
                summary_path.write_text(
                    json.dumps(_summary(config, benchmark_commit_sha=commit)),
                    encoding="utf-8",
                )
                rows.append(
                    {
                        **config,
                        "status": "admitted",
                        "evaluator_returncode": 0,
                        "summary_path": summary_path.relative_to(ROOT).as_posix(),
                    }
                )
            report = {
                "phase": "smoke",
                "benchmark_commit_sha": commit,
                "matrix_path": DEFAULT_MATRIX.relative_to(ROOT).as_posix(),
                "matrix_sha256": hashlib.sha256(DEFAULT_MATRIX.read_bytes()).hexdigest(),
                "codex_cli_version": EXPECTED_CLI_VERSION,
                "global_blocker": None,
                "requested_configuration_count": len(configurations),
                "attempted_configuration_count": len(configurations),
                "configurations": rows,
            }

            admitted = _validated_admitted_configurations(
                report,
                configurations,
                benchmark_commit_sha=commit,
                matrix_path=DEFAULT_MATRIX,
            )
            self.assertEqual(admitted, configurations)

            incomplete = report | {"configurations": rows[:-1]}
            with self.assertRaisesRegex(ValueError, "every matrix configuration"):
                _validated_admitted_configurations(
                    incomplete,
                    configurations,
                    benchmark_commit_sha=commit,
                    matrix_path=DEFAULT_MATRIX,
                )

            forged_rows = [dict(row) for row in rows]
            forged_rows[0]["model"] = "forged-model"
            forged = report | {"configurations": forged_rows}
            with self.assertRaisesRegex(ValueError, "model/effort"):
                _validated_admitted_configurations(
                    forged,
                    configurations,
                    benchmark_commit_sha=commit,
                    matrix_path=DEFAULT_MATRIX,
                )

    def test_matrix_refuses_stale_report_and_run_directories(self) -> None:
        config = {"id": "gpt-5-4-mini-low", "model": "gpt-5.4-mini", "effort": "low"}
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            report_path = results_dir / "codex-matrix-smoke-stale.json"
            report_path.write_text("{}\n", encoding="utf-8")
            with patch(
                "scripts.run_codex_model_matrix._require_clean_worktree",
                return_value="a" * 40,
            ):
                with self.assertRaisesRegex(ValueError, "existing matrix report"):
                    run_matrix(
                        [config],
                        phase="smoke",
                        run_label="stale",
                        results_dir=results_dir,
                        codex_path=Path(__file__),
                        model_timeout_seconds=10,
                        matrix_path=DEFAULT_MATRIX,
                    )

        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)
            (results_dir / "codex-gpt-5-4-mini-low-smoke-stale").mkdir()
            with (
                patch(
                    "scripts.run_codex_model_matrix._require_clean_worktree",
                    return_value="a" * 40,
                ),
                patch("scripts.run_codex_model_matrix.subprocess.run") as run_mock,
                patch(
                    "scripts.run_codex_model_matrix._require_codex_cli_version",
                    return_value=EXPECTED_CLI_VERSION,
                ),
            ):
                with self.assertRaisesRegex(ValueError, "existing matrix run directory"):
                    run_matrix(
                        [config],
                        phase="smoke",
                        run_label="stale",
                        results_dir=results_dir,
                        codex_path=Path(__file__),
                        model_timeout_seconds=10,
                        matrix_path=DEFAULT_MATRIX,
                    )
            run_mock.assert_not_called()

    def test_limited_smoke_is_explicitly_diagnostic_partial(self) -> None:
        configurations = load_matrix(DEFAULT_MATRIX)[:2]
        commit = "a" * 40
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)

            def completed(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
                run_id = command[command.index("--run-id") + 1]
                run_dir = results_dir / run_id
                run_dir.mkdir(parents=True)
                (run_dir / "summary.json").write_text(
                    json.dumps(_summary(configurations[0], benchmark_commit_sha=commit)),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with (
                patch(
                    "scripts.run_codex_model_matrix._require_clean_worktree",
                    return_value=commit,
                ),
                patch("scripts.run_codex_model_matrix.subprocess.run", side_effect=completed),
                patch(
                    "scripts.run_codex_model_matrix._require_codex_cli_version",
                    return_value=EXPECTED_CLI_VERSION,
                ),
            ):
                report = run_matrix(
                    configurations,
                    phase="smoke",
                    run_label="limited",
                    results_dir=results_dir,
                    codex_path=Path(__file__),
                    model_timeout_seconds=10,
                    matrix_path=DEFAULT_MATRIX,
                    max_configurations=1,
                )

        self.assertEqual(report["matrix_configuration_count"], 2)
        self.assertEqual(report["requested_configuration_count"], 2)
        self.assertEqual(report["selected_configuration_count"], 1)
        self.assertEqual(report["attempted_configuration_count"], 1)
        self.assertEqual(report["phase_status"], "diagnostic_partial")

    def test_matrix_stops_after_first_global_credit_blocker(self) -> None:
        configurations = load_matrix(DEFAULT_MATRIX)[:2]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            results_dir = Path(tmp)

            def blocked(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
                run_id = command[command.index("--run-id") + 1]
                run_dir = results_dir / run_id
                run_dir.mkdir(parents=True)
                (run_dir / "codex-global-blocker.json").write_text(
                    '{"code":"codex_workspace_out_of_credits"}\n',
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command, 2, stdout="", stderr="")

            with (
                patch(
                    "scripts.run_codex_model_matrix._require_clean_worktree",
                    return_value="a" * 40,
                ),
                patch("scripts.run_codex_model_matrix.subprocess.run", side_effect=blocked) as run_mock,
                patch(
                    "scripts.run_codex_model_matrix._require_codex_cli_version",
                    return_value=EXPECTED_CLI_VERSION,
                ),
            ):
                report = run_matrix(
                    configurations,
                    phase="smoke",
                    run_label="blocked",
                    results_dir=results_dir,
                    codex_path=Path(__file__),
                    model_timeout_seconds=10,
                    matrix_path=DEFAULT_MATRIX,
                )

        self.assertEqual(run_mock.call_count, 1)
        self.assertEqual(report["phase_status"], "blocked")
        self.assertEqual(report["attempted_configuration_count"], 1)
        self.assertEqual(report["global_blocker"], "codex_workspace_out_of_credits")

    def test_public_credit_blocker_artifact_contract(self) -> None:
        matrix = json.loads(DEFAULT_MATRIX.read_text(encoding="utf-8"))
        artifact_rel = matrix["current_blocker"]["evidence_artifact"]
        blocker = json.loads((ROOT / artifact_rel).read_text(encoding="utf-8"))

        self.assertEqual(artifact_rel, "artifact/openai-codex-credit-blocker-2026-07-12.json")
        self.assertFalse(blocker["comparison_eligible"])
        self.assertTrue(blocker["source_binding"]["tracked_worktree_dirty"])
        self.assertEqual(
            blocker["requested_configuration"]["model_identity_status"],
            "requested_only_unverified",
        )
        self.assertEqual(blocker["execution"]["event_count"], 5)
        self.assertEqual(
            blocker["execution"]["event_type_sequence"],
            ["thread.started", "turn.started", "item.completed:error", "error", "turn.failed"],
        )
        self.assertEqual(blocker["execution"]["tool_attempt_count"], 0)
        self.assertFalse(blocker["blocker"]["model_inference_completed"])
        self.assertEqual(
            blocker["content_hashes"],
            {
                "events_sha256": "131c1839cf0e73fe846d449499ceba3e844c37da27c9d73e5a0d8cc41acad1cb",
                "stderr_sha256": "b7318ce49e5f6b0864b732a48fdb2a58833df687a3f87d1e9282d071e9d89364",
                "prompt_sha256": "651ebdbd8374b4c7e268bbf9dc268f69cec9aee2e75d776080105b8308226ad2",
                "output_schema_sha256": "cfdbba230d14a6b1dee02bca45798e99ed1bdfb2a75af9454a5bf5565c6c9ea1",
            },
        )

    def test_evaluator_command_hashes_adapter_runner_and_matrix_sources(self) -> None:
        config = {"id": "gpt-5-4-mini-low", "model": "gpt-5.4-mini", "effort": "low"}
        command, run_id = _evaluator_command(
            config,
            phase="smoke",
            run_label="test",
            task_pattern="tasks/example.json",
            results_dir=Path("results/test"),
            codex_path=Path("/usr/local/bin/codex"),
            model_timeout_seconds=60,
            matrix_path=DEFAULT_MATRIX,
        )

        self.assertEqual(run_id, "codex-gpt-5-4-mini-low-smoke-test")
        self.assertEqual(command.count("--agent-source"), 4)
        agent_command = command[command.index("--agent-cmd") + 1]
        self.assertIn("--model gpt-5.4-mini", agent_command)
        self.assertIn("--effort low", agent_command)
        self.assertIn("--codex-path /usr/local/bin/codex", agent_command)


if __name__ == "__main__":
    unittest.main()
