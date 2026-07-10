from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def validate_packaged_harbor() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="authzbench-wheel-smoke-") as tmp:
        temp_root = Path(tmp)
        source_copy = temp_root / "source"
        source_copy.mkdir()
        for filename in ("pyproject.toml", "README.md", "LICENSE"):
            shutil.copyfile(ROOT / filename, source_copy / filename)
        for package_name in ("authzbench", "authzbench_harbor", "apps"):
            shutil.copytree(
                ROOT / package_name,
                source_copy / package_name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        wheel_dir = temp_root / "wheel"
        wheel_dir.mkdir()
        _run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                ".",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(wheel_dir),
            ],
            cwd=source_copy,
        )
        wheels = list(wheel_dir.glob("authzbench_saas-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"expected one authzbench wheel, found {len(wheels)}")
        wheel_path = wheels[0]
        with zipfile.ZipFile(wheel_path) as archive:
            names = set(archive.namelist())
        required_members = {
            "authzbench/__init__.py",
            "authzbench_harbor/__init__.py",
            "authzbench_harbor/adapter.py",
            "authzbench_harbor/cli.py",
            "authzbench_harbor/dataset_builder.py",
            "authzbench_harbor/redaction.py",
            "authzbench_harbor/schemas.py",
            "authzbench_harbor/scorer_bridge.py",
        }
        missing = sorted(required_members - names)
        if missing:
            raise RuntimeError(f"wheel is missing packaged Harbor files: {', '.join(missing)}")

        install_dir = temp_root / "installed"
        isolated_env = os.environ.copy()
        isolated_env.pop("PYTHONPATH", None)
        _run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--target",
                str(install_dir),
                str(wheel_path),
            ],
            cwd=temp_root,
            env=isolated_env,
        )
        module_runner = (
            "import runpy,sys; "
            "sys.path.insert(0, sys.argv.pop(1)); "
            "runpy.run_module('authzbench_harbor.cli', run_name='__main__')"
        )
        _run(
            [sys.executable, "-I", "-c", module_runner, str(install_dir), "--help"],
            cwd=temp_root,
            env=isolated_env,
        )

        shutil.copyfile(
            ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json",
            temp_root / "task.json",
        )
        output_dir = temp_root / "dataset"
        completed = _run(
            [
                sys.executable,
                "-I",
                "-c",
                module_runner,
                str(install_dir),
                "build",
                "--tasks",
                "task.json",
                "--output-dir",
                str(output_dir),
                "--harness-lane",
                "no_tools",
                "--benchmark-source-sha",
                "0" * 40,
            ],
            cwd=temp_root,
            env=isolated_env,
        )
        cli_result = json.loads(completed.stdout)
        manifest = json.loads((output_dir / "dataset-manifest.json").read_text(encoding="utf-8"))
        if cli_result.get("status") != "ok" or manifest.get("task_count") != 1:
            raise RuntimeError("installed Harbor CLI did not build the one-task smoke dataset")

        submission_path = temp_root / "submission.json"
        submission_path.write_text('{"findings":[]}\n', encoding="utf-8")
        bridge_output = temp_root / "bridge-output.json"
        bridge_runner = (
            "import runpy,sys; "
            "sys.path.insert(0, sys.argv.pop(1)); "
            "runpy.run_module('authzbench_harbor.scorer_bridge', run_name='__main__')"
        )
        _run(
            [
                sys.executable,
                "-I",
                "-c",
                bridge_runner,
                str(install_dir),
                "--task-file",
                str(temp_root / "task.json"),
                "--submission-file",
                str(submission_path),
                "--output",
                str(bridge_output),
            ],
            cwd=temp_root,
            env=isolated_env,
        )
        bridge_result = json.loads(bridge_output.read_text(encoding="utf-8"))
        if bridge_result.get("reward") != 1.0 or bridge_result.get("passed") is not True:
            raise RuntimeError("installed Harbor scorer bridge failed the secure-control smoke")

        return {
            "passed": True,
            "wheel_name": wheel_path.name,
            "required_member_count": len(required_members),
            "built_task_count": manifest["task_count"],
            "scorer_bridge_reward": bridge_result["reward"],
        }


def main() -> int:
    print(json.dumps(validate_packaged_harbor(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
