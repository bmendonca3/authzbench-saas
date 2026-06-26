# AuthZBench-SaaS v1 Goal

## Purpose

AuthZBench-SaaS tests one narrow claim:

> Can an AI agent prove SaaS authorization failures with backend evidence while
> avoiding false positives on correct secure behavior?

Current status: v1.0-internal is complete under the internal/non-external
scope, with release-time evidence still requiring a coherent source-boundary
refresh before any new final validation claim.

v1 does not claim external review, hosted public leaderboard readiness,
SaaS-provider validation, or platform acceptance.
Those are tracked as v2 gates in `docs/claims-and-evidence.md`.

Do not claim `v1` external readiness, hosted-leaderboard readiness, platform
acceptance, or third-party endorsement. Completed external review is a separate
v2 claim.

## v1 Release-Candidate Statement

AuthZBench-SaaS v1 is an internally validated SaaS authorization-agent benchmark
artifact with a 63-task public split, maintainer-private holdout operation,
111 total public/private task scale, deterministic backend replay scoring,
protected private-evaluation plumbing, local/containerized execution smoke
evidence, and Harbor-compatible local execution scaffolding. External review,
SaaS-provider validation, hosted leaderboard operation, and platform acceptance
are explicitly deferred to v2.

## v1 Release Checklist

v1 release gates:

- [x] 63-task public split validated
- [x] 48-task maintainer-private holdout evidence summarized
- [x] 111 total public + private task scale
- [x] deterministic replay scorer validated
- [x] public baselines current or clearly marked stale
- [x] private execution smoke passed
- [x] protected private-path denial recorded
- [x] leaderboard schema/provenance validation passed
- [x] Harbor-compatible scaffold and local smoke recorded
- [x] paper/tables/charts regenerated
- [x] exact-head CI green
- [x] privacy scan clean
- [x] release-candidate evidence recorded

Deferred to v2:

- [ ] independent external review
- [ ] SaaS-provider scenario validation
- [ ] hosted public leaderboard
- [ ] Harbor/Kaggle/platform acceptance
- [ ] third-party submissions

## Current State

- Frozen release boundary: v0.0 remains historical and auditable.
- Historical checkpoint: 49-task public split, preserved only for history.
- Active public split: 63 tasks.
- Public evidence: scripted 63-task sanity baseline complete. The repeated
  60-task, 54-task, 49-task, and v0.0 model/tool-agent rows are stale
  diagnostic rows until rerun on the 63-task split or explicitly promoted as
  composite baseline refreshes.
- Harbor repo-side prep: skeletons, validators, metadata checks, public-safe
  docs, and a one-task local Harbor smoke artifact are complete and validated.
  Full Harbor parity evidence still requires a real multi-task Harbor/native
  parity experiment; the checked-in local smoke has `parity_verified=false`.
- Private evidence: active and shadow holdout packs, protected private-path
  denial, repeated no-tools private evidence, and repeated tool-agent private
  evidence are summarized through public-safe fingerprints and counts only.
- Current local gate note: strict v1 readiness still requires a coherent
  release-evidence refresh against one benchmark source boundary before making
  a new final validation claim.

## Operating Rules

- Keep `v1_ready: false` for current validation runs until strict release
  validation passes with coherent release evidence.
- External review is a v2 goal; keep the packet clean as v2 preparation.
- Do not synthesize reviewer evidence or infer endorsement from informal
  interest.
- Do not commit private task bodies, private manifests, raw private evidence,
  captures, credentials, local absolute paths, private meeting details, calendar
  links, or private reviewer notes.
- Do not count roadmap-only tasks. A task counts only after manifest, app,
  scorer, and task-quality checks pass.
- Keep `docs/goal.md` local unless explicitly approved for commit.

## Completion Gate

The internal v1 goal is complete only when every item below is true. Items
marked complete are supported by current public-safe evidence; unchecked items
remain release-time or v2 work.

- [x] Local Harbor execution smoke evidence exists, not just template validation.
- [x] The task-quality gate is enforced for new task families.
- [x] Public plus validated private tasks reach at least 100.
- [x] One active and one separate shadow/candidate private holdout pack exist in
  ignored maintainer-only paths with valid rotation metadata.
- [x] Protected private execution proves submitter-private-path denial, scorer
  access, protected raw evidence, and redacted public summaries.
- [x] Repeated private no-tools and tool-agent baselines exist with `run_count >=
  2`, active private-pack fingerprint, benchmark source SHA, source summaries,
  and protected-execution metadata.
- [ ] Paper, report, charts, and tables are refreshed against the current
  release source boundary without overclaiming.

- [ ] Strict release evidence exists outside public Git.
- [ ] `python3 scripts/validate_v1_readiness.py --release-evidence
  <external-json>` passes without `--allow-incomplete`.
- [ ] Final release commit is authored as `bmendonca3`, pushed only when
  authorized, and exact-head CI is green.

## Work Order

### 1. Baseline Lock

Goal: confirm the starting point before changing anything.

Acceptance:

- [ ] Branch and dirty state are understood.
- [ ] Public readiness still reports `v1_ready: false`.
- [ ] Existing private/raw artifact scan is empty.

Commands:

```bash
git status --short --branch
python3 scripts/validate_public.py
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view --expected-output artifact/expected-output/v1-readiness-public-view.json
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

### 2. Harbor Local Execution

Goal: convert Harbor prep from repo-side skeleton readiness into real local
execution evidence.

Acceptance:

- [ ] Harbor CLI/package/SDK availability is recorded from public instructions.
- [ ] A minimal public Harbor skeleton dataset runs through the real Harbor path.
- [ ] `adapter_metadata.json` is generated from the runtime, not copied.
- [ ] `parity_experiment.json` compares Harbor output with matching native
  AuthZBench-SaaS public-run evidence.
- [ ] Public outputs remain redacted.

Commands:

```bash
python3 scripts/check_harbor_local_execution.py
python3 scripts/validate_harbor_integration.py
python3 scripts/validate_harbor_adapter_blockers.py
python3 scripts/validate_harbor_adapter_templates.py
```

Blocker rule: if the runtime is unavailable, record the exact missing package,
command, or environment requirement and leave this track blocked.

### 3. Task-Quality Verification

Goal: make every new task earn its count.

Each new family must include:

- SaaS workflow and authorization-boundary spec.
- Vulnerable behavior.
- Secure denial control.
- Authorized-allow control.
- False-positive trap.
- Scorer replay contract or equivalent fixture evidence.

Validators/tests must reject:

- Missing actor, tenant, object, role, or token boundary.
- Duplicated structures, ids, or seeds.
- Vague oracle language.
- Missing scorer replay contract.
- Missing secure denial or authorized-allow coverage.
- Vacuous body-only controls.

Required scorer fixtures:

- Positive exploit submission.
- Wrong actor failure.
- Wrong tenant failure.
- Wrong object failure.
- Missing-boundary failure.
- Secure-control false-positive failure.
- Secure-control empty-findings pass.

Commands:

```bash
python3 scripts/validate_task_quality_gate.py --contract artifact/task-quality-gate-contract.json --task 'tasks/*/*.json'
python3 -m unittest discover -s tests
```

### 4. Scale to 100+ Validated Tasks

Goal: reach at least 100 real validated tasks across public and protected
private splits.

Candidate waves:

- File-share revoke and stale-link access.
- API-token scope change and unauthorized export/read.
- Cross-org audit exports.
- Invitation, role downgrade, and stale-permission workflows.
- Additional billing, support, admin/config, and collaboration flows.

Acceptance:

- [ ] Counts are recomputed from manifests.
- [ ] Vulnerable/control mix remains meaningful.
- [ ] Denial and authorized-allow controls are preserved.
- [ ] New scorer fixtures or replay evidence exist.
- [ ] Scripted baseline sanity passes on the expanded split.
- [ ] Task matrix, charts, tables, status docs, and report language regenerate
  cleanly.
- [ ] Old baselines are marked stale after task or scoring changes.

Blocker rule: planned roadmap tasks do not count.

### 5. Private Holdout Rotation

Goal: create real maintainer-only active and shadow/candidate holdout packs.

Acceptance:

- [ ] One active pack exists in ignored maintainer-only storage.
- [ ] One separate shadow/candidate pack exists in ignored maintainer-only
  storage.
- [ ] `tasks_private/holdout/rotation-metadata.json` records pack ids, roles,
  safe relative paths, version labels, fingerprints, compatibility rules,
  retirement rules, and exactly one active pack.
- [ ] Declared fingerprints match computed fingerprints.
- [ ] Pack ids, task ids, paths, and fingerprints are unique where required.
- [ ] Public Git tracks no private manifests or raw private artifacts.

Commands:

```bash
python3 scripts/validate_holdout_pack.py <active-pack-args>
python3 scripts/validate_holdout_pack.py <shadow-pack-args>
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

Blocker rule: one pack alone is partial evidence, not rotation.

### 6. Protected Private Execution

Goal: prove submitter isolation and scorer-controlled private evaluation.

Acceptance:

- [ ] Submitter receives only rendered context and output paths.
- [ ] Submitter attempts to read private manifests fail.
- [ ] Scorer can read and evaluate the active private pack.
- [ ] Raw private evidence is written only to ignored/protected paths.
- [ ] Public summaries are redacted.
- [ ] `artifact/submission-runner-smoke.json` is replaced only by real
  release-candidate smoke evidence tied to the active private-pack fingerprint.

Blocker rule: do not replace blocker evidence without a real private pack,
private-pack fingerprint, command, runner version/image, isolation model, result,
and cleanup status.

### 7. Repeated Private Baselines

Goal: produce private leaderboard-quality evidence.

Acceptance:

- [ ] At least one private no-tools row has `run_count >= 2`.
- [ ] At least one private tool-agent row has `run_count >= 2`.
- [ ] Each row records benchmark source SHA, active private-pack version,
  active private-pack fingerprint, source summaries, comparability key, and
  protected-execution metadata.
- [ ] Tool-agent rows include target-request coverage.
- [ ] Old private rows affected by task, scoring, pack, or evidence-contract
  changes are marked stale, legacy, or deprecated.
- [ ] Baseline registry and variance docs distinguish public diagnostics from
  private leaderboard candidates.

Commands:

```bash
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary
```

### 8. Report, Paper, Charts, Tables

Goal: refresh research artifacts after the evidence changes, without
overclaiming.

Acceptance:

- [ ] Frozen v0.0, current v1-prep, and true v1 claims are clearly separated.
- [ ] External review and infrastructure findings are reflected only after they
  exist.
- [ ] Generated tables and charts regenerate without diff.
- [ ] IEEE scaffold compiles when `latexmk` is available.
- [ ] Wording does not imply completed external review, hosted release,
  platform acceptance, or third-party endorsement.

Commands:

```bash
python3 scripts/generate_paper_tables.py
git diff --exit-code -- paper/shared
latexmk -pdf -interaction=nonstopmode -halt-on-error paper/ieee-sp/main.tex
```

### 9. Full Local Validation

Goal: prove the local repo remains stable while true v1 is still blocked.

Commands:

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_v0_release.py
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view --expected-output artifact/expected-output/v1-readiness-public-view.json
git diff --check
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

Expected before release evidence: local checks pass,
`v1_ready: false` remains correct.

### 10. External Review (v2 Prep)

Goal: preserve the external review packet and tracker as v2 preparation.

Required lanes:

- Application Security.
- Benchmark/Evals methodology.
- AI-agent/tooling.

Acceptance per lane:

- [ ] Reviewer role/scope and date are recorded.
- [ ] Reviewed artifacts are listed.
- [ ] Bounded questions are recorded.
- [ ] Findings or explicit no-finding disposition is recorded.
- [ ] Every finding has an accepted, rejected, or unresolved decision.
- [ ] Accepted findings link to concrete commits, docs, tests, tasks, or other
  repo artifacts.
- [ ] Claim-boundary impact is recorded.
- [ ] Reviewer identity is recorded only with permission.

Commands:

```bash
python3 scripts/validate_v1_readiness.py --allow-incomplete
```

Gate closes only when `external_review_completed` passes.

### 11. Strict Release Candidate

Goal: move from `v1-prep` to true `v1-ready`.

Acceptance:

- [ ] Release evidence JSON exists outside tracked public Git.
- [ ] Release evidence records schema version, commit SHA, benchmark source SHA,
  active private-pack fingerprint, command outcomes, exact-head CI run id/url,
  workflow name, head SHA, and privacy-scan result.
- [ ] Every required command records `exit_code: 0` and non-placeholder evidence.
- [ ] Public-view readiness fixture command is recorded as passing.
- [ ] Template placeholders such as `<log-or-run-id>` are absent.
- [ ] Strict release validation passes without `--allow-incomplete`.
- [ ] Release commit is authored as `bmendonca3`.
- [ ] Push occurs only when explicitly authorized.
- [ ] Exact-head CI passes after push.

Commands:

```bash
python3 scripts/validate_v1_readiness.py --release-evidence <external-json>
git diff --check
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

## Shared Verification Ladder

Use this after every material change:

1. Run focused tests for the changed behavior.
2. Run the relevant validator for the affected gate.
3. Run `python3 scripts/validate_public.py` after shared validator, task,
   scorer, Harbor, artifact, or claim-boundary changes.
4. Run public-view v1 readiness and confirm `v1_ready: false` until strict
   release evidence exists.
5. Run `git diff --check`.
6. Run private-source and overclaim scans before public artifact handoff.
7. Confirm tracked private/raw path scan is empty.
8. If the local review gate is used, honor the no-push constraint unless pushing is
   explicitly authorized.

## Public-Safe External Platform Follow-Up

Keep platform/framework work technical and non-attributive:

- Map AuthZBench runner, scorer, task manifest, source-summary, run-bundle,
  Docker, and private-pack assumptions to the candidate evaluation framework.
- Document expected run metadata: benchmark source SHA, task split/fingerprint,
  comparability key, source summaries, target-request coverage, private-pack
  fingerprint where applicable, and redaction rules.
- Treat outside feedback as bounded review/advisory evidence, not endorsement.
- Do not publish private names, emails, meeting details, calendar links, or
  informal signals.

## Existing Public Evidence Pointers

- 49-task checkpoint:
  `docs/checkpoints/2026-06-07-49-task-v1-prep-checkpoint.md`
- v1 hardening history:
  `docs/checkpoints/2026-06-08-v1-readiness-hardening-history.md`
- External review packet:
  `docs/reviews/external-review-packet.md`
- External review tracker:
  `docs/reviews/external-review-summary.json`
- Private holdout blocker/runbook:
  `artifact/private-holdout-operation-blocker.json`
  `artifact/private-holdout-operation-runbook.json`
- Hosted submission smoke blocker/runbook:
  `artifact/submission-runner-smoke.json`
  `artifact/hosted-submission-execution-runbook.json`
- Task scale roadmap:
  `artifact/v1-task-scale-roadmap.json`
