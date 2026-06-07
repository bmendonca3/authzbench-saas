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
auditable, the current 49-task v1-prep split has verified sanity evidence, and
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
- [ ] GitHub Actions no longer relies on the deprecated Node 20 default for
  JavaScript actions.
  Blocker: GitHub rejected the workflow-file update because the current token
  does not have `workflow` scope. Leave this open until the workflow can be
  updated and a pushed `main` run confirms the warning is gone.
- [x] Focused tests for changed validation behavior pass.
  Evidence: `python3 -m unittest discover -s tests -p
  'test_validate_public.py'` and the full test suite pass.
- [x] Full public validation without local Docker smoke passes.
  Evidence: `python3 scripts/validate_public.py --include-scripted-baseline`
  passes on the current 49-task public split.
- [ ] Docker-backed public validation is confirmed by GitHub Actions on `main`.
  Blocker: pending push and new workflow run on `main`.
- [x] Privacy scan shows no tracked private holdouts, raw results, captures, or
  panel logs.
  Evidence: `git ls-files tasks_private/holdout results captures
  docs/reviews/panel-logs` returns no tracked paths.
- [ ] Working tree is clean after generated validation artifacts are removed.
  Blocker: pending commit.
- [ ] Commit is authored as `bmendonca3` and pushed to `main`.
  Blocker: pending commit and push.

### Open Perfection Gaps

These remain intentionally open until real evidence exists:

- [ ] Current 49-task no-tools model baselines rerun with repeated artifacts.
- [ ] Current 49-task live HTTP tool-agent baselines rerun with target-request
  correlation.
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
