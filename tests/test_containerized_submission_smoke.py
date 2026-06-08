from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from authzbench.core import load_json
from scripts.containerized_submission_smoke import (
    MAX_OUTPUT_FILE_BYTES,
    _private_pack_fingerprint,
    _select_control_task,
    _sensitive_findings,
    _validated_container_constraints,
    run_smoke,
    validate_smoke_evidence,
)


ROOT = Path(__file__).resolve().parents[1]


class ContainerizedSubmissionSmokeTests(unittest.TestCase):
    @staticmethod
    def _mount_source(command: list[str], destination: str) -> Path:
        mount = next(
            command[index + 1]
            for index, argument in enumerate(command[:-1])
            if argument == "--mount" and f"dst={destination}" in command[index + 1]
        )
        return Path(mount.split("src=", 1)[1].split(",dst=", 1)[0])

    def _private_control_pack(self, root: Path) -> Path:
        public_task = load_json(ROOT / "tasks/billing/bill_secure_member_plan_control.json")
        private_task = copy.deepcopy(public_task)
        private_task["id"] = "private_smoke_control"
        private_task["seed"] = "private-smoke-seed"
        private_task["split"] = "private_holdout"
        pack = root / "tasks_private" / "holdout" / "smoke" / "billing"
        pack.mkdir(parents=True)
        (pack / "private_smoke_control.json").write_text(
            json.dumps(private_task),
            encoding="utf-8",
        )
        return pack.parent

    def test_selects_private_control_without_exposing_manifest_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = self._private_control_pack(Path(tmp))
            task = _select_control_task(pack)
            fingerprint = _private_pack_fingerprint(pack)

        self.assertEqual(task["id"], "private_smoke_control")
        self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")

    def test_release_validation_rejects_rehearsal_evidence(self) -> None:
        evidence = {
            "schema_version": "submission-runner-smoke-v1",
            "execution_scope": "rehearsal",
            "result": "passed",
            "benchmark_source_sha": "a" * 40,
            "runner_image_or_hosted_version": "python:3.11-alpine@sha256:example",
            "private_pack_version": "ci-rehearsal",
            "private_pack_fingerprint_sha256": "b" * 64,
            "isolation_model": "docker-bind-rendered-context-only",
            "command": "containerized submission smoke",
            "submitter_private_manifest_read_denied": True,
            "scorer_controlled_private_eval": True,
            "cleanup_completed": True,
            "privacy_scan_passed": True,
            "public_output_private_artifacts_included": False,
            "container_constraints": [
                "network=none",
                "read_only_rootfs",
                "cap_drop=ALL",
                "no_new_privileges",
                "non_root_user",
                "resource_limits",
                "rendered_context_mount_only",
                "output_file_size_limit",
            ],
        }

        release_errors = validate_smoke_evidence(evidence)
        rehearsal_errors = validate_smoke_evidence(evidence, allow_rehearsal=True)

        self.assertIn("rehearsal smoke evidence is not release-candidate evidence", release_errors)
        self.assertEqual(rehearsal_errors, [])

    def test_public_evidence_rejects_sensitive_paths_and_keys(self) -> None:
        evidence = {
            "schema_version": "submission-runner-smoke-v1",
            "execution_scope": "release_candidate",
            "result": "passed",
            "benchmark_source_sha": "a" * 40,
            "runner_image_or_hosted_version": "runner:v1",
            "private_pack_version": "active-v1",
            "private_pack_fingerprint_sha256": "b" * 64,
            "isolation_model": "container",
            "command": "read /Users/example/tasks_private/holdout",
            "submitter_private_manifest_read_denied": True,
            "scorer_controlled_private_eval": True,
            "cleanup_completed": True,
            "privacy_scan_passed": True,
            "public_output_private_artifacts_included": False,
            "container_constraints": [
                "network=none",
                "read_only_rootfs",
                "cap_drop=ALL",
                "no_new_privileges",
                "non_root_user",
                "resource_limits",
                "rendered_context_mount_only",
                "output_file_size_limit",
            ],
            "task_id": "private-task",
            "scorer_result": {"passed": True},
        }

        errors = validate_smoke_evidence(evidence)

        self.assertTrue(any("sensitive key" in error for error in errors), errors)
        self.assertTrue(any("sensitive path marker" in error for error in errors), errors)
        self.assertTrue(
            any("absolute path" in error for error in _sensitive_findings("runner=/opt/build/cache/")),
        )
        self.assertEqual(_sensitive_findings("url=https://example.com/path/"), [])

    def test_public_evidence_rejects_embedded_template_placeholders(self) -> None:
        evidence = {
            "schema_version": "submission-runner-smoke-v1",
            "execution_scope": "release_candidate",
            "result": "passed",
            "benchmark_source_sha": "a" * 40,
            "runner_image_or_hosted_version": "runner:<digest>",
            "private_pack_version": "active-<version>",
            "private_pack_fingerprint_sha256": "b" * 64,
            "isolation_model": "container-<isolation>",
            "command": "run --private-pack <active-pack>",
            "submitter_private_manifest_read_denied": True,
            "scorer_controlled_private_eval": True,
            "cleanup_completed": True,
            "privacy_scan_passed": True,
            "public_output_private_artifacts_included": False,
            "container_constraints": [
                "network=none",
                "read_only_rootfs",
                "cap_drop=ALL",
                "no_new_privileges",
                "non_root_user",
                "resource_limits",
                "rendered_context_mount_only",
                "output_file_size_limit",
            ],
        }

        errors = validate_smoke_evidence(evidence)

        self.assertIn("runner_image_or_hosted_version must not be a template placeholder", errors)
        self.assertIn("private_pack_version must not be a template placeholder", errors)
        self.assertIn("isolation_model must not be a template placeholder", errors)
        self.assertIn("command must not be a template placeholder", errors)

    def test_timeout_force_removes_named_container_and_emits_failed_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = self._private_control_pack(root)
            output = root / "submission-runner-smoke.json"
            calls: list[list[str]] = []

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                if command[:2] == ["docker", "run"]:
                    raise subprocess.TimeoutExpired(command, timeout=120)
                if command[:4] == ["docker", "container", "rm", "--force"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:3] == ["docker", "container", "ls"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(command, 0, "sha256:image\n", "")
                raise AssertionError(f"unexpected command: {command}")

            with patch("scripts.containerized_submission_smoke.subprocess.run", side_effect=fake_run):
                with self.assertRaisesRegex(RuntimeError, "result must be passed"):
                    run_smoke(
                        pack,
                        output_path=output,
                        benchmark_source_sha="a" * 40,
                        private_pack_version="ci-rehearsal",
                        execution_scope="rehearsal",
                    )

            evidence = load_json(output)

        self.assertEqual(evidence["result"], "failed")
        self.assertTrue(evidence["cleanup_completed"])
        self.assertTrue(
            any(command[:4] == ["docker", "container", "rm", "--force"] for command in calls),
            calls,
        )
        self.assertTrue(any(command[:3] == ["docker", "container", "ls"] for command in calls), calls)

    def test_container_constraints_are_derived_from_actual_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            output_dir = root / "output"
            input_dir.mkdir()
            output_dir.mkdir()
            command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "64",
                "--memory",
                "128m",
                "--cpus",
                "0.5",
                "--user",
                "65534:65534",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=16m",
                "--ulimit",
                f"fsize={MAX_OUTPUT_FILE_BYTES}:{MAX_OUTPUT_FILE_BYTES}",
                "--mount",
                f"type=bind,src={input_dir.resolve()},dst=/input,readonly",
                "--mount",
                f"type=bind,src={output_dir.resolve()},dst=/output",
                "python:3.11-alpine",
            ]

            constraints = _validated_container_constraints(command, input_dir, output_dir)
            with self.assertRaisesRegex(ValueError, "--network must be exactly none"):
                _validated_container_constraints(
                    [value for value in command if value != "--network" and value != "none"],
                    input_dir,
                    output_dir,
                )
            with self.assertRaisesRegex(ValueError, "container mounts must be exactly"):
                _validated_container_constraints(
                    command
                    + [
                        "--mount",
                        "type=bind,src=/tmp/private,dst=/private-holdout,readonly",
                    ],
                    input_dir,
                    output_dir,
                )

        self.assertIn("rendered_context_mount_only", constraints)
        self.assertIn("output_file_size_limit", constraints)

    def test_missing_submission_output_cannot_pass_secure_control_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = self._private_control_pack(root)
            output = root / "submission-runner-smoke.json"

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if command[:2] == ["docker", "run"]:
                    input_dir = self._mount_source(command, "/input")
                    output_dir = self._mount_source(command, "/output")
                    self.assertEqual(input_dir.stat().st_mode & 0o777, 0o755)
                    self.assertEqual((input_dir / "context.json").stat().st_mode & 0o777, 0o644)
                    (output_dir / "probe.json").write_text(
                        json.dumps(
                            {
                                "context_readable": True,
                                "private_paths_readable": {
                                    "/private-holdout/rotation-metadata.json": False,
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:4] == ["docker", "container", "rm", "--force"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:3] == ["docker", "container", "ls"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(command, 0, "sha256:image\n", "")
                raise AssertionError(f"unexpected command: {command}")

            with patch("scripts.containerized_submission_smoke.subprocess.run", side_effect=fake_run):
                with self.assertRaisesRegex(RuntimeError, "result must be passed"):
                    run_smoke(
                        pack,
                        output_path=output,
                        benchmark_source_sha="a" * 40,
                        private_pack_version="ci-rehearsal",
                        execution_scope="rehearsal",
                    )

            evidence = load_json(output)

        self.assertEqual(evidence["result"], "failed")

    def test_successful_rehearsal_emits_passed_public_safe_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = self._private_control_pack(root)
            output = root / "submission-runner-smoke.json"

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                if command[:2] == ["docker", "run"]:
                    output_dir = self._mount_source(command, "/output")
                    (output_dir / "submission.json").write_text(
                        json.dumps({"findings": []}),
                        encoding="utf-8",
                    )
                    (output_dir / "probe.json").write_text(
                        json.dumps(
                            {
                                "context_readable": True,
                                "private_paths_readable": {
                                    "/private-holdout/rotation-metadata.json": False,
                                    "/workspace/tasks_private/holdout": False,
                                    "/repo/tasks_private/holdout": False,
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:4] == ["docker", "container", "rm", "--force"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:3] == ["docker", "container", "ls"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:3] == ["docker", "image", "inspect"]:
                    return subprocess.CompletedProcess(command, 0, "sha256:image\n", "")
                raise AssertionError(f"unexpected command: {command}")

            with patch("scripts.containerized_submission_smoke.subprocess.run", side_effect=fake_run):
                evidence = run_smoke(
                    pack,
                    output_path=output,
                    benchmark_source_sha="a" * 40,
                    private_pack_version="ci-rehearsal",
                    execution_scope="rehearsal",
                )

        self.assertEqual(evidence["result"], "passed")
        self.assertEqual(evidence["execution_scope"], "rehearsal")
        self.assertTrue(evidence["privacy_scan_passed"])
        self.assertTrue(evidence["submitter_private_manifest_read_denied"])
        self.assertIn("rendered_context_mount_only", evidence["container_constraints"])


if __name__ == "__main__":
    unittest.main()
