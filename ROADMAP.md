# Roadmap

AuthZBench-SaaS is a v0.0 release candidate for evaluating whether AI agents
can prove SaaS authorization failures with backend evidence while avoiding false
positives on secure controls.

The project should stay focused. It is not a general cyber benchmark. It is a
benchmark for authorization boundaries: tenants, organizations, users, roles,
objects, API tokens, scopes, sharing flows, admin actions, and replayable proof.

## North Star

A strong AuthZBench-SaaS result should mean that an agent:

- found a real authorization failure
- identified the correct actor, role, tenant, organization, object, or token
  boundary
- submitted evidence that replays against the backend
- avoided false positives on secure controls
- stayed inside the benchmark policy

The project becomes valuable only if those results are comparable, repeatable,
and hard to game through public task memorization.

## Current Release State

Current state: **v0.0 release candidate**.

Evidence already in place:

- 6 synthetic SaaS apps
- 46 public tasks
- 24 maintainer-only private holdout tasks in the local private pack
- deterministic backend replay scoring
- target-side request logging for live HTTP runs
- five repeated current public model/agent baseline families
- one repeated current public live HTTP tool-agent family
- protected private-holdout aggregate evidence
- one source-backed private no-tools leaderboard-candidate row
- public-safe charts and task-quality matrix
- release evidence registry
- privacy checks, fresh-clone validation path, Docker smoke, and CI

Not yet in place:

- pushed `v0.0` tag for the final post-CI commit
- hosted public leaderboard
- repeated private tool-agent leaderboard row
- rotating private holdout packs
- third-party runs or independent external review
- v1-scale task volume and methodology paper

## Maturity Levels

**Level 1: v0 benchmark.** The first legitimate public release. It requires a
frozen public split, frozen scoring/evidence contracts, repeated current
baselines, verified private-holdout separation, release evidence, privacy
checks, CI, fresh-clone validation, and a `v0.0` tag. It does not require a
hosted leaderboard.

**Level 2: research artifact.** A benchmark that can support academic or
industry research. It needs independent review, reproducibility evidence,
variance analysis, comparison against existing security benchmarks, and a paper
or technical report.

**Level 3: community benchmark.** A benchmark people can submit to and track
over time. It needs a public submission pipeline, hosted or fully containerized
evaluation, rotating holdouts, multiple task packs, external contributors, and
leaderboard governance.

## Immediate Release Path: v0.0

Status: in progress.

Goal: publish a clean `v0.0` tag only after release evidence, README wording,
privacy checks, fresh-clone validation, and CI all align to the final pushed
commit.

- [x] Build public 46-task split across 6 apps.
- [x] Add current repeated public baselines for 5 model/agent families.
- [x] Add strict v0 release-gate validator.
- [x] Add protected private-holdout aggregate evidence.
- [x] Add source-backed leaderboard-submission validation.
- [x] Add release notes for `v0.0`.
- [x] Update README and roadmap to reflect v0.0 release-candidate status.
- [ ] Commit final release-wiring changes.
- [ ] Run local validation on the final commit candidate.
- [ ] Run privacy checks against tracked files.
- [ ] Run public fresh-clone validation from GitHub.
- [ ] Push final release-wiring commit to `main`.
- [ ] Confirm GitHub Actions passes on that exact commit.
- [ ] Tag and push `v0.0`.

Exit criteria:

- `python3 scripts/validate_public.py --include-scripted-baseline` passes
- container smoke path passes locally or in CI
- `python3 scripts/validate_v0_release.py` passes in a maintainer checkout
- `git ls-files tasks_private/holdout results captures docs/reviews/panel-logs`
  returns nothing
- fresh public clone validates
- exact-head GitHub Actions passes
- tag target is the same pushed commit that passed CI

## Milestone 1: Public Scaffold and v0 Scope

Status: complete for v0.0.

- [x] Publish six synthetic SaaS target apps.
- [x] Publish 46 seeded public tasks.
- [x] Include vulnerable tasks, denial controls, and authorized-allow controls.
- [x] Add deterministic scorer replay transcripts.
- [x] Add Docker request logging for live HTTP runs.
- [x] Add route aliases and decoy endpoints.
- [x] Add first public multi-step workflow wave.
- [x] Add public benchmark card and methodology docs.
- [x] Add task-quality rubric and generated task-quality matrix.
- [x] Add public-safe benchmark charts.

Next improvements:

- [ ] Expand multi-step workflows beyond the first project-management wave.
- [ ] Add more state-changing authorization tasks across billing, support,
      file sharing, API tokens, and audit settings.
- [ ] Increase task count toward v1 scale without diluting control quality.

## Milestone 2: Baseline Credibility

Status: v0.0 candidate complete; v1 work remains.

- [x] Run repeated current baselines for at least five model/agent families.
- [x] Include at least one live HTTP tool-agent family.
- [x] Preserve exact model labels, harness settings, commands, commit SHAs, and
      source artifact paths.
- [x] Separate exploit-proven success, vulnerable full pass, false-positive
      rate, boundary reasoning, control execution, and target-request coverage.
- [x] Mark stale 44-task snapshots as historical only.
- [x] Add baseline registry validation.
- [x] Add generated public-safe charts from baseline artifacts.

Next improvements:

- [ ] Add repeated private tool-agent evidence.
- [ ] Add at least one third-party or independently operated agent run.
- [ ] Add statistical variance analysis for repeated baselines.
- [ ] Re-run key baselines after any task/scoring change before comparing
      scores.

## Milestone 3: Private Holdouts and Anti-Gaming

Status: v0.0 candidate evidence exists; v1 hardening remains.

- [x] Keep private holdouts out of public Git history.
- [x] Validate private holdout app coverage, vulnerable/control mix, route
      variants, decoys, and public-overlap checks.
- [x] Add protected private execution with host private-path denial on macOS.
- [x] Publish only redacted aggregate private evidence.
- [x] Add one eligible source-backed private no-tools leaderboard-candidate row.
- [x] Document rotating private holdout protocol.

Next improvements:

- [ ] Implement rotating multi-pack private holdouts.
- [ ] Add repeated private tool-agent leaderboard-candidate rows.
- [ ] Add leakage-response and holdout-retirement workflow tests.
- [ ] Add stronger non-macOS isolation story for protected private execution.

## Milestone 4: Leaderboard and Submission Infrastructure

Status: schema ready; hosted/community path not ready.

- [x] Add `leaderboard-submission-v1` schema.
- [x] Add source-summary validation.
- [x] Add benchmark fingerprints and comparability keys.
- [x] Require repeated-run provenance for eligible rows.
- [x] Separate schema-valid evidence from leaderboard eligibility.

Next improvements:

- [ ] Add a maintainer-operated submission review workflow.
- [ ] Add hosted or fully containerized evaluation.
- [ ] Add signed or attestable run bundles.
- [ ] Publish leaderboard governance rules.
- [ ] Add clear rules for reruns, ties, stale scores, and task-pack rotations.

## Milestone 5: Research-Grade v1

Status: future.

Save the `v1` label for a version that has scale, independent review, and
research-grade methodology.

- [ ] At least 100 total tasks across public and private splits.
- [ ] Multiple multi-step workflow families.
- [ ] Independent external task and scoring review.
- [ ] Third-party agent runs.
- [ ] Statistical variance analysis across repeated baselines.
- [ ] Comparison against existing security benchmarks.
- [ ] Public technical report or benchmark paper.
- [ ] Reproducibility packet for researchers.

Exit criteria:

- outside users can run the public harness without local handholding
- private evaluation can be operated without leaking holdouts
- score comparability is clear across versions
- task quality has survived independent review
- claims are backed by repeatable artifacts, not just documentation

## SDLC and Review Rhythm

Changes should land in auditable checkpoints:

1. Scope or design commit for goals, roadmap, release gates, or architecture.
2. Target-app/task commits for new benchmark surfaces.
3. Scorer, runner, logging, and anti-gaming commits when proof semantics change.
4. Baseline/status commits after result artifacts or task counts change.
5. Release-readiness commits after validation, privacy scans, review
   dispositions, and fresh-clone checks.

For release-facing sections, preserve a short public-safe review artifact under
`docs/reviews/`. Raw model or CLI logs should not be committed.

## Version Labels

- `alpha/pre-v0`: development state before a clean first release
- `v0.0-candidate`: strict v0 evidence exists, but final tag has not landed
- `v0.0`: first evidence-backed release snapshot
- `v1`: externally reviewed, scaled, research-grade benchmark

Do not call the project leaderboard-ready until the hosted or containerized
submission process exists and private-holdout scoring is operational at that
level.
