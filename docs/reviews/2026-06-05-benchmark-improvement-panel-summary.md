# Benchmark Improvement Panel Summary

Date: 2026-06-05

## Question

What changes would most improve AuthZBench-SaaS as a serious public benchmark,
not just as a polished repo, while preserving honest alpha/pre-v0 framing?

## Evidence Packet

Reviewers were given public-safe context covering:

- current README, roadmap, methodology, benchmark card, leaderboard schema, and
  v0 release plan
- baseline registry status
- current public task counts and strict release-candidate validation status
- limitations around public-split baselines, private holdouts, hosted
  leaderboard readiness, and v1-scale external validation

Raw model outputs and panel logs are intentionally not committed.

## Reviewers

Substantive reviewer outputs were received from:

- Gemini 3.5 Flash (High)
- Gemini 3.1 Pro (High)
- Kiro CLI `claude-opus-4.8`
- panel reviewer

Antigravity Claude labels were attempted and model routing was verified, but the
captured reviewer outputs were not substantive enough to count as findings.

## Consensus

The panel agreed that the largest benchmark-quality improvements are:

- clearer evidence and claims boundaries
- a public task-quality rubric for external review
- stronger metric policy that avoids ranking by legacy `mean_score`
- better third-party agent onboarding
- future rotating private-holdout packs and hosted/containerized leaderboard
  execution
- future route/API de-telegraphing and dynamic route aliases, with baseline
  reruns before those changes support comparison claims
- broader task realism and multi-step SaaS workflows before v1

## Accepted Immediate Changes

The public-safe immediate changes accepted from this review are:

- add `docs/task-quality-rubric.md`
- add `docs/evidence-and-claims.md`
- add `docs/agent-evaluator-kit.md`
- add `docs/score-policy.md`
- add `docs/score-stability-policy.md`
- add a minimal no-findings agent template under `examples/agents/`
- link the new materials from README, benchmark card, contributing guide, and
  roadmap

These changes improve benchmark trust and adoption without exposing private
holdouts or invalidating current baseline artifacts.

## Deferred Changes

The following recommendations are deferred because they affect scoring,
baseline comparability, private infrastructure, or task semantics:

- make live target-request correlation a scored leaderboard gate
- de-telegraph public route names and API docs
- add seed-dependent public route aliases
- expand to 100+ total tasks with multi-step workflow families
- add rotating multi-pack private holdouts
- add hosted or fully containerized leaderboard execution
- produce additional private-holdout leaderboard rows
- obtain independent third-party researcher/agent runs

## Claim Boundaries

This review does not authorize claims that AuthZBench-SaaS is:

- tagged v0
- hosted-leaderboard-ready
- a validated model benchmark
- externally validated at v1 scale
- protected against all public-task memorization
