# Improvement Roadmap Audit Plan

## Technical Context

- Named checkout: this repository's `main` worktree at `f5c6a17`, with 38
  user-owned changed/untracked entries at audit start.
- Latest candidate: the linked `improve/evidence-backed-hardening` worktree at
  `aae81c0f`, then clean and 18 commits ahead of `main`.
- Existing durable state: the ignored local `GOAL_STATE.md`.
- External status surface: connected Gmail account, read-only for this audit.

## Governing Gates

1. Preserve user-owned changes and exact target paths.
2. Keep public diagnostics, private evidence, hosted evidence, and external
   validation as separate claim classes.
3. Avoid raw private holdout bodies and external state changes.
4. Use bounded validation before any full or paid benchmark run.
5. Reconcile subagent findings against direct evidence in the parent lane.

## Workstreams

### W1 — Source and state reconciliation

Inventory branch/worktree state, existing goal/spec artifacts, project memory,
and the 18-commit candidate delta. Build a source hierarchy so older main-branch
documents do not override newer candidate evidence.

### W2 — Benchmark validity

Audit task diversity and leakage, task IDs/seeds/evidence requirements, scorer
semantics, fail-closed behavior, controls, task generators, contamination
resistance, and statistical design.

### W3 — Runner and result integrity

Audit Kiro/AGY/Codex adapters, run manifests, effective-model identity,
timeouts/retries, output parsing, request correlation, artifact hashing,
baseline registry, variance, charts, and report aggregation.

### W4 — Research artifact and documentation

Audit README/navigation, canonical status/claims, roadmap, technical report,
paper, reviewer packets, and stale/historical wording. Separate a concise public
story from deep evidence references.

### W5 — Kaggle/Harbor and external validation

Reconcile Gmail status with current primary Kaggle Benchmarks/CLI and Harbor
contracts. Define distinct native Kaggle task, Harbor dataset, and host-onboarding
tracks plus external AppSec/evals/agent/SaaS-provider review work.

### W6 — Validation and synthesis

Run targeted public-safe validators and focused tests, decide whether Kiro adds
information, then produce the ordered roadmap with dependencies, owner roles,
acceptance commands, claim limits, and a 30/60/90-day sequence.

## Verification Strategy

- Fast checks: `rg`, bounded JSON inspection, task counts/uniqueness, focused
  scorer/runner/registry tests, claim and host validators.
- Final local gate: relevant public validation, workflow check, diff check, and
  readback of the new audit artifacts.
- Independent gate: subagent audit lanes plus a separate completeness/adversarial
  review after synthesis.
- Kiro gate: no run unless it closes a named unresolved measurement question;
  prefer one smoke task before any full row and stop on structural failure.

## Expected Deliverables

- `docs/improvement-roadmap-2026-07.md`
- This feature packet: `spec.md`, `plan.md`, `tasks.md`, `traceability.md`, and
  `checklists/requirements.md`
- Updated top section and attempt ledger in `GOAL_STATE.md`

## Risks

- Stale documentation can make a completed improvement look absent.
- Dirty main-branch artifacts may not match the clean candidate source.
- Offline rescoring and requested-only model labels can be over-interpreted.
- Current public Kaggle task tooling may not represent Kaggle's separate
  Docker/Harbor hosting contract.
- A broad roadmap can become non-actionable unless every item has a concrete
  acceptance gate and dependency order.
