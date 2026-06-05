from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PRIVACY_PATTERN_PARTS = [
    ("at least", " 12"),
    ("v0", r"\.0\.1-public"),
    ("non-", "Gatech"),
    ("/Users/", "brianmendonca"),
    ("Bri", "an"),
    ("Men", "donca"),
    ("Georgia", " Tech"),
    ("gat", "ech"),
    ("OPENAI", "_API_KEY"),
    ("GITHUB", "_TOKEN"),
    ("PRIVATE", " KEY"),
    ("ghp_", r"[A-Za-z0-9_]{20,}"),
    ("sk-", r"[A-Za-z0-9]{20,}"),
]

PRIVACY_PATTERNS = [re.compile("".join(parts)) for parts in PRIVACY_PATTERN_PARTS]


def run(
    cmd: list[str],
    cwd: Path = ROOT,
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=check, env=env)


def git_files(cwd: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return [cwd / line for line in result.stdout.splitlines() if line]


def scan_privacy(cwd: Path) -> None:
    hits: list[str] = []
    for path in git_files(cwd):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(cwd)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in PRIVACY_PATTERNS):
                hits.append(f"{relative}:{line_number}:{line}")
    if hits:
        joined = "\n".join(hits)
        raise SystemExit(f"privacy scan found disallowed text:\n{joined}")


def run_container_smoke(cwd: Path) -> None:
    if shutil.which("docker") is None:
        raise SystemExit("docker is required for --include-container-smoke")
    compose_env = os.environ.copy()
    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        compose_env.setdefault("AUTHZBENCH_DOCKER_UID", str(os.getuid()))
        compose_env.setdefault("AUTHZBENCH_DOCKER_GID", str(os.getgid()))
    (cwd / "captures" / "request-logs").mkdir(parents=True, exist_ok=True)
    project_name = f"authzbench-public-smoke-{os.getpid()}"
    try:
        run(["docker", "compose", "-p", project_name, "up", "--build", "-d"], cwd, env=compose_env)
        try:
            run([sys.executable, "scripts/container_smoke.py"], cwd)
        except Exception:
            run(["docker", "compose", "-p", project_name, "logs", "--no-color", "--tail", "200"], cwd, check=False, env=compose_env)
            raise
    finally:
        run(["docker", "compose", "-p", project_name, "down"], cwd, check=False, env=compose_env)


def validate(cwd: Path, include_scripted_baseline: bool, include_container_smoke: bool) -> None:
    run([sys.executable, "-Wd", "-m", "unittest", "discover", "-s", "tests"], cwd)
    run([sys.executable, "-m", "authzbench.validate_manifests", "--task", "tasks/*/*.json"], cwd)
    run([sys.executable, "scripts/validate_baseline_registry.py"], cwd)
    run([sys.executable, "-m", "compileall", "-q", "authzbench", "apps", "tests", "scripts"], cwd)
    run(["docker", "compose", "config"], cwd)
    scan_privacy(cwd)
    if include_scripted_baseline:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        run(
            [
                sys.executable,
                "-m",
                "authzbench.run",
                "--task",
                "tasks/*/*.json",
                "--agent-cmd",
                f"{sys.executable} scripts/scripted_baseline_agent.py",
                "--results-dir",
                "results/validation-scripted-baseline",
                "--timeout-seconds",
                "10",
                "--benchmark-commit-sha",
                commit,
                "--agent",
                "scripted_baseline_agent",
                "--model",
                "deterministic-script",
                "--harness-type",
                "scripted",
            ],
            cwd,
        )
    if include_container_smoke:
        run_container_smoke(cwd)


def validate_fresh_clone(repo_url: str, include_scripted_baseline: bool, include_container_smoke: bool) -> None:
    if shutil.which("git") is None:
        raise SystemExit("git is required for --fresh-clone")
    with tempfile.TemporaryDirectory(prefix="authzbench-public-clone.") as tmp:
        clone_dir = Path(tmp) / "authzbench-saas"
        run(["git", "clone", "--depth", "1", repo_url, str(clone_dir)], Path.cwd())
        validate(clone_dir, include_scripted_baseline, include_container_smoke)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AuthZBench-SaaS public validation gates.")
    parser.add_argument(
        "--include-scripted-baseline",
        action="store_true",
        help="Run the deterministic scripted baseline after static validation.",
    )
    parser.add_argument(
        "--include-container-smoke",
        action="store_true",
        help="Build and start Docker Compose targets, run container_smoke.py, and tear them down.",
    )
    parser.add_argument(
        "--fresh-clone",
        metavar="REPO_URL",
        help="Clone the public repository into a temporary directory and validate that clone.",
    )
    args = parser.parse_args()

    if args.fresh_clone:
        validate_fresh_clone(args.fresh_clone, args.include_scripted_baseline, args.include_container_smoke)
    else:
        validate(ROOT, args.include_scripted_baseline, args.include_container_smoke)
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    raise SystemExit(main())
