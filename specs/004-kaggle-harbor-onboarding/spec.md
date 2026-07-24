# AuthZBench-SaaS Kaggle / Harbor Onboarding Specification

Status: current-starter local compatibility verified; external Kaggle gates remain open
Classification: full Spec Kit workflow

## Purpose

Produce one preserved implementation source, one reviewable Kaggle benchmark
design contract, and one representative Harbor pilot with real NOP, Oracle, and
protected verifier evidence. Then close every locally actionable requirement in
the current Kaggle Harbor starter while tracking Model Proxy, Kaggle executor,
scaled-cohort, independent-review, organization, and launch evidence separately.

The detailed shaped execution contract is in `task-contract.md`; the
requirements-quality gate is in `checklist.md`.

## User Scenarios

### US-001 — Kaggle reviewer can understand the benchmark

Given the design contract, a reviewer can identify the single measured
capability, task/dataset strategy, runtime, interaction flow, scoring,
anti-gaming controls, maintenance owner, and unresolved platform questions
without inferring acceptance or launch readiness.

### US-002 — Maintainer can run current-starter local controls

Given the generated public pilot, the maintainer can validate a digest-backed
Harbor dataset manifest, run NOP and Oracle, and inspect trial, CTRF, score, and
reward artifacts for the exact generated task digests.

### US-003 — Credentialed platform work has a safe handoff

Given explicit user authorization, the maintainer can mint short-lived Kaggle
Model Proxy credentials, run one LLM agent, exercise Kaggle's published Harbor
executor, and preserve redacted parity evidence without storing secrets.

### US-004 — Launch owners can see every remaining gate

Given the task contract and traceability table, the benchmark owner and Kaggle
can distinguish pilot mechanics from scaled-cohort validity, independent
review, organization approval, private synchronization, and public launch.

## Functional Requirements

- **FR-001**: Preserve all user-owned changes and name one exact implementation source.
- **FR-002**: Treat the July 22 onboarding direction as current without inferring FDE assignment or acceptance.
- **FR-003**: Decide or explicitly question capability, harness, data,
  contamination, runtime, interaction, scoring, verifier isolation, Model Proxy,
  maintenance, and launch topics.
- **FR-004**: Map pilot tasks to Harbor environment, instruction, solution,
  verifier/tests, and task metadata surfaces.
- **FR-005**: Pilot vulnerable, secure-denial, and authorized-allow behavior.
- **FR-006**: Implement substantive public reference solutions; a vulnerable
  placeholder or sentinel-only script is insufficient.
- **FR-007**: Prove deterministic NOP `0.0` and Oracle `1.0` for every pilot task.
- **FR-008**: Fail closed on malformed, forged, wrong-actor, wrong-boundary, or
  superficial evidence while keeping verifier inputs inaccessible to the agent.
- **FR-009**: Validate generated artifacts for public safety and inspectability.
- **FR-010**: Keep credentials, hosted execution, communications, private
  sharing, organization creation, and launch as explicit external gates.
- **FR-011**: Maintain requirement-to-evidence traceability and terminal worker accounting.
- **FR-012**: Record the complete onboarding guide and current public starter
  as dated sources without treating email links as completed implementation.
- **FR-013**: Generate a Harbor 0.13.2-compatible dataset manifest using
  `[dataset]`, `[[dataset.authors]]`, and digest-backed `[[tasks]]`.
- **FR-014**: Make every generated verifier write a CTRF report alongside
  score and reward artifacts, including fail-closed NOP behavior.
- **FR-015**: Preserve credential-safe Model Proxy health and one-agent run
  evidence; execute only with explicit authorization and keep compatibility,
  isolation, executor, hosted, and acceptance claims separate.
- **FR-016**: Preserve a version/digest-bound Kaggle executor parity contract;
  do not substitute a local run for executor evidence.
- **FR-017**: Require a reviewed minimum scored-cohort size, cluster-disjoint
  public/private strategy, contamination controls, and independent methodology,
  AppSec, agent/tooling, and SaaS-provider validation before leaderboard claims.
- **FR-018**: Track backup maintenance ownership, organization approval, launch
  tier/date, messaging/assets, privacy review, publication, and leaderboard
  evidence as separate launch gates.
- **FR-019**: Treat private GitHub-to-Kaggle synchronization as conditional on
  the chosen private-dataset architecture, never as a default credential step.

## Success Criteria

- **SC-001**: Exact source and preservation strategy are recorded.
- **SC-002**: Every Kaggle design topic is a decision with an observable check or a named question.
- **SC-003**: Each pilot task repeats its NOP and real-Oracle expected reward.
- **SC-004**: Adversarial verifier controls fail closed without scorer/privacy regressions.
- **SC-005**: Focused and strongest feasible integrated local gates pass.
- **SC-006**: External states remain `not-run` or `blocked` until directly evidenced.
- **SC-007**: Generated dataset digests match the installed Harbor 0.13.2
  content-hash computation for the exact generated task trees.
- **SC-008**: Fresh NOP and Oracle jobs contain inspectable `trial.log`,
  `verifier/ctrf.json`, score, and reward evidence.
- **SC-009**: Model Proxy, Kaggle executor, scaled cohort, independent reviews,
  organization, and launch are never collapsed into a single readiness flag.

## Non-Goals

Paid/full model matrices, private holdout inspection, unapproved credential
handling, external messages, Kaggle organization changes, uploads, publication,
pushes, hosted-acceptance claims, and launch claims. Credentialed and external
steps may proceed only after a later explicit gate.
