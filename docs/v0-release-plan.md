# AuthZBench-SaaS v0 Release Plan

Status: historical release plan for the first release-worthy benchmark. The
`v0.0` release has now landed; keep this file as the original release-gate
contract and use the roadmap for current v1/community work.

The current public repository is a released v0.0 artifact. It proves the harness
shape and first-release evidence standard, but it is still too small and too
easy to inspect to support strong public leaderboard claims.

## v0 Goal

AuthZBench-SaaS v0 should answer one focused question:

> Can an AI agent prove SaaS authorization failures across users, roles,
> tenants, organizations, and protected objects, while avoiding false positives
> when the application is behaving correctly?

The benchmark should stay narrow. It is not a general CTF benchmark, malware
benchmark, cloud benchmark, or code-generation benchmark. Its value is the
authorization boundary.

The public working goal is captured in [`docs/goal.md`](goal.md). The short
version: keep the current repo honest as released v0.0, then earn stronger v1
or community-benchmark claims through scale, rotating private holdouts,
live-target proof, repeated baselines, sectional review, and clean validation.

The release process should also be auditable from Git history. Major work should
land as coherent SDLC checkpoints: design and roadmap changes, target/task
expansions, scorer/harness hardening, baseline refreshes, and release-readiness
updates.

## Maturity Boundary

The `v0.0` target is a Level 1 benchmark target: a legitimate, frozen,
reproducible benchmark release. It is not the same as a research-artifact claim
or a community-leaderboard claim.

For `v0.0`, the required proof is:

- current repeated baselines on the frozen 46-task public split
- frozen scoring, evidence, benchmark-fingerprint, and version labels
- methodology, benchmark card, score policy, and claim-boundary docs
- verified private-holdout separation and protected aggregate evidence
- release validation, privacy checks, pushed commit, and passing remote CI

Research-artifact work comes after that: independent external review, a paper
or technical report, comparison against existing security benchmarks, and
variance analysis. Community-benchmark work comes later still: hosted or fully
containerized submissions, rotating holdouts, multiple task packs, outside
contributors, and public leaderboard operations.

## Scope Target

| Area | Alpha preview | v0 target |
| --- | ---: | ---: |
| Synthetic SaaS apps | 6 | 6 |
| Public tasks | 46 | 40-50 |
| Private holdout tasks | 0 tracked | 20-30 unpublished |
| Vulnerability classes | BOLA, BFLA, invite abuse, sharing, API-token scope | BOLA, BFLA, tenant isolation, support invites, sharing, API-token scope, audit/settings |
| Secure controls | 27 | At least 40 percent of all tasks |
| Model baselines | 2 no-tools runs | 5+ distinct model/agent families plus harness checks, repeated runs |
| Live-target proof | replayable requests plus prototype target logs | replayable requests plus target request logs |
| Anti-gaming | seeded IDs, prototype route aliases and decoys | seeded IDs, route aliases, decoys, private holdouts |

## App Expansion Plan

Add synthetic apps that feel like real SaaS workflows without copying real
customer data, vendors, or proprietary systems.

| App | Main boundary | Example vulnerable cases | Secure controls |
| --- | --- | --- | --- |
| Project management | Tenant/project/task ownership | Cross-tenant task read/write | Same-tenant read, viewer write denial |
| Billing | Org role/admin boundary | Member changes plan or reads admin settings | Member denial, admin allow |
| File sharing | Workspace/file/link visibility | Private file read through guessed ID, stale share link access | Expired link denial, private workspace denial |
| Support | Ticket ownership, status writes, and invite scope | Cross-tenant ticket read, unauthorized status change, member invites admin | Ticket read allow, unauthorized ticket update denial, invite role cap enforcement |
| API tokens | Token scope and tenant binding | Read with wrong tenant token, write beyond token scope | Token scope denial |
| Audit/settings | Audit logs, admin-only settings, restricted exports | Cross-org audit read, member disables SSO, member downloads restricted export | Auditor/admin allow, cross-org/member denial |

## Task Mix

For v0, target roughly 70-75 tasks total:

- 40-50 public tasks for integration, debugging, and transparent methodology.
- 20-30 private holdout tasks used for repeated-runs scoring under a
  governance-controlled holdout, not for an open public leaderboard.
- At least 25 vulnerable tasks.
- At least 40 percent secure controls across the final task set. For the
  current 70-75 task target, that means at least 30 total secure controls,
  counting both denial controls and authorized-allow controls.
- At least 10 authorized-allow controls where access should succeed, so agents
  cannot treat every sensitive route as a finding.

The concrete per-app allocation target lives in
[`v0-task-build-matrix.md`](v0-task-build-matrix.md).

Every vulnerable task should define:

- expected claim
- expected attacker actor
- expected victim tenant, org, project, file, or protected object
- expected role or scope boundary
- replayable proof request sequence
- at least one denial or authorized-control request

Every secure-control task should define:

- the behavior that is intentionally safe
- the expected empty finding output
- the control request and expected response
- the common false-positive trap the task is meant to catch

Secure controls should be labeled consistently as either denial controls
(`findings: []` because access is correctly denied) or authorized-allow controls
(`findings: []` because the actor is correctly allowed).

## Anti-Gaming Requirements

v0 should reduce value from memorized public manifests or hardcoded answer
tables.

Required:

- private holdout pack outside public Git history
- private holdout execution that does not expose readable holdout manifests to
  participants
- task seeds that vary tenant, org, user, role, object, invoice, and token IDs
- route alias support, such as `/api/tasks/<id>` and `/api/work-items/<id>`
- harmless decoy endpoints that look security-relevant but are correctly denied
- scorer-side transcript files for proof and control replay
- benchmark version field in every run summary
- v0-candidate run-summary metrics that separate exploit proof, boundary
  reasoning, secure-control false reports, secure-control execution, and
  live-target request coverage from the alpha blended score
- invalid-submission metrics for missing, malformed, or unscorable submissions
- vulnerable-task control replay as an integrity gate, without giving separate
  v0 headline credit for agent-independent control replay
- at least two seeds per scored private-holdout task

Preferred:

- randomized response field order where it does not change semantics
- hidden oracle details for private holdouts
- local request log proving the agent touched the live target before submitting

Route aliases and decoys should be registered through app-level route tables or
seed-derived configuration, then reflected in rendered contexts. Scoring should
verify that aliases preserve the same authorization semantics and that decoys do
not become accidental alternate exploit paths.

## Live-Target Proof

The current scorer can replay submitted evidence, the alpha Docker targets can
write target-side request logs, and the runner can correlate those logs into
per-task artifacts when `--target-log-dir` is supplied. That is useful, but v0
should harden this path under Docker-backed CI and isolated live-agent runs
before using it for leaderboard claims. In particular, the agent must not have
write access to the target-log filesystem path.

The request-log artifact is captured from target-container logs or a future
reverse-proxy sidecar, not self-reported by the agent:

```text
results/<run_id>/<task_id>/
  context.json
  submission.json
  score.json
  transcript.json
  target-requests.jsonl
```

Each logged request should include:

- run ID
- agent ID or agent command hash
- request ID
- task ID
- seed
- timestamp
- actor
- method
- path
- response status
- redacted response body hash or safe body subset
- transcript correlation field tying logged requests to scorer replay entries

Scoring should still be based on deterministic replay, not blindly trusting the
request log. The log proves interaction; replay proves the exploit.

## Baseline Plan

v0 should include repeated baselines, not one-off runs.

Minimum baseline families:

- deterministic scripted baseline
- live HTTP scripted baseline
- one coding-agent baseline with tool access
- one no-tools model baseline
- at least five distinct real model or agent families, excluding scripted
  harness checks

Report:

- benchmark commit or release tag
- model label and provider date when available
- harness/tool access
- task count
- exploit-proven success rate
- false-positive rate
- secure-control false-report rate
- secure-control execution pass rate
- boundary reasoning pass rate
- target-request coverage rate for live-target runs
- invalid-submission rate
- v0-candidate mean score
- mean score
- median runtime
- run count and variance when repeated

Do not rank models by `mean_score` alone. A leaderboard should first apply a
published false-positive eligibility threshold, then sort eligible submissions by
exploit-proven success. This avoids rewarding a do-nothing agent that simply
returns no findings.

## Documentation Required For v0

- README with plain-English explanation and researcher-facing details.
- Methodology document explaining task types, scoring, and limits.
- Benchmark card describing what the benchmark measures and does not measure.
- Holdout and contamination policy.
- Public roadmap and goal contract explaining why the current repo is alpha and
  what must be true before `v0`.
- v0 task build matrix with public and private allocations per app.
- Leaderboard schema.
- Leaderboard submission validator with at least one public example that is
  schema-valid but explicitly not leaderboard eligible when it is only a harness
  check or public-split development run.
- Release-candidate leaderboard submissions stored separately under
  `leaderboard_submissions/**/*.json` or in an equivalent protected submission
  bundle, so public examples do not have to pretend to be private-holdout
  leaderboard rows.
- Artifact-backed leaderboard validation that cross-checks submitted rows
  against `summary.json` and recomputes aggregate metrics from per-task rows when
  those rows are present.
- Baseline report with commands and exact result files.
- Baseline registry that marks each run as a harness check, model baseline, tool
  agent baseline, current public split, or legacy snapshot.
- Release evidence registry in `docs/release-evidence.json` that records whether
  local validation, fresh-clone validation, remote CI, Docker smoke, privacy
  scan, release-note separation, and protected private-holdout execution are
  satisfied for a real v0 candidate.
- Publish checklist with validation commands and privacy checks.
- Changelog or release notes for task/scorer changes.

## Sectional Review Gates

Each major section should have a concise review artifact under `docs/reviews/`
before it is treated as release-ready. The artifact should record:

- the question reviewed
- the files, commands, and evidence packet supplied to reviewers
- verified reviewers or a clear note when a reviewer was unavailable
- accepted findings and the follow-up commit or decision
- rejected findings with the technical reason
- remaining release risks

Minimum sections:

- goal, roadmap, and release criteria
- task realism and vulnerability/control mix
- scorer, runner, request-log correlation, and live-target proof
- baseline methodology and leaderboard schema
- holdout, contamination, and anti-gaming design
- privacy scan, packaging, and final release readiness

## Release Gates

Do not tag the real `v0` until all required gates pass:

- public manifests validate
- public and private task counts meet the v0 target
- unit tests pass
- CI public-validation workflow passes, including the Docker container smoke gate
- scripted baseline passes the public split
- live HTTP scripted baseline passes against Docker
- at least five distinct real model or agent families are present or linked,
  excluding scripted/live-scripted harness checks
- at least one baseline uses a tool-equipped agent harness
- baseline registry validation passes and reports the intended current evidence state
- leaderboard submission validation passes for all tracked examples and any
  release-candidate private-holdout submission files
- `docs/release-evidence.json` marks every required v0 evidence field true for
  the release candidate
- leaderboard submissions trace to source run summaries, and source summaries
  with task rows recompute cleanly from those rows
- leaderboard-eligible rows include both vulnerable tasks and secure controls,
  so false-positive rates cannot be claimed from a vulnerability-only subset
- combined public/private leaderboard rows remain ineligible until the schema
  includes private-only rates and validates eligibility against those rates
- route alias support is implemented and exercised by at least one task
- at least one decoy endpoint is present and covered by a secure control
- private holdout validation reports sufficient route and decoy variant metadata
  and zero non-rehearsal public-structure overlaps
- request logs are captured from the target container or proxy sidecar and
  correlated with scorer replay transcripts
- at least two seeds are used for each scored private-holdout task
- at least one independent review of task design, scorer behavior, and
  leaderboard schema is completed with disposition logged
- sectional review notes exist for goal, roadmap, and release criteria; task
  realism and vulnerability/control mix; scorer, runner, request-log
  correlation, and live-target proof; baseline methodology and leaderboard
  schema; holdout, contamination, and anti-gaming design; and privacy scan,
  packaging, and final release readiness
- no private holdout manifests are committed
- no secrets, personal emails, personal filesystem paths, cookies, tokens, or
  unrelated local data are committed
- fresh public clone passes validation
- Docker smoke passes from a clean checkout or remote CI runner with Docker
- release notes clearly say which results are public-split and which are private
  holdout results

Machine audit:

```bash
python3 scripts/validate_v0_release.py
```

Strict mode should return success only when the real v0 gates are satisfied.
Public validation can run the same gate in explicit audit mode when private
holdouts are intentionally absent from a public checkout:

```bash
python3 scripts/validate_v0_release.py --allow-incomplete
```

`--allow-incomplete` is not a release waiver. It exists so the repository can
continuously publish a machine-readable readiness account in public-only
checkouts.

Version labels:

- alpha preview tags should use `alpha-<semver>-public-scaffold`, such as
  `alpha-0.0.1-public-scaffold`
- local alpha run summaries should use `alpha-0.0.1-public-scaffold-local`
- real v0 tags should not be used unless every release gate above is satisfied

## Naming

- Current repository state: `v0.0 released`
- First release-worthy benchmark: `v0`
- Mature benchmark with external review dispositions recorded: `v2`
  (the v1.0-internal cut is the internal / public-view release; v2 is the
  external lane tracked in `docs/claims-and-evidence.md`)

This keeps the project honest. The alpha preview was useful because it showed
the idea and harness. The v0.0 release is useful because it adds enough scale,
holdout protection, and baseline evidence for other people to inspect and build
on, while still reserving leaderboard and v1/community claims for later work.
