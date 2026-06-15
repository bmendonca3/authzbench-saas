# Benchmark Card

> **See also:** [`docs/current-claim-boundary.md`](current-claim-boundary.md) for the canonical claim ledger and `scripts/check_claim_boundary.py` for CI-enforced forbidden-phrase checks.


## Name

AuthZBench-SaaS

## Current Status

v1 internal release-candidate infrastructure validated.

Released v0.0 benchmark artifact. The current split is useful for local
integration, methodology review, and early baseline comparison, and the strict
maintainer gate has release evidence. It is not a hosted leaderboard or
community-scale benchmark.

v1 does not claim external review, hosted public leaderboard readiness, SaaS-provider validation, or platform acceptance. Those are tracked as v2 gates
in [`docs/v2-external-validation-roadmap.md`](v2-external-validation-roadmap.md).

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
- 60 public tasks
- 24 vulnerable tasks
- 36 secure-control tasks
- 21 denial controls and 15 authorized-allow controls
- billing entitlement and support ticket reassignment expansion slices
- current 60-task scripted sanity baseline
- five repeated stale 54-task public no-tools model-family baselines: Qwen
  with explicit command/output failure diagnostics, Claude Haiku 4.5 and Claude
  Sonnet 4.6 with zero adapter, runner, and invalid-submission failures, GLM-5
  with one retained outer runner failure in run 1 and a clean 54/54 artifact run
  2, and Claude Opus 4.6 with complete zero-failure task artifacts
- one repeated stale 54-task public live HTTP Kiro `claude-sonnet-4.6`
  tool-agent baseline with 54/54 target-request correlation in both runs
- five repeated 49-task public no-tools Kiro model-family baselines, now stale
  after 54-task reruns
- one repeated 49-task public live HTTP Kiro tool-agent baseline with 49/49
  target-request correlation in both historical runs, now stale
- public-safe boundary-reasoning calibration for the 49-task tool-agent runs

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
- Five 49-task public no-tools Kiro model-family baselines exist as repeated
  diagnostic evidence, but they are stale for the current 60-task split.
- Repeated 54-task public no-tools Qwen, Claude Haiku 4.5, Claude Sonnet 4.6,
  GLM-5, and Claude Opus 4.6 baselines are stale. Qwen's command/output
  failures, Haiku's repeated authorized-allow false report, Sonnet's two
  different support-control false reports, GLM's retained runner failure, and
  Opus's zero-failure artifact pair are part of the reported results; these
  public-only rows do not establish private-holdout or leaderboard comparison.
- One 49-task public live HTTP Kiro tool-agent baseline exists with 49/49
  target-request correlation in both runs, but it is stale for the current
  54-task split.
- One stale 54-task public live HTTP Kiro `claude-sonnet-4.6` tool-agent
  baseline exists with 54/54 target-request correlation in both runs, zero
  planner/parser failures, zero invalid submissions, and zero secure-control
  false reports. It is public-split diagnostic evidence only, not private
  holdout, hosted leaderboard, or v1 release evidence.
- Boundary-reasoning calibration on the historical 49-task public tool-agent
  pair shows that exploit-proven submissions often used alternate keys or
  runtime identifiers instead of the oracle-compatible boundary vocabulary. The
  stale 54-task live tool-agent pair repeats the high-exploit-proof,
  zero-boundary-credit pattern, but it has not had a separate calibration study.
  The zero boundary-reasoning credit should not be retroactively relaxed under
  `score-policy-v1`.
- The repeated 46-task public live HTTP tool-agent baseline remains auditable as
  frozen v0.0 evidence, but it is stale for the current 60-task split. The older
  44-task baselines are retained as stale public-split snapshots only.
- Baseline registry validation is present and keeps the frozen v0.0 snapshot
  auditable while reporting five stale 54-task no-tools families and one
  stale 54-task live HTTP tool-agent family for the previous 54-task public split.
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
