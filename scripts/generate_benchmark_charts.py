from __future__ import annotations

import json
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets" / "benchmark-charts"

COLORS = {
    "navy": "#0b1f4d",
    "teal": "#2ea8a1",
    "blue": "#2f7de1",
    "orange": "#f59e0b",
    "green": "#2f9e44",
    "red": "#d9480f",
    "gray": "#64748b",
    "light": "#f6f8fb",
    "line": "#d8dee9",
    "text": "#172033",
    "muted": "#5b667a",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def text(x: float, y: float, value: str, *, size: int = 13, color: str = "text", weight: str = "400") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{COLORS[color]}" '
        f'font-family="Inter, Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}">{escape(value)}</text>'
    )


def rect(x: float, y: float, w: float, h: float, fill: str, *, rx: int = 3) -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"/>'


def svg(title: str, subtitle: str, width: int, height: int, body: list[str]) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{escape(title)}</title>",
        f"<desc id=\"desc\">{escape(subtitle)}</desc>",
        rect(0, 0, width, height, "#ffffff", rx=0),
        rect(18, 18, width - 36, height - 36, COLORS["light"], rx=8),
        text(36, 54, title, size=22, color="navy", weight="700"),
        text(36, 78, subtitle, size=12, color="muted"),
        *body,
        text(36, height - 24, "Source: tracked AuthZBench-SaaS baseline and redacted evidence JSON. Public-split evidence is not leaderboard ranking.", size=11, color="muted"),
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def baseline_rows(registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in registry["baselines"]:
        if entry["release_suitability"] not in {"current_public_split", "current_public_stale"}:
            continue
        if entry["kind"] not in {"model_baseline", "tool_agent_baseline"}:
            continue
        artifact_names = entry.get("run_artifacts") or [entry["summary_path"]]
        artifacts = [load_json(ROOT / "baselines" / name) for name in artifact_names]
        model = str(entry.get("expected_model") or entry["id"])
        label = {
            "claude-sonnet-4.6": "Claude Sonnet 4.6",
            "claude-opus-4.6": "Claude Opus 4.6",
            "claude-haiku-4.5": "Claude Haiku 4.5",
            "deepseek-3.2": "DeepSeek 3.2",
            "Gemini 3.1 Pro (High)": "Gemini 3.1 Pro",
            "glm-5": "GLM-5",
            "qwen3-coder-next": "Qwen3 Coder Next",
        }.get(model, model)
        if entry["kind"] == "tool_agent_baseline":
            label = f"Tool agent: {label}"
        row = {
            "id": entry["id"],
            "label": label,
            "kind": entry["kind"],
            "harness_type": entry.get("expected_harness_type"),
            "release_suitability": entry["release_suitability"],
            "requires_rerun_before_current_comparison": bool(
                entry.get("requires_rerun_before_current_comparison")
            ),
            "run_count": len(artifacts),
            "task_count": artifacts[0]["task_count"],
            "pass_rate": mean(item["passed_count"] / item["task_count"] for item in artifacts),
            "exploit_proven_success_rate": mean(item["exploit_proven_success_rate"] for item in artifacts),
            "false_positive_rate": mean(item["false_positive_rate"] for item in artifacts),
            "boundary_reasoning_pass_rate": mean(item["boundary_reasoning_pass_rate"] for item in artifacts),
            "target_request_coverage_rate": mean(
                item["target_request_coverage_rate"]
                for item in artifacts
                if isinstance(item.get("target_request_coverage_rate"), (int, float))
            )
            if any(isinstance(item.get("target_request_coverage_rate"), (int, float)) for item in artifacts)
            else None,
        }
        rows.append(row)
    rows.sort(
        key=lambda item: (
            item["release_suitability"] == "current_public_stale",
            item["kind"] != "tool_agent_baseline",
            -item["exploit_proven_success_rate"],
            item["label"],
        )
    )
    return rows


def grouped_metric_chart(rows: list[dict[str, Any]]) -> str:
    width = 1380
    row_h = 62
    height = 138 + len(rows) * row_h
    left = 430
    metric_gap = 205
    bar_width = 128
    metrics = [
        ("pass_rate", "Pass", COLORS["teal"]),
        ("exploit_proven_success_rate", "Exploit proof", COLORS["blue"]),
        ("boundary_reasoning_pass_rate", "Boundary", COLORS["orange"]),
        ("false_positive_rate", "False positive (lower is better)", COLORS["red"]),
    ]
    body: list[str] = []
    y0 = 118
    if not rows:
        body.append(text(36, 140, "No current public model/tool-agent baseline rows are tracked yet.", size=14, color="text", weight="600"))
        body.append(text(36, 164, "Rerun model and tool-agent baselines before using this chart for comparison.", size=12, color="muted"))
        return svg(
            "Public Baseline Metrics",
            "No current model/tool-agent comparison rows are available; not private leaderboard results.",
            width,
            height + 70,
            body,
        )
    for i, (_, label, color) in enumerate(metrics):
        x = left + i * metric_gap
        body.append(rect(x, 94, 12, 12, color, rx=2))
        body.append(text(x + 18, 105, label, size=12, color="muted"))
    for idx, row in enumerate(rows):
        y = y0 + idx * row_h
        is_stale = row["release_suitability"] == "current_public_stale"
        status = "current split" if not is_stale else f'stale {row["task_count"]}-task split; rerun required'
        label = row["label"] if not is_stale else f'{row["label"]} (stale)'
        body.append(text(36, y + 22, label, size=13, color="gray" if is_stale else "text", weight="600"))
        body.append(text(36, y + 40, f'{row["kind"].replace("_", " ")}; {row["run_count"]} run(s); {status}', size=11, color="muted"))
        for i, (key, _, color) in enumerate(metrics):
            value = float(row[key])
            x = left + i * metric_gap
            fill = COLORS["gray"] if is_stale else color
            body.append(rect(x, y + 12, bar_width, 12, "#e6ebf2", rx=3))
            body.append(rect(x, y + 12, bar_width * min(value, 1.0), 12, fill, rx=3))
            body.append(text(x, y + 34, fmt_pct(value), size=11, color="muted"))
    return svg(
        "Public Baseline Metrics",
        "Current rows plus stale public-split snapshots where rerun is required; not private leaderboard results.",
        width,
        height,
        body,
    )


def focused_metric_chart(
    rows: list[dict[str, Any]],
    *,
    metric_key: str,
    title: str,
    subtitle: str,
    explanation: str,
    color_key: str,
    lower_is_better: bool = False,
) -> str:
    width = 980
    row_h = 54
    height = 164 + max(len(rows), 1) * row_h
    label_x = 42
    bar_x = 430
    bar_width = 260
    body: list[str] = [
        text(label_x, 104, explanation, size=12, color="muted"),
        text(bar_x, 130, "0%", size=11, color="muted"),
        text(bar_x + bar_width - 26, 130, "100%", size=11, color="muted"),
    ]
    if lower_is_better:
        body.append(text(bar_x + bar_width + 86, 130, "lower is better", size=11, color="muted"))
    if not rows:
        body.append(text(label_x, 156, "No current public baseline rows are tracked yet.", size=14, color="text", weight="600"))
        return svg(title, subtitle, width, height + 50, body)
    for idx, row in enumerate(rows):
        y = 152 + idx * row_h
        value = float(row[metric_key])
        is_stale = row["release_suitability"] == "current_public_stale"
        label = row["label"] if not is_stale else f'{row["label"]} (stale)'
        status = f'current {row["task_count"]}-task split' if not is_stale else f'stale {row["task_count"]}-task split'
        fill = COLORS["gray"] if is_stale else COLORS[color_key]
        body.append(text(label_x, y + 4, label, size=13, color="gray" if is_stale else "text", weight="600"))
        body.append(text(label_x, y + 22, status, size=11, color="muted"))
        body.append(rect(bar_x, y - 10, bar_width, 14, "#e6ebf2", rx=3))
        body.append(rect(bar_x, y - 10, bar_width * min(value, 1.0), 14, fill, rx=3))
        body.append(text(bar_x + bar_width + 18, y + 2, fmt_pct(value), size=13, color="text", weight="700"))
    return svg(title, subtitle, width, height, body)


def task_mix_chart(public_split: dict[str, Any], private_summaries: list[dict[str, Any]]) -> str:
    width = 920
    height = 360
    body: list[str] = []
    rows = [
        {
            "label": "Public development split",
            "total": public_split["task_count"],
            "vulnerable": public_split["vulnerable_task_count"],
            "denial": public_split["denial_control_task_count"],
            "allow": public_split["authorized_allow_control_task_count"],
        }
    ]
    if private_summaries:
        first = private_summaries[0]
        rows.append(
            {
                "label": "Private holdout evidence",
                "total": first["private_holdout_task_count"],
                "vulnerable": first["vulnerable_task_count"],
                "denial": first["denial_control_task_count"],
                "allow": first["authorized_allow_control_task_count"],
            }
        )
    x0 = 260
    max_total = max(row["total"] for row in rows)
    colors = [("vulnerable", "Vulnerable", COLORS["blue"]), ("denial", "Denial controls", COLORS["teal"]), ("allow", "Authorized-allow controls", COLORS["orange"])]
    for i, (_, label, color) in enumerate(colors):
        x = 260 + i * 170
        body.append(rect(x, 96, 12, 12, color, rx=2))
        body.append(text(x + 18, 107, label, size=12, color="muted"))
    for idx, row in enumerate(rows):
        y = 140 + idx * 84
        body.append(text(36, y + 19, row["label"], size=14, color="text", weight="600"))
        body.append(text(36, y + 39, f'{row["total"]} tasks', size=12, color="muted"))
        x = x0
        for key, _, color in colors:
            segment = 520 * (row[key] / max_total)
            body.append(rect(x, y + 8, segment, 26, color, rx=2))
            if segment > 42:
                body.append(text(x + 8, y + 26, str(row[key]), size=12, color="light", weight="700"))
            x += segment
        body.append(text(x + 12, y + 27, f'total {row["total"]}', size=12, color="muted"))
    return svg(
        "Task Mix",
        "Public task mix plus redacted private-holdout count evidence; private task bodies are not included.",
        width,
        height,
        body,
    )


def validate_private_summaries(private_summaries: list[dict[str, Any]]) -> None:
    if not private_summaries:
        return
    required_flags = {
        "redacted_private_holdout_source": True,
        "raw_private_artifacts_tracked": False,
        "tracked_private_manifest_count": 0,
    }
    expected_mix = {
        key: private_summaries[0].get(key)
        for key in (
            "private_holdout_task_count",
            "vulnerable_task_count",
            "control_task_count",
            "denial_control_task_count",
            "authorized_allow_control_task_count",
        )
    }
    for index, summary in enumerate(private_summaries, start=1):
        for key, expected in required_flags.items():
            if summary.get(key) != expected:
                raise ValueError(f"private summary {index} is not public-safe: {key}={summary.get(key)!r}")
        observed_mix = {key: summary.get(key) for key in expected_mix}
        if observed_mix != expected_mix:
            raise ValueError("redacted private summaries have inconsistent task mix; chart generation needs an explicit aggregation policy")


def evidence_status_chart(registry: dict[str, Any], private_summaries: list[dict[str, Any]]) -> str:
    public = registry["public_split"]
    tool_entries = [entry for entry in registry["baselines"] if entry["kind"] == "tool_agent_baseline" and entry["release_suitability"] == "current_public_split"]
    stale_tool_entries = [entry for entry in registry["baselines"] if entry["kind"] == "tool_agent_baseline" and entry["release_suitability"] == "current_public_stale"]
    repeated_model_agent_families = {
        entry.get("model_family")
        for entry in registry["baselines"]
        if entry["kind"] in {"model_baseline", "tool_agent_baseline"}
        and entry["release_suitability"] == "current_public_split"
        and int(entry.get("run_count", 0)) >= int(registry.get("v0_requirements", {}).get("min_runs_per_serious_baseline", 2))
    }
    private_tool = [item for item in private_summaries if item.get("harness_type") == "tool-agent"]
    family_label = "family" if len(repeated_model_agent_families) == 1 else "families"
    tool_detail = (
        "Current public tool-agent summary with target correlation"
        if tool_entries
        else "Only stale public tool-agent evidence is tracked" if stale_tool_entries
        else "No public tool-agent summary tracked"
    )
    rows = [
        ("Public split validated", public["task_count"] >= 40, f'{public["task_count"]} public tasks across 6 apps'),
        (
            "Repeated model/agent families",
            len(repeated_model_agent_families) >= 5,
            f"{len(repeated_model_agent_families)} repeated current model/agent {family_label}",
        ),
        ("Public tool-agent baseline", bool(tool_entries), tool_detail),
        ("Protected private runs", len(private_summaries) >= 2, f"{len(private_summaries)} redacted protected-private summaries"),
        ("Private tool-agent coverage", bool(private_tool) and private_tool[0].get("target_request_coverage_rate") == 1.0, "Redacted private tool-agent summary reports 100% target coverage"),
        ("Hosted leaderboard service", False, "Planned; not claimed ready"),
        ("Independent third-party run", False, "Planned; not claimed complete"),
    ]
    width = 980
    height = 470
    body: list[str] = []
    for idx, (label, ready, detail) in enumerate(rows):
        y = 112 + idx * 48
        color = COLORS["green"] if ready else COLORS["gray"]
        status = "Ready evidence" if ready else "Not yet"
        body.append(rect(42, y - 17, 22, 22, color, rx=11))
        body.append(text(78, y, label, size=14, color="text", weight="600"))
        body.append(text(360, y, status, size=13, color="green" if ready else "gray", weight="700"))
        body.append(text(520, y, detail, size=12, color="muted"))
    return svg(
        "Evidence Readiness",
        "What existing public-safe artifacts support today, and what is still not claimed.",
        width,
        height,
        body,
    )


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    registry = load_json(ROOT / "baselines" / "baseline-registry.json")
    private_summaries = [
        load_json(path)
        for path in sorted(ROOT.glob("docs/protected-private*-2026-06-05.redacted.json"))
    ]
    validate_private_summaries(private_summaries)
    rows = baseline_rows(registry)
    baseline_sources: list[str] = ["baselines/baseline-registry.json"]
    for entry in registry["baselines"]:
        for artifact in entry.get("run_artifacts") or [entry.get("summary_path")]:
            if artifact:
                source = f"baselines/{artifact}"
                if source not in baseline_sources:
                    baseline_sources.append(source)
    chart_data = {
        "source_files": [
            *baseline_sources,
            *[str(path.relative_to(ROOT)) for path in sorted(ROOT.glob("docs/protected-private*-2026-06-05.redacted.json"))],
        ],
        "chart_files": [
            "current-public-baselines.svg",
            "model-pass-rate.svg",
            "exploit-proven-success.svg",
            "false-positive-rate.svg",
            "boundary-reasoning.svg",
            "task-mix.svg",
            "evidence-readiness.svg",
        ],
        "public_split": registry["public_split"],
        "public_baselines": rows,
        "private_redacted_evidence_count": len(private_summaries),
        "claim_boundary": "Charts summarize public-safe artifacts. Stale public baselines are historical only and are not hosted leaderboard rankings.",
    }
    write(ASSET_DIR / "current-public-baselines.svg", grouped_metric_chart(rows))
    write(
        ASSET_DIR / "model-pass-rate.svg",
        focused_metric_chart(
            rows,
            metric_key="pass_rate",
            title="Model Pass Rate",
            subtitle="Public-split pass rate from tracked baseline summaries; stale rows require rerun.",
            explanation="Overall pass rate mixes vulnerable tasks and secure controls, so it is not a leaderboard ranking by itself.",
            color_key="teal",
        ),
    )
    write(
        ASSET_DIR / "exploit-proven-success.svg",
        focused_metric_chart(
            rows,
            metric_key="exploit_proven_success_rate",
            title="Exploit-Proven Success",
            subtitle="How often vulnerable tasks had replayable exploit evidence in tracked public runs.",
            explanation="This measures proven vulnerable-task success, separate from merely avoiding false positives.",
            color_key="blue",
        ),
    )
    write(
        ASSET_DIR / "false-positive-rate.svg",
        focused_metric_chart(
            rows,
            metric_key="false_positive_rate",
            title="False-Positive Rate",
            subtitle="How often secure-control tasks were incorrectly reported as vulnerable.",
            explanation="Lower is better. A useful security agent must avoid inventing bugs when controls are working.",
            color_key="red",
            lower_is_better=True,
        ),
    )
    write(
        ASSET_DIR / "boundary-reasoning.svg",
        focused_metric_chart(
            rows,
            metric_key="boundary_reasoning_pass_rate",
            title="Boundary Reasoning",
            subtitle="How often reports correctly identified the tenant, role, token, or object boundary.",
            explanation="This separates real authorization reasoning from generic vulnerability language.",
            color_key="orange",
        ),
    )
    write(ASSET_DIR / "task-mix.svg", task_mix_chart(registry["public_split"], private_summaries))
    write(ASSET_DIR / "evidence-readiness.svg", evidence_status_chart(registry, private_summaries))
    write(ASSET_DIR / "chart-data.json", json.dumps(chart_data, indent=2, sort_keys=True) + "\n")
    write(
        ASSET_DIR / "README.md",
        "\n".join(
            [
                "# Benchmark Charts",
                "",
                "Generated public-safe charts for AuthZBench-SaaS.",
                "",
                "Regenerate with:",
                "",
                "```bash",
                "python3 scripts/generate_benchmark_charts.py",
                "```",
                "",
                "These charts summarize tracked public-split baselines and redacted",
                "private-evidence summaries. Stale public baselines need rerun before",
                "current comparison, and these charts are not hosted leaderboard rankings.",
                "",
                "Included charts:",
                "",
                "- `current-public-baselines.svg`: compact multi-metric overview",
                "- `model-pass-rate.svg`: model pass rate",
                "- `exploit-proven-success.svg`: vulnerable-task exploit proof",
                "- `false-positive-rate.svg`: secure-control false-positive rate",
                "- `boundary-reasoning.svg`: authorization-boundary reasoning",
                "- `task-mix.svg`: public and redacted private task mix",
                "- `evidence-readiness.svg`: current evidence gaps",
                "",
            ]
        ),
    )
    print(f"wrote charts to {ASSET_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
