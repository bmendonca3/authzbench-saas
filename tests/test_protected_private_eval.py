from __future__ import annotations

import json
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from authzbench.core import load_json
from scripts.protected_private_eval import (
    ROOT,
    _loaded_pack_fingerprint,
    redacted_summary,
    run_protected_private_eval,
)


class ProtectedPrivateEvalTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("sandbox-exec"), "requires macOS sandbox-exec")
    def test_agent_cannot_read_private_holdout_root_from_host(self) -> None:
        private_root = ROOT / "tasks_private" / "holdout"
        private_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=private_root, suffix=".json") as private_fixture:
            private_path = Path(private_fixture.name)
            private_path.write_text('{"private": true}', encoding="utf-8")
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                task = load_json(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")
                task["id"] = "private_test_host_denial"
                task["split"] = "private_holdout"
                task_path = tmp_path / "holdout.json"
                task_path.write_text(json.dumps(task), encoding="utf-8")
                agent_path = tmp_path / "agent.py"
                agent_path.write_text(
                    textwrap.dedent(
                        f"""
                        import json
                        import os
                        from pathlib import Path

                        denied = Path({str(private_path)!r})
                        try:
                            denied.read_text()
                        except PermissionError:
                            pass
                        else:
                            raise AssertionError("private holdout was readable")
                        Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                            json.dumps({{"findings": []}})
                        )
                        """
                    ).strip()
                    + "\n",
                    encoding="utf-8",
                )

                summary = run_protected_private_eval(
                    [str(task_path)],
                    agent_cmd=f"python3 {agent_path}",
                    results_dir=tmp_path / "results",
                    timeout_seconds=10,
                    benchmark_version="test",
                    benchmark_commit_sha=None,
                    agent="dummy-agent",
                    model="dummy-model",
                    harness_type="no-tools-model",
                    run_id="host-denial-run",
                )

        self.assertEqual(summary["tasks"][0]["agent_returncode"], 0, summary)
        self.assertTrue(summary["protected_execution"]["host_private_paths_denied"], summary)
        self.assertEqual(summary["protected_execution"]["isolation_backend"], "macos-sandbox-exec", summary)

    def test_agent_receives_rendered_context_from_empty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")
            task["id"] = "private_test_same_tenant_read_control"
            task["split"] = "private_holdout"
            task["holdout_variant"] = {"route_variant": "test", "decoy_variant": "test"}
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")

            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    cwd_entries = [path.name for path in Path.cwd().iterdir()]
                    assert cwd_entries == [], cwd_entries
                    assert not (Path.cwd() / "tasks_private").exists()
                    context = json.loads(Path(os.environ["AUTHZBENCH_CONTEXT"]).read_text())
                    assert "oracle" not in context
                    assert "controls" not in context
                    assert "holdout_variant" not in context
                    assert context["task_id"] == "private_test_same_tenant_read_control"
                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps({"findings": []})
                    )
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="dummy-agent",
                model="dummy-model",
                harness_type="no-tools-model",
                run_id="test-run",
            )

        self.assertEqual(summary["task_count"], 1, summary)
        self.assertEqual(summary["passed_count"], 1, summary)
        self.assertEqual(summary["scored_submission_finding_total"], 0, summary)
        self.assertIsNone(summary["submitted_finding_total"], summary)
        self.assertEqual(summary["tool_probe_telemetry_status"], "unobserved", summary)
        self.assertEqual(summary["benchmark_fingerprint"]["task_count"], 1, summary)
        self.assertEqual(
            summary["benchmark_fingerprint"]["schema_version"],
            "benchmark-fingerprint-v2",
            summary,
        )
        self.assertRegex(
            summary["benchmark_fingerprint"]["source_set_sha256"],
            r"^[0-9a-f]{64}$",
        )
        self.assertEqual(summary["promotion_eligible_count"], 0, summary)
        self.assertEqual(summary["safety_observation_coverage_rate"], 0.0, summary)
        self.assertFalse(summary["protected_execution"]["private_manifests_readable_in_agent_workspace"], summary)
        self.assertEqual(summary["protected_execution"]["agent_received"], "rendered-context-only", summary)

    def test_protected_eval_correlates_target_logs_without_exposing_log_dir_to_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")
            task["id"] = "private_test_live_control"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")

            target_log_dir = tmp_path / "request-logs"
            target_log_dir.mkdir()
            stale_entry = {
                "agent_id": "private-live-agent",
                "app": "project_mgmt",
                "method": "GET",
                "path": "/stale",
                "response_body_sha256": "0" * 64,
                "run_id": "protected-live-run",
                "seed": "stale-seed",
                "status": 200,
                "task_id": "private_test_live_control",
            }
            (target_log_dir / "project_mgmt.jsonl").write_text(json.dumps(stale_entry) + "\n", encoding="utf-8")

            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    f"""
                    import json
                    import os
                    from pathlib import Path

                    assert "AUTHZBENCH_TARGET_LOG_DIR" not in os.environ
                    assert "AUTHZBENCH_REQUEST_LOG_DIR" not in os.environ
                    context = json.loads(Path(os.environ["AUTHZBENCH_CONTEXT"]).read_text())
                    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission_path.write_text(json.dumps({{"findings": []}}))
                    (submission_path.parent / "model-tool-plan.json").write_text(
                        json.dumps({{"probes": [], "finding": None}})
                    )
                    (submission_path.parent / "tool-probes.json").write_text(
                        json.dumps({{"task_id": context["task_id"], "executed_probe_count": 1}})
                    )
                    log_path = Path({str(target_log_dir)!r}) / f"{{context['app']}}.jsonl"
                    with log_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({{
                            "agent_id": os.environ["AUTHZBENCH_AGENT_ID"],
                            "app": context["app"],
                            "method": "GET",
                            "path": "/api/projects/proof/tasks/proof",
                            "response_body_sha256": "1" * 64,
                            "run_id": os.environ["AUTHZBENCH_RUN_ID"],
                            "seed": context["seed"],
                            "status": 200,
                            "task_id": os.environ["AUTHZBENCH_TASK_ID"],
                        }}, sort_keys=True) + "\\n")
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {
                    "AUTHZBENCH_TARGET_LOG_DIR": str(target_log_dir),
                    "AUTHZBENCH_REQUEST_LOG_DIR": str(target_log_dir),
                },
            ):
                summary = run_protected_private_eval(
                    [str(task_path)],
                    agent_cmd=f"python3 {agent_path}",
                    results_dir=tmp_path / "results",
                    timeout_seconds=10,
                    benchmark_version="test",
                    benchmark_commit_sha=None,
                    agent="private-live-agent",
                    model="dummy-model",
                    harness_type="tool-agent",
                    target_log_dir=target_log_dir,
                    run_id="protected-live-run",
                )

            self.assertEqual(summary["target_request_correlated_task_count"], 1, summary)
            self.assertEqual(summary["target_request_coverage_rate"], 1.0, summary)
            self.assertEqual(summary["tasks"][0]["target_request_count"], 1, summary)
            task_dir = tmp_path / "results" / "protected-live-run" / "private_test_live_control"
            entries = [
                json.loads(line)
                for line in (task_dir / "target-requests.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["path"], "/api/projects/proof/tasks/proof")
            self.assertEqual(
                entries[0]["correlation"]["matched_on"],
                ["app", "seed", "run_id", "task_id", "agent_id"],
            )
            self.assertEqual(entries[0]["correlation"]["status"], "matched")
            self.assertTrue((task_dir / "model-tool-plan.json").exists())
            self.assertEqual(load_json(task_dir / "tool-probes.json")["executed_probe_count"], 1)
            redacted = redacted_summary(summary)
            self.assertEqual(redacted["target_request_correlated_task_count"], 1)
            self.assertEqual(redacted["target_request_coverage_rate"], 1.0)
            self.assertNotIn("target_log_dir", redacted)
            self.assertNotIn("private_test_live_control", str(redacted))
            self.assertEqual(
                redacted["runner_integrity"]["schema_version"],
                "runner-integrity-v2",
            )
            self.assertEqual(
                redacted["runner_integrity"]["claim_scope"],
                "unkeyed-tamper-evidence-not-origin-attestation",
            )
            self.assertRegex(
                redacted["runner_integrity"]["raw_summary_sha256"],
                r"^[0-9a-f]{64}$",
            )

    def test_loaded_private_pack_fingerprint_is_computed_and_caller_claim_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(
                ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json"
            )
            task["id"] = "private_test_pack_binding"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            fingerprint = _loaded_pack_fingerprint([(task_path, task)])

            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps({"findings": []})
                    )
                    """
                ),
                encoding="utf-8",
            )
            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="dummy-agent",
                model="dummy-model",
                harness_type="no-tools-model",
                run_id="pack-binding-run",
                private_pack_fingerprint_sha256=fingerprint,
                private_pack_id="private-pack-test",
                private_pack_version="test-v1",
            )

            self.assertEqual(
                summary["private_pack_fingerprint_sha256"],
                fingerprint,
                summary,
            )
            self.assertEqual(
                summary["private_pack_loaded_fingerprint_sha256"],
                fingerprint,
                summary,
            )
            self.assertEqual(
                summary["private_pack_fingerprint_provenance"],
                "runner-computed-loaded-manifests",
                summary,
            )
            self.assertEqual(summary["private_pack_id"], "private-pack-test", summary)
            self.assertEqual(summary["private_pack_version"], "test-v1", summary)
            redacted = redacted_summary(summary)
            self.assertEqual(
                redacted["private_pack_loaded_fingerprint_sha256"],
                fingerprint,
            )
            self.assertEqual(redacted["private_pack_id"], "private-pack-test")
            self.assertEqual(redacted["private_pack_version"], "test-v1")
            with self.assertRaisesRegex(
                ValueError,
                "does not match the loaded manifest set",
            ):
                run_protected_private_eval(
                    [str(task_path)],
                    agent_cmd=f"python3 {agent_path}",
                    results_dir=tmp_path / "mismatched-results",
                    timeout_seconds=10,
                    benchmark_version="test",
                    benchmark_commit_sha=None,
                    agent="dummy-agent",
                    model="dummy-model",
                    harness_type="no-tools-model",
                    run_id="mismatched-pack-run",
                    private_pack_fingerprint_sha256="0" * 64,
                )
            self.assertFalse((tmp_path / "mismatched-results").exists())

    def test_execution_failures_reduce_completion_and_increment_infrastructure_failures(self) -> None:
        cases = {
            "agent-command-failure": (
                """
                import json
                import os
                from pathlib import Path
                Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(json.dumps({"findings": []}))
                raise SystemExit(7)
                """,
                10,
                "agent_command_failure",
                None,
            ),
            "submission-missing": (
                "pass",
                10,
                "submission_missing",
                None,
            ),
            "submission-invalid": (
                """
                import os
                from pathlib import Path
                Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text("{")
                """,
                10,
                "submission_invalid",
                None,
            ),
            "adapter-invalid": (
                """
                import json
                import os
                from pathlib import Path
                submission = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                submission.write_text(json.dumps({"findings": []}))
                (submission.parent / "model-output.json").write_text("{")
                """,
                10,
                "adapter_failure",
                "adapter_metadata_failure",
            ),
            "agent-timeout": (
                """
                import time
                time.sleep(2)
                """,
                0.05,
                "agent_timeout",
                None,
            ),
        }
        for label, (
            source,
            timeout_seconds,
            expected_status,
            expected_adapter_failure,
        ) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                task = load_json(
                    ROOT
                    / "tasks"
                    / "project_mgmt"
                    / "pm_same_tenant_read_control.json"
                )
                task["id"] = f"private_test_{label.replace('-', '_')}"
                task["split"] = "private_holdout"
                task_path = tmp_path / "holdout.json"
                task_path.write_text(json.dumps(task), encoding="utf-8")
                agent_path = tmp_path / "agent.py"
                agent_path.write_text(
                    textwrap.dedent(source).strip() + "\n",
                    encoding="utf-8",
                )

                summary = run_protected_private_eval(
                    [str(task_path)],
                    agent_cmd=f"python3 {agent_path}",
                    results_dir=tmp_path / "results",
                    timeout_seconds=timeout_seconds,
                    benchmark_version="test",
                    benchmark_commit_sha=None,
                    agent="dummy-agent",
                    model="dummy-model",
                    harness_type="no-tools-model",
                    run_id=f"{label}-run",
                )

                self.assertEqual(summary["task_completion_count"], 0, summary)
                self.assertEqual(summary["task_incomplete_count"], 1, summary)
                self.assertEqual(summary["infrastructure_failure_count"], 1, summary)
                self.assertEqual(
                    summary["benchmark_execution_status"],
                    "completed_with_infrastructure_failures",
                    summary,
                )
                self.assertEqual(summary["passed_count"], 0, summary)
                self.assertEqual(
                    summary["tasks"][0]["task_execution_status"],
                    expected_status,
                    summary,
                )
                self.assertEqual(
                    summary["tasks"][0]["adapter_failure_type"],
                    expected_adapter_failure,
                    summary,
                )

    def test_scorer_exception_is_an_infrastructure_failure_not_a_completed_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(
                ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json"
            )
            task["id"] = "private_test_scorer_failure"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                "import json, os\n"
                "from pathlib import Path\n"
                'Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(json.dumps({"findings": []}))\n',
                encoding="utf-8",
            )

            with patch(
                "scripts.protected_private_eval.score_submission",
                side_effect=RuntimeError("private scorer detail must not leak"),
            ):
                summary = run_protected_private_eval(
                    [str(task_path)],
                    agent_cmd=f"python3 {agent_path}",
                    results_dir=tmp_path / "results",
                    timeout_seconds=10,
                    benchmark_version="test",
                    benchmark_commit_sha=None,
                    agent="dummy-agent",
                    model="dummy-model",
                    harness_type="no-tools-model",
                    run_id="scorer-failure-run",
                )

        self.assertEqual(summary["task_completion_count"], 0, summary)
        self.assertEqual(summary["scoring_failure_count"], 1, summary)
        self.assertEqual(summary["infrastructure_failure_count"], 1, summary)
        self.assertEqual(
            summary["tasks"][0]["task_execution_status"],
            "scorer_failure",
            summary,
        )
        self.assertNotIn("private scorer detail", str(redacted_summary(summary)))

    def test_correlation_mismatch_captures_all_rows_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(
                ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json"
            )
            task["id"] = "private_test_correlation_mismatch"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            target_log_dir = tmp_path / "request-logs"
            target_log_dir.mkdir()
            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    f"""
                    import json
                    import os
                    from pathlib import Path

                    context = json.loads(Path(os.environ["AUTHZBENCH_CONTEXT"]).read_text())
                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps({{"findings": []}})
                    )
                    common = {{
                        "agent_id": os.environ["AUTHZBENCH_AGENT_ID"],
                        "app": context["app"],
                        "method": "GET",
                        "path": "/api/projects/proof/tasks/proof",
                        "request_body_sha256": "0" * 64,
                        "response_body_sha256": "1" * 64,
                        "run_id": os.environ["AUTHZBENCH_RUN_ID"],
                        "seed": context["seed"],
                        "status": 200,
                        "task_id": os.environ["AUTHZBENCH_TASK_ID"],
                    }}
                    mismatched = dict(common)
                    mismatched["task_id"] = "private_other_task"
                    log_path = Path({str(target_log_dir)!r}) / f"{{context['app']}}.jsonl"
                    with log_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(common, sort_keys=True) + "\\n")
                        fh.write(json.dumps(mismatched, sort_keys=True) + "\\n")
                    """
                ),
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="correlation-agent",
                model="dummy-model",
                harness_type="tool-agent",
                target_log_dir=target_log_dir,
                run_id="correlation-mismatch-run",
            )

            row = summary["tasks"][0]
            self.assertEqual(row["target_post_offset_request_count"], 2, summary)
            self.assertEqual(row["target_request_count"], 1, summary)
            self.assertEqual(
                row["target_request_correlation_mismatch_count"],
                1,
                summary,
            )
            self.assertEqual(
                row["target_request_observation_status"],
                "target_request_correlation_mismatch",
                summary,
            )
            self.assertEqual(row["task_execution_status"], "target_observation_failure")
            self.assertEqual(summary["target_request_correlated_task_count"], 0)
            self.assertEqual(summary["target_request_coverage_rate"], 0.0)
            self.assertEqual(summary["task_completion_count"], 0)
            self.assertEqual(summary["infrastructure_failure_count"], 1)
            captured = [
                json.loads(line)
                for line in (
                    tmp_path
                    / "results"
                    / "correlation-mismatch-run"
                    / task["id"]
                    / "target-requests.jsonl"
                )
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(captured), 2)
            self.assertEqual(
                [entry["correlation"]["status"] for entry in captured],
                ["matched", "mismatch"],
            )
            redacted = redacted_summary(summary)
            self.assertNotIn("private_other_task", str(redacted))
            self.assertNotIn(task["id"], str(redacted))

    def test_absent_correlated_target_request_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(
                ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json"
            )
            task["id"] = "private_test_absent_target_request"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            target_log_dir = tmp_path / "request-logs"
            target_log_dir.mkdir()
            (target_log_dir / "project_mgmt.jsonl").write_text(
                "",
                encoding="utf-8",
            )
            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                "import json, os\n"
                "from pathlib import Path\n"
                'Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(json.dumps({"findings": []}))\n',
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="absent-request-agent",
                model="dummy-model",
                harness_type="tool-agent",
                target_log_dir=target_log_dir,
                run_id="absent-request-run",
            )

        self.assertEqual(
            summary["tasks"][0]["target_request_observation_status"],
            "no_target_requests_correlated",
            summary,
        )
        self.assertEqual(
            summary["tasks"][0]["task_execution_status"],
            "target_observation_failure",
            summary,
        )
        self.assertEqual(summary["task_completion_count"], 0, summary)
        self.assertEqual(summary["infrastructure_failure_count"], 1, summary)

    def test_requested_and_effective_model_mismatch_fails_identity_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(
                ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json"
            )
            task["id"] = "private_test_model_identity_mismatch"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    submission = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission.write_text(json.dumps({"findings": []}))
                    (submission.parent / "model-output.json").write_text(
                        json.dumps(
                            {
                                "returncode": 0,
                                "requested_model": "different-model",
                                "effective_model_label": "different-model",
                                "model_label_verified": True,
                                "model_identity_status": "verified",
                                "json_only_compliant": True,
                                "output_format": "json",
                            }
                        )
                    )
                    """
                ),
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="identity-agent",
                model="declared-model",
                harness_type="no-tools-model",
                run_id="model-identity-mismatch-run",
            )

        row = summary["tasks"][0]
        self.assertEqual(row["adapter_requested_model"], "different-model", summary)
        self.assertEqual(
            row["adapter_effective_model_label"],
            "different-model",
            summary,
        )
        self.assertFalse(row["adapter_model_label_verified"], summary)
        self.assertEqual(
            row["adapter_model_identity_status"],
            "mismatch_or_ambiguous",
            summary,
        )
        self.assertTrue(row["adapter_model_label_mismatch"], summary)
        self.assertEqual(row["adapter_failure_type"], "model_label_failure", summary)
        self.assertEqual(summary["model_label_mismatch_task_count"], 1, summary)
        self.assertEqual(summary["model_label_verified_task_count"], 0, summary)
        self.assertEqual(summary["task_completion_count"], 0, summary)
        integrity = redacted_summary(summary)["runner_integrity"]
        self.assertRegex(
            integrity["adapter_artifact_set_sha256"],
            r"^[0-9a-f]{64}$",
        )
        self.assertRegex(
            integrity["task_rows_digest_sha256"],
            r"^[0-9a-f]{64}$",
        )

    def test_trailing_same_route_different_body_mutation_is_captured_and_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(
                ROOT / "tasks" / "billing" / "bill_bfla_member_plan_change.json"
            )
            task["id"] = "private_test_trailing_body_mutation"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")
            submission = load_json(
                ROOT
                / "examples"
                / "submissions"
                / "bill_bfla_member_plan_change.valid.json"
            )
            target_log_dir = tmp_path / "request-logs"
            target_log_dir.mkdir()
            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    f"""
                    import hashlib
                    import json
                    import os
                    import subprocess
                    import sys
                    from pathlib import Path

                    def body_hash(body):
                        encoded = json.dumps(
                            body, sort_keys=True, separators=(",", ":")
                        ).encode()
                        return hashlib.sha256(encoded).hexdigest()

                    context = json.loads(
                        Path(os.environ["AUTHZBENCH_CONTEXT"]).read_text()
                    )
                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps({submission!r})
                    )
                    org_id = context["refs"]["ATLAS_ORG_ID"]
                    common = {{
                        "agent_id": os.environ["AUTHZBENCH_AGENT_ID"],
                        "app": context["app"],
                        "run_id": os.environ["AUTHZBENCH_RUN_ID"],
                        "seed": context["seed"],
                        "task_id": os.environ["AUTHZBENCH_TASK_ID"],
                    }}
                    negative = common | {{
                        "actor": "atlas_member",
                        "method": "GET",
                        "path": f"/api/secure/orgs/{{org_id}}/settings/plan",
                        "request_body_sha256": body_hash({{}}),
                        "response_body_sha256": "1" * 64,
                        "status": 403,
                    }}
                    allowed = common | {{
                        "actor": "atlas_member",
                        "method": "PATCH",
                        "path": f"/api/orgs/{{org_id}}/settings/plan",
                        "request_body_sha256": body_hash({{"plan": "enterprise"}}),
                        "response_body_sha256": "2" * 64,
                        "status": 200,
                    }}
                    trailing = common | {{
                        "actor": "atlas_member",
                        "method": "PATCH",
                        "path": f"/api/orgs/{{org_id}}/settings/plan",
                        "request_body_sha256": body_hash({{"plan": "free"}}),
                        "response_body_sha256": "3" * 64,
                        "status": 200,
                    }}
                    log_path = (
                        Path({str(target_log_dir)!r}) / f"{{context['app']}}.jsonl"
                    )
                    with log_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(negative, sort_keys=True) + "\\n")
                        fh.write(json.dumps(allowed, sort_keys=True) + "\\n")
                    child_code = (
                        "import sys,time\\n"
                        "time.sleep(0.35)\\n"
                        "with open(sys.argv[1], 'a', encoding='utf-8') as fh:\\n"
                        "    fh.write(sys.argv[2] + '\\\\n')\\n"
                    )
                    subprocess.Popen(
                        [
                            sys.executable,
                            "-c",
                            child_code,
                            str(log_path),
                            json.dumps(trailing, sort_keys=True),
                        ],
                        start_new_session=True,
                    )
                    """
                ),
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="trailing-mutation-agent",
                model="dummy-model",
                harness_type="tool-agent",
                target_log_dir=target_log_dir,
                run_id="trailing-mutation-run",
            )

        row = summary["tasks"][0]
        self.assertEqual(row["target_request_count"], 3, summary)
        self.assertEqual(row["target_post_offset_request_count"], 3, summary)
        self.assertTrue(row["target_request_quiescence_reached"], summary)
        self.assertEqual(row["observed_request_count"], 3, summary)
        self.assertEqual(row["observed_mutation_count"], 2, summary)
        self.assertEqual(row["observed_out_of_scope_mutation_count"], 1, summary)
        self.assertEqual(row["safety"], 0, summary)
        self.assertEqual(row["safety_observation_status"], "observed_violation", summary)
        self.assertTrue(row["evidence_chain_complete"], summary)
        self.assertTrue(row["core_passed"], summary)
        self.assertFalse(row["passed"], summary)
        self.assertFalse(row["promotion_eligible"], summary)
        self.assertEqual(summary["evidence_chain_complete_count"], 1, summary)
        self.assertEqual(summary["safety_violations"], 1, summary)
        self.assertEqual(summary["task_completion_count"], 1, summary)
        self.assertEqual(summary["infrastructure_failure_count"], 0, summary)

    def test_protected_eval_ignores_malformed_optional_tool_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")
            task["id"] = "private_test_malformed_tool_artifacts"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")

            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission_path.write_text(json.dumps({"findings": []}))
                    (submission_path.parent / "model-tool-plan.json").write_text("{not-json")
                    (submission_path.parent / "tool-probes.json").write_text("{also-not-json")
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="dummy-agent",
                model="dummy-model",
                harness_type="tool-agent",
                run_id="malformed-tool-artifacts-run",
            )

        self.assertEqual(summary["task_count"], 1, summary)
        self.assertEqual(summary["model_tool_plan_artifact_count"], 0, summary)
        self.assertEqual(summary["per_task_tool_probe_artifact_count"], 0, summary)
        self.assertIsNone(summary["executed_tool_probe_total"], summary)
        self.assertEqual(summary["tool_probe_telemetry_status"], "unobserved", summary)
        self.assertFalse(summary["tasks"][0]["model_tool_plan_artifact"], summary["tasks"][0])
        self.assertFalse(summary["tasks"][0]["tool_probe_artifact"], summary["tasks"][0])

    def test_protected_eval_separates_scored_and_adapter_finding_totals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")
            task["id"] = "private_test_finding_total_separation"
            task["split"] = "private_holdout"
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")

            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
                    submission_path.write_text(json.dumps({"findings": [{}]}))
                    (submission_path.parent / "tool-probes.json").write_text(
                        json.dumps(
                            {
                                "executed_probe_count": 2,
                                "fallback_probe_count": 0,
                                "submitted_finding_count": 2,
                            }
                        )
                    )
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="dummy-agent",
                model="dummy-model",
                harness_type="tool-agent",
                run_id="finding-total-separation-run",
            )

        self.assertEqual(summary["scored_submission_finding_total"], 1, summary)
        self.assertEqual(summary["submitted_finding_total"], 2, summary)
        self.assertEqual(summary["tool_probe_telemetry_status"], "complete", summary)
        self.assertEqual(summary["control_false_report_count"], 1, summary)
        self.assertEqual(summary["tasks"][0]["submission_finding_count"], 1, summary)
        self.assertEqual(summary["tasks"][0]["submitted_finding_count"], 2, summary)
        redacted = redacted_summary(summary)
        self.assertEqual(redacted["scored_submission_finding_total"], 1, redacted)
        self.assertEqual(redacted["submitted_finding_total"], 2, redacted)
        self.assertNotIn("private_test_finding_total_separation", str(redacted))

    def test_protected_eval_separates_control_failure_from_false_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(ROOT / "tasks" / "billing" / "bill_secure_member_plan_control.json")
            task["id"] = "private_test_broken_control_replay"
            task["split"] = "private_holdout"
            for control in task["controls"]:
                control["status"] = 418
            task_path = tmp_path / "holdout.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")

            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps({"findings": []})
                    )
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha=None,
                agent="dummy-agent",
                model="dummy-model",
                harness_type="no-tools-model",
                run_id="broken-control-replay-run",
            )

        self.assertEqual(summary["control_false_report_count"], 0, summary)
        self.assertEqual(summary["control_false_report_rate"], 0.0, summary)
        self.assertEqual(summary["control_execution_pass_rate"], 0.0, summary)
        self.assertEqual(summary["false_positive_rate"], 0.0, summary)
        self.assertEqual(summary["tasks"][0]["submission_finding_count"], 0, summary)
        self.assertEqual(summary["tasks"][0]["control_replay_passed"], False, summary)

    def test_redacted_summary_omits_task_rows_and_ids(self) -> None:
        summary = {
            "agent": "dummy-agent",
            "authorized_allow_control_task_count": 0,
            "benchmark_commit_sha": "abc123",
            "benchmark_fingerprint": {
                "authorized_allow_control_task_count": 0,
                "control_task_count": 1,
                "denial_control_task_count": 1,
                "evidence_contract_version": "evidence-requirements-v1",
                "schema_version": "benchmark-fingerprint-v1",
                "score_policy_version": "score-policy-v1",
                "scorer_contract": "v0-candidate-authz-evidence",
                "task_count": 1,
                "task_path_set_sha256": "1" * 64,
                "task_set_sha256": "2" * 64,
                "vulnerable_task_count": 0,
            },
            "benchmark_version": "test",
            "control_task_count": 1,
            "denial_control_task_count": 1,
            "harness_type": "no-tools-model",
            "model": "dummy-model",
            "protected_execution": {
                "agent_cwd": "temporary-empty-workspace",
                "agent_received": "rendered-context-only",
                "private_manifests_readable_in_agent_workspace": False,
                "raw_result_bundle_tracked": False,
                "tracked_private_manifest_count": 0,
            },
            "run_id": "private-run",
            "scored_submission_finding_total": 3,
            "submitted_finding_total": 2,
            "target_request_correlated_task_count": 0,
            "target_request_coverage_rate": None,
            "task_count": 1,
            "tasks": [{"task_id": "private_hidden_task"}],
            "v0_metric_profile": "v0-candidate-authz-evidence",
            "vulnerable_task_count": 0,
        }

        redacted = redacted_summary(summary)

        self.assertNotIn("tasks", redacted)
        self.assertNotIn("private_hidden_task", str(redacted))
        self.assertEqual(redacted["private_holdout_task_count"], 1)
        self.assertEqual(redacted["benchmark_fingerprint"]["task_count"], 1)
        self.assertEqual(redacted["scored_submission_finding_total"], 3)
        self.assertEqual(redacted["submitted_finding_total"], 2)
        self.assertTrue(redacted["redacted_private_holdout_source"])


if __name__ == "__main__":
    unittest.main()
