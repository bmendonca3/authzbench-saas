# AuthZBench-SaaS v0 Release Plan

Status: planning target for the first release-worthy benchmark.

The current public repository is an alpha/pre-v0 preview. It proves the harness
shape, but it is too small and too easy to inspect to support strong public
leaderboard claims. The real `v0` should be the first version that a security or
AI-agent researcher can use without needing to mentally discount every headline
number.

## v0 Goal

AuthZBench-SaaS v0 should answer one focused question:

> Can an AI agent prove SaaS authorization failures across users, roles,
> tenants, organizations, and protected objects, while avoiding false positives
> when the application is behaving correctly?

The benchmark should stay narrow. It is not a general CTF benchmark, malware
benchmark, cloud benchmark, or code-generation benchmark. Its value is the
authorization boundary.

The public working goal is captured in [`docs/goal.md`](goal.md). The short
version: keep the current repo honest as alpha/pre-v0, then earn the `v0` label
by adding scale, private holdouts, live-target proof, repeated baselines,
sectional review, and clean release validation.

## Scope Target

| Area | Alpha preview | v0 target |
| --- | ---: | ---: |
| Synthetic SaaS apps | 3 | 5-6 |
| Public tasks | 21 | 40-50 |
| Private holdout tasks | 0 tracked | 20-30 unpublished |
| Vulnerability classes | BOLA, BFLA, invite abuse | BOLA, BFLA, tenant isolation, invite/membership, sharing, API-token scope |
| Secure controls | 12 | At least 40 percent of all tasks |
| Model baselines | 2 no-tools runs | 5+ distinct model/agent families plus harness checks, repeated runs |
| Live-target proof | replayable requests | replayable requests plus target request logs |
| Anti-gaming | seeded IDs | seeded IDs, route aliases, decoys, private holdouts |

## App Expansion Plan

Add synthetic apps that feel like real SaaS workflows without copying real
customer data, vendors, or proprietary systems.

| App | Main boundary | Example vulnerable cases | Secure controls |
| --- | --- | --- | --- |
| Project management | Tenant/project/task ownership | Cross-tenant task read/write | Same-tenant read, viewer write denial |
| Billing | Org role/admin boundary | Member changes plan or reads admin settings | Member denial, admin allow |
| File sharing | Workspace/file/link visibility | Private file read through guessed ID, stale share link access | Expired link denial, private workspace denial |
| Invites and membership | Role assignment and invite scope | Member invites admin, cross-org invite accept | Invite expiration, role cap enforcement |
| API tokens | Token scope and tenant binding | Read with wrong tenant token, write beyond token scope | Token scope denial |
| Audit/settings | Admin-only configuration | Member reads audit log or changes security setting | Admin allow, member denial |

## Task Mix

For v0, target about 70 tasks total:

- 40-50 public tasks for integration, debugging, and transparent methodology.
- 20-30 private holdout tasks for leaderboard-grade scoring.
- At least 25 vulnerable tasks.
- At least 25 secure controls.
- At least 10 authorized-allow controls where access should succeed, so agents
  cannot treat every sensitive route as a finding.

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
- boundary reasoning pass rate
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
- Leaderboard schema.
- Baseline report with commands and exact result files.
- Publish checklist with validation commands and privacy checks.
- Changelog or release notes for task/scorer changes.

## Release Gates

Do not tag the real `v0` until all required gates pass:

- public manifests validate
- public and private task counts meet the v0 target
- unit tests pass
- scripted baseline passes the public split
- live HTTP scripted baseline passes against Docker
- at least five distinct real model or agent families are present or linked,
  excluding scripted/live-scripted harness checks
- at least one baseline uses a tool-equipped agent harness
- route alias support is implemented and exercised by at least one task
- at least one decoy endpoint is present and covered by a secure control
- request logs are captured from the target container or proxy sidecar and
  correlated with scorer replay transcripts
- at least two seeds are used for each scored private-holdout task
- at least one independent review of task design, scorer behavior, and
  leaderboard schema is completed with disposition logged
- sectional review notes exist for roadmap/goal, task design, scoring/harness
  behavior, baseline methodology, privacy, and release readiness
- no private holdout manifests are committed
- no secrets, personal emails, personal filesystem paths, cookies, tokens, or
  unrelated local data are committed
- fresh public clone passes non-Docker validation
- Docker smoke passes from a clean checkout when Docker is available
- release notes clearly say which results are public-split and which are private
  holdout results

Version labels:

- alpha preview tags should use `alpha-<semver>-public-scaffold`, such as
  `alpha-0.0.1-public-scaffold`
- local alpha run summaries should use `alpha-0.0.1-public-scaffold-local`
- real v0 tags should not be used until every release gate above is satisfied

## Naming

- Current repository state: `alpha preview` or `pre-v0`
- First release-worthy benchmark: `v0`
- Mature, externally validated benchmark: `v1`

This keeps the project honest. The alpha preview is useful because it shows the
idea and harness. The v0 release should be useful because it has enough scale,
holdout protection, and baseline evidence for other people to rely on it.
