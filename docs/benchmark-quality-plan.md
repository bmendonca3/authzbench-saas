# Benchmark Quality Plan

Status: active, evidence-backed improvement plan for the public benchmark.

This plan treats AuthZBench-SaaS as a measurement instrument. It does not turn
public-split runs into private-holdout leaderboard evidence, external review,
hosted operation, or platform acceptance.

## Current Audit Snapshot

The tracked public split has 63 tasks across six apps: 27 vulnerable tasks and
36 secure controls (21 denial and 15 authorized-allow). All public seeds are
unique. Eight vulnerable tasks have explicit multi-step evidence requirements;
19 still rely on a final oracle replay plus controls. The vulnerable set has 24
claim families, with two families reused across five tasks.

Regenerate the public-safe structural evidence with:

```bash
python3 scripts/generate_task_quality_matrix.py
python3 scripts/validate_task_quality_gate.py --task 'tasks/*/*.json'
```

## Highest-Priority Measurement Risks

1. Authored objectives, policies, output wording, and canonical task ids can
   reveal whether a public task is a control. A filesystem-capable agent started
   in the repository can also inspect public manifests and oracles.
2. Under the historical protocol, `findings: []` receives secure-control credit
   from scorer-owned replay even when the participant supplies no tested request.
3. Requested model labels, CLI versions, prompts, and adapter behavior have not
   always been bound together in one run manifest.
4. A completed evaluation can look like a shell failure when the model does not
   pass every task, which conflates capability with infrastructure status.
5. Nineteen vulnerable tasks lack explicit request-shape evidence requirements,
   and public fixed seeds remain susceptible to memorization over time.

## Implemented Protocol Upgrade

`python3 -m authzbench.evaluate` is the opt-in
`blinded-control-evidence-v1` protocol. It deliberately leaves the historical
`authzbench.run` and score-policy-v2 rescore path unchanged.

The new protocol:

- replaces canonical task ids with opaque per-run case ids in participant
  context and environment variables;
- uses one neutral objective, policy, and output contract for both vulnerable
  tasks and controls;
- host-replays only the bounded candidate requests and exposes their observed
  responses without a control name, oracle, or vulnerability label;
- runs the adapter from the per-task artifact directory instead of the repo
  root;
- requires a participant-selected verification request and a participant-reported
  expected status that matches host replay before a secure control can receive credit;
- records source hashes, tracked-diff provenance, prompt hashes, requested Kiro
  model/effort, CLI version, explicit model-identity verification status,
  output-format compliance, and protocol hash;
- separates completed-run exit status from model accuracy and uses a distinct
  exit for infrastructure failures;
- adds Wilson 95% intervals, balanced authorization accuracy, and a
  discrimination index (`vulnerable_full_pass_rate - false_positive_rate`).

Working-directory isolation is not an operating-system sandbox. A
filesystem-capable untrusted agent still requires a container or equivalent
isolation boundary. Public tasks remain development and diagnostic evidence;
credible ranking still requires protected holdouts.

## Roadmap

### Phase 1 — Protocol integrity

- [x] Blind authored class/outcome hints and canonical task ids.
- [x] Require participant evidence on secure controls.
- [x] Bind Kiro adapter and protocol provenance in each run.
- [x] Separate evaluation completion, model performance, and infrastructure
  failure exits.
- [x] Add calibrated aggregate metrics and confidence intervals.
- [ ] Add a containerized filesystem/network sandbox profile for tool-capable
  agents and verify it with a malicious file-read/egress fixture.

### Phase 2 — Task anti-gaming

- [ ] Add explicit evidence requirements to all 27 vulnerable tasks, beginning
  with the 19 measured gaps; version the task fingerprint and mark affected
  baselines stale before comparison.
- [ ] Replace magic claim strings with a structured vulnerability taxonomy while
  preserving score-policy-v2 history.
- [ ] Add generated run seeds or task generators so public semantics remain
  stable while concrete identifiers vary.
- [ ] Expand non-alias authorization families: search/list leakage, async export
  ownership, webhook/integration boundaries, delegation/revocation, inheritance,
  body/path tenant mismatch, and ownership transfer.
- [ ] Add variable finding-count tasks and stronger tempting secure controls.

### Phase 3 — Empirical calibration

- [ ] Run repeated blinded-protocol baselines across multiple model families and
  seeds with identical protocol hashes.
- [ ] Publish per-task difficulty, bootstrap or repeated-run intervals, and
  small-`n` warnings; do not rank unlike harness types on one axis.
- [ ] Retire or redesign tasks with near-zero discrimination after repeated
  protected evaluation.

### Phase 4 — Protected validation

- [ ] Rotate protected holdouts after public task/protocol changes.
- [ ] Complete external AppSec and benchmark-methodology review.
- [ ] Promote a row only after clean-source provenance, repeated runs, privacy
  validation, registry checks, and the normal release gate all pass.

## Full Public Kiro Run

Use an explicit supported Python and an explicit model from
`kiro chat --list-models`. The adapter path is absolute because the blinded
protocol runs each participant from an isolated task artifact directory.

```bash
ROOT="$(pwd)"
PYTHON="python3.11"
MODEL="claude-sonnet-5"

"$PYTHON" -m authzbench.evaluate \
  --task 'tasks/*/*.json' \
  --agent-cmd "$PYTHON $ROOT/scripts/kiro_baseline_agent.py --model $MODEL --effort high --timeout-seconds 120" \
  --agent-source "$ROOT/scripts/kiro_baseline_agent.py" \
  --results-dir "results/kiro-$MODEL-blinded-public-63" \
  --timeout-seconds 150 \
  --agent kiro_baseline_agent \
  --model "$MODEL" \
  --harness-type no-tools-model
```

A local run from a dirty worktree is diagnostic evidence only. Do not copy it
into `baselines/` or call it current registry evidence without a clean source
boundary, repeated runs, and registry/provenance review.

### Multi-model host-replayed diagnostic

Four local high-effort Kiro runs completed all 63 public tasks under protocol
manifest `2359b92f...` and source set `db602fb2...`. Every valid row had 63
opaque participant paths, 63 unique prompts, and zero adapter, infrastructure,
or invalid-submission failures. Tool-probe telemetry was not captured, so these
diagnostics do not make a tool-attempt claim.

The public-safe aggregate is recorded in
[`artifact/kiro-multimodel-blinded-public-diagnostic-2026-07-12.json`](../artifact/kiro-multimodel-blinded-public-diagnostic-2026-07-12.json).
Raw run bundles remain ignored local evidence. These runs predate required
`--agent-source` provenance and explicit replay-app hashing, so the aggregate is
pre-hardening diagnostic evidence rather than an exact-source reproduction
baseline.

The Kiro CLI recorded explicit requested model options but did not expose an
independently observed effective backend model label. These model names are
therefore requested-only diagnostic labels. The current registry validator
rejects blinded-protocol rows without verified effective model identity.

| Model | Binary pass | Mean score | Exploit proof | Full vulnerable | Secure controls | False reports | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude Opus 4.8 | 38/63 | 0.6333 | 3/27 | 2/27 | 36/36 | 0/36 | 0.5371 |
| Claude Sonnet 4.6 | 36/63 | 0.6357 | 6/27 | 1/27 | 35/36 | 1/36 | 0.5046 |
| Claude Sonnet 5 | 33/63 | 0.6032 | 6/27 | 0/27 | 33/36 | 3/36 | 0.4583 |
| Claude Haiku 4.5 | 33/63 | 0.5643 | 3/27 | 0/27 | 33/36 | 2/36 | 0.4583 |

GLM-5 was excluded from model-quality comparison after 21/63 full-run outputs
failed parsing because ANSI reset sequences were interleaved inside
pretty-printed JSON. Qwen3 Coder Next and DeepSeek 3.2 showed the same failure
in admission smokes and were not given full runs. All valid rows also had 0%
strict JSON-only compliance because the Kiro CLI wrapped recoverable JSON in
terminal output. Because all four comparable rows are Claude models, this is not
yet a valid cross-family comparison.

These are single-run dirty-worktree diagnostics, not registry baselines or
statistically stable rankings. Opus led binary/control performance while Sonnet
4.6 had the highest mean score and tied Sonnet 5 for exploit proofs. The split
result reinforces the next priorities: version a structured claim taxonomy and
participant-facing boundary schema, then repeat clean-source multi-seed runs
before leaderboard use.
