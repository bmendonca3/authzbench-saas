from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_public


class ValidatePublicScriptTests(unittest.TestCase):
    def test_container_smoke_requires_docker_cli(self) -> None:
        with patch.object(validate_public.shutil, "which", return_value=None):
            with self.assertRaisesRegex(SystemExit, "docker is required"):
                validate_public.run_container_smoke(validate_public.ROOT)

    def test_container_smoke_tears_down_compose_on_failure(self) -> None:
        calls: list[tuple[list[str], Path, bool, dict[str, str] | None]] = []

        def fake_run(
            cmd: list[str],
            cwd: Path = validate_public.ROOT,
            *,
            check: bool = True,
            env: dict[str, str] | None = None,
        ) -> None:
            calls.append((cmd, cwd, check, env))
            if cmd == [validate_public.sys.executable, "scripts/container_smoke.py"]:
                raise subprocess.CalledProcessError(1, cmd)

        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            with (
                patch.object(validate_public.shutil, "which", return_value="/usr/bin/docker"),
                patch.object(validate_public.os, "getpid", return_value=4242),
                patch.object(validate_public.os, "getuid", return_value=501),
                patch.object(validate_public.os, "getgid", return_value=20),
                patch.object(validate_public, "run", side_effect=fake_run),
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    validate_public.run_container_smoke(cwd)

        self.assertEqual(calls[0][0], ["docker", "info"])
        self.assertEqual(calls[0][1], cwd)
        self.assertEqual(calls[1][0], ["docker", "compose", "config"])
        self.assertEqual(calls[1][1], cwd)
        self.assertEqual(calls[2][0], ["docker", "compose", "-p", "authzbench-public-smoke-4242", "up", "--build", "-d"])
        self.assertEqual(calls[3][0], [validate_public.sys.executable, "scripts/container_smoke.py"])
        self.assertEqual(calls[4][0], ["docker", "compose", "-p", "authzbench-public-smoke-4242", "logs", "--no-color", "--tail", "200"])
        self.assertEqual(calls[4][1], cwd)
        self.assertFalse(calls[4][2])
        self.assertEqual(calls[5][0], ["docker", "compose", "-p", "authzbench-public-smoke-4242", "down"])
        self.assertEqual(calls[5][1], cwd)
        self.assertFalse(calls[5][2])
        self.assertEqual(calls[2][3]["AUTHZBENCH_DOCKER_UID"], "501")
        self.assertEqual(calls[2][3]["AUTHZBENCH_DOCKER_GID"], "20")

    def test_container_smoke_requires_running_docker_daemon(self) -> None:
        def fake_run(
            cmd: list[str],
            cwd: Path = validate_public.ROOT,
            *,
            check: bool = True,
            env: dict[str, str] | None = None,
        ) -> None:
            if cmd == ["docker", "info"]:
                raise subprocess.CalledProcessError(1, cmd)

        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.object(validate_public.shutil, "which", return_value="/usr/bin/docker"),
                patch.object(validate_public, "run", side_effect=fake_run),
            ):
                with self.assertRaisesRegex(SystemExit, "docker daemon is required"):
                    validate_public.run_container_smoke(Path(tmp))

    def test_validate_does_not_check_compose_without_container_smoke(self) -> None:
        with (
            patch.object(validate_public, "run") as run,
            patch.object(validate_public, "scan_privacy"),
            patch.object(validate_public, "run_container_smoke"),
        ):
            validate_public.validate(validate_public.ROOT, include_scripted_baseline=False, include_container_smoke=False)

        commands = [call.args[0] for call in run.call_args_list]
        self.assertNotIn(["docker", "info"], commands)
        self.assertNotIn(["docker", "compose", "config"], commands)

    def test_validate_runs_container_smoke_only_when_requested(self) -> None:
        with (
            patch.object(validate_public, "run"),
            patch.object(validate_public, "scan_privacy"),
            patch.object(validate_public, "run_container_smoke") as smoke,
        ):
            validate_public.validate(validate_public.ROOT, include_scripted_baseline=False, include_container_smoke=False)
            self.assertFalse(smoke.called)

            validate_public.validate(validate_public.ROOT, include_scripted_baseline=False, include_container_smoke=True)
            smoke.assert_called_once_with(validate_public.ROOT)

    def test_validate_runs_baseline_registry_gate(self) -> None:
        with (
            patch.object(validate_public, "run") as run,
            patch.object(validate_public, "scan_privacy"),
            patch.object(validate_public, "run_container_smoke"),
        ):
            validate_public.validate(validate_public.ROOT, include_scripted_baseline=False, include_container_smoke=False)

        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn([validate_public.sys.executable, "scripts/validate_baseline_registry.py"], commands)

    def test_validate_runs_v0_release_audit_gate_in_allow_incomplete_mode(self) -> None:
        with (
            patch.object(validate_public, "run") as run,
            patch.object(validate_public, "scan_privacy"),
            patch.object(validate_public, "run_container_smoke"),
        ):
            validate_public.validate(validate_public.ROOT, include_scripted_baseline=False, include_container_smoke=False)

        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn(
            [validate_public.sys.executable, "scripts/validate_v0_release.py", "--allow-incomplete"],
            commands,
        )

    def test_validate_runs_leaderboard_submission_gate(self) -> None:
        with (
            patch.object(validate_public, "run") as run,
            patch.object(validate_public, "scan_privacy"),
            patch.object(validate_public, "run_container_smoke"),
        ):
            validate_public.validate(validate_public.ROOT, include_scripted_baseline=False, include_container_smoke=False)

        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn(
            [
                validate_public.sys.executable,
                "scripts/validate_leaderboard_submission.py",
                "--submission",
                "examples/leaderboard/*.json",
                "--require-source-summary",
            ],
            commands,
        )

    def test_validate_regenerates_benchmark_charts_and_checks_drift(self) -> None:
        with (
            patch.object(validate_public, "run") as run,
            patch.object(validate_public, "scan_privacy"),
            patch.object(validate_public, "run_container_smoke"),
        ):
            validate_public.validate(validate_public.ROOT, include_scripted_baseline=False, include_container_smoke=False)

        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn([validate_public.sys.executable, "scripts/generate_benchmark_charts.py"], commands)
        self.assertIn(["git", "diff", "--exit-code", "--", "docs/assets/benchmark-charts"], commands)

    def test_validate_regenerates_task_quality_matrix_and_checks_drift(self) -> None:
        with (
            patch.object(validate_public, "run") as run,
            patch.object(validate_public, "scan_privacy"),
            patch.object(validate_public, "run_container_smoke"),
        ):
            validate_public.validate(validate_public.ROOT, include_scripted_baseline=False, include_container_smoke=False)

        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn([validate_public.sys.executable, "scripts/generate_task_quality_matrix.py"], commands)
        self.assertIn(
            ["git", "diff", "--exit-code", "--", "docs/task-quality-matrix.json", "docs/task-quality-matrix.md"],
            commands,
        )


if __name__ == "__main__":
    unittest.main()
