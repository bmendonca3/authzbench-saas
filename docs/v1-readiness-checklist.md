# v1 Readiness Checklist

Status: startup checklist for v1 preparation. This is not a v1 release claim.

AuthZBench-SaaS v0.0 remains frozen as historical release evidence. v1 begins
when task bodies, task count, scoring semantics, evidence contracts, or runner
contracts change. From that point forward, old 46-task baselines are stale for
current comparison until rerun against the v1 task set and scoring contract.
`main` is now post-v0 active development; the frozen v0.0 claim boundary lives
at the v0.0 release/tag and in the release snapshot metadata.

## Claim Boundary

Use this language while v1 is in progress:

- `main post-v0 active development`
- `v1 task expansion work`
- `v1.0-internal public-view readiness checklist`
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

- [ ] Confirm whether the work is intended for active `main` development or a
  separate feature branch.
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
- replay expectations that use an integer `status` or non-empty
  `body_contains` check;
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
- update `docs/status.md`, `docs/claims-and-evidence.md`,
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
python3 scripts/validate_task_quality_gate.py --contract artifact/task-quality-gate-contract.json --task 'tasks/*/*.json'
python3 scripts/validate_harbor_adapter_blockers.py
python3 scripts/validate_harbor_adapter_templates.py
python3 scripts/validate_harbor_integration.py
python3 scripts/check_harbor_local_execution.py
python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary
artifact/run-public-validation.sh
python3 scripts/generate_paper_tables.py
git diff --exit-code -- paper/shared
git diff --check
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

Add Docker/container smoke when app routes, fixtures, request logging, or live
HTTP tool-agent behavior changes.

## Release Evidence Validation

The public-view readiness fixture is checked with the public-safe
validator invocation:

```bash
python3 scripts/validate_v1_readiness.py \
  --allow-incomplete \
  --public-view \
  --expected-output artifact/expected-output/v1-readiness-public-view.json
```

`--allow-incomplete` returns 0 when the rendered output matches the
expected fixture match, even if `v1_ready` is false under honest
post-cleanup evidence. The current fixture reports `v1_ready: false`
with 1 unmet gate. This does not infer external release evidence from
public artifacts; external release evidence is a v2/release-time gate
kept outside public Git per the completion gate in
[`docs/goal.md`](goal.md).

For a one-line reviewer-readable summary of the headline verdict, add
`--summary` (default invocation is silent on stderr so test contracts
that pipe the JSON dump stay unchanged):

```bash
python3 scripts/validate_v1_readiness.py --summary
```

The summary stderr line names the failing gate(s) when `v1_ready: false`,
so the headline verdict is grep-friendly in CI logs without parsing JSON.

## v1 Startup Exit Criteria

The v1 startup slice is complete when:

- this checklist exists and is linked from the v1 expansion plan;
- status and claims docs distinguish v1-prep from v1 release;
- focused validation passes;
- the branch is pushed;
- remote CI status is known.

The next slice should implement the first small task family and immediately
mark affected baselines stale for v1 comparison.

## v1 Final Done Checklist (section 12)

The fix-plan section 12 splits the v1 done criteria into three tiers.
This checklist records the current status of each item, the evidence
path, and whether the item is release-time work, external-party work,
or local work that the maintainer controls.

### Internal v1 complete

- [x] 63 public tasks. Evidence: `tasks/*/*.json`; `artifact/expected-output/v1-readiness-public-view.json` shows `public_task_count=63`.
- [x] 48 private holdout tasks by protected evidence. Evidence: `tasks_private/holdout/`; `artifact/v1-task-scale-roadmap.json` shows `current_validated_private_holdout_task_count=48`.
- [x] Deterministic scorer. Evidence: `authzbench/score.py`; `tests/test_scorer_adversarial_submissions.py` (19/19).
- [x] Public validation. Evidence: `python3 scripts/validate_public.py --include-scripted-baseline`; CI step in `.github/workflows/validate.yml`.
- [x] Private artifact exclusion. Evidence: `scripts/redact_protected_private.py`; `docs/private-holdout-lifecycle.md`.
- [x] Claim boundary docs. Evidence: `docs/claims-and-evidence.md`; `docs/benchmark-spec.md`; `scripts/check_claim_boundary.py`.
- [x] Positive-claim over-claim check. Evidence: `scripts/check_v1_overclaim.py` (6 phrases, negation-aware, v2-marker-aware, backtick-aware, Python-literal-aware); wired into `scripts/validate_public.py`; tests in `tests/test_v1_overclaim_check.py` (5/5).
- [x] v2 roadmap. Evidence: `docs/claims-and-evidence.md#5-deferred-v2-validation-tracks`.
- [x] Ambiguous gate names cleaned up. Evidence: `local_or_containerized_submission_smoke`; `hosted_leaderboard_operation_claimed=false`; `has_current_public_scripted_sanity_baseline` and `has_current_public_model_or_tool_agent_baseline` split.
- [x] Current 63-task scripted sanity baseline. Evidence: `baselines/scripted-baseline-public-63-summary.json`; `python3 scripts/validate_baseline_registry.py` exits 0 with `has_current_public_scripted_sanity_baseline=true`.
- [ ] Current 63-task public model and tool-agent capability baselines. Evidence: the prior `baselines/kiro-*-current-public-60-run{1,2}-summary.json` rows are retained as `current_public_stale`; `current_public_model_family_count=0` until six-family no-tools reruns and the live HTTP tool-agent rerun are refreshed for 63 tasks. A promoted-composite refresh is acceptable only when each row is labeled `baseline_construction=promoted_cohort_delta_merge`, preserves base and delta summary provenance, sets `not_full_rerun=true`, and avoids "fresh full rerun" wording.
- [x] Task taxonomy generated. Evidence: `docs/task-taxonomy.md`; `artifact/task-taxonomy.json`.
- [x] Oracle audit generated. Evidence: `docs/task-oracle-audit.md`; `artifact/task-oracle-audit.json`.
- [x] Adversarial scorer tests added. Evidence: `tests/test_scorer_adversarial_submissions.py` (19/19).

### Community benchmark candidate

- [x] Fresh private repeated rows and public scripted sanity baseline. Evidence: `leaderboard_submissions/2026-06-20/`, `leaderboard_sources/`, and `baselines/scripted-baseline-public-63-summary.json`.
- [ ] External AppSec review. Evidence: `docs/reviews/external-review-registry.json` (pending lane); `docs/reviews/appsec-review-packet.md`; `docs/reviews/schemas/appsec-review.schema.json`.
- [ ] External evals methodology review. Evidence: `docs/reviews/benchmark-methodology-review-packet.md`; `docs/reviews/schemas/evals-review.schema.json`.
- [ ] External agent and tooling review. Evidence: `docs/reviews/agent-tooling-review-packet.md`; `docs/reviews/schemas/agent-tooling-review.schema.json`.
- [ ] SaaS-provider or senior AppSec scenario validation. Evidence: pending external engagement.
- [x] Private holdout lifecycle policy. Evidence: `docs/private-holdout-lifecycle.md`; `tasks_private/holdout/rotation-metadata.json`.
- [x] Local row eligibility tiers. Evidence: `docs/scoring-and-submissions.md`.
- [x] Clean-room reproduction command. Evidence: `python3 scripts/reproduce_public_artifact.py`; `Dockerfile`; `.env.example`; `docs/container-digests.md`.
- [x] Public artifact index. Evidence: `artifact/INDEX.md`; `docs/artifact-index.md`.
- [ ] Current per-task Harbor parity, if Harbor is part of the claim. Evidence: `artifact/harbor-parity-experiment.json` (per_task_pairing contract, currently `evidence_status=blocked`); historical aggregate-means run preserved at `artifact/historical/harbor-parity-experiment-aggregate-means.json`. The per_task_pairing map will be populated when a real Harbor run completes.

### Externally validated benchmark

- [ ] All external review lanes complete. Evidence: `docs/reviews/external-review-registry.json` (currently all three pending).
- [ ] Blocking issues resolved. Evidence: pending external review completion.
- [ ] Private evaluation governance externally auditable. Evidence: lifecycle policy in place; external audit pending.
- [ ] Hosted or containerized third-party submission path operational. Evidence: v2 work per the plan.
- [ ] Multiple third-party submissions or independent reruns. Evidence: requires external parties.
- [ ] Public release notes with exact claim boundary. Evidence: v1.0-internal release notes in `docs/releases/v1.0-internal.md`; v2 release notes pending external review completion.
- [ ] Stable version tag. Evidence: release-time action; requires user input on tag string.
- [ ] Archived artifacts with hashes. Evidence: release-time action; requires user input on archive strategy.


## v1.1-prep cohort

The v1.1-prep cohort has been promoted into `tasks/` and demonstrates the
`multi_step_discovery` task type and plan-4.2 categories the previous public
60-task split did not cover:

- `sup_bfla_viewer_updates_assigned_ticket_status_discovery` (team
  membership boundary in support)
- `bill_bfla_member_disables_export_entitlement_discovery` (billing
  plan entitlement downgrade)
- `fs_team_membership_cross_workspace_discovery` (team membership
  boundary in file_sharing)

The promoted cohort is covered by the public manifest/scorer validators and by
the 63-task scripted sanity baseline. The former 60-task live public baseline
summaries remain stale; regenerating public model/tool capability baselines is
the remaining follow-on for current public comparison evidence. That refresh can
be a full 63-task rerun or an explicitly labeled promoted-composite baseline
built from the immutable 60-task public evidence plus fresh reruns of exactly
the three promoted public tasks.

## v1.1 promotion checklist

The v1.1-prep cohort promotion status:

- [x] Move the three task files from `tasks_v11_prep/` into the
  appropriate `tasks/<app>/` directory.
- [x] Update `docs/task-taxonomy.md` and `artifact/task-taxonomy.json`
  with the new public count.
- [ ] Refresh the public 63-task live baselines (six families x two
  runs) and refresh `baselines/kiro-*-current-public-63-run{1,2}-summary.json`,
  either as full reruns or as `promoted_cohort_delta_merge` composites with
  explicit base/delta provenance and `not_full_rerun=true`.
- [x] Update `artifact/expected-output/v1-readiness-public-view.json`
  with `public_task_count=63`.
- [x] Update `artifact/v1-task-scale-roadmap.json` to reflect the new
  count and refresh the planned-waves list.
- [x] Update `docs/v1-readiness-checklist.md` to mark the v1.1
  promotion items as complete and re-run the v1-readiness gate.

## Notes for the next release

The following items are release-time actions that require explicit user
input before completion:

1. Stable version tag (e.g. v1.0-internal vs v1.0-community-candidate).
   The maintainer should pick the tag string and update the
   `docs/releases/v1.0-internal.md` accordingly.
2. Archived artifacts with hashes. The maintainer should decide
   whether the archive is git-tag-only, signed-tarball, or
   container-image-digest.
3. Hosted or containerized third-party submission path. This is v2
   work per the fix plan and is not in the current v1 internal scope.

The following items require external parties:

1. External AppSec, evals methodology, and agent-tooling reviews.
2. SaaS-provider or senior AppSec scenario validation.
3. Multiple third-party submissions or independent reruns.

## Claim boundary for this checklist

This checklist is the v1 final-done record. It does not claim hosted
leaderboard operation, external review completion, or community-scale
benchmark maturity until each item is checked off with cited evidence.
