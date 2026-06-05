# Roadmap

AuthZBench-SaaS is currently an alpha/pre-v0 preview. The long-term goal is to
make it a top benchmark for measuring whether AI agents can prove SaaS
authorization bugs without inventing findings.

The benchmark should become known for one thing: realistic authorization
boundary testing. It should stay focused on users, roles, tenants,
organizations, objects, API tokens, sharing flows, and backend proof.

## North Star

AuthZBench-SaaS should be useful to three groups:

- security researchers evaluating AI agents
- builders comparing agent harnesses
- application-security teams checking whether an AI can prove access-control
  bugs instead of writing plausible reports

A top result should mean the agent:

- found real authorization failures
- identified the correct actor, role, tenant, organization, and object boundary
- submitted evidence that replays against the backend
- avoided false positives on secure controls
- stayed inside the benchmark policy

The working goal is tracked in [`docs/goal.md`](docs/goal.md). In short: keep
the current repo honest as alpha/pre-v0, then earn the `v0` label through scale,
protected holdouts, live-target proof, repeated baselines, and sectional review.

## SDLC And Review Rhythm

Changes should land in auditable checkpoints instead of one large release dump.
The intended contribution rhythm is:

1. Scope or design commit for goals, roadmap, release gates, or architecture.
2. Target-app/task commits for each new benchmark surface.
3. Scorer, runner, logging, and anti-gaming commits when proof semantics change.
4. Baseline/status commits after result artifacts or task counts change.
5. Release-readiness commits after validation, privacy scans, panel review
   dispositions, and fresh-clone checks.

For material sections, preserve a short review artifact under `docs/reviews/`
with the review question, evidence packet, accepted findings, rejected findings
when relevant, and follow-up work. Raw model or CLI logs should not be committed.

Sectional panel review is required before the project claims a section is
release-ready. The minimum sections are:

- goal, roadmap, and release criteria
- task realism and vulnerability/control mix
- scorer, runner, live-target proof, and request-log correlation
- baseline methodology and leaderboard schema
- holdout, contamination, and anti-gaming design
- privacy scan, packaging, and final release readiness

## Milestone 1: Alpha Preview Stabilization

Status: in progress.

This milestone keeps the current public split honest and easy to inspect.

- [x] Publish six synthetic SaaS target apps.
- [x] Publish 44 seeded public tasks.
- [x] Include vulnerable tasks and secure controls.
- [x] Add deterministic scorer replay transcripts.
- [x] Add scripted and live HTTP scripted harness baselines.
- [x] Add early model baselines.
- [x] Reframe the repository as alpha/pre-v0 instead of a finished v0.
- [x] Add public v0 release criteria.
- [x] Add a draft benchmark card.
- [x] Add a changelog for task and scorer changes.
- [x] Add a prototype route alias and decoy endpoint exercised by public
      controls.
- [x] Add target-side JSONL request logs for Docker HTTP targets.
- [x] Add alpha runner correlation from target logs into per-task artifacts.
- [ ] Add CI for unit tests, manifest validation, compile checks, and Docker
      config.
- [x] Keep sectional review notes current as each benchmark section changes.
- [x] Preserve a public roadmap and goal contract for the path to v0.

Exit criteria:

- local validation passes
- docs avoid overclaiming
- public clone validates
- no private or personal data is committed
- commits are grouped into meaningful SDLC checkpoints

## Milestone 2: Real v0 Scope

Status: planned.

This milestone turns the prototype into a credible public benchmark.

Milestones 2, 3, and 4 are all prerequisites for the real `v0` release tag.
Detailed task counts live in [`docs/v0-release-plan.md`](docs/v0-release-plan.md).

- [x] Expand from 5 to 6 synthetic SaaS apps.
- [x] Grow to 40-50 public tasks.
- [ ] Add 20-30 private holdout tasks outside public Git history.
- [x] Add an ignored local private-holdout rehearsal generator and validator
      path so maintainers can test the private-pack workflow without committing
      private JSON.
- [ ] Keep secure controls at 40 percent or more of total tasks.
- [x] Add deeper invite/membership and audit/settings boundaries.
- [x] Add at least 10 authorized-allow controls so agents cannot classify every
      sensitive route as a bug.
- [ ] Expand route aliases and decoy endpoints across apps.
- [ ] Harden per-task request-log correlation for leaderboard-grade live-agent
      runs and Docker CI.
- [ ] Add benchmark version fields to all run summaries.
- [x] Add a v0 task build matrix with public/private allocations per app.
- [ ] Require sectional panel review before declaring any new app/task family
      release-ready.

Exit criteria:

- public and private task counts meet the v0 target
- task manifests validate
- scorer replay and leaderboard-grade per-task request-log correlation both work
- public docs clearly separate public-split results from private holdout results

## Milestone 3: Baseline Credibility

Status: planned.

This milestone makes the benchmark useful for comparison rather than only
inspection.

- [ ] Run at least five agent/model families.
- [ ] Run repeated trials for each serious baseline.
- [ ] Report exploit-proven success separately from false-positive rate.
- [ ] Preserve exact model labels, harness settings, commands, commit SHA, and
      result bundles.
- [ ] Add variance or confidence notes when runs are repeated.
- [ ] Add leaderboard examples that do not rank by blended score alone.
- [ ] Preserve one public baseline report per serious model/agent family.
- [ ] Re-run legacy model baselines after task-set changes before release tags.
- [ ] Replace alpha compatibility subscores with v0 metrics that avoid
      agent-independent control credit on vulnerable tasks.

Exit criteria:

- baseline table has enough coverage to show model differences
- result artifacts can be traced back to commands and commit IDs
- no one-off model score is presented as a stable leaderboard result

## Milestone 4: Benchmark Hardening

Status: planned.

This milestone protects against gaming and accidental leakage.

- [ ] Keep private holdouts out of public Git history.
- [ ] Add multiple seeds per task for scored runs.
- [ ] Randomize harmless response details where semantics are unchanged.
- [ ] Add hidden oracle details for private holdouts.
- [ ] Add isolated or containerized agent execution for leaderboard runs.
- [ ] Add hosted, maintainer-run, or otherwise protected private-holdout
      execution so participants do not receive readable holdout manifests.
- [x] Add privacy and secret scanning to the release validation script and
      checklist.
- [x] Add a reproducible fresh-clone validation script.
- [x] Harden private holdout pack validation for app coverage, control subtype
      mix, and public ID/seed overlap.
- [x] Add an ignored local rehearsal-pack generator that validates the private
      holdout machinery while clearly disallowing leaderboard use.
- [ ] Add a release-readiness panel review with explicit dispositions for
      privacy, holdouts, anti-gaming, and baseline claims.

Exit criteria:

- a public model cannot get a strong score by memorizing public task manifests
- private holdout scores are separated from public development scores
- release validation can be repeated by another maintainer

## Milestone 5: v1 Candidate

Status: future.

Save the `v1` label for a version with external feedback and enough scale to be
used seriously.

- [ ] At least 100 total tasks across public and private splits.
- [ ] Independent external review of task design and scoring.
- [ ] External-review-ready benchmark card with limitations and intended use.
- [ ] Stable leaderboard submission schema.
- [ ] Documented policy for task additions, removals, and deprecated scores.
- [ ] At least one third-party agent or researcher run.

Exit criteria:

- outside users can run the benchmark without local handholding
- task quality has survived independent review
- leaderboard claims are backed by private holdouts and repeatable artifacts

## Version Labels

- Current repository state: `alpha preview` or `pre-v0`
- Alpha tags: `alpha-<semver>-public-scaffold`
- Local alpha runs: `alpha-<semver>-public-scaffold-local`
- First release-worthy benchmark: `v0`, only after Milestones 2, 3, and 4 meet
  their exit criteria
- Mature, externally validated benchmark: `v1`
