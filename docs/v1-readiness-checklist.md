# v1 Readiness Checklist

Status: startup checklist for v1 preparation. This is not a v1 release claim.

AuthZBench-SaaS v0.0 remains frozen as historical release evidence. v1 begins
when task bodies, task count, scoring semantics, evidence contracts, or runner
contracts change. From that point forward, old 46-task baselines are stale for
current comparison until rerun against the v1 task set and scoring contract.

## Claim Boundary

Use this language while v1 is in progress:

- `v1-prep branch`
- `v1 task expansion work`
- `v1 readiness checklist`
- `candidate v1 task family`
- `stale v0.0 baseline for v1 comparison`

Do not claim:

- v1 release readiness;
- hosted leaderboard operation;
- public-split scores as private-holdout rankings;
- old 46-task baseline comparability after task or scoring changes;
- production vulnerability discovery capability;
- community-scale benchmark maturity.

## Before Adding Tasks

- [ ] Confirm branch is not `main`.
- [ ] Confirm v0.0 release evidence remains documented as historical evidence.
- [ ] Define the first task family and its expected authorization boundary.
- [ ] Identify the target app surface and fixture data needed.
- [ ] Decide whether the task is public reproducibility evidence or private
  holdout evidence.
- [ ] Define controls before implementing the vulnerable path.
- [ ] Record how old baselines will be marked stale after the first task or
  scoring change.

## New Task Acceptance Criteria

Every new vulnerable task must include:

- clear `expected_vulnerable: true`;
- public-safe `policy` and `objective`;
- explicit `expected_boundary` keys such as actor, tenant, organization, role,
  object, scope, or link state;
- scorer-owned replay through `oracle`;
- at least one denial control;
- an authorized-allow control when the workflow has a legitimate allowed path;
- decoy or alias routes only when they do not make the task ambiguous;
- no private credentials, local paths, raw captures, or private holdout details;
- a stable seed and fixture names that do not overlap private holdout content.

Every new secure-control task must include:

- clear `expected_vulnerable: false`;
- `control_type` set to `denial` or `authorized_allow`;
- expected agent behavior of `findings: []`;
- backend replay that proves the control behavior;
- wording that discourages false reports without revealing the scorer oracle.

## First v1 Task Wave

Start with one family and complete all controls before adding the next family.
Recommended order:

1. Billing entitlement misuse.
2. Support ticket reassignment or unauthorized update.
3. File share revoke or stale-link access.
4. API token scope change to unauthorized export/read.
5. Audit export cross-organization access.
6. Invitation or role downgrade with stale permissions.

The first implementation wave should be small enough to validate deeply. A good
initial slice is one vulnerable billing entitlement task plus denial and
authorized-allow controls.

## Baseline Staleness Policy

When any task body, task count, scorer rule, score policy, evidence contract, or
runner contract changes:

- mark all old 46-task current-public baselines stale for v1 comparison;
- preserve v0.0 summaries as historical evidence;
- regenerate public-safe charts and paper tables only after the new task set is
  stable enough for docs;
- rerun the deterministic scripted sanity baseline first;
- rerun repeated no-tools model families before model comparisons;
- rerun repeated live HTTP tool-agent families before tool-agent comparisons;
- update `docs/status.md`, `docs/evidence-and-claims.md`,
  `baselines/baseline-registry.json`, and any paper tables that reference
  current task counts.

## Minimum Rerun Matrix

Before any v1 release-style claim, collect:

| Evidence | Minimum v1 expectation |
| --- | --- |
| Scripted sanity baseline | 1 clean run across the full v1 public split |
| No-tools model families | repeated runs for the selected current model families |
| Live HTTP tool-agent family | repeated runs with plan/probe artifacts and target-request correlation |
| Private holdout candidate | protected execution with private-path denial and redacted summaries |
| Leaderboard row | validator-accepted submission with source summaries and comparability key |

These are minimum readiness gates, not proof of hosted leaderboard operation.

## Boundary-Reasoning Calibration Gate

Before changing scoring strictness or output-schema requirements, execute the
public-safe calibration plan in
`docs/boundary-reasoning-calibration-plan.md`.

The calibration should classify failures as:

- true boundary misunderstanding;
- missing field;
- synonym or schema mismatch;
- insufficient task instruction;
- scorer strictness.

Do not relax scoring based on anecdotal examples. If scoring or schema changes,
bump the relevant score-policy or evidence-contract version and rerun baselines.

## Validation Commands

Run these before committing a v1 planning-only change:

```bash
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_v0_release.py
python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary
python3 scripts/generate_paper_tables.py
git diff --exit-code -- paper/shared
git diff --check
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

Run these before committing task, scoring, runner, or artifact-contract changes:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_v0_release.py
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary
artifact/run-public-validation.sh
python3 scripts/generate_paper_tables.py
git diff --exit-code -- paper/shared
git diff --check
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

Add Docker/container smoke when app routes, fixtures, request logging, or live
HTTP tool-agent behavior changes.

## v1 Startup Exit Criteria

The v1 startup slice is complete when:

- this checklist exists and is linked from the v1 expansion plan;
- status and claims docs distinguish v1-prep from v1 release;
- focused validation passes;
- the branch is pushed;
- remote CI status is known.

The next slice should implement the first small task family and immediately
mark affected baselines stale for v1 comparison.
