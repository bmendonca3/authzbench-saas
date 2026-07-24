# Kaggle Benchmark Design Contract

Status: current-starter local controls and one local Model Proxy agent/verifier
completion verified; Kaggle executor parity and review not yet completed
Evidence date: 2026-07-24
Implementation source: AuthZBench-SaaS `main` at `2025dc0` plus the current
uncommitted output-schema clarification; historical pilot checkpoint `7f3da26`

The executed generated-task checksums and compact local results are recorded in
`artifact/harbor-kaggle-public-pilot/local-harbor-evidence.json`. No hosted
Kaggle executor run, organization change, upload, publication, or launch action
is claimed.

## 1. Status And Claim Boundary

The July 22 Google/Kaggle onboarding direction supersedes the July 14 document
access status. The current relationship is treated as consult/advisory unless
Kaggle explicitly assigns an FDE. This document and its pilot can establish
local implementation evidence only; they do not establish Kaggle execution,
acceptance, independent validation, organization approval, or launch.

Observable check: every status artifact names the evidence layer as one of
`local`, `kaggle-executor`, `platform-accepted`, `independently-validated`, or
`launched`; only `local` may be set by this work.

Local status is verified for the three-task NOP/Oracle pilot and one
Model-Proxy-backed secure-control compatibility run. The prior 12-cell repeat
matrix and a fresh six-run current-starter matrix completed with zero
exceptions; every fresh control run contains `trial.log` and verifier CTRF. The
model run completed its agent and verifier, but its temporary public-network
mode prevents treating it as network-isolation or Kaggle-executor evidence.

### Current official starter comparison

Nicholas Kang's July 22 onboarding update supplied the current
[Google/Kaggle Harbor starter repository](https://github.com/Kaggle/kaggle-benchmark-harbor-starter-template).
Its current workflow confirms the pilot's task-directory surfaces
(`environment/`, `instruction.md`, `solution/`, `tests/`, and `task.toml`),
local NOP/Oracle expectations, `jobs/` result inspection, and Model Proxy
boundary.

The starter's manifest uses `[dataset]`, `[[dataset.authors]]`, and
digest-backed `[[tasks]]` entries. The tracked pilot now uses that shape, and
all three pinned content digests match an independent Harbor 0.13.2 `harbor
add` result for the exact generated task trees. The manifest remains a local
registration artifact, not publish or Kaggle-executor evidence; `harbor
publish` was not run.

## 2. Capability And Construct Boundary

The benchmark measures whether an LLM agent can produce a structured,
backend-replayable proof of a SaaS authorization failure while avoiding false
reports on secure denial and authorized-allow controls. The scored construct is
authorization-boundary reasoning plus replayable evidence, not general cyber
security ability, production exploitability, code repair, or broad web use.

Observable check: vulnerable credit requires a replayed request that satisfies
the task oracle, complete structured boundary reasoning, passing controls, and
no out-of-scope actions. Secure controls receive credit only when the protected
verifier replays their declared behavior and the agent reports no false finding.

## 3. Cohorts, Contamination, And Clusters

- Public examples and the three-task pilot are development/calibration material,
  not a scored leaderboard cohort.
- The pilot spans one API-token authorization cluster with three behaviors:
  `tok_cross_tenant_secret_read` (vulnerable),
  `tok_secure_export_scope_control` (denial), and
  `tok_export_token_reads_export_control` (authorized allow).
- Fixed public manifests and deterministic per-task seeds are memorizable. They
  demonstrate mechanics, not contamination resistance or generalization.
- A private scored cohort must stay outside public output and must be grouped by
  semantic scenario clusters before discriminability or confidence claims.
- Public and private variants from the same semantic cluster must not be split
  across calibration and scored evaluation without an explicit contamination review.

Observable check: the pilot manifest contains exactly the three named public
tasks and all three behavior classes. Private launch admission remains blocked
until cluster IDs, cluster-disjoint cohort rules, and a minimum discriminating
task count are versioned and independently reviewed.

## 4. Harness Decision

The proposed first launch track uses one canonical `no_tools` Harbor harness.
The agent receives a rendered authorization context and writes one structured
submission. The protected verifier owns deterministic backend replay. The
existing `live_http_tool_agent` lane remains a separate research diagnostic and
must not be ranked against the canonical lane.

Observable check: a run fingerprint fixes `harness_lane=no_tools`; mixed-harness
rows are rejected from a common comparison artifact.

## 5. Runtime And Network Contract

- Agent environment: Linux, `python:3.11-alpine`, 1 CPU, 2 GiB RAM, 120 seconds.
- Verifier environment: separate Linux container, Python 3.11, 1 CPU, 2 GiB RAM,
  120 seconds, no network.
- Agent filesystem output: `/logs/artifacts/submission.json` only.
- Agent target/network access: none in the canonical track. Model calls are made
  by the Harbor agent adapter through Kaggle Model Proxy, not by arbitrary code
  in the task container.
- Verifier inputs and scorer source are mounted or copied only into the separate
  verifier environment and are not exposed in the agent image.
- Harbor 0.13.2 invokes Docker commands with `bash -c`; each generated Alpine
  image supplies a network-free POSIX wrapper at `/bin/bash` that forwards to
  `/bin/sh`. Generated task and verifier scripts remain POSIX `sh`.

The pilot request is below the onboarding guide's documented default envelope
of 4 CPUs, 32 GiB, and 20 minutes per task; no resource exception is requested.

Observable check: generated `task.toml` and Dockerfiles match these limits;
direct agent and verifier egress fail closed; the agent image contains no task
manifest, oracle, scorer, or verifier source.

## 6. Agent Interaction Contract

Input is one rendered JSON context containing the task objective, policy,
actors, public references, API documentation, and output schema. The agent may
reason over this input and use the model/tooling supplied by the Harbor adapter;
it receives no shell/network target tool in the canonical track. It must write
exactly one JSON submission with a `findings` list. A vulnerable finding needs a
claim, structured boundary, impact, one or more evidence requests, and an empty
`out_of_scope_actions` list. A control submission reports no finding.

Observable check: missing, non-JSON, multi-artifact, or schema-invalid output
receives reward `0.0`; verifier artifacts identify the failure without exposing
private or oracle data to the agent.

## 7. Scoring And Verifier Contract

The local pilot freezes `score-policy-v2-boundary-normalization` through the
executed generated-task checksums recorded in the compact evidence artifact.
Reward is the deterministic native AuthZBench score in `[0.0, 1.0]`; pass
requires exactly `1.0`.

Alternative natural-language claims are diagnostic, but alternate solutions
are accepted when their structured request sequence replays to the same final
oracle, satisfies any evidence-chain requirements, semantically matches every
required boundary field, passes controls, and stays in scope. Superficial prose,
forged response bodies, wrong actors, wrong boundaries, malformed requests, and
unreplayable evidence fail closed.

The verifier executes in a separate no-network environment and writes
structured score, reward, and `/logs/verifier/ctrf.json` artifacts. The local
CTRF contract passes current-starter runs; exact hosted parser acceptance
remains part of KQ-001. The agent cannot inspect or mutate the task manifest,
oracle, scorer, or verifier environment.

Observable check: repeated NOP and Oracle executions are identical; adversarial
submissions fail; valid replay-equivalent submissions pass; the agent image and
trajectory contain no verifier-only inputs.

## 8. Model Proxy Contract

All model API traffic must route through Kaggle Model Proxy. Provider keys are
never embedded in the dataset, task image, instructions, logs, or artifacts.
Direct provider egress is denied. The proxy configuration and injected
short-lived credentials belong to the runner/platform boundary, not task files.
Reference solutions and verifiers are deterministic and make no model calls.

Observable check: a model-agent smoke has proxy request telemetry, no direct
provider connection, redacted logs, and a fail-closed negative test for proxy
bypass.

Kaggle OAuth, phone/identity verification, short-lived credential minting, and
a direct proxy HTTP 200 response of `ok` are verified. Harbor 0.13.2 adapter
inspection establishes the required OpenAI-compatible configuration:
provider-qualified model `openai/google/gemini-3.5-flash`,
the OpenAI provider API-key variable carrying the short-lived proxy credential,
the OpenAI API-base variable set to the Model Proxy `/openapi/v1` base, and the
mini-swe-agent fallback-key variable unset because it otherwise takes
precedence.

The corrected local mini-swe-agent run completed the secure-denial control with
a valid empty-findings submission, passing score and CTRF, reward `1.0`, and no
trial exception. Its retained trajectory records seven ATIF steps, 24,514 input
tokens, 6,007 cached-input tokens, and 2,552 output tokens. The final ATIF step
is the required completion-marker command and records the action as not
executed after terminalization; batch and trial exception fields remain empty.
Exact-secret scans found zero credential or proxy-base matches in the retained
proxy and local control files. The generated exact dataset also retains NOP
`0.0` and Oracle `1.0` for all three tasks.

This closes local Model Proxy agent/verifier completion, but not the entire
observable check above. Local Harbor 0.13.2 Docker cannot enforce hostname
allowlists or dynamic phase network switching, so the model run used a
temporary task copy whose agent, environment, and verifier network modes were
all `public`. It is compatibility evidence only, not direct-provider-denial,
offline-verifier-isolation, Kaggle-executor, Kaggle-hosted, or platform
acceptance evidence.

## 9. Pilot Acceptance

For each of the three public pilot tasks:

1. NOP creates no submission and receives `0.0`.
2. Oracle runs a substantive generated reference solution and receives `1.0`.
3. Both outcomes repeat deterministically.
4. The generated tree has `environment/Dockerfile`, `instruction.md`,
   `solution/solve.sh`, `tests/`, and `task.toml`.
5. The separate verifier emits inspectable score/reward artifacts and a clean
   public-safety scan.

Existing skeleton generation and secure-control empty-findings smoke evidence
remain historical local adapter evidence and do not satisfy this gate.

Local acceptance evidence: all three tasks retain two sequential NOP runs at
`0.0` and two sequential Oracle runs at `1.0`. A fresh current-starter pass
also completed one NOP and one Oracle per task with six `trial.log` files, six
CTRF reports, and inspected score/reward artifacts. Deterministic controls do
not establish the model result; the separately retained Model Proxy run
establishes only local compatibility and completion.

## 10. Operations And Launch Proposal

Primary maintainer: `bmendonca3`. The maintainer owns task/scorer versioning,
dependency refreshes, verifier regressions, holdout rotation coordination,
incident triage, and rollback to the last accepted dataset version. A backup
maintainer is required before launch.

Proposed rollout: a private technical pilot first, then a supporting campaign
only after local acceptance, Kaggle-executor parity, independent methodology
and AppSec review, privacy review, maintenance coverage, and platform approval.
No calendar date is committed before those gates. A hero campaign is out of
scope for the first release.

Observable check: every release has an immutable source/task/scorer fingerprint,
named primary and backup owners, rollback target, dependency review record, and
separate Kaggle go/no-go evidence.

## 11. Questions For Kaggle

- **KQ-001 — Hosted verifier acceptance:** Does Kaggle's executor require any
  CTRF fields or separate-verifier behavior beyond the current starter
  contract? Acceptance: the exact digest-bound pilot passes Kaggle's official
  parser without compatibility shims.
- **KQ-002 — Service topology:** Are Docker Compose or multiple target services
  supported if a later live-tool track is admitted? Acceptance: one documented
  supported topology and lifecycle.
- **KQ-003 — Resource policy:** Are 4 CPU, 32 GiB, and 20 minutes defaults or
  hard limits, and what is the exception path? Acceptance: platform-validated
  limits recorded in task metadata.
- **KQ-004 — Model Proxy:** What endpoint/configuration, credential injection,
  client-library support, telemetry, retry/rate-limit behavior, and bypass
  enforcement are required? Acceptance: one proxy-only model smoke with
  observable fail-closed direct egress.
- **KQ-005 — Network isolation:** What policies apply separately to agent,
  target, verifier, and Model Proxy traffic? Acceptance: platform evidence that
  the declared allow/deny matrix is enforced.
- **KQ-006 — Launch and private evaluation:** What review tier, minimum task
  count, private synchronization method, maintenance coverage, and staged
  launch gate apply? Acceptance: a written platform checklist with owners and
  go/no-go criteria.
