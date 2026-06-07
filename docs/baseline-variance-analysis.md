# Baseline Variance Analysis

Status: descriptive two-run analysis from current v1-prep 49-task public
no-tools artifacts plus the frozen v0.0 46-task release snapshot. These ranges
are diagnostic public-split evidence only, not confidence intervals, private
holdout evidence, or leaderboard rankings.

This file uses only tracked public-safe summaries named by
`baselines/baseline-registry.json`. Each row below has exactly two runs.

## Artifact Set

### Current v1-prep 49-task public split

| Baseline family | Harness | Model | Source summaries |
| --- | --- | --- | --- |
| `kiro-claude-haiku-4-5-current-public-49` | `no-tools-model` | `claude-haiku-4.5` | `kiro-claude-haiku-4.5-current-public-49-run1-summary.json`; `kiro-claude-haiku-4.5-current-public-49-run2-summary.json` |
| `kiro-claude-sonnet-4-6-current-public-49` | `no-tools-model` | `claude-sonnet-4.6` | `kiro-claude-sonnet-4.6-current-public-49-run1-summary.json`; `kiro-claude-sonnet-4.6-current-public-49-run2-summary.json` |
| `kiro-qwen3-coder-next-current-public-49` | `no-tools-model` | `qwen3-coder-next` | `kiro-qwen3-coder-next-current-public-49-run1-summary.json`; `kiro-qwen3-coder-next-current-public-49-run2-summary.json` |
| `kiro-glm-5-current-public-49` | `no-tools-model` | `glm-5` | `kiro-glm-5-current-public-49-run1-summary.json`; `kiro-glm-5-current-public-49-run2-summary.json` |
| `kiro-claude-opus-4-6-current-public-49` | `no-tools-model` | `claude-opus-4.6` | `kiro-claude-opus-4.6-current-public-49-run1-summary.json`; `kiro-claude-opus-4.6-current-public-49-run2-summary.json` |

### Frozen v0.0 46-task release snapshot

| Baseline family | Harness | Model | Source summaries |
| --- | --- | --- | --- |
| `kiro-qwen3-coder-next-current-public-46` | `no-tools-model` | `qwen3-coder-next` | `kiro-qwen3-coder-next-current-public-46-run1-summary.json`; `kiro-qwen3-coder-next-current-public-46-run2-summary.json` |
| `kiro-claude-haiku-4-5-current-public-46` | `no-tools-model` | `claude-haiku-4.5` | `kiro-claude-haiku-4.5-current-public-46-run1-summary.json`; `kiro-claude-haiku-4.5-current-public-46-run2-summary.json` |
| `kiro-claude-sonnet-4-6-current-public-46` | `no-tools-model` | `claude-sonnet-4.6` | `kiro-claude-sonnet-4.6-current-public-46-run1-summary.json`; `kiro-claude-sonnet-4.6-current-public-46-run2-summary.json` |
| `kiro-glm-5-current-public-46` | `no-tools-model` | `glm-5` | `kiro-glm-5-current-public-46-run1-summary.json`; `kiro-glm-5-current-public-46-run2-summary.json` |
| `kiro-live-tool-agent-sonnet-current-public-46` | `tool-agent` | `claude-sonnet-4.6` | `kiro-live-tool-agent-sonnet-current-public-46-summary.json`; `kiro-live-tool-agent-sonnet-current-public-46-run2-summary.json` |

## Two-Run Metric Ranges

### Current v1-prep 49-task public split

| Baseline family | `mean_score` | `exploit_proven_success_rate` | `vulnerable_full_pass_count` | `boundary_reasoning_pass_rate` | `false_positive_rate` | `invalid_submission_rate` | `target_request_coverage_rate` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude Haiku no-tools | 0.6622-0.7020 | 0.1500-0.3000 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |
| Claude Sonnet no-tools | 0.6592-0.6653 | 0.2000-0.2000 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |
| Qwen no-tools | 0.5990-0.6224 | 0.0500-0.1000 | 0-0 | 0.0000-0.0000 | 0.0000-0.0345 | 0.0000-0.0000 | n/a |
| GLM no-tools | 0.6082-0.6439 | 0.1000-0.1500 | 0-0 | 0.0000-0.0000 | 0.0000-0.0345 | 0.0204-0.0408 | n/a |
| Claude Opus no-tools | 0.7724-0.7847 | 0.5500-0.5500 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |

### Frozen v0.0 46-task release snapshot

| Baseline family | `v0_mean_score` | `exploit_proven_success_rate` | `vulnerable_full_pass_count` | `boundary_reasoning_pass_rate` | `false_positive_rate` | `invalid_submission_rate` | `target_request_coverage_rate` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen no-tools | 0.5870-0.5870 | 0.0000-0.0526 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0217 | n/a |
| Claude Haiku no-tools | 0.5652-0.5870 | 0.0526-0.2632 | 0-0 | 0.0000-0.0000 | 0.0000-0.0370 | 0.0000-0.0000 | n/a |
| Claude Sonnet no-tools | 0.5652-0.5870 | 0.4211-0.6316 | 0-0 | 0.0000-0.0000 | 0.0000-0.0370 | 0.0000-0.0000 | n/a |
| GLM no-tools | 0.5870-0.5870 | 0.0526-0.2105 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |
| Claude Sonnet live tool-agent | 0.5870-0.5870 | 0.7368-0.7368 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | 1.0000-1.0000 |

## Interpretation

The current 49-task no-tools public runs now clear the five-family repeat
evidence gate, but they do not close the current tool-agent gate. All five
current no-tools families record zero vulnerable full passes because boundary
reasoning remains at `0.0000`. Opus is the strongest public no-tools replay
signal in this pair, proving 11 of 20 vulnerable tasks in both runs
(`0.5500` exploit-proven success) with zero false positives, but it still does
not satisfy the full vulnerable-task scoring contract.

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
success), and current Opus no-tools proves 11 of 20 vulnerable public tasks in
both runs, yet both still record zero vulnerable full passes because boundary
reasoning remains at `0.0000`.

## Reproduction Notes

The table was recomputed by reading `baselines/baseline-registry.json`,
selecting current public split no-tools model baselines plus the five entries in
the `v0.0` release snapshot, and loading each entry's `run_artifacts` from
`baselines/`.

Useful checks:

```bash
python3 scripts/validate_baseline_registry.py
python3 - <<'PY'
import json
from pathlib import Path
registry = json.loads(Path("baselines/baseline-registry.json").read_text())
current = [
    entry
    for entry in registry["baselines"]
    if entry["release_suitability"] == "current_public_split"
    and entry["kind"] == "model_baseline"
]
snapshot = next(item for item in registry["release_snapshots"] if item["id"] == "v0.0")
print(len(current))
print(len([
    baseline_id
    for baseline_id in snapshot["baseline_ids"]
    if baseline_id != "scripted-sanity-public-46"
]))
PY
```

Expected counts: `5` current public no-tools model families and `5` frozen
v0.0 repeated model/agent families.

Recompute this file after any task-count, scoring-contract, baseline-registry,
or run-artifact change. Mark older 46-task ranges stale before comparing them
with a changed task set; the `v0.0` release snapshot remains historical evidence,
not current/v1 comparison evidence.
