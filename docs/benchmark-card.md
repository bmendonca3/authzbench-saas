# Benchmark Card

## Name

AuthZBench-SaaS

## Current Status

Released v0.0 benchmark artifact. The current split is useful for local
integration, methodology review, and early baseline comparison, and the strict
maintainer gate has release evidence. It is not a hosted leaderboard or
community-scale benchmark.

## What It Measures

AuthZBench-SaaS measures whether an AI agent can prove SaaS authorization bugs
with backend-replayable evidence.

The benchmark focuses on:

- BOLA and BFLA-style authorization failures
- tenant, organization, project, object, role, and token boundaries
- replayable HTTP-style proof
- correct actor/tenant/role boundary reasoning
- false-positive avoidance on secure controls
- safe behavior inside an intentionally vulnerable local target

## What It Does Not Measure

AuthZBench-SaaS does not claim to measure:

- general cyber capability
- exploit development against real CVEs
- cloud exploitation
- malware analysis
- phishing, credential attacks, or social engineering
- production-target vulnerability discovery
- report-writing quality independent of proof

## Intended Users

- security researchers evaluating AI agents
- agent builders testing security harnesses
- application-security teams interested in access-control proof quality
- benchmark designers studying false-positive controls and replay scoring

## Frozen v0.0 Public Split

- 6 Dockerized synthetic SaaS apps
- 46 public tasks
- 19 vulnerable tasks
- 27 secure-control tasks
- 16 denial controls and 11 authorized-allow controls
- seeded IDs for tenants, objects, orgs, invoices, files, links, workspaces, API tokens, scopes, and actors
- deterministic scorer-owned replay transcripts
- route alias and decoy endpoint controls across all six target apps
- target-side JSONL request logs for Docker HTTP targets
- alpha runner correlation into per-task `target-requests.jsonl` artifacts
- scripted, no-tools model, and live HTTP tool-agent baseline summaries

## Current v1-Prep Public Split

- 6 synthetic SaaS apps
- 49 public tasks
- 20 vulnerable tasks
- 29 secure-control tasks
- 17 denial controls and 12 authorized-allow controls
- first billing entitlement expansion slice
- current 49-task scripted sanity baseline
- five repeated current public no-tools Kiro model-family baselines
- one repeated current public live HTTP Kiro tool-agent baseline with 49/49
  target-request correlation in both runs
- public-safe boundary-reasoning calibration for the current tool-agent runs

## Main Metrics

- `exploit_proven_success_rate`
- `false_positive_rate`
- `boundary_reasoning_pass_rate` for v0+ reporting
- `control_execution_pass_rate` for v0+ reporting
- `authorized_allow_pass_rate` for v0+ reporting
- `mean_score` as a coarse compatibility field, not the primary ranking metric

Release-facing summaries should follow [`score-policy.md`](score-policy.md) and
use v0-candidate metrics as the headline interpretation.
Task and scorer changes should follow
[`score-stability-policy.md`](score-stability-policy.md) so old scores are not
mixed with current evidence without a compatibility label.

## Known Limitations

- The v0.0 split is still small compared with mature community
  benchmarks.
- Public tasks are inspectable and should not support strong leaderboard claims.
- Private holdouts exist for maintainer-side validation but are intentionally
  excluded from the public repo.
- The API-token target and scorer replay support seeded bearer-token requests,
  while remaining actor-compatible for deterministic local evaluation.
- Route alias and decoy coverage exists across the public and maintainer
  private-holdout workflows, but public tasks remain inspectable and should not
  be treated as leaderboard-grade anti-gaming protection.
- Docker HTTP targets write target-side request logs, and the alpha runner can
  correlate them into per-task artifacts when `--target-log-dir` is supplied.
  Public runs should still be treated separately from protected private
  evaluation.
- Five current 49-task public no-tools Kiro model-family baselines exist as
  repeated diagnostic evidence. They are not private-holdout, tool-agent,
  hosted-leaderboard, or v1 release evidence.
- One current 49-task public live HTTP Kiro tool-agent baseline exists as
  repeated diagnostic evidence with 49/49 target-request correlation in both
  runs. It is not private-holdout, hosted-leaderboard, or v1 release evidence.
- Boundary-reasoning calibration shows that exploit-proven public tool-agent
  submissions often used alternate keys or runtime identifiers instead of the
  oracle-compatible boundary vocabulary. The current zero boundary-reasoning
  credit should not be retroactively relaxed under `score-policy-v1`.
- The repeated 46-task public live HTTP tool-agent baseline remains auditable as
  frozen v0.0 evidence, but it is stale for the current 49-task split. The older
  44-task baselines are retained as stale public-split snapshots only.
- Baseline registry validation is present and currently reports the baseline
  sub-gate as complete for the live 49-task public baseline bar, while keeping
  public-split and private-holdout claims separate.
- Stable leaderboard submission validation is present. A source-backed
  protected private no-tools row with runner-emitted fingerprint provenance is
  eligible as release-candidate schema evidence. An older reconstructed
  historical private row remains non-eligible. The private tool-agent summary
  currently supports execution evidence, not a repeated eligible leaderboard
  row.

## Ethical And Safety Notes

The apps are synthetic and intentionally vulnerable. They should be run locally
or inside an isolated environment and should not be exposed to the public
internet. Tasks should not require destructive behavior, credential attacks,
external network calls, brute force, or testing against systems outside the local
benchmark environment.

## Release Direction

The next milestone is v1 credibility: repeated private tool-agent evidence,
implemented rotating holdout packs, stronger multi-step workflows, independent
review, and a hosted or fully containerized submission path. Governance for that
path is specified in
[`v1-community-submission-governance.md`](v1-community-submission-governance.md),
but hosted/containerized execution is not yet implemented.

External reviewers should use [`task-quality-rubric.md`](task-quality-rubric.md)
when assessing task realism, false-positive traps, replay proof, and anti-gaming
risk. The generated [`task-quality-matrix.md`](task-quality-matrix.md) provides
a public-safe structural audit of the current task split, but it is not a
leaderboard-readiness claim.
