# Project Goal

AuthZBench-SaaS is being built to become a top benchmark for one narrow,
important question:

> Can an AI agent prove SaaS authorization failures with backend evidence, while
> avoiding false positives when the application is behaving correctly?

The current repository is a released v0.0 benchmark artifact. It is useful for
reviewing the idea, running the harness, and comparing early agents on a
medium-size public split. It is not a hosted leaderboard or community-scale
benchmark, and the project should not claim the `v1` label until the scale,
review, and submission-infrastructure gaps below are closed.

## Active Perfection Pass

Status: active as of 2026-06-07.

This pass exists to make current `main` as trustworthy as possible after the
first v1-prep task expansion. Do not mark this pass complete until every closed
item below has direct evidence, and leave externally blocked work open with the
exact blocker.

### Current Objective

Keep `main` honest as post-v0 active development: frozen v0.0 evidence remains
auditable, the current 49-task v1-prep split has verified public baseline evidence, and
every remaining v1/community-benchmark gap is visible rather than implied away.

### Verification Checklist

- [x] Active goal/checklist in this file names the exact perfection criteria.
  Evidence: this section defines the pass objective, verification checklist, and
  open gaps that must remain unchecked until real evidence exists.
- [x] Docker smoke fails clearly when Docker CLI exists but the daemon is not
  available locally.
  Evidence: direct local call to `run_container_smoke(ROOT)` prints Docker client
  information and exits with `docker daemon is required for
  --include-container-smoke; start Docker and rerun validation` when the daemon
  socket is unavailable.
- [x] GitHub Actions no longer relies on the deprecated Node 20 default for
  JavaScript actions.
  Evidence: workflow opts into Node 24 and uses Node-24-native
  `actions/checkout@v6` and `actions/setup-python@v6`; GitHub Actions run
  `27083608925` passed on `main` with no Node 20 annotation in the watch output.
- [x] Focused tests for changed validation behavior pass.
  Evidence: `python3 -m unittest discover -s tests -p
  'test_validate_public.py'` and the full test suite pass.
- [x] Full public validation without local Docker smoke passes.
  Evidence: `python3 scripts/validate_public.py --include-scripted-baseline`
  passed on commit `ede97d01ecb708feb24985dec0fc3b51d37ac7d1` for the current
  49-task public split.
- [x] Docker-backed public validation is confirmed by GitHub Actions on `main`.
  Evidence: GitHub Actions run `27083952334` passed on `main` for commit
  `ede97d01ecb708feb24985dec0fc3b51d37ac7d1`.
- [x] Privacy scan shows no tracked private holdouts, raw results, captures, or
  panel logs.
  Evidence: `git ls-files tasks_private/holdout results captures
  docs/reviews/panel-logs` returns no tracked paths.
- [x] Tracked working tree is clean after generated validation artifacts are
  removed.
  Evidence: generated `results/validation-scripted-baseline/...` output was
  removed after validation, leaving no tracked working-tree changes before the
  pushed implementation commit.
- [x] Commit is authored as `bmendonca3` and pushed to `main`.
  Evidence: commit `ede97d01ecb708feb24985dec0fc3b51d37ac7d1` is authored and
  committed as `bmendonca3 <bmendonca3@users.noreply.github.com>` and is present
  on both `origin/main` and `origin/v1-task-expansion`.
- [x] One current 49-task no-tools model-family baseline has repeated tracked
  artifacts.
  Evidence: `kiro-claude-haiku-4-5-current-public-49` is registered with two
  current public split Haiku runs, `task_count: 49`, `run_count: 2`,
  `harness_type: no-tools-model`, and explicit non-leaderboard claim-boundary
  text.
- [x] Current 49-task no-tools model baselines have five repeated tracked model
  families.
  Evidence: `kiro-claude-haiku-4-5-current-public-49`,
  `kiro-claude-sonnet-4-6-current-public-49`,
  `kiro-qwen3-coder-next-current-public-49`, `kiro-glm-5-current-public-49`,
  and `kiro-claude-opus-4-6-current-public-49` are registered as current public
  split no-tools model baselines with `run_count: 2`, distinct
  `run_artifacts`, `task_count: 49`, matching model labels, benchmark commit
  `1eaac973ffe5229dad5796b9a5b144fa3af37a3a`, and non-leaderboard
  claim-boundary notes.
- [x] Current 49-task live HTTP tool-agent baseline has repeated tracked runs
  with target-request correlation.
  Evidence: `kiro-live-tool-agent-sonnet-current-public-49` is registered as a
  current public split tool-agent baseline with two `claude-sonnet-4.6` Kiro live
  HTTP runs from benchmark commit
  `3d4293cd24305ad410ddad8cb68654bf10adc9ff`. Run
  `20260607T071431380750Z-fc6636f1` reports `task_count: 49`,
  `model_tool_plan_artifact_count: 49`, `per_task_tool_probe_artifact_count:
  49`, `target_request_correlated_task_count: 49`,
  `target_request_coverage_rate: 1.0`, `planner_failure_count: 0`,
  `planner_parse_error_count: 0`, and `executed_tool_probe_total: 124`. Run
  `20260607T072056877797Z-2be17ca0` reports the same 49/49 artifact and
  correlation counts, `target_request_coverage_rate: 1.0`, zero planner/parser
  failures, and `executed_tool_probe_total: 126`.
- [x] Baseline registry and release gates recognize the new evidence.
  Evidence: `python3 scripts/validate_baseline_registry.py` passes with
  `baseline_count: 23`, `current_public_model_family_count: 6`,
  `repeated_model_baseline_count: 6`, `has_current_public_tool_agent_baseline:
  true`, `v0_baseline_ready: true`, `v0_release_snapshot_ready: true`, and no
  unmet baseline requirements. Strict `python3 scripts/validate_v0_release.py`
  passes with all 8 gates green and `v0_ready: true` in this maintainer checkout.
- [x] Current public tool-agent baseline checkpoint is committed, pushed, and CI
  verified.
  Evidence: commit `fd0bfcb41e0f8db0b52a0a7f56106c9c2e2e416b` (`Add current
  public tool-agent baseline evidence`) is authored as `bmendonca3`, pushed to
  both `origin/v1-task-expansion` and `origin/main`, and GitHub Actions run
  `27086361745` passed the `Validate AuthZBench-SaaS` workflow on `main`.

### Open Perfection Gaps

These remain intentionally open until real evidence exists:

- [ ] Boundary-reasoning calibration study completed and reflected in the paper.
- [ ] External AppSec, benchmark/evals, and AI-agent/tooling review lanes
  completed.
- [ ] Rotating private holdout and hosted or fully containerized submission
  governance defined for v1/community use.

## Current Goal Statement

Build AuthZBench-SaaS into a public benchmark that serious AI-agent and
application-security researchers can trust for SaaS authorization testing. The
work should move through normal SDLC checkpoints: goal and roadmap design,
target/task expansion, scorer and runner hardening, baseline refreshes,
sectional panel review, privacy validation, fresh-clone validation, and
release-readiness review. The repository should include a clear roadmap and
should use commits that match those checkpoints instead of burying the work in
one large change.

The ambition is to become a top benchmark, but the label has to be earned. The
current repo has crossed the v0.0 release threshold with protected private
evidence, live-target proof, repeated real model and agent baselines,
anti-gaming controls, clean packaging, and review artifacts. It still needs v1
scale, rotating holdouts, external review, and hosted or fully containerized
submission infrastructure before stronger community-benchmark claims are fair.

## Operating Contract

### Outcome

Turn AuthZBench-SaaS from a promising alpha into one of the strongest public
benchmarks for multi-tenant SaaS authorization reasoning. A strong score should
mean an agent can reason through actors, roles, tenants, organizations, objects,
API tokens, audit logs, admin settings, sharing links, secure controls, and
replayable HTTP evidence.

The benchmark should reward agents that:

- prove vulnerable behavior with replayable backend evidence
- name the correct actor, role, tenant, organization, object, and scope boundary
- distinguish allowed access from broken authorization
- avoid findings on secure controls
- stay inside the benchmark policy and target scope

The benchmark should penalize agents that:

- guess from route names or task wording alone
- submit polished prose without replayable proof
- over-report every sensitive endpoint
- rely on memorized public manifests instead of live reasoning
- ignore tenant, role, token, or object boundaries

### Verification Surface

Progress toward a release-worthy benchmark must be backed by concrete evidence:

- unit tests, manifest validation, compile checks, and Docker Compose validation
- deterministic scorer transcripts and scripted sanity baselines
- live HTTP target smoke tests and target-side request-log correlation when
  Docker is available
- repeated real model or agent baselines with exact commands, model labels,
  commit SHAs, result bundles, and variance notes
- private holdout validation outside public Git history
- privacy scans proving no secrets, personal paths, private holdouts, cookies,
  tokens, or unrelated local data are committed
- sectional panel review notes under `docs/reviews/` for major benchmark areas
- fresh public-clone validation before public release claims

### Top-Benchmark Bar

To be worth citing, AuthZBench-SaaS has to do more than run. It has to be
harder to game than a task list, clearer than a demo repo, and fair enough that
model comparisons mean something.

The benchmark should be judged on five qualities:

- realism: tasks should resemble real SaaS authorization mistakes without using
  real customer, employer, school, bounty, or personal data
- proof: successful findings should replay against the backend, not just read
  well as vulnerability reports
- controls: safe behavior should be tested as carefully as vulnerable behavior
- comparability: model and agent runs should preserve exact commands, settings,
  commit SHAs, result bundles, and repeated-run notes
- resilience: private holdouts, seeds, route aliases, decoys, and protected
  execution should reduce the value of memorizing public manifests

### Constraints

- Keep the public repo honest as a released v0.0 artifact until v1 gates pass.
- Keep the benchmark focused on SaaS authorization, not generic CTF coverage.
- Keep synthetic data synthetic; do not copy real customer, employer, bug bounty,
  school, or personal data.
- Keep private holdouts out of public Git history.
- Do not let headline scores hide false-positive behavior.
- Do not present one-off model runs as stable leaderboard results.
- Do not commit raw panel logs, local captures, result bundles, secrets, or
  personal/private information.

### Boundaries

Work should stay inside the benchmark repo and its ignored local evidence
folders. Public-facing changes belong in docs, tasks, apps, scorer/harness code,
tests, baseline summaries, and release artifacts. Externally visible GitHub work
must use the public `github.com` repo, the configured maintainer author identity,
and normal commits at meaningful SDLC checkpoints.

High-blast-radius actions require explicit review before proceeding: publishing
a release tag, changing leaderboard scoring semantics, exposing private holdouts,
rewriting public history, adding real-world data, or changing external GitHub
state beyond ordinary commits and pushes for this repo.

### Iteration Policy

Improve the benchmark section by section:

1. Define the section's purpose and threat model.
2. Add or update target behavior, tasks, scorer logic, docs, and tests.
3. Run focused local verification.
4. Run sectional panel review and record accepted/rejected findings.
5. Fix valid findings.
6. Refresh baselines or status docs when behavior changes.
7. Commit at a natural SDLC checkpoint with a clear message.
8. Re-run public validation and privacy scans before pushing.

If a section cannot be fully validated because Docker, model quota, credentials,
or private holdout infrastructure is unavailable, record the gap plainly and
continue with the strongest safe local work.

### Blocked Stop Condition

Do not claim the benchmark is leaderboard-ready, v1, community-scale, or
top-tier if any core proof surface is missing: rotating private holdouts,
third-party runs, repeated private tool-agent evidence, hosted/containerized
submission handling, variance analysis, external review, or public-clone
validation for the relevant release. If a blocker requires unavailable
infrastructure or user action, record the exact blocker, preserve the evidence
gathered, and keep the goal active rather than downgrading the standard.

## v0 Release Goal

The real `v0` goal was to ship the first version that other researchers can use
without mentally discounting every headline score. The `v0.0` release now
satisfies this Level 1 goal while leaving v1/community-benchmark work open.

To call the project `v0`, the repo should have:

- 6 synthetic SaaS apps
- 40-50 public tasks
- 20-30 private holdout tasks outside public Git history
- at least 40 percent secure controls, counting both denial controls and
  authorized-allow controls
- at least 10 authorized-allow controls that prevent "everything is a bug"
  strategies
- route aliases, decoys, seeded IDs, and multi-seed private holdouts
- target/proxy-side request logs correlated into per-task result artifacts
- repeated baselines across at least five real model or agent families
- one or more tool-equipped agent baselines, not only no-tools model runs
- CI, live Docker validation, and fresh public-clone validation
- sectional panel review for goal, roadmap, and release criteria; task realism
  and vulnerability/control mix; scorer, runner, request-log correlation, and
  live-target proof; baseline methodology and leaderboard schema; holdout,
  contamination, and anti-gaming design; and privacy scan, packaging, and final
  release readiness
- public docs that clearly separate alpha results, public-split development
  results, and private-holdout leaderboard results

Those gates are now met for the v0.0 release. The honest next label remains
released v0.0 until v1-scale evidence is added.
