# Baseline Variance Analysis

Status: descriptive two-run analysis from the historical v1-prep 49-task public
no-tools and live HTTP tool-agent artifacts plus the frozen v0.0 46-task release
snapshot. These ranges are diagnostic public-split evidence only, not confidence
intervals, private holdout evidence, or leaderboard rankings. The 49-task rows
are stale for the active 54-task split.

This file uses only tracked public-safe summaries named by
`baselines/baseline-registry.json`. Each row below has exactly two runs.

## Artifact Set

### Historical v1-prep 49-task public split

| Baseline family | Harness | Model | Source summaries |
| --- | --- | --- | --- |
| `kiro-claude-haiku-4-5-current-public-49` | `no-tools-model` | `claude-haiku-4.5` | `kiro-claude-haiku-4.5-current-public-49-run1-summary.json`; `kiro-claude-haiku-4.5-current-public-49-run2-summary.json` |
| `kiro-claude-sonnet-4-6-current-public-49` | `no-tools-model` | `claude-sonnet-4.6` | `kiro-claude-sonnet-4.6-current-public-49-run1-summary.json`; `kiro-claude-sonnet-4.6-current-public-49-run2-summary.json` |
| `kiro-qwen3-coder-next-current-public-49` | `no-tools-model` | `qwen3-coder-next` | `kiro-qwen3-coder-next-current-public-49-run1-summary.json`; `kiro-qwen3-coder-next-current-public-49-run2-summary.json` |
| `kiro-glm-5-current-public-49` | `no-tools-model` | `glm-5` | `kiro-glm-5-current-public-49-run1-summary.json`; `kiro-glm-5-current-public-49-run2-summary.json` |
| `kiro-claude-opus-4-6-current-public-49` | `no-tools-model` | `claude-opus-4.6` | `kiro-claude-opus-4.6-current-public-49-run1-summary.json`; `kiro-claude-opus-4.6-current-public-49-run2-summary.json` |
| `kiro-live-tool-agent-sonnet-current-public-49` | `tool-agent` | `claude-sonnet-4.6` | `kiro-live-tool-agent-sonnet-current-public-49-run1-summary.json`; `kiro-live-tool-agent-sonnet-current-public-49-run2-summary.json` |

### Frozen v0.0 46-task release snapshot

| Baseline family | Harness | Model | Source summaries |
| --- | --- | --- | --- |
| `kiro-qwen3-coder-next-current-public-46` | `no-tools-model` | `qwen3-coder-next` | `kiro-qwen3-coder-next-current-public-46-run1-summary.json`; `kiro-qwen3-coder-next-current-public-46-run2-summary.json` |
| `kiro-claude-haiku-4-5-current-public-46` | `no-tools-model` | `claude-haiku-4.5` | `kiro-claude-haiku-4.5-current-public-46-run1-summary.json`; `kiro-claude-haiku-4.5-current-public-46-run2-summary.json` |
| `kiro-claude-sonnet-4-6-current-public-46` | `no-tools-model` | `claude-sonnet-4.6` | `kiro-claude-sonnet-4.6-current-public-46-run1-summary.json`; `kiro-claude-sonnet-4.6-current-public-46-run2-summary.json` |
| `kiro-glm-5-current-public-46` | `no-tools-model` | `glm-5` | `kiro-glm-5-current-public-46-run1-summary.json`; `kiro-glm-5-current-public-46-run2-summary.json` |
| `kiro-live-tool-agent-sonnet-current-public-46` | `tool-agent` | `claude-sonnet-4.6` | `kiro-live-tool-agent-sonnet-current-public-46-summary.json`; `kiro-live-tool-agent-sonnet-current-public-46-run2-summary.json` |

## Two-Run Metric Ranges

### Historical v1-prep 49-task public split

| Baseline family | `mean_score` | `exploit_proven_success_rate` | `vulnerable_full_pass_count` | `boundary_reasoning_pass_rate` | `false_positive_rate` | `invalid_submission_rate` | `target_request_coverage_rate` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude Haiku no-tools | 0.6622-0.7020 | 0.1500-0.3000 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |
| Claude Sonnet no-tools | 0.6592-0.6653 | 0.2000-0.2000 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |
| Qwen no-tools | 0.5990-0.6224 | 0.0500-0.1000 | 0-0 | 0.0000-0.0000 | 0.0000-0.0345 | 0.0000-0.0000 | n/a |
| GLM no-tools | 0.6082-0.6439 | 0.1000-0.1500 | 0-0 | 0.0000-0.0000 | 0.0000-0.0345 | 0.0204-0.0408 | n/a |
| Claude Opus no-tools | 0.7724-0.7847 | 0.5500-0.5500 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |
| Claude Sonnet live tool-agent | 0.8500-0.8520 | 0.7500-0.7500 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | 1.0000-1.0000 |

### Frozen v0.0 46-task release snapshot

| Baseline family | `v0_mean_score` | `exploit_proven_success_rate` | `vulnerable_full_pass_count` | `boundary_reasoning_pass_rate` | `false_positive_rate` | `invalid_submission_rate` | `target_request_coverage_rate` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen no-tools | 0.5870-0.5870 | 0.0000-0.0526 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0217 | n/a |
| Claude Haiku no-tools | 0.5652-0.5870 | 0.0526-0.2632 | 0-0 | 0.0000-0.0000 | 0.0000-0.0370 | 0.0000-0.0000 | n/a |
| Claude Sonnet no-tools | 0.5652-0.5870 | 0.4211-0.6316 | 0-0 | 0.0000-0.0000 | 0.0000-0.0370 | 0.0000-0.0000 | n/a |
| GLM no-tools | 0.5870-0.5870 | 0.0526-0.2105 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |
| Claude Sonnet live tool-agent | 0.5870-0.5870 | 0.7368-0.7368 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | 1.0000-1.0000 |

## Interpretation

The 49-task public runs cleared the five-family no-tools repeat evidence gate
and the repeated live HTTP tool-agent gate for that fingerprint. All five
no-tools families and the live tool-agent family record zero vulnerable
full passes because boundary reasoning remains at `0.0000`. Opus is the
strongest public no-tools replay signal in this pair, proving 11 of 20
vulnerable tasks in both runs (`0.5500` exploit-proven success) with zero false
positives. The 49-task live tool-agent proves 15 of 20 vulnerable tasks in both
runs (`0.7500` exploit-proven success), records zero false positives, and has
1.0000 target-request coverage in both runs, but it still does not satisfy the
full vulnerable-task scoring contract.

The repeated frozen v0.0 public runs show stable false-positive behavior,
stable authorized-allow behavior, and zero vulnerable full-pass counts across
these families. Exploit proof varies meaningfully for several no-tools
families: Claude Haiku and Claude Sonnet each span roughly 0.21
exploit-proven success rate, GLM spans roughly 0.16, and Qwen spans roughly
0.05. The frozen v0.0 live tool-agent runs are stable on exploit proof and
target-request coverage in this pair.

The central research signal is not a model ranking. It is the gap between
exploit replay and boundary reasoning: the frozen v0.0 live tool-agent proves
14 of 19 vulnerable public tasks in both runs (`0.7368` exploit-proven
success), the 49-task live tool-agent proves 15 of 20 vulnerable public tasks in
both runs (`0.7500` exploit-proven success), and 49-task Opus no-tools proves 11
of 20 vulnerable public tasks in both runs, yet all still record zero vulnerable
full passes because boundary reasoning remains at `0.0000`.

## Reproduction Notes

The table was recomputed by reading `baselines/baseline-registry.json`,
selecting the stale 49-task model and tool-agent baselines plus the five
non-scripted entries in the `v0.0` release snapshot, and loading each entry's
`run_artifacts` from `baselines/`.

Useful checks:

```bash
python3 scripts/validate_baseline_registry.py
python3 - <<'PY'
import json
from pathlib import Path
registry = json.loads(Path("baselines/baseline-registry.json").read_text())
stale_49 = [
    entry
    for entry in registry["baselines"]
    if entry["release_suitability"] == "current_public_stale"
    and entry.get("expected_task_count") == 49
    and entry["kind"] in {"model_baseline", "tool_agent_baseline"}
]
snapshot = next(item for item in registry["release_snapshots"] if item["id"] == "v0.0")
print(len(stale_49))
print(len([
    baseline_id
    for baseline_id in snapshot["baseline_ids"]
    if baseline_id != "scripted-sanity-public-46"
]))
PY
```

Expected counts: `6` stale 49-task model/agent families and `5` frozen v0.0
repeated model/agent families.

Recompute this file after any task-count, scoring-contract, baseline-registry,
or run-artifact change. Mark older 46-task ranges stale before comparing them
with a changed task set; the `v0.0` release snapshot remains historical evidence,
not current/v1 comparison evidence.
