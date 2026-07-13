# Feature Specification: OpenAI Model-Effort Benchmark Matrix

**Feature Branch**: `improve/evidence-backed-hardening`
**Created**: 2026-07-12
**Status**: In progress
**Input**: Test every compatible authenticated OpenAI/Codex model at each supported non-delegating reasoning effort under the same AuthZBench-SaaS public protocol.

## User Scenarios & Testing

### User Story 1 - Compare structurally equivalent model configurations (P1)

A benchmark maintainer can admit a model/effort configuration only after one public task proves that the current CLI can execute it with structured output, no callable tools, complete provenance, and the same blinded protocol used by every other row.

**Why this priority**: Accuracy comparisons are misleading when model identity, reasoning effort, source, prompt, or tool access differs between rows.

**Independent Test**: Run the smoke phase against fixture evaluator outputs and verify that all and only the 27 declared configurations are admitted or excluded with a reason.

**Acceptance Scenarios**:

1. **Given** the versioned 27-configuration matrix, **when** a smoke summary has matching model, effort, CLI, schema, prompt, protocol, source, and tool telemetry, **then** that configuration is admitted.
2. **Given** a stale or forged summary, **when** any binding differs, **then** admission fails with a specific reason.
3. **Given** an admitted configuration, **when** the full phase runs, **then** it evaluates exactly 63 public tasks without changing the protocol or source boundary.

---

### User Story 2 - Fail safely when hosted execution is unavailable (P1)

A maintainer can distinguish a workspace-credit or policy failure from model quality and prevent one global blocker from triggering an expensive sequence of doomed hosted calls.

**Why this priority**: Infrastructure failure is not a model result, and uncontrolled retries waste credits without adding evidence.

**Independent Test**: Feed the adapter a lifecycle-complete failed event stream containing the exact workspace-credit message and verify that a run-level sentinel stops later remote calls while preserving public-safe hashes and status.

**Acceptance Scenarios**:

1. **Given** the exact authenticated workspace-credit failure, **when** the first task fails before inference, **then** the run records a global blocker and later tasks do not invoke the hosted CLI.
2. **Given** a legitimate model output or parse failure after inference, **when** scoring completes, **then** the row preserves the failure as a benchmark result rather than censoring the configuration.
3. **Given** an incomplete or out-of-order JSONL lifecycle, **when** the adapter validates it, **then** the invocation fails closed.

---

### User Story 3 - Publish auditable claims without raw private traces (P2)

A reviewer can reproduce why a configuration was admitted, excluded, completed, or blocked from public-safe artifacts without receiving local paths, credentials, raw prompts, or unverified model-quality claims.

**Why this priority**: Benchmark credibility depends on traceable evidence and accurate claim boundaries.

**Independent Test**: Run the public validators and privacy scan against the matrix, blocker artifact, documentation, and copied summaries.

**Acceptance Scenarios**:

1. **Given** a blocked preflight, **when** public artifacts are generated, **then** they identify the requested model/effort, CLI version, source/protocol bindings, event hashes, and blocker class without presenting an accuracy score.
2. **Given** an incomplete full run, **when** completion is evaluated, **then** it cannot be promoted as a completed comparison row.
3. **Given** a complete run containing legitimate invalid submissions, **when** completion is evaluated, **then** the row remains eligible for comparison if infrastructure and provenance gates pass and the failures are scored truthfully.

## Edge Cases

- A run directory or report already exists from an earlier source boundary.
- A matrix report claims all configurations but omits or duplicates a model/effort pair.
- The CLI emits a nonfatal item-level error before a valid structured result.
- An event arrives after the terminal event or a terminal event appears before `turn.started`.
- Structured JSON contains correct values plus unexpected keys, methods, statuses, or nested shapes.
- Model metadata is requested-only rather than independently effective-model verified.
- The CLI ignores user config/rules but still loads profile skill metadata, and the exposed feature list has no skill-loading disable.
- The authenticated CLI is available but the workspace has no credits.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST define exactly 27 supported, non-delegating model/effort configurations in a versioned public matrix artifact.
- **FR-002**: The smoke phase MUST evaluate exactly one public task for every declared configuration and validate full matrix coverage before reporting admission complete.
- **FR-003**: Admission MUST bind the summary to the current commit, clean worktree, protocol manifest, source set, adapter sources, matrix digest, CLI version, model, effort, output schema, and prompt.
- **FR-004**: The adapter MUST disable callable tools and fail closed on tool calls, unknown event types, malformed JSONL, invalid lifecycle ordering, or post-terminal events.
- **FR-005**: The structured-output normalizer MUST enforce exact keys, supported HTTP methods, valid status codes, object-valued JSON bodies, and canonical boundary pairs.
- **FR-006**: A global hosted-service blocker MUST create a run-level sentinel that prevents subsequent remote invocations in the same run.
- **FR-007**: Infrastructure and policy failures MUST be separated from model output, parse, and scoring failures.
- **FR-008**: Full completion MUST require 63 task artifacts, complete tool telemetry, matching provenance for every task, and zero infrastructure failures; it MUST NOT require perfect model output.
- **FR-009**: The full phase MUST only run configurations admitted by a complete, current, source-bound smoke report.
- **FR-010**: Existing run directories and reports MUST not be silently reused or overwritten.
- **FR-011**: Public blocker evidence MUST expose only public-safe status, counts, versions, identifiers, and cryptographic hashes, with an explicit no-model-quality claim boundary.
- **FR-012**: The matrix runner MUST exit nonzero when a phase is incomplete and use a distinct status for the global hosted-service blocker.
- **FR-013**: Every row MUST state that its prompt hash covers only the host-supplied user prompt and MUST record the current profile-skill loading limitation; such rows remain diagnostic while that runtime context is neither disabled nor source-bound.

### Key Entities

- **Model configuration**: Requested model, reasoning effort, expected CLI version, and admission status.
- **Source binding**: Commit, clean-tree status, protocol manifest/source-set hashes, adapter source hashes, schema hash, prompt hash, and matrix digest.
- **Event lifecycle**: Ordered thread start, turn start, item events, and exactly one final terminal event.
- **Global blocker**: Run-scoped classification and public-safe evidence showing that hosted inference could not start.
- **Comparison row**: A complete 63-task summary whose provenance and telemetry match the admitted configuration.

## Success Criteria

- **SC-001**: Focused adapter and matrix tests cover lifecycle ordering, strict normalization, stale artifacts, forged coverage, source binding, and global-blocker short-circuiting with no failures.
- **SC-002**: The complete repository public validator passes without weakening any existing benchmark, privacy, provenance, or claim-boundary gate.
- **SC-003**: A complete smoke report accounts for all 27 configurations exactly once, or records a truthful global blocker before making further hosted calls.
- **SC-004**: Every completed comparison row contains exactly 63 task results with complete zero-tool telemetry and matching source/protocol hashes.
- **SC-005**: Public documentation never represents a credit-blocked preflight, requested-only identity, public-split result, or incomplete run as a verified model-quality ranking.
- **SC-006**: Admission and full-completion tests reject rows that omit or misstate prompt-hash scope or profile-skill loading status.

## Assumptions

- The authenticated Codex CLI is the authorized execution surface; an API key is not assumed.
- The public 63-task split is diagnostic evidence and does not replace private holdout evaluation.
- Hosted workspace credits are an external dependency and may remain unavailable after local implementation is complete.
- Spec Kit CLI initialization is not required to use these feature artifacts; the local CLI is currently unavailable.
