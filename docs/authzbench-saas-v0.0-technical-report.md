# AuthZBench-SaaS v0.0 Technical Report Draft

Status: public v0.0 technical-report draft for the released benchmark artifact.
This document is claim-disciplined by design: it describes what the repository
currently proves, what it partially supports, and what remains future work.

## Title Options

Recommended title:

**AuthZBench-SaaS: Evaluating Replayable Authorization-Failure Proofs in AI
Security Agents**

Alternatives:

- **AuthZBench-SaaS v0.0: A Benchmark for SaaS Authorization Proof Quality**
- **Measuring Whether AI Agents Can Prove SaaS Authorization Failures**
- **Replay, Reason, and Refrain: A SaaS Authorization Benchmark for AI Agents**

## Abstract

AI security agents can produce plausible vulnerability reports without proving
that an authorization failure occurred. AuthZBench-SaaS v0.0 introduces a narrow
benchmark for this proof gap. The benchmark contains 6 synthetic SaaS targets
and 46 public tasks covering tenant, organization, object, role, API-token,
scope, sharing, and admin-action boundaries. It evaluates whether an agent can
submit backend-replayable evidence for vulnerable tasks while avoiding false
reports on secure controls. The current public split includes 19 vulnerable
tasks, 27 secure-control tasks, 16 denial controls, and 11 authorized-allow
controls. Scoring separates exploit proof, boundary reasoning, false-positive
behavior, control execution, safety, and live-target request correlation when
Docker HTTP targets are used. Repeated public baselines across five current
model/agent families show that agents can sometimes produce replayable exploit
evidence, but current runs often fail full vulnerable-task passes because
authorization-boundary reasoning remains weak. AuthZBench-SaaS v0.0 is a
released benchmark artifact, not a hosted leaderboard or community-scale
benchmark. Its contribution is an evidence-backed harness for studying SaaS
authorization proof quality, false-positive discipline, and replay-centered
evaluation design.

## Extended Introduction

Authorization bugs are common in SaaS systems because the same application
usually serves many tenants, roles, objects, scopes, and workflows. A useful
security agent must do more than notice a sensitive endpoint. It must identify
which actor made the request, which tenant or organization owned the target
object, which role or token scope should have been required, and whether the
backend behavior can be replayed as evidence.

This makes SaaS authorization a useful evaluation target for AI agents. A
prose-only report can sound convincing while failing to prove that access was
improper. Conversely, an agent can sometimes hit a vulnerable route without
correctly explaining the authorization boundary. AuthZBench-SaaS separates these
cases. It asks for evidence that replays against the backend, and it scores
boundary reasoning separately from exploit replay.

The benchmark also includes secure controls. This matters because a security
agent that reports every sensitive route as a bug is not useful in practice.
Some controls check that unsafe access is correctly denied. Others are
authorized-allow controls, where access should succeed and the correct agent
behavior is to report no vulnerability. These controls make false-positive
discipline measurable.

AuthZBench-SaaS v0.0 is intentionally narrow. It does not evaluate broad cyber
capability, real CVE exploitation, phishing, malware analysis, cloud compromise,
or production vulnerability discovery. It evaluates a specific capability:
whether an agent can prove SaaS authorization failures with backend-replayable
evidence while avoiding unsupported findings on secure controls.

The v0.0 release includes a public split for reproducibility, repeated public
baseline summaries, protected private-holdout evidence summarized only at
redacted aggregate level, validation scripts, release gates, public-safe charts,
and documentation for scoring and leaderboard submission shape. Public tasks are
inspectable and should not be treated as private leaderboard tasks. The
maintainer-only private evidence is useful for release confidence, but the
project is not yet a hosted public leaderboard.

## Contributions

1. **A focused SaaS authorization benchmark.** AuthZBench-SaaS v0.0 provides 6
   synthetic SaaS apps and 46 public tasks covering BOLA/BFLA-style failures,
   secure denials, and authorized-allow controls.
2. **Replay-centered scoring.** The scorer checks submitted evidence through
   deterministic backend replay and records scorer-owned transcripts rather than
   relying on prose-only claims.
3. **False-positive controls.** Secure-control tasks require `findings: []`,
   allowing the benchmark to penalize over-reporting on both denial and
   authorized-allow paths.
4. **Boundary reasoning as a separate signal.** The benchmark distinguishes
   making a request that demonstrates bad behavior from correctly identifying
   the actor, tenant, object, role, or token boundary.
5. **Evidence and release discipline.** The repository includes baseline
   registry validation, release gates, public-safe charts, privacy checks,
   protected private-holdout summaries, and explicit unsupported-claim
   boundaries.

## Methodology

AuthZBench-SaaS evaluates agents through rendered task contexts. Each task
contains seeded fixtures for actors, tenants, organizations, roles, objects,
tokens, scopes, routes, and expected behavior. The agent receives a task context
and writes a structured JSON submission. The runner then scores the submission
against task-specific oracles.

The public split covers six SaaS target families:

| Target family | Authorization surface |
| --- | --- |
| Project management | project and task tenant boundaries |
| Billing | plan, invoice, entitlement, and admin-action boundaries |
| Support | ticket access, status changes, and invite abuse |
| File sharing | files, workspaces, share links, and stale-link behavior |
| API tokens | tenant-bound tokens and scope checks |
| Audit/settings | audit logs, exports, and admin settings |

Task types include vulnerable tasks and secure controls. Vulnerable tasks expect
one or more findings with replayable proof. Secure controls expect no findings.
Denial controls verify that unsafe access is correctly blocked. Authorized-allow
controls verify that legitimate access is not misreported as a vulnerability.

For live HTTP runs, Docker targets can write target-side JSONL request logs. The
runner can correlate those logs into per-task artifacts when `--target-log-dir`
is supplied. Request-log correlation is useful evidence that the agent exercised
live targets, but it does not replace scorer-owned replay as the authoritative
proof mechanism.

## Scoring

Release-facing interpretation uses the v0 evidence metrics rather than legacy
`mean_score` alone. The current metric profile string in stored artifacts is
`v0-candidate-authz-evidence` for compatibility with the pre-tag release
candidate, but this report refers to the released v0.0 metric set. The main axes
are:

| Metric | Meaning |
| --- | --- |
| `exploit_proven_success_rate` | vulnerable-task proof that replays against the backend |
| `boundary_reasoning_pass_rate` | vulnerable-task rate for naming the expected authorization boundary |
| `false_positive_rate` | rate of false reports on secure controls |
| `control_execution_pass_rate` | whether secure-control replay behaved as expected |
| `authorized_allow_pass_rate` | whether the agent avoided false reports where access should be allowed |
| `target_request_coverage_rate` | live-target request correlation coverage for HTTP tool-agent runs |
| `invalid_submission_rate` | malformed, missing, or unscorable submissions |
| `v0_mean_score` | secondary full-pass aggregate, not the primary ranking metric |

For vulnerable tasks, a full pass requires replayable exploit proof, correct
boundary reasoning, a successful control replay, and safe behavior. For secure
controls, a full pass requires no findings. This design prevents a model from
receiving a full vulnerable-task pass merely by making a successful request
without explaining why the authorization boundary is wrong.

## Experimental Results

The current public split contains 46 tasks: 19 vulnerable and 27 secure
controls. The control set includes 16 denial controls and 11 authorized-allow
controls. The deterministic scripted baseline is a harness sanity check, not a
model-capability result; it passes all 46 public tasks and verifies that the
scorer, task manifests, and expected oracle path fit the active split.

Current public baselines include four repeated no-tools model-family baselines
and one repeated live HTTP tool-agent family. These runs are public-split
evidence only; they are not private-holdout leaderboard rankings.

| Baseline | Harness | Tasks | V0 passed | Exploit proof | Boundary reasoning | False positives | Authorized allow | Target requests |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Scripted sanity baseline | scripted | 46 | 46 | 1.0 | 1.0 | 0.0 | 1.0 | n/a |
| Qwen run 1 | no-tools model | 46 | 27 | 0.0 | 0.0 | 0.0 | 1.0 | n/a |
| Qwen run 2 | no-tools model | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 | n/a |
| Claude Haiku run 1 | no-tools model | 46 | 26 | 0.2632 | 0.0 | 0.037 | 1.0 | n/a |
| Claude Haiku run 2 | no-tools model | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 | n/a |
| Claude Sonnet run 1 | no-tools model | 46 | 27 | 0.6316 | 0.0 | 0.0 | 1.0 | n/a |
| Claude Sonnet run 2 | no-tools model | 46 | 26 | 0.4211 | 0.0 | 0.037 | 1.0 | n/a |
| GLM run 1 | no-tools model | 46 | 27 | 0.2105 | 0.0 | 0.0 | 1.0 | n/a |
| GLM run 2 | no-tools model | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 | n/a |
| Claude Sonnet tool-agent run 1 | live HTTP tool-agent | 46 | 27 | 0.7368 | 0.0 | 0.0 | 1.0 | 1.0 |
| Claude Sonnet tool-agent run 2 | live HTTP tool-agent | 46 | 27 | 0.7368 | 0.0 | 0.0 | 1.0 | 1.0 |

The main empirical signal is not that these public runs establish a model
ranking. They do not. The useful signal is diagnostic: several runs produce
some replayable exploit evidence, but vulnerable-task full passes remain blocked
because boundary reasoning is weak. The live HTTP tool-agent repeatedly proves
14 of 19 vulnerable replays and correlates target requests for all 46 tasks, yet
still has `boundary_reasoning_pass_rate: 0.0`. This suggests a gap between
exercising an endpoint and correctly explaining the authorization violation.

The public baselines also show why secure controls matter. Most current runs
keep false-positive rates at 0.0, but Claude Haiku run 1 and Claude Sonnet run 2
each produce one secure-control false report. That is a small count, but it is
important: a benchmark without controls could not distinguish a cautious
evidence-backed agent from one that over-reports.

## Threats To Validity And Limitations

- **Synthetic targets.** The target apps are intentionally vulnerable local
  fixtures. Results do not prove production vulnerability-discovery ability.
- **Small v0 scale.** The public split has 46 tasks. That is enough for a first
  release artifact, but not enough for v1 or community-scale claims.
- **Inspectable public tasks.** Public tasks support reproducibility and
  integration, but they are not suitable for strong private leaderboard claims.
- **Maintainer-side private evidence.** Protected private-holdout evidence is
  summarized at aggregate level. Private task bodies, seeds, routes, and oracles
  are intentionally not public.
- **Baseline scope.** Current baselines are useful public-split diagnostics, not
  broad model rankings. Some repeated tool-agent runs span adjacent commits with
  matching task fingerprints rather than identical SHAs.
- **Boundary-reasoning strictness.** A `0.0` boundary-reasoning rate in current
  baselines may reflect stringent schema and wording requirements as well as
  model capability gaps. This should be studied further rather than treated as a
  final model-quality conclusion.
- **No hosted leaderboard yet.** The repository has schema and validation
  machinery, but not a hosted or fully containerized third-party submission
  service.
- **Isolation story is still maturing.** Protected private execution has host
  isolation evidence, but v1 should strengthen non-macOS isolation and
  submission governance.

## Roadmap To v1

The v1 path should focus on credibility rather than polish:

1. Add more multi-step workflow tasks across billing, support, file sharing,
   API-token, and audit/settings surfaces.
2. Increase public and private task volume while preserving high-quality
   controls.
3. Add rotating private holdout packs and documented leakage-response rules.
4. Add repeated private tool-agent leaderboard-candidate rows.
5. Add independently operated third-party runs and reviewer feedback.
6. Add variance analysis across repeated baselines.
7. Build hosted or fully containerized submission infrastructure.
8. Publish a reproducibility packet and a revised benchmark paper grounded in
   external review.

## Supported, Partially Supported, And Unsupported Claims

The detailed claim table is maintained in
[`authzbench-saas-v0.0-evidence-map.md`](authzbench-saas-v0.0-evidence-map.md).
The short version is:

- Supported: v0.0 released benchmark artifact, 6 apps, 46 public tasks,
  deterministic replay scoring, secure controls, repeated current public
  model/agent baselines, protected private aggregate evidence.
- Partially supported: private-holdout evaluation credibility, early
  leaderboard-submission shape, live tool-agent execution evidence.
- Unsupported: hosted leaderboard readiness, production vulnerability discovery,
  broad cyber capability, definitive model rankings, and v1/community-scale
  maturity.

## Reviewer-Risk Checklist

| Reviewer concern | Current answer | v1 improvement |
| --- | --- | --- |
| The benchmark is too small. | True for v1 claims; acceptable for a first v0.0 release artifact. | Expand to at least 100 tasks across public/private splits. |
| Public tasks are gameable. | Public tasks are for reproducibility, not leaderboard ranking. | Add rotating private packs and leakage-response rules. |
| Synthetic apps may not transfer. | The benchmark measures proof mechanics in controlled SaaS authorization fixtures. | Add broader task families and external review. |
| Baselines are not enough for ranking. | Correct; current baselines are diagnostic public-split evidence. | Add third-party runs, private repeats, and variance analysis. |
| Boundary reasoning may be too strict. | Possible; it is intentionally separated from replay proof and should be audited. | Run reviewer calibration and scorer-ablation studies. |
| Tool-agent evidence is still early. | Current public tool-agent runs show full target-request correlation, not private leaderboard performance. | Add repeated private tool-agent rows and containerized submissions. |
| Release docs overclaim readiness. | The intended framing is v0.0 released artifact, not hosted/community benchmark. | Keep claim ledger and benchmark card current after every release. |

## Self-Critique

The strongest part of AuthZBench-SaaS is not the current model table. The
strongest part is the evaluation design: replayable proof, explicit boundary
reasoning, and false-positive controls on a focused SaaS authorization problem.
The model table is useful because it exposes failure modes, especially the gap
between exploit replay and correct boundary explanation.

The weakest parts are scale, external validation, and leaderboard operations.
The benchmark should not be presented as a finished community benchmark until it
has rotating holdouts, third-party submissions, independent review, and a stable
hosted or containerized evaluation path. The paper should therefore frame v0.0
as an evidence-backed release artifact and methodology foundation, not as the
final benchmark for AI security agents.
