"""Harbor adapter: builds Harbor-compatible datasets from AuthZBench-SaaS tasks.

Wraps the existing skeleton builder to provide a stable adapter API.
Claim boundary: dataset generation is a v2 technical milestone and does not
claim Harbor platform acceptance, external review, or hosted leaderboard readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dataset_builder import build_harbor_dataset_skeleton


ADAPTER_VERSION = "0.1.0"


def build_dataset(
    task_patterns: list[str],
    output_dir: Path,
    *,
    harness_lane: str = "no_tools",
    task_ids: list[str] | None = None,
    task_id: str | None = None,
    limit: int | None = None,
    overwrite: bool = False,
    oracle_solution_mode: str = "none",
    benchmark_source_sha: str | None = None,
) -> dict[str, Any]:
    """Build a Harbor-compatible dataset directory from public AuthZBench-SaaS tasks.

    Returns the dataset manifest dict.
    Raises ValueError if any private holdout tasks are included.
    """
    resolved_task_ids: list[str] | None = task_ids
    if task_id:
        resolved_task_ids = list(task_ids or []) + [task_id]

    manifest = build_harbor_dataset_skeleton(
        task_patterns,
        output_dir,
        harness_lane=harness_lane,
        oracle_solution_mode=oracle_solution_mode,
        task_ids=resolved_task_ids,
        limit=limit,
        clean=overwrite,
    )
    if benchmark_source_sha:
        manifest["benchmark_source_sha"] = benchmark_source_sha
    manifest["adapter_version"] = ADAPTER_VERSION
    import json
    manifest_path = output_dir / "dataset-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
