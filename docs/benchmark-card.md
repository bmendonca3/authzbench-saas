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

- 2 Dockerized synthetic SaaS apps
- 15 public tasks
- 6 vulnerable tasks
- 9 secure-control tasks
- seeded IDs for tenants, objects, orgs, invoices, and actors
- deterministic scorer-owned replay transcripts
- prototype route alias and decoy endpoint controls
- scripted and model baseline summaries

## Main Metrics

- `exploit_proven_success_rate`
- `false_positive_rate`
- `boundary_reasoning_pass_rate` for v0+ reporting
- `control_execution_pass_rate` for v0+ reporting
- `authorized_allow_pass_rate` for v0+ reporting
- `mean_score` as a coarse compatibility field, not the primary ranking metric

## Known Limitations

- The alpha split is small.
- Public tasks are inspectable and should not support strong leaderboard claims.
- Private holdouts are planned but not yet implemented.
- Route alias and decoy coverage is currently a small alpha prototype, not a
  broad randomized anti-gaming system.
- Live-target request logging is planned but not yet implemented.
- Current model baselines are sparse and include no-tools runs.

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
