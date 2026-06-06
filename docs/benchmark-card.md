# Benchmark Card

## Name

AuthZBench-SaaS

## Current Status

Alpha/pre-v0 public preview. The current split is useful for local integration,
methodology review, and early baseline comparison. It is not yet a finished
leaderboard benchmark.

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

## Current Public Split

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

- The alpha split is small.
- Public tasks are inspectable and should not support strong leaderboard claims.
- Private holdouts exist for maintainer-side validation but are intentionally
  excluded from the public repo.
- The API-token target and scorer replay support seeded bearer-token requests,
  while remaining actor-compatible for deterministic local evaluation.
- Route alias and decoy coverage exists across the public target apps, but it
  is not yet randomized and should not be treated as a private-holdout
  anti-gaming system.
- Docker HTTP targets write target-side request logs, and the alpha runner can
  correlate them into per-task artifacts when `--target-log-dir` is supplied.
  Leaderboard-grade Docker/agent isolation is still planned.
- Current public model/tool-agent baselines need reruns after the 46-task
  multi-step task-wave change. The older 44-task baselines are retained as
  stale public-split snapshots only.
- Baseline registry validation is present and currently reports the baseline
  sub-gate as not ready until those reruns exist.
- Leaderboard submission validation is present, and one redacted
  private-holdout no-tools model row is currently eligible. It proves the
  submission pipeline, not strong model performance.

## Ethical And Safety Notes

The apps are synthetic and intentionally vulnerable. They should be run locally
or inside an isolated environment and should not be exposed to the public
internet. Tasks should not require destructive behavior, credential attacks,
external network calls, brute force, or testing against systems outside the local
benchmark environment.

## Release Direction

The next serious milestone is the real `v0` release described in
[`v0-release-plan.md`](v0-release-plan.md). The v0 bar requires larger task
coverage, private holdouts, stronger anti-gaming, protected holdout execution,
target/proxy-side request logging, tool-equipped baselines, and independent
review.

External reviewers should use [`task-quality-rubric.md`](task-quality-rubric.md)
when assessing task realism, false-positive traps, replay proof, and anti-gaming
risk.
