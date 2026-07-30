"""Baseline variance and confidence reporting.

The current v1 readiness gate already requires two repeated 60-task public
baselines per model family, but the published per-baseline summary files
only carry point estimates. Reviewers should not have to compute variance
themselves, and a small-n=2 repeated run does not justify claiming a tight
confidence interval. This script consumes the per-run summary JSONs, joins
them by their registry entry id, and emits:

  * mean pass rate
  * standard deviation, standard error
  * 95% confidence interval, with a clear small-n warning
  * per-task agreement rate (how often did both runs reach the same verdict)
  * changed-verdict count between repeated runs

It is intentionally a script you run on demand, not part of every CI run.

Usage:
    python3 scripts/analyze_baseline_variance.py
    python3 scripts/analyze_baseline_variance.py --require-current-public
    python3 scripts/analyze_baseline_variance.py --json-output artifact/variance.json
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINES_DIR = ROOT / "baselines"
REGISTRY_PATH = BASELINES_DIR / "baseline-registry.json"
DEFAULT_JSON_OUTPUT = ROOT / "artifact" / "baseline-variance-summary.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "docs" / "baseline-variance-analysis.md"

# Map summary_path strings into on-disk paths under baselines/.
SUMMARY_KEYS_FOR_PASS_RATE = (
    "vulnerable_full_pass_count",
    "exploit_proven_task_count",
    "exploit_proven_success_rate",
    "boundary_reasoning_pass_rate",
    "control_execution_pass_rate",
    "false_positive_rate",
    "vulnerable_task_count",
    "control_task_count",
)

SMALL_N_THRESHOLD = 2


def _load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _load_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _cohort_for_entry(entry: dict[str, Any]) -> str:
    if entry.get("release_suitability") == "current_public_harness_check":
        return "scripted-sanity"
    if entry.get("release_suitability") != "current_public_split":
        return "stale"
    kind = entry.get("kind")
    if kind == "harness_check":
        return "scripted-sanity"
    if kind == "tool_agent_baseline":
        return "current-tool-agent"
    if kind == "model_baseline":
        return "current-model"
    return "other"


def _small_n_warning(run_count: int) -> str | None:
    if run_count < SMALL_N_THRESHOLD:
        return (
            f"n={run_count}: confidence interval is a textbook normal approximation;"
            " for n<2 there is no variance signal at all"
        )
    if run_count < 5:
        return (
            f"n={run_count}: 95% CI below uses the normal approximation and is"
            " best read as a coarse ordering signal, not a hard bound"
        )
    return None


def _ci95(values: list[float]) -> tuple[float, float, float, float] | None:
    if len(values) < 2:
        return None
    mean = statistics.fmean(values)
    std_dev = statistics.stdev(values)
    std_error = std_dev / math.sqrt(len(values))
    half_width = 1.96 * std_error
    return mean, std_dev, std_error, half_width


def _agreement_rate(per_run_verdicts: list[dict[str, bool]]) -> dict[str, Any]:
    if not per_run_verdicts or len(per_run_verdicts) < 2:
        return {"task_count": 0, "agreement_rate": None, "changed_verdict_count": 0}
    task_ids = sorted({tid for verdicts in per_run_verdicts for tid in verdicts})
    agreed = 0
    changed = 0
    for tid in task_ids:
        seen = [v[tid] for v in per_run_verdicts if tid in v]
        if len(seen) < len(per_run_verdicts):
            continue
        if all(value == seen[0] for value in seen):
            agreed += 1
        else:
            changed += 1
    total = agreed + changed
    return {
        "task_count": total,
        "agreement_rate": round(agreed / total, 4) if total else None,
        "changed_verdict_count": changed,
    }


def _per_task_verdicts(summary: dict[str, Any]) -> dict[str, bool]:
    verdicts: dict[str, bool] = {}
    tasks = summary.get("tasks")
    if not isinstance(tasks, list):
        return verdicts
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        for verdict_key in ("passed", "v0_passed", "v0_verdict"):
            verdict = task.get(verdict_key)
            if isinstance(verdict, bool):
                verdicts[task_id] = verdict
                break
    return verdicts


def _is_stale_pending_rerun(entry: dict[str, Any]) -> bool:
    """Return True if a capability row is honestly non-current and needs rerun."""
    if entry.get("kind") not in ("model_baseline", "tool_agent_baseline"):
        return False
    if entry.get("release_suitability") not in {
        "current_public_stale",
        "legacy_snapshot",
    }:
        return False
    if not entry.get("requires_rerun_before_current_comparison"):
        return False
    if entry.get("leaderboard_eligible"):
        return False
    task_count = entry.get("expected_task_count", 0)
    if not isinstance(task_count, int) or task_count <= 0:
        return False
    return True


def _has_current_63_scripted_sanity(registry: dict[str, Any]) -> bool:
    for entry in registry.get("baselines", []):
        if (
            entry.get("release_suitability") == "current_public_harness_check"
            and entry.get("kind") == "harness_check"
            and entry.get("expected_harness_type") == "scripted"
            and entry.get("expected_task_count") == 63
            and not entry.get("requires_rerun_before_current_comparison")
        ):
            return True
    return False


def _all_capability_rows_stale_pending(registry: dict[str, Any]) -> bool:
    capability_rows = [
        e for e in registry.get("baselines", [])
        if e.get("kind") in ("model_baseline", "tool_agent_baseline")
    ]
    if not capability_rows:
        return False
    return all(_is_stale_pending_rerun(e) for e in capability_rows)


def analyze_registry(
    registry: dict[str, Any],
    baselines_dir: Path = BASELINES_DIR,
    require_current_public: bool = False,
    allow_stale_pending_rerun: bool = False,
) -> dict[str, Any]:
    cohort_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    issues: list[str] = []
    for entry in registry.get("baselines", []):
        cohort = _cohort_for_entry(entry)
        summary_path = baselines_dir / entry.get("summary_path", "")
        if not summary_path.exists():
            issues.append(f"missing summary file for entry {entry.get('id')}: {summary_path}")
            continue
        summary = _load_summary(summary_path)
        if summary is None:
            issues.append(f"unreadable summary file for entry {entry.get('id')}: {summary_path}")
            continue
        cohort_buckets[cohort].append(
            {
                "id": entry.get("id"),
                "kind": entry.get("kind"),
                "model_family": entry.get("model_family"),
                "harness_type": entry.get("expected_harness_type") or summary.get("harness_type"),
                "release_suitability": entry.get("release_suitability"),
                "run_count": entry.get("run_count", 1),
                "run_summaries": [summary],
                "summary_path": str(summary_path.relative_to(baselines_dir)),
            }
        )
        # If the registry entry lists additional run_artifacts, load them all
        # so the variance math actually has n=run_count data points.
        for run_path in entry.get("run_artifacts", []):
            additional = baselines_dir / run_path
            if additional == summary_path:
                continue
            additional_summary = _load_summary(additional)
            if additional_summary is None:
                issues.append(
                    f"missing/unreadable run artifact for entry {entry.get('id')}: {additional}"
                )
                continue
            cohort_buckets[cohort][-1]["run_summaries"].append(additional_summary)

    cohorts: dict[str, Any] = {}
    for cohort, entries in cohort_buckets.items():
        cohort_record: dict[str, Any] = {
            "cohort": cohort,
            "entry_count": len(entries),
            "capability_baseline": cohort in {"current-model", "current-tool-agent"},
            "entries": [],
        }
        for entry in entries:
            run_summaries = entry["run_summaries"]
            run_count = max(entry["run_count"], len(run_summaries))
            metric_runs: dict[str, list[float]] = defaultdict(list)
            for run in run_summaries:
                for key in SUMMARY_KEYS_FOR_PASS_RATE:
                    if key in run and isinstance(run[key], (int, float)):
                        metric_runs[key].append(float(run[key]))
            metric_variance: dict[str, Any] = {}
            for key, values in metric_runs.items():
                ci = _ci95(values)
                if ci is None:
                    metric_variance[key] = {
                        "mean": values[0] if values else None,
                        "std_dev": None,
                        "std_error": None,
                        "ci95_half_width": None,
                        "ci95_low": None,
                        "ci95_high": None,
                        "small_n_warning": f"n={len(values)}: variance undefined",
                    }
                    continue
                mean, std_dev, std_error, half_width = ci
                metric_variance[key] = {
                    "mean": round(mean, 4),
                    "std_dev": round(std_dev, 4),
                    "std_error": round(std_error, 4),
                    "ci95_low": round(mean - half_width, 4),
                    "ci95_high": round(mean + half_width, 4),
                    "ci95_half_width": round(half_width, 4),
                    "small_n_warning": _small_n_warning(len(values)),
                }
            cohort_record["entries"].append(
                {
                    "id": entry["id"],
                    "kind": entry["kind"],
                    "model_family": entry["model_family"],
                    "harness_type": entry["harness_type"],
                    "release_suitability": entry["release_suitability"],
                    "run_count": run_count,
                    "metric_variance": metric_variance,
                    "per_task_agreement": _agreement_rate(
                        [_per_task_verdicts(run) for run in run_summaries]
                    ),
                    "summary_path": entry["summary_path"],
                }
            )
        cohorts[cohort] = cohort_record

    capability_baseline_status = "current"
    capability_baseline_disclosure: str | None = None

    if require_current_public:
        missing_cohorts = []
        for cohort_name in ("current-model", "current-tool-agent"):
            cohort = cohorts.get(cohort_name, {})
            if not cohort.get("entries"):
                missing_cohorts.append(cohort_name)

        if missing_cohorts and allow_stale_pending_rerun:
            has_sanity_63 = _has_current_63_scripted_sanity(registry)
            all_stale = _all_capability_rows_stale_pending(registry)
            if has_sanity_63 and all_stale:
                capability_baseline_status = "stale_pending_current_policy_rerun"
                capability_baseline_disclosure = (
                    "No current score-policy-v3 model/tool-agent capability baselines "
                    "exist. Every tracked model/tool-agent row is historical or stale "
                    "(requires_rerun_before_current_comparison=true and "
                    "leaderboard_eligible=false), including the prior 63-task "
                    "score-policy-v2 rows. A current 63-task score-policy-v3 scripted "
                    "sanity row validates manifest/scorer/runner wiring but is not a "
                    "model result. Fresh exact-source model/tool-agent runs are required "
                    "to restore current capability evidence."
                )
            else:
                if not has_sanity_63:
                    issues.append(
                        "missing current 63-task scripted sanity row for "
                        "--allow-stale-pending-rerun"
                    )
                if not all_stale:
                    issues.append(
                        "not all model/tool-agent rows are honestly stale pending "
                        "rerun for --allow-stale-pending-rerun"
                    )
                for cohort_name in missing_cohorts:
                    issues.append(f"missing required {cohort_name} cohort for --require-current-public")
        elif missing_cohorts:
            for cohort_name in missing_cohorts:
                issues.append(f"missing required {cohort_name} cohort for --require-current-public")

    return {
        "schema_version": "baseline-variance-v1",
        "registry_path": str(REGISTRY_PATH.relative_to(ROOT)),
        "cohorts": cohorts,
        "issues": issues,
        "capability_baseline_status": capability_baseline_status,
        "capability_baseline_disclosure": capability_baseline_disclosure,
        "summary": {
            "current_model_entries": len(cohorts.get("current-model", {}).get("entries", [])),
            "current_tool_agent_entries": len(cohorts.get("current-tool-agent", {}).get("entries", [])),
            "scripted_sanity_entries": len(cohorts.get("scripted-sanity", {}).get("entries", [])),
            "stale_entries": len(cohorts.get("stale", {}).get("entries", [])),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Baseline variance and confidence")
    lines.append("")
    lines.append(
        "This document is generated by `python3 scripts/analyze_baseline_variance.py`."
        " It joins each registry entry to its per-run summary file and reports"
        " variance, standard error, 95% CI, and per-task agreement for every metric"
        " carried in the summary. The variance is real signal only when"
        " `run_count >= 2`."
    )
    lines.append("")
    lines.append("## Cohort summary")
    lines.append("")
    lines.append("| Cohort | Entries | Capability baseline? |")
    lines.append("| --- | --- | --- |")
    for cohort, record in report["cohorts"].items():
        lines.append(
            f"| `{cohort}` | {record['entry_count']} | "
            f"{'yes' if record['capability_baseline'] else 'no'} |"
        )
    lines.append("")
    disclosure = report.get("capability_baseline_disclosure")
    if disclosure:
        status = report.get("capability_baseline_status", "current")
        lines.append(f"**Capability baseline status:** `{status}`")
        lines.append("")
        lines.append(f"> {disclosure}")
        lines.append("")
    lines.append("## Per-entry variance")
    for cohort, record in report["cohorts"].items():
        if not record["entries"]:
            continue
        lines.append("")
        lines.append(f"### Cohort: `{cohort}`")
        lines.append("")
        for entry in record["entries"]:
            lines.append(f"#### `{entry['id']}`")
            lines.append("")
            lines.append(f"- kind: `{entry['kind']}`")
            lines.append(f"- harness_type: `{entry['harness_type']}`")
            lines.append(f"- model_family: `{entry['model_family']}`")
            lines.append(f"- release_suitability: `{entry['release_suitability']}`")
            lines.append(f"- run_count: {entry['run_count']}")
            lines.append(f"- summary_path: `{entry['summary_path']}`")
            lines.append("")
            agreement = entry["per_task_agreement"]
            if agreement["task_count"]:
                lines.append(
                    f"- per-task agreement: {agreement['agreement_rate']:.2%}"
                    f" over {agreement['task_count']} tasks,"
                    f" {agreement['changed_verdict_count']} changed verdicts"
                )
            else:
                lines.append(
                    "- per-task agreement: not available"
                    " (per-task verdicts are not in the public-safe summary schema)"
                )
            lines.append("")
            for metric, stats in entry["metric_variance"].items():
                if stats["mean"] is None:
                    continue
                if stats["std_dev"] is None:
                    line = f"- {metric}: mean={stats['mean']:.4f}, std_dev=undefined (n<2)"
                else:
                    line = (
                        f"- {metric}: mean={stats['mean']:.4f},"
                        f" std_dev={stats['std_dev']:.4f},"
                        f" 95% CI=[{stats['ci95_low']:.4f}, {stats['ci95_high']:.4f}]"
                    )
                if stats["small_n_warning"]:
                    line += f"  _{stats['small_n_warning']}_"
                lines.append(line)
    if report["issues"]:
        lines.append("")
        lines.append("## Issues")
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    return "\n".join(lines) + "\n"


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument(
        "--require-current-public",
        action="store_true",
        help="Fail when the report has no current-model or current-tool-agent entries.",
    )
    parser.add_argument(
        "--allow-stale-pending-rerun",
        action="store_true",
        help=(
            "With --require-current-public, pass when no current-policy "
            "model/tool-agent cohorts exist but a current 63-task scripted sanity "
            "row exists and all model/tool-agent rows are honestly stale pending "
            "rerun. Does not weaken the claim boundary; adds an explicit "
            "stale_pending_current_policy_rerun disclosure to the report."
        ),
    )
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    registry = json.loads((root / REGISTRY_PATH.relative_to(ROOT)).read_text(encoding="utf-8"))
    baselines_dir = root / BASELINES_DIR.relative_to(ROOT)
    json_output = args.json_output if args.json_output.is_absolute() else root / args.json_output
    md_output = args.markdown_output if args.markdown_output.is_absolute() else root / args.markdown_output

    report = analyze_registry(
        registry,
        baselines_dir=baselines_dir,
        require_current_public=args.require_current_public,
        allow_stale_pending_rerun=args.allow_stale_pending_rerun,
    )

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(render_markdown(report), encoding="utf-8")

    if report["issues"] and args.require_current_public:
        print("baseline variance: FAILED", file=sys.stderr)
        for issue in report["issues"]:
            print(f"  - {issue}", file=sys.stderr)
        return 1
    print(
        f"baseline variance: wrote {_display_path(json_output, root)} and"
        f" {_display_path(md_output, root)}; cohorts={list(report['cohorts'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
