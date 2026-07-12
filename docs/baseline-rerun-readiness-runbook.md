# Baseline Rerun Readiness Runbook

> **See also:** [`docs/baseline-credibility.md`](baseline-credibility.md) for stale-baseline labeling and [`docs/claims-and-evidence.md`](claims-and-evidence.md) for the canonical claim ledger.

This runbook documents the exact commands, prerequisites, and post-run steps
for fresh model and tool-agent re-execution at the current 63-task public split.
It remains useful when a fresh prompt/adapter/environment run is required.

## Why This Exists

Older model and tool-agent baselines at 60/54/49/46/44/15 tasks are stale. The
current public split is 63 tasks. Fourteen saved full-63-task executions now
have current offline policy-v2 rescores with explicit provenance, so the
registry's strict current-public path passes. Those rows are not fresh model
executions under v2; use this runbook when that stronger evidence is needed.

## Prerequisites

1. **Kiro CLI installed and authenticated.** Verify:
   ```bash
   kiro chat --list-models
   ```
   Required models: `claude-sonnet-4.6`, `claude-haiku-4.5`, `claude-opus-4.6`, `glm-5`, `qwen3-coder-next`.

2. **Docker running** for live HTTP tool-agent reruns (the tool-agent adapter probes local fixture apps):
   ```bash
   docker compose up -d
   ```

3. **Clean working tree on main.**
   ```bash
   git checkout main && git pull --ff-only
   git status  # must be clean
   ```

4. **Public validation passes before rerun:**
   ```bash
   BENCHMARK_COMMIT_SHA="$(git rev-parse HEAD)"
   python3 scripts/check_claim_boundary.py
   python3 scripts/validate_public.py --include-scripted-baseline
   python3 scripts/validate_host_presentation.py
   ```

## Run Matrix

| Baseline type | Models | Runs | Tasks | Kiro calls |
| --- | --- | --- | --- | --- |
| Scripted sanity | 1 (deterministic) | 1 | 63 | 0 (no Kiro) |
| No-tools model baselines | 5 models | 2 | 63 | 630 |
| Live HTTP tool-agent | 1 (claude-sonnet-4.6) | 2 | 63 | 126 planner calls (up to 756 live HTTP probes at default max-probes=6) |
| **Total** | | | | **756 Kiro chat invocations** |

### Cost disclosure

Expected operational budget is 756 Kiro chat invocations plus local Docker runtime. Monetary cost depends on the active Kiro plan/provider billing and must be checked in Kiro before execution.

### New blinded-protocol diagnostic

Before repeating the legacy matrix, run one complete public diagnostic through
the blinded protocol documented in
[`benchmark-quality-plan.md`](benchmark-quality-plan.md). It uses opaque case
ids, neutral context, participant control evidence, and stronger provenance.
Because it is a different evaluation protocol, do not mix its numbers with the
historical policy-v2 context rows.

```bash
ROOT="$(pwd)"
PYTHON="python3.11"
MODEL="claude-sonnet-5"  # verify with: kiro chat --list-models

"$PYTHON" -m authzbench.evaluate \
  --task 'tasks/*/*.json' \
  --agent-cmd "$PYTHON $ROOT/scripts/kiro_baseline_agent.py --model $MODEL --effort high --timeout-seconds 120" \
  --results-dir "results/kiro-$MODEL-blinded-public-63" \
  --timeout-seconds 150 \
  --agent kiro_baseline_agent \
  --model "$MODEL" \
  --harness-type no-tools-model
```

## Commands

### 1. Scripted sanity baseline (no Kiro needed)

```bash
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 scripts/scripted_baseline_agent.py' \
  --results-dir results/scripted-sanity-public-63 \
  --timeout-seconds 10 \
  --benchmark-commit-sha "$BENCHMARK_COMMIT_SHA" \
  --agent scripted_baseline_agent \
  --model deterministic-script \
  --harness-type scripted
```

### 2. No-tools model baselines (5 models × 2 runs)

```bash
for MODEL in claude-sonnet-4.6 claude-haiku-4.5 claude-opus-4.6 glm-5 qwen3-coder-next; do
  for RUN in 1 2; do
    python3 -m authzbench.run \
      --task 'tasks/*/*.json' \
      --agent-cmd "python3 scripts/kiro_baseline_agent.py --model $MODEL --timeout-seconds 90" \
      --results-dir "results/kiro-${MODEL}-current-public-63-run${RUN}" \
      --timeout-seconds 120 \
      --benchmark-commit-sha "$BENCHMARK_COMMIT_SHA" \
      --agent kiro_baseline_agent \
      --model "$MODEL" \
      --harness-type no-tools-model
  done
done
```

### 3. Live HTTP tool-agent baseline (1 model × 2 runs)

```bash
# Ensure Docker targets are running
docker compose up -d

for RUN in 1 2; do
  python3 -m authzbench.run \
    --task 'tasks/*/*.json' \
    --agent-cmd 'python3 scripts/kiro_live_tool_agent.py --model claude-sonnet-4.6 --timeout-seconds 45 --max-probes 6' \
    --results-dir "results/kiro-live-tool-agent-sonnet-current-public-63-run${RUN}" \
    --timeout-seconds 120 \
    --benchmark-commit-sha "$BENCHMARK_COMMIT_SHA" \
    --agent kiro_live_tool_agent \
    --model claude-sonnet-4.6 \
    --harness-type tool-agent \
    --target-log-dir captures/request-logs
done
```

## Post-Run Steps

1. **Locate the nested run summaries and copy each to an explicit,
   collision-free registry filename:**
   ```bash
   find results -path '*current-public-63-run*/*/summary.json' -print
   ```
   Review each printed summary first, then copy it to the exact `summary_path`
   named by the intended registry entry. Do not bulk-copy generic
   `summary.json` filenames because they collide.

2. **Update `baselines/baseline-registry.json`** from stale 60-task rows to new 63-task rows. For each model family:
   - Set `expected_task_count: 63`
   - Set `requires_rerun_before_current_comparison: false`
   - Set `evidence_status: "current"`
   - Set `release_suitability: "current_public_split"`
   - Update `summary_path` and `run_artifacts` to the new 63-task files
   - Set `run_date` to the current date

3. **Validate the updated registry:**
   ```bash
   python3 scripts/validate_baseline_registry.py
   python3 scripts/analyze_baseline_variance.py --require-current-public
   python3 scripts/check_claim_boundary.py
   python3 scripts/validate_public.py --include-scripted-baseline
   python3 scripts/validate_host_presentation.py
   ```

4. **The strict `--require-current-public` path should now pass without `--allow-stale-pending-rerun`.** If it does not, the registry update is incomplete.

5. **Regenerate the stale-wording inventory** (the new 63-task rows will change the hit counts):
   ```bash
   python3 scripts/generate_docs_alignment_inventory.py
   ```

6. **Update `artifact/expected-output/v1-readiness-public-view.json`** if the readiness fixture gates change:
   ```bash
   python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view \
     > artifact/expected-output/v1-readiness-public-view.json
   ```

7. **Commit, push, open PR, wait for CI, merge.**

## Rollback

If a rerun produces unexpected failures or corrupted evidence:
1. Do not update the registry.
2. Keep the stale 60-task rows as-is.
3. Delete the new `results/` directories.
4. The `--allow-stale-pending-rerun` path continues to pass until a clean rerun is completed.
