# Baseline Variance Analysis

Status: descriptive two-run analysis from two current v1-prep 54-task public
no-tools families, the historical 49-task public no-tools and live HTTP tool-agent
artifacts, and the frozen v0.0 46-task release snapshot. These ranges are
diagnostic public-split evidence only, not confidence intervals, private holdout
evidence, or leaderboard rankings. The 49-task rows are stale for the active
54-task split.

This file uses only tracked public-safe summaries named by
`baselines/baseline-registry.json`. Each row below has exactly two runs.

## Artifact Set

### Current v1-prep 54-task public split

| Baseline family | Harness | Model | Source summaries |
| --- | --- | --- | --- |
| `kiro-qwen3-coder-next-current-public-54` | `no-tools-model` | `qwen3-coder-next` | `kiro-qwen3-coder-next-current-public-54-run1-summary.json`; `kiro-qwen3-coder-next-current-public-54-run2-summary.json` |
| `kiro-claude-haiku-4-5-current-public-54` | `no-tools-model` | `claude-haiku-4.5` | `kiro-claude-haiku-4.5-current-public-54-run1-summary.json`; `kiro-claude-haiku-4.5-current-public-54-run2-summary.json` |

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

### Current v1-prep 54-task public split

| Baseline family | `mean_score` | `exploit_proven_success_rate` | `vulnerable_full_pass_count` | `boundary_reasoning_pass_rate` | `false_positive_rate` | `invalid_submission_rate` | `target_request_coverage_rate` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen no-tools | 0.5981-0.6528 | 0.0000-0.1429 | 0-0 | 0.0000-0.0000 | 0.0000-0.0303 | 0.0000-0.0370 | n/a |
| Claude Haiku no-tools | 0.6815-0.6954 | 0.1905-0.2381 | 0-0 | 0.0000-0.0000 | 0.0303-0.0303 | 0.0000-0.0000 | n/a |

The two current Qwen runs also preserve adapter diagnostics. Run 1 records
seven task-level adapter failures: two inner Kiro command failures and five
outputs without a usable submission object, plus two outer runner failures.
Run 2 records twelve task-level adapter failures: seven inner Kiro command
failures and five outputs without a usable submission object, with no outer
runner failure. The adapter converts each inner failure to a valid
`{"findings":[]}` fallback, which stays in the 54-task scored denominator and
can pass a secure control or fail a vulnerable task. The outer runner failures
become invalid submissions. The agent command uses a 60-second inner
model-call timeout while the runner uses a 75-second per-task timeout.

Both current Claude Haiku 4.5 runs have zero adapter failures, zero outer runner
failures, and zero invalid submissions. They contain 11 and 12 scorer-counted
findings, respectively; the promoted aggregates were derived exactly from the
retained per-task rows because the runs completed immediately before the runner
began emitting `scored_submission_finding_total`. Both runs submit one false
finding on the same authorized-allow support reassignment control.

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

The current 54-task Qwen and Claude Haiku pairs establish repeated evidence for
two no-tools model families on the active fingerprint. The Qwen pair passes
32-33 of 54 tasks,
proves 0-3 of 21 vulnerable replays, keeps vulnerable boundary reasoning at
`0.0000`, and fully passes zero vulnerable tasks. One run has one reported
secure-control failure caused by an invalid submission, but no submitted
control finding; its two invalid submissions produce the `0.0370`
invalid-submission rate and the reported `0.0303` false-positive rate. The
second run has no invalid submissions or secure-control failures. The command
and missing-submission diagnostics make the pair useful for adapter and
model-output variance analysis, but they also make clear why this is diagnostic
public evidence rather than a polished ranking row.

The Claude Haiku pair passes 32 of 54 tasks in both runs, proves 4-5 of 21
vulnerable replays, keeps boundary reasoning at `0.0000`, and fully passes zero
vulnerable tasks. Both runs have a `0.0303` false-positive and false-report rate
because each reports the same authorized-allow control as vulnerable; the
authorized-allow pass rate is `0.9286`. The absence of adapter, runner, and
invalid-submission failures makes this a cleaner model-output comparison than
the current Qwen pair, but two families remain insufficient for stable
cross-model conclusions.

Qwen run 1's `vulnerable_safety_pass_rate` is `0.9524` because its outer
runner failure on one vulnerable task produced an invalid submission with no
safety credit. This is a malformed-submission outcome, not evidence that the
model attempted an unsafe or out-of-scope action.

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
selecting the current 54-task Qwen row, the stale 49-task model and tool-agent
baselines, and the five non-scripted entries in the `v0.0` release snapshot,
then loading each entry's `run_artifacts` from `baselines/`.

Useful checks:

```bash
python3 scripts/validate_baseline_registry.py
python3 - <<'PY'
import json
from pathlib import Path
registry = json.loads(Path("baselines/baseline-registry.json").read_text())
current_54 = [
    entry
    for entry in registry["baselines"]
    if entry["release_suitability"] == "current_public_split"
    and entry.get("expected_task_count") == 54
    and entry["kind"] in {"model_baseline", "tool_agent_baseline"}
]
stale_49 = [
    entry
    for entry in registry["baselines"]
    if entry["release_suitability"] == "current_public_stale"
    and entry.get("expected_task_count") == 49
    and entry["kind"] in {"model_baseline", "tool_agent_baseline"}
]
snapshot = next(item for item in registry["release_snapshots"] if item["id"] == "v0.0")
print(len(current_54))
print(len(stale_49))
print(len([
    baseline_id
    for baseline_id in snapshot["baseline_ids"]
    if baseline_id != "scripted-sanity-public-46"
]))
PY
```

Expected counts: `2` current 54-task model families, `6` stale 49-task
model/agent families, and `5` frozen v0.0 repeated model/agent families.

Recompute this file after any task-count, scoring-contract, baseline-registry,
or run-artifact change. Mark older 46-task ranges stale before comparing them
with a changed task set; the `v0.0` release snapshot remains historical evidence,
not current/v1 comparison evidence.
