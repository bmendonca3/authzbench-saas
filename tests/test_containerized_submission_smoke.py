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
    _private_pack_fingerprint,
    _select_control_task,
    run_smoke,
    validate_smoke_evidence,
)


ROOT = Path(__file__).resolve().parents[1]


class ContainerizedSubmissionSmokeTests(unittest.TestCase):
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
            ],
            "task_id": "private-task",
            "scorer_result": {"passed": True},
        }

        errors = validate_smoke_evidence(evidence)

        self.assertTrue(any("sensitive key" in error for error in errors), errors)
        self.assertTrue(any("sensitive path marker" in error for error in errors), errors)

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


if __name__ == "__main__":
    unittest.main()
