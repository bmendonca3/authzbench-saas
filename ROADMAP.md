# Roadmap

AuthZBench-SaaS is an internally validated SaaS authorization benchmark artifact
for evaluating whether AI agents can prove access-control failures with backend
evidence while avoiding false reports on secure controls.

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

Current state: **v1.0-internal complete** under the internal/non-external release
definition.

`v1.0-internal` means the repository-side benchmark artifact, validators,
public/private task scale, claim boundary, and host-review packaging are aligned.
It does not claim independent external review, SaaS-provider validation, hosted
operation, platform acceptance, or third-party submissions. Those remain v2
external-validation tracks in
[`docs/claims-and-evidence.md`](docs/claims-and-evidence.md#5-deferred-v2-validation-tracks).

Evidence already in place:

- 6 synthetic SaaS apps
- frozen v0.0 release snapshot with 46 public tasks
- current v1.0-internal public split with 63 public tasks
- 48 maintainer-private holdout tasks, summarized only
- 111 total public + private task scale
- deterministic backend replay scoring
- target-side request logging for live HTTP runs
- five repeated frozen v0.0 public model/agent baseline families
- one repeated frozen v0.0 public live HTTP tool-agent family
- current 63-task scripted harness sanity baseline
- current 63-task public model and live HTTP tool-agent capability baselines remain a gap until full reruns or promoted-composite refreshes complete
- five repeated historical 49-task public no-tools model-family baselines,
  now stale for current comparison
- one repeated historical 49-task public live HTTP tool-agent baseline, now
  stale for current comparison
- protected private-holdout aggregate evidence
- one source-backed private no-tools leaderboard-candidate row with
  runner-emitted fingerprint provenance
- public-safe charts and task-quality matrix
- release evidence registry
- privacy checks, fresh-clone validation path, Docker smoke, and CI
- public-safe task-quality gate contract
- repo-side Harbor adapter package, CLI, scorer bridge, local smoke, parity
  methodology, dataset validator, and metadata/parity validators
- Kaggle-like host review package and validation commands

Not yet in place:

- independent external review
- SaaS-provider scenario validation
- hosted/public submission operation
- Harbor/Kaggle/platform acceptance
- third-party runs
- externally validated methodology paper or research-grade review packet

## Maturity Levels

**Level 1: v0 benchmark.** The first legitimate public release. It requires a
frozen public split, frozen scoring/evidence contracts, repeated release-snapshot
baselines, verified private-holdout separation, release evidence, privacy checks,
CI, fresh-clone validation, and a `v0.0` tag. It does not require a hosted
leaderboard.

**Level 2: v1 internal artifact.** The current repository-side release state. It
requires 63 public tasks, private-holdout governance, 111 total public/private
task scale, deterministic scoring, current public-view readiness gates, public
validation, host-review packaging, and claim-boundary enforcement. It does not
require external review or platform acceptance.

**Level 3: v2 externally validated benchmark.** A benchmark that can support
external research or broader submissions. It needs independent review,
SaaS-provider validation, hosted or fully containerized operation, third-party
runs, platform review if pursued, and leaderboard governance. This is not in the
`v1.0-internal` release scope and uses the forbidden-phrase list in
`docs/claims-and-evidence.md` to gate wording.

## Reviewer Roadmap At A Glance

This section is the reviewer-facing roadmap. It separates what is left to call
v1 fully done, what must happen before v2 external validation can start, and
what polish is needed for host/reviewer presentation. The historical milestone
detail follows below. The canonical claim ledger remains
[`docs/claims-and-evidence.md`](docs/claims-and-evidence.md); nothing in this
section strengthens or weakens any canonical claim, and all wording is subject
to the CI forbidden-phrase check at `scripts/check_claim_boundary.py`.

### roadmap gaps

`v1.0-internal` is complete under the internal/public-view release definition.
The gaps below are remaining v1-scope improvements that do **not** gate the
`v1.0-internal` label and do not introduce any external-validation claim. Each
row lists an owner role, a verification command, and a status.

| Gap | Owner | Verification | Status |
| --- | --- | --- | --- |
| Expand multi-step workflow tasks without diluting control quality | maintainer | `python3 scripts/validate_public.py --include-scripted-baseline` exits 0 and task-quality gate passes | open |
| Add state-changing authorization tasks across billing, support, file sharing, API tokens, and audit settings | maintainer | public task-quality matrix regenerates and task-quality gate passes | open |
| Keep public/private task-pack changes tied to refreshed baselines | maintainer | baseline registry validation passes and stale rows are marked | open |
| Add repeated private tool-agent leaderboard-candidate rows | maintainer | leaderboard submission validation accepts the new rows with runner-emitted fingerprint provenance | open |
| Add leakage-response and holdout-retirement workflow tests | maintainer | private-holdout lifecycle validators pass | open |
| Add stronger non-macOS isolation story for protected private execution | maintainer | protected private execution denial recorded on at least one non-macOS host | open |
| Add a maintainer-operated submission review workflow | maintainer | leaderboard governance rules validator passes against the new workflow | open |
| Add at least one third-party or independently operated agent run (v1-scope sanity, not external review) | maintainer | baseline registry records the run with provenance; row is not labeled external review | open |

None of the above claims independent external review, SaaS-provider validation,
hosted leaderboard availability, Harbor/Kaggle platform acceptance, or
third-party submissions as completed. Those remain v2 prep tracks below.

### v2 external-validation prep

The v2 tracks are deferred and gated. They are listed here as prep work with
dependencies and entry criteria so a reviewer can see what must happen before
v2 external validation can start. None of these tracks has happened yet; the
forbidden-phrase boundary in `docs/claims-and-evidence.md` enforces that
wording stays preparatory.

| Track | Dependencies | Entry criteria | Status |
| --- | --- | --- | --- |
| Independent AppSec review | reviewer recruitment; `docs/reviews/external-review-packet.md` intake packet | packet complete and at least one independent AppSec reviewer engaged | not started |
| Benchmark and evals methodology review | independent AppSec review lane scoped | technical reports and split/scoring semantics packaged for an independent evals reviewer | not started |
| AI-agent and tooling review | independent evals review lane scoped | harness types, tool access, and comparability keys documented for an independent agent reviewer | not started |
| SaaS-provider scenario validation | at least one SaaS authorization provider willing to validate task scenarios | oracle logic and task scenarios packaged for provider review | not started |
| Hosted leaderboard operation | submission review workflow proven; containerized evaluation path proven | hosted or fully containerized evaluation exists and private-holdout scoring is operational at that level | not started |
| Harbor / Kaggle platform review (optional) | full Harbor adapter parity proven; hosted leaderboard operation track advanced | platform publishing and platform review pursued only after parity and hosted operation are real | not started |
| Third-party submissions | submission governance rules published; hosted leaderboard operation track advanced | submission gates opened only after governance and hosted operation are real | not started |
| Externally validated v1 release | all three required review lanes (AppSec, evals, agent/tooling) record real human decisions | v2 validation release complete only after all three lanes record real dispositions | not started |

The dependency chain is: recruit reviewers → run the three independent review
lanes → record real dispositions → only then pursue SaaS-provider validation,
hosted leaderboard operation, optional platform review, and third-party
submissions. Do not mark any v2 track complete until its entry criteria are met
and real evidence is recorded in `docs/reviews/external-review-summary.json`.

### repo-presentation polish

A concise checklist for host/reviewer presentation readiness. Items that would
require editing files other than `ROADMAP.md` are listed as future checklist
items only and are not in scope for a roadmap-only round.

- [x] One canonical docs navigation map reachable from README and ROADMAP
      (`docs/index.md`) so a reviewer has a single entry point.
- [ ] Evidence pointers from ROADMAP and README resolve to the canonical claim
      ledger and the release-evidence registry without dead links.
- [x] Reviewer walkthrough (`docs/reviewer-walkthrough.md`) matches the current
      63-task public split and 111 total public/private task scale.
- [x] Host review package and validation commands
      (`docs/validation-commands.md`) match the current validator set.
- [ ] Public-safe charts and task-quality matrix reflect the current public
      split, not a stale snapshot.
- [x] Harbor integration runbook (`docs/harbor-integration-runbook.md`) wording
      stays local-maintainer-only and does not claim Harbor platform acceptance
      or endorsement.
- [x] README "Roadmap At A Glance" table stays aligned with this section.
- [x] No tracked file contains a forbidden phrase outside an allowed negation
      context (`scripts/check_claim_boundary.py` exits 0).

## Completed Release Path: v0.0

Status: complete.

Goal: publish a clean `v0.0` tag only after release evidence, README wording,
privacy checks, fresh-clone validation, and CI all align to the final pushed
commit.

- [x] Build public 46-task split across 6 apps.
- [x] Add repeated frozen v0.0 public baselines for 5 model/agent families.
- [x] Add strict v0 release-gate validator.
- [x] Add protected private-holdout aggregate evidence.
- [x] Add source-backed leaderboard-submission validation.
- [x] Add release notes for `v0.0`.
- [x] Update README and roadmap to reflect v0.0 release status.
- [x] Commit final release-wiring changes.
- [x] Run local validation on the final commit candidate.
- [x] Run privacy checks against tracked files.
- [x] Run public fresh-clone validation from GitHub.
- [x] Push final release-wiring commit to `main`.
- [x] Confirm GitHub Actions passes on that exact commit.
- [x] Tag and push `v0.0`.

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

Status: complete for v1.0-internal.

- [x] Publish six synthetic SaaS target apps.
- [x] Publish 46 seeded public tasks.
- [x] Expand to 60 current public tasks.
- [x] Include vulnerable tasks, denial controls, and authorized-allow controls.
- [x] Add deterministic scorer replay transcripts.
- [x] Add Docker request logging for live HTTP runs.
- [x] Add route aliases and decoy endpoints.
- [x] Add public multi-step workflow coverage.
- [x] Consolidate benchmark scope and methodology into
      `docs/benchmark-spec.md`.
- [x] Add task-quality rubric and generated task-quality matrix.
- [x] Add machine-readable task-quality gate validation for public manifests.
- [x] Add public-safe benchmark charts.

Next improvements:

- [ ] Continue expanding multi-step workflows without diluting control quality.
- [ ] Add more state-changing authorization tasks across billing, support, file
      sharing, API tokens, and audit settings.
- [ ] Keep public/private task-pack changes tied to refreshed baselines.

## Milestone 2: Baseline Credibility

Status: complete for v1.0-internal; external run evidence remains v2 work.

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
- [x] Add statistical variance analysis for repeated baselines.
- [x] Add boundary-reasoning calibration for the historical 49-task public
      tool-agent evidence and carry the interpretation forward only as
      claim-boundary guidance for current comparisons.
- [ ] Re-run key baselines after any task/scoring change before comparing
      scores.

## Milestone 3: Private Holdouts and Anti-Gaming

Status: complete for v1.0-internal; external/private operation remains bounded.

- [x] Keep private holdouts out of public Git history.
- [x] Validate private holdout app coverage, vulnerable/control mix, route
      variants, decoys, and public-overlap checks.
- [x] Add protected private execution with host private-path denial on macOS.
- [x] Publish only redacted aggregate private evidence.
- [x] Add one source-backed private no-tools leaderboard-candidate row with
      runner-emitted fingerprint provenance.
- [x] Document rotating private holdout protocol.

Next improvements:

- [x] Implement active/shadow private holdout metadata.
- [ ] Add repeated private tool-agent leaderboard-candidate rows.
- [ ] Add leakage-response and holdout-retirement workflow tests.
- [ ] Add stronger non-macOS isolation story for protected private execution.

## Milestone 4: Leaderboard and Submission Infrastructure

Status: repo-side and local/containerized paths ready; hosted/community path not
ready.

- [x] Add `leaderboard-submission-v1` schema.
- [x] Add source-summary validation.
- [x] Add benchmark fingerprints and comparability keys.
- [x] Require repeated-run provenance for eligible rows.
- [x] Separate schema-valid evidence from local row eligibility.

Next improvements:

- [ ] Add a maintainer-operated submission review workflow.
- [ ] Add hosted or fully containerized evaluation.
- [x] Add signed or attestable run-bundle guidance.
- [x] Publish leaderboard governance rules.
- [x] Add clear rules for reruns, ties, stale scores, and task-pack rotations.
- [x] Add a public-safe Harbor adapter target contract, skeleton builder, and
      blocker record without claiming Harbor execution.
- [x] Implement full Harbor adapter path: adapter package, CLI, scorer bridge,
      redaction helpers, local 6-task smoke, native-vs-Harbor parity experiment,
      dataset validator, and adapter metadata/parity validators.
      Harbor platform acceptance, Kaggle acceptance, hosted leaderboard operation,
      and third-party submissions remain v2 gates.

## Milestone 5: v1 Internal Release — Complete

Status: complete. v1 internal release-candidate infrastructure validated; external validation deferred to v2.

v1 does not claim external review, hosted leaderboard operation, SaaS-provider validation, or platform acceptance.
Those are tracked as v2 gates in
`docs/claims-and-evidence.md#5-deferred-v2-validation-tracks`.

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
- [ ] hosted leaderboard operation
- [ ] Harbor/Kaggle/platform acceptance
- [ ] third-party submissions

## Milestone 6: v2 External Validation

Status: future.

Save the external-validation release for a version that has independent review,
third-party runs, and research-grade methodology confirmation.

- [ ] At least 100 total tasks across public and private splits.
- [ ] Multiple multi-step workflow families.
- [ ] Independent external AppSec, benchmark/evals, and AI-agent/tooling review.
- [ ] Third-party agent runs.
- [ ] Statistical variance analysis across repeated baselines.
- [ ] Comparison against existing security benchmarks.
- [ ] Public technical report or benchmark paper.
- [ ] Reproducibility packet for researchers.

Exit criteria:

- outside users can run the public harness without local handholding
- private evaluation can be operated without leaking holdouts
- score comparability is clear across versions
- task quality has survived independent external review
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
- `v1-RC` / `v1.0-internal`: internally validated release-candidate infrastructure; 108 public/private task scale; external review, SaaS validation, and platform acceptance are v2 gates
- `v2`: externally reviewed, scaled, research-grade benchmark

Do not call the project leaderboard-ready until the hosted or containerized
submission process exists and private-holdout scoring is operational at that
level.
