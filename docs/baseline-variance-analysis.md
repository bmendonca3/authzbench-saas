# Baseline Variance Analysis

Status: descriptive two-run analysis from current public 46-task baseline
artifacts.

This file uses only tracked public-safe summaries named by
`baselines/baseline-registry.json` entries with
`release_suitability: current_public_split`. Each row below has exactly two
runs. These ranges are descriptive stability checks, not confidence intervals
and not private-holdout leaderboard evidence.

## Artifact Set

| Baseline family | Harness | Model | Source summaries |
| --- | --- | --- | --- |
| `kiro-qwen3-coder-next-current-public-46` | `no-tools-model` | `qwen3-coder-next` | `kiro-qwen3-coder-next-current-public-46-run1-summary.json`; `kiro-qwen3-coder-next-current-public-46-run2-summary.json` |
| `kiro-claude-haiku-4-5-current-public-46` | `no-tools-model` | `claude-haiku-4.5` | `kiro-claude-haiku-4.5-current-public-46-run1-summary.json`; `kiro-claude-haiku-4.5-current-public-46-run2-summary.json` |
| `kiro-claude-sonnet-4-6-current-public-46` | `no-tools-model` | `claude-sonnet-4.6` | `kiro-claude-sonnet-4.6-current-public-46-run1-summary.json`; `kiro-claude-sonnet-4.6-current-public-46-run2-summary.json` |
| `kiro-glm-5-current-public-46` | `no-tools-model` | `glm-5` | `kiro-glm-5-current-public-46-run1-summary.json`; `kiro-glm-5-current-public-46-run2-summary.json` |
| `kiro-live-tool-agent-sonnet-current-public-46` | `tool-agent` | `claude-sonnet-4.6` | `kiro-live-tool-agent-sonnet-current-public-46-summary.json`; `kiro-live-tool-agent-sonnet-current-public-46-run2-summary.json` |

## Two-Run Metric Ranges

| Baseline family | `v0_mean_score` | `exploit_proven_success_rate` | `vulnerable_full_pass_count` | `boundary_reasoning_pass_rate` | `false_positive_rate` | `invalid_submission_rate` | `target_request_coverage_rate` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen no-tools | 0.5870-0.5870 | 0.0000-0.0526 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0217 | n/a |
| Claude Haiku no-tools | 0.5652-0.5870 | 0.0526-0.2632 | 0-0 | 0.0000-0.0000 | 0.0000-0.0370 | 0.0000-0.0000 | n/a |
| Claude Sonnet no-tools | 0.5652-0.5870 | 0.4211-0.6316 | 0-0 | 0.0000-0.0000 | 0.0000-0.0370 | 0.0000-0.0000 | n/a |
| GLM no-tools | 0.5870-0.5870 | 0.0526-0.2105 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | n/a |
| Claude Sonnet live tool-agent | 0.5870-0.5870 | 0.7368-0.7368 | 0-0 | 0.0000-0.0000 | 0.0000-0.0000 | 0.0000-0.0000 | 1.0000-1.0000 |

## Interpretation

The repeated current public runs show stable false-positive behavior, stable
authorized-allow behavior, and zero vulnerable full-pass counts across these
families. Exploit proof varies meaningfully for several no-tools families:
Claude Haiku and Claude Sonnet each span roughly 0.21 exploit-proven success
rate, GLM spans roughly 0.16, and Qwen spans roughly 0.05. The live tool-agent
runs are stable on exploit proof and target-request coverage in this pair.

The central current research signal is not a model ranking. It is the gap
between exploit replay and boundary reasoning: the live tool-agent proves 14 of
19 vulnerable public tasks in both runs (`0.7368` exploit-proven success), yet
still records zero vulnerable full passes because boundary reasoning remains at
`0.0000`.

## Reproduction Notes

The table was recomputed by reading `baselines/baseline-registry.json`, selecting
the five `current_public_split` entries, and loading each entry's
`run_artifacts` from `baselines/`.

Useful checks:

```bash
python3 scripts/validate_baseline_registry.py
python3 - <<'PY'
import json
from pathlib import Path
registry = json.loads(Path("baselines/baseline-registry.json").read_text())
print(sum(
    1
    for entry in registry["baselines"]
    if entry.get("release_suitability") == "current_public_split"
))
PY
```

Expected count: `5`.

Recompute this file after any task-count, scoring-contract, baseline-registry,
or run-artifact change. Mark older 46-task ranges stale before comparing them
with a changed task set.
