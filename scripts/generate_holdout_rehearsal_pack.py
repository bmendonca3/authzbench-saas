from __future__ import annotations

import argparse
import copy
import glob
import hashlib
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
from scripts.validate_holdout_pack import validate_holdout_pack


DEFAULT_OUTPUT_DIR = ROOT / "tasks_private" / "holdout" / "rehearsal"


def _manifest_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(path) for path in glob.glob(pattern, recursive=True))
    return sorted({path for path in paths if path.is_file()})


def _public_tasks_by_app(patterns: list[str]) -> dict[str, list[dict[str, Any]]]:
    by_app: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in _manifest_paths(patterns):
        task = load_json(path)
        task["_source_path"] = str(path)
        by_app[str(task["app"])].append(task)
    return dict(sorted(by_app.items()))


def _private_id(index: int, public_id: str) -> str:
    digest = hashlib.sha256(f"{index}:{public_id}".encode("utf-8")).hexdigest()[:8]
    return f"holdout_rehearsal_{index:03d}_{digest}"


def _private_seed(index: int, public_id: str) -> str:
    digest = hashlib.sha256(f"private-rehearsal:{index}:{public_id}".encode("utf-8")).hexdigest()[:12]
    return f"private-v0-rehearsal-{index:03d}-{digest}"


def _private_rehearsal_copy(task: dict[str, Any], index: int) -> dict[str, Any]:
    private_task = copy.deepcopy(task)
    private_task.pop("_source_path", None)
    private_task["id"] = _private_id(index, str(task["id"]))
    private_task["seed"] = _private_seed(index, str(task["id"]))
    private_task["split"] = "private_holdout"
    private_task["leaderboard_suitable"] = False
    private_task["rehearsal_note"] = (
        "Generated from public task structure for local private-pack workflow validation only; "
        "not suitable for private leaderboard scoring."
    )
    return private_task


def generate_holdout_rehearsal_tasks(public_patterns: list[str]) -> list[dict[str, Any]]:
    by_app = _public_tasks_by_app(public_patterns)
    tasks: list[dict[str, Any]] = []
    index = 1
    for app, app_tasks in by_app.items():
        vulnerable = [task for task in app_tasks if task.get("expected_vulnerable") is True]
        controls = [task for task in app_tasks if task.get("expected_vulnerable") is False]
        denial_controls = [task for task in controls if task.get("control_type") == "denial"]
        allow_controls = [task for task in controls if task.get("control_type") == "authorized_allow"]
        selected = vulnerable[:2]
        if allow_controls:
            selected.append(allow_controls[0])
        if denial_controls:
            selected.append(denial_controls[0])
        for fallback in controls:
            if len(selected) >= 4:
                break
            if fallback not in selected:
                selected.append(fallback)
        if len(selected) < 4:
            raise ValueError(f"app {app} does not have enough public tasks to build a rehearsal holdout slice")
        for task in selected[:4]:
            tasks.append(_private_rehearsal_copy(task, index))
            index += 1
    return tasks


def _assert_ignored_holdout_path(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    repo_root = ROOT.resolve()
    ignored_holdout_root = (ROOT / "tasks_private" / "holdout").resolve()
    if resolved == repo_root or repo_root in resolved.parents:
        if resolved != ignored_holdout_root and ignored_holdout_root not in resolved.parents:
            raise ValueError("in-repo output directory must be under the ignored tasks_private/holdout path")
        return
    if "tasks_private" not in resolved.parts or "holdout" not in resolved.parts:
        raise ValueError("out-of-repo output directory must include a tasks_private/holdout path")


def write_rehearsal_pack(tasks: list[dict[str, Any]], output_dir: Path, *, force: bool) -> list[Path]:
    _assert_ignored_holdout_path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        if not force:
            raise FileExistsError(f"{output_dir} is not empty; pass --force to replace the rehearsal pack")
        shutil.rmtree(output_dir)
    written: list[Path] = []
    for task in tasks:
        path = output_dir / str(task["app"]) / f"{task['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dump_json(task) + "\n", encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an ignored local private-holdout rehearsal pack. "
            "This proves the private-pack workflow but is not a real leaderboard holdout."
        )
    )
    parser.add_argument("--public-task", action="append", default=["tasks/*/*.json"])
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--force", action="store_true", help="Replace an existing rehearsal pack.")
    parser.add_argument("--dry-run", action="store_true", help="Print the generated summary without writing files.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    tasks = generate_holdout_rehearsal_tasks(args.public_task)
    summary = {
        "output_dir": str(output_dir),
        "task_count": len(tasks),
        "apps": sorted({str(task["app"]) for task in tasks}),
        "vulnerable_count": sum(1 for task in tasks if task.get("expected_vulnerable") is True),
        "control_count": sum(1 for task in tasks if task.get("expected_vulnerable") is False),
        "denial_control_count": sum(1 for task in tasks if task.get("control_type") == "denial"),
        "authorized_allow_control_count": sum(1 for task in tasks if task.get("control_type") == "authorized_allow"),
        "leaderboard_suitable": False,
    }
    if args.dry_run:
        print(dump_json(summary))
        return 0

    try:
        written = write_rehearsal_pack(tasks, output_dir, force=args.force)
    except (FileExistsError, ValueError) as exc:
        print(dump_json(summary | {"passed": False, "error": str(exc)}))
        return 1
    validation = validate_holdout_pack(
        [str(output_dir / "**" / "*.json")],
        public_patterns=args.public_task,
        min_count=20,
        preferred_count=24,
        max_count=30,
        min_vulnerable=12,
        min_controls=8,
        min_apps=6,
        max_per_app=8,
        min_denial_controls=4,
        min_authorized_allow_controls=4,
    )
    print(dump_json(summary | {"written_count": len(written), "validation": validation}))
    return 0 if validation["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
