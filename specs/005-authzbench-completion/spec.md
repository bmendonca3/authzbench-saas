# AuthZBench-SaaS Product And Benchmark Completion Specification

Status: active
Evidence date: 2026-07-29
Classification: full Spec Kit workflow (`specify` CLI unavailable; artifacts maintained manually)

## Outcome

Finish every locally actionable AuthZBench-SaaS product, benchmark, packaging,
review-contract, documentation, and verification item, then leave one
Kaggle-reviewable release candidate whose remaining gates require real external
actors or a deliberate source freeze. The result must be technically sound,
reproducible, fail closed, and explicit about what has and has not been
validated.

The canonical source is `<canonical-checkout>` on
`main`. The starting Git commit for this tranche is
`acb6434c4bb25cce53a1a9f4eb31c869986743ca`; accepted work remains uncommitted
until the user separately authorizes a commit. The benchmark task contract used
by the latest published-runner attempt is
`20cd189072b25dc406bd4fff03672a4ab0268648`.

## Current Evidence

- The checkout and `origin/main` started at `acb6434`; the current dirty tree
  contains preserved completion work and must not be reset, cleaned, or
  partially promoted.
- The three-task Harbor pilot, current digest-backed dataset manifest, NOP
  `0.0`, Oracle `1.0`, deterministic CTRF, and one local Model Proxy agent run
  are verified.
- Kaggle's current public starter still points to
  `harbor-git-v1:latest`. On 2026-07-28 that tag still resolved to
  `sha256:772dfa2383c07928ee020f8235323a81dee9ff519750e978f776cc0448533f32`,
  the same digest used by the failed exact-commit attempt.
- The latest AuthZBench-SaaS Gmail thread still ends with Nicholas Kang's
  2026-07-22 onboarding message; targeted searches found no later
  AuthZBench/Harbor/Kaggle reply through 2026-07-28.
- The public-view readiness baseline reports 9/10 gates passing. The remaining
  gate is intentionally source-bound: a new candidate needs a deliberate
  commit/source freeze and fresh matching paper, smoke, private aggregate,
  fixture, and CI evidence. Historical evidence cannot be relabeled as
  current-head proof.
- Independent AppSec, benchmark/evals, and agent/tooling lanes remain pending.
  SaaS-provider validation, Kaggle executor parity, organization approval,
  hosted operation, and launch are not complete.
- Independent audit on 2026-07-29 identified local release, review-contract,
  benchmark-integrity, runtime-reproduction, paper, and documentation defects.
  Those findings are now first-class backlog items; prior T001-T007 completion
  is historical and does not close this tranche.
- The separately scoped OpenAI model-effort matrix remains optional,
  credit-dependent research. It is not a substitute for benchmark validity,
  Kaggle executor parity, human review, or launch evidence.

## Functional Requirements

- **FR-001 — Canonical source and preservation:** Work only in the named
  canonical repository, preserve all user changes and private boundaries, and
  do not commit, push, upload, send, deploy, authenticate, or publish without
  separate current authorization.
- **FR-002 — One truthful backlog:** Reconcile status, roadmap, Spec Kit,
  readiness, release, paper, host, and review surfaces so historical,
  current-local, external, deferred, and optional work cannot be conflated.
- **FR-003 — Benchmark integrity:** Bind task manifests, task IDs, apps,
  taxonomy, oracle audit, scorer semantics, evidence requirements, baseline
  provenance, fingerprints, and Harbor metadata to exact validated inputs.
  Malformed, duplicate, non-finite, stale, or unsupported inputs must fail
  closed.
- **FR-004 — Cohort methodology:** Maintain a versioned scored-cohort contract
  with semantic clusters, public/private disjointness rules, negative controls,
  seed/variant policy, numeric minimum analysis requirements, and an explicit
  independent decision artifact. Pending evidence must not imply admission or
  launch readiness.
- **FR-005 — Runtime and reproduction:** A clean checkout and container must
  install and run the canonical public validator without undeclared test
  dependencies, fail-open wrappers, ambient working-tree leakage, or accidental
  output writes.
- **FR-006 — Release and artifact integrity:** Host bundles must materialize
  the exact requested Git ref; package metadata, license, supported Python,
  CI, walkthroughs, generated artifacts, and release records must agree.
- **FR-007 — Paper and claims:** The paper, technical report, tables, charts,
  README, roadmap, artifact index, and claim ledger must describe the current
  63-public / 48-private-summary / 111-total boundary and distinguish offline
  rescores, historical runs, local validation, and external validation.
- **FR-008 — Review contracts:** Three independent review lanes and the
  separate SaaS/product-security lane need closed schemas, public-safe intake,
  exact reviewed-SHA/artifact binding, reject/unresolved semantics, and
  mutation-tested strict validation. Private review uses a separate controlled
  response contract and only aggregate public projection.
- **FR-009 — Executor parity:** Re-run exact source and task digests only on a
  Kaggle-supported host/image whose Harbor 0.15 egress sidecar starts, then
  preserve trajectory, submission, CTRF, reward, verifier, token, resource,
  and source/digest evidence.
- **FR-010 — Launch governance:** Keep independent human dispositions,
  cohort freeze, backup maintainer, organization, privacy/private-sync, hosted
  operation, launch tier/date/assets, publication, and leaderboard evidence as
  separately observable gates.
- **FR-011 — Optional research boundary:** Do not spend hosted credits or run
  the remaining OpenAI matrix without separate authorization. It cannot close
  FR-008 through FR-010.
- **FR-012 — Verification discipline:** Every material edit must have focused
  regression coverage, parent readback, strongest feasible clean/public gates,
  an adversarial challenge, and an explicit residual-risk statement.

## Success Criteria

- **SC-001:** The task list contains every audit finding, owner, dependency,
  verification command, and honest status; no prior “complete” label masks an
  open defect.
- **SC-002:** All locally actionable P0/P1 items are implemented or rejected
  with documented evidence and rationale.
- **SC-003:** Public benchmark truth is internally consistent: 63 tasks across
  6 apps, 27 vulnerable, 21 denial controls, 15 authorized-allow controls, 48
  public-safe private-summary tasks, and 111 total scale.
- **SC-004:** Dependency-free unit discovery executes all intended tests;
  focused mutation tests prove validators reject malformed, duplicate,
  non-finite, stale, source-drifted, rejected, unresolved, and privacy-unsafe
  evidence.
- **SC-005:** A clean/source-materialized reproduction path and the strongest
  feasible public validation pass without modifying canonical generated
  artifacts unexpectedly.
- **SC-006:** Public-view readiness and strict external gates either pass on an
  exact frozen candidate or name the smallest real blocker; validators are not
  weakened to force green output.
- **SC-007:** Kaggle executor, human review, private methodology, organization,
  hosted operation, and launch remain `blocked` or `not-run` until direct
  evidence exists.
- **SC-008:** Parent inspection and independent post-change audit find no known
  local defect, privacy leak, claim overreach, or unaccounted delegated edit.

## Non-Goals

This packet does not authorize credentials, paid or hosted model runs, private
task-body/raw-result access, external messages, issue creation, invitations,
uploads, organization forms, publication, commits, pushes, releases, deploys,
or launch. It does not treat a locally prepared review packet as review
evidence, and it does not make the optional model matrix a prerequisite for the
benchmark.
