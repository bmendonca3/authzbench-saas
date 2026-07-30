from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import reproduce_public_artifact
from scripts import run_public_validation


ROOT = Path(__file__).resolve().parents[1]


class RootDockerfileTests(unittest.TestCase):
    def test_editable_install_inputs_are_copied(self) -> None:
        copied_sources: set[str] = set()
        for line in (ROOT / "Dockerfile").read_text(encoding="utf-8").splitlines():
            if not line.startswith("COPY "):
                continue
            tokens = shlex.split(line)
            copied_sources.update(token.rstrip("/") for token in tokens[1:-1])

        self.assertTrue(
            {"pyproject.toml", "README.md", "LICENSE", "authzbench", "authzbench_harbor", "apps"}
            <= copied_sources
        )


class PublicPrivacyWrapperTests(unittest.TestCase):
    def test_privacy_check_fails_when_git_returns_nonzero(self) -> None:
        result = subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repository",
        )
        with patch.object(run_public_validation.subprocess, "run", return_value=result):
            self.assertFalse(run_public_validation.run_privacy_check())

    def test_privacy_check_fails_when_git_inspection_raises(self) -> None:
        with patch.object(
            run_public_validation.subprocess,
            "run",
            side_effect=OSError("git unavailable"),
        ):
            self.assertFalse(run_public_validation.run_privacy_check())

    def test_privacy_check_fails_when_denied_paths_are_tracked(self) -> None:
        result = subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=0,
            stdout="tasks_private/holdout/example.json\n",
            stderr="",
        )
        with patch.object(run_public_validation.subprocess, "run", return_value=result):
            self.assertFalse(run_public_validation.run_privacy_check())

    def test_privacy_check_passes_only_for_clean_git_inspection(self) -> None:
        result = subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with patch.object(run_public_validation.subprocess, "run", return_value=result):
            self.assertTrue(run_public_validation.run_privacy_check())


class PublicReproductionTests(unittest.TestCase):
    def _minimal_root(self, directory: str) -> Path:
        root = Path(directory)
        scripts = root / "scripts"
        scripts.mkdir()
        (scripts / "validate_public.py").write_text("# test fixture\n", encoding="utf-8")
        return root

    def test_public_step_delegates_to_dependency_free_gate(self) -> None:
        step = reproduce_public_artifact._public_validation_step(
            skip_container_smoke=False
        )

        self.assertEqual(step["command"][0], sys.executable)
        self.assertEqual(step["command"][1], "scripts/validate_public.py")
        self.assertIn("--include-scripted-baseline", step["command"])
        self.assertIn("--include-container-smoke", step["command"])
        self.assertNotIn("pytest", step["command"])

    def test_skip_container_smoke_removes_container_flag(self) -> None:
        step = reproduce_public_artifact._public_validation_step(
            skip_container_smoke=True
        )

        self.assertNotIn("--include-container-smoke", step["command"])

    def test_default_requires_docker_before_running_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._minimal_root(tmp)
            with (
                patch.object(reproduce_public_artifact.shutil, "which", return_value=None),
                patch.object(reproduce_public_artifact, "_run_step") as run_step,
            ):
                result = reproduce_public_artifact.main(["--root", str(root)])

        self.assertEqual(result, 2)
        run_step.assert_not_called()

    def test_skip_container_smoke_runs_without_docker_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._minimal_root(tmp)
            (root / "scripts" / "validate_public.py").write_text(
                "import sys\n"
                "expected = ['--include-scripted-baseline']\n"
                "raise SystemExit(0 if sys.argv[1:] == expected else 3)\n",
                encoding="utf-8",
            )
            with patch.object(
                reproduce_public_artifact.shutil,
                "which",
                return_value=None,
            ):
                result = reproduce_public_artifact.main(
                    ["--root", str(root), "--skip-container-smoke"]
                )

            self.assertEqual(result, 0)
            self.assertFalse((root / "artifact").exists())

    def test_explicit_output_writes_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._minimal_root(tmp)
            output = root / "output" / "summary.json"
            passed = {
                "id": "public_validation",
                "description": "Dependency-free public validation gate",
                "command": [],
                "passed": True,
                "returncode": 0,
                "elapsed_seconds": 0.0,
                "stdout_tail": "",
                "stderr_tail": "",
            }
            with (
                patch.object(reproduce_public_artifact.shutil, "which", return_value=None),
                patch.object(
                    reproduce_public_artifact,
                    "_run_step",
                    return_value=passed,
                ),
            ):
                result = reproduce_public_artifact.main(
                    [
                        "--root",
                        str(root),
                        "--skip-container-smoke",
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            summary = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(summary["overall_passed"])
            self.assertFalse(summary["container_smoke_included"])


if __name__ == "__main__":
    unittest.main()
