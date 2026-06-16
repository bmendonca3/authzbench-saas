# Benchmark Comparison

AuthZBench-SaaS is not a general software-engineering benchmark like
SWE-bench. It is a narrow SaaS authorization proof benchmark. This
document compares it to a representative set of existing benchmarks
so a reviewer can see at a glance what AuthZBench-SaaS is narrower
at, what it is stronger at, and what it does not claim.

## Compared to SWE-bench

- **SWE-bench** is a large-scale software-engineering benchmark:
  real GitHub issues, real repositories, real patches, real test
  suites. An agent's job is to produce a patch that makes the test
  suite pass.
- **AuthZBench-SaaS** is a narrow SaaS authorization proof benchmark
  on synthetic app targets. An agent's job is to produce a JSON
  finding that survives a deterministic backend replay and a
  control-mix replay.
- **What AuthZBench-SaaS is narrower at**: it does not measure
  general code generation, refactoring, debugging, or test-writing.
  It is one narrow security class (SaaS authorization proof) on one
  narrow surface (synthetic multi-tenant apps).
- **What it is stronger at**: deterministic backend-replay evidence
  for every finding, secure-control false-positive checks, private
  holdout governance, claim-boundary discipline, and an explicit
  anti-gaming policy.
- **What it does not claim**: it is not a substitute for SWE-bench
  and it is not a general coding-ability benchmark.

## Compared to HumanEval / MBPP / APPS

- **HumanEval, MBPP, APPS** are code-generation benchmarks: an
  agent produces a function from a natural-language prompt and the
  function is evaluated against a test suite.
- **AuthZBench-SaaS** is not a code-generation benchmark. The agent
  produces a JSON finding, not source code.
- **What it is stronger at**: the agent is evaluated on its
  reasoning about authorization, not on code synthesis quality. The
  scorer explicitly distinguishes "exploit proven but boundary
  wrong" from "exploit wrong but boundary text sounds right" via
  the `exploit_proven`, `boundary_exact_match`,
  `boundary_semantic_match`, and `boundary_schema_mismatch` fields.
- **What it does not claim**: it is not a measure of code synthesis
  quality or general programming ability.

## Compared to WebArena / OSWorld / AgentBench

- **WebArena, OSWorld, AgentBench** are general web / OS / agent
  benchmarks: an agent is given a goal in a real web or OS
  environment and is scored on whether it accomplishes the goal.
- **AuthZBench-SaaS** is not a goal-completion benchmark. The agent
  is given a specific authorization-testing objective and is scored
  on whether the JSON finding is correct.
- **What it is narrower at**: it does not measure general web /
  OS navigation, multi-modal perception, or long-horizon planning.
- **What it is stronger at**: deterministic replayability. Every
  finding can be re-scored end-to-end against the seeded fixture
  via `authzbench/score.py::_evidence_requirement_matches`, and the
  scorer is the only path that produces a `proof` response.

## Compared to CyberSecEval / Cybench / CyberGym

- **CyberSecEval, Cybench, CyberGym** are cybersecurity benchmarks:
  capture-the-flag style tasks, vulnerability discovery, or
  exploit development.
- **AuthZBench-SaaS** is narrower. It is one cybersecurity class
  (SaaS authorization proof) on one target surface (synthetic
  multi-tenant apps). It does not measure general vulnerability
  discovery, exploit development, network penetration, malware
  analysis, or reverse engineering.
- **What it is stronger at**: it is the only one of these that
  scores the agent's boundary reasoning explicitly. The
  `boundary_exact_match` / `boundary_semantic_match` /
  `boundary_schema_mismatch` separation is the project's core
  contribution.
- **What it does not claim**: it is not a measure of broad cyber
  capability. An agent that scores 1.0 on AuthZBench-SaaS has not
  demonstrated general cybersecurity skill.

## What AuthZBench-SaaS is narrower at (summary)

- General software engineering (SWE-bench territory).
- General code generation (HumanEval / MBPP / APPS territory).
- General web / OS agent capability (WebArena / OSWorld /
  AgentBench territory).
- General cybersecurity skill (CyberSecEval / Cybench / CyberGym
  territory).

## What AuthZBench-SaaS is stronger at (summary)

- Deterministic backend-replay evidence for every finding.
- Secure-control false-positive checks on every vulnerable task.
- Private holdout governance with active / shadow / retired
  lifecycle stages.
- Claim-boundary discipline: the `v1_ready: true` field is scoped
  to internal/public-view readiness, not external acceptance.
- Anti-gaming policy: documented, CI-enforced rules for the
  public task memorization, hardcoded task ids, known routes,
  report-all-routes, ignored secure controls, private leakage,
  malformed output, tool budget abuse, and multiple-submission
  shapes.
- Reproducible evaluation: the public split, the private
  holdout governance, the leaderboard tiers, the submission
  bundle validator, the tool-agent comparability keys, and the
  Harbor adapter path are all documented in
  [`docs/reviewer-walkthrough.md`](reviewer-walkthrough.md).

## What AuthZBench-SaaS does not claim (summary)

- It is not externally validated. The three external review
  lanes (AppSec, benchmark / evals, agent / tooling) are pending;
  see [`docs/reviews/external-review-registry.json`](reviews/external-review-registry.json).
- It is not hosted on a public leaderboard. The
  `hosted_leaderboard_operation_claimed` field is explicitly
  `false`.
- It is not accepted by Harbor, Kaggle, or any other platform.
  The `harbor_acceptance_claimed`, `kaggle_acceptance_claimed`,
  and `platform_acceptance_claimed` fields are explicitly
  `false`.
- It is not a measure of broad cyber capability or general
  software engineering.
- It is not a substitute for a real-SaaS penetration test.
