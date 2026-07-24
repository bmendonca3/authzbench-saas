# Blinded Control Evidence V2 Specification

Status: locally verified foundation specification
Classification: full Spec Kit workflow

## Purpose

Define a versioned, machine-readable evidence protocol before changing task
manifests or score semantics. The foundation must expose the current migration
gap without changing the meaning or promotability of any existing result.

## User Scenarios

### US-001 — Participant receives one unambiguous contract

A benchmark adapter can generate a participant submission from a canonical
schema covering vulnerable findings, replay requests, concise proof chains,
and secure-control verification.

### US-002 — Maintainer audits migration readiness

A maintainer can deterministically inventory vulnerable tasks and see which
ones lack explicit, contiguous, replayable evidence requirements. A strict
mode fails until every in-scope vulnerable task has a contract.

### US-003 — Reviewer distinguishes draft from comparable evidence

A reviewer can tell that v2 schemas are draft/non-promotable until task,
score-policy, isolation, canary, and registry gates are explicitly activated.
Existing v1 and score-policy-v2 evidence remains unchanged.

## Functional Requirements

- **FR-001**: Publish one canonical JSON Schema bundle for replay requests, vulnerable evidence items/findings, secure-control verification, participant submissions, task evidence requirements, and run-summary contract identity.
- **FR-002**: Give every contract and the bundle stable version identifiers and a deterministic SHA-256 identity.
- **FR-003**: Provide a standard-library audit that rejects malformed manifests and reports evidence-contract coverage deterministically.
- **FR-004**: Strict audit mode must fail when any vulnerable task lacks a non-empty, contiguous, replayable `evidence_requirements` chain.
- **FR-005**: Default audit mode must report current migration debt without changing existing public validation or task fingerprints.
- **FR-006**: The v2 participant contract must separate submitted proof requests from scorer-owned transcripts/exploration logs.
- **FR-007**: The foundation must preserve compliant `score-policy-v2-boundary-normalization` and `blinded-control-evidence-v1` behavior, current task manifests, fingerprints, and baseline records. Bounded fail-closed validator fixes must be explicit and regression-tested.
- **FR-008**: Documentation must name the later activation gates: 27/27 evidence coverage, new score-policy identifier for safety changes, OS-level isolation, malicious escape fixture, canaries, comparability-key expansion, and promotion-validator support.
- **FR-009**: Malformed request/status/body, ambiguous finding/verification combinations, non-contiguous requirement indexes, duplicate task ids, and invalid JSON roots must fail closed in the audit or contract tests.
- **FR-010**: Use no new runtime dependency and perform no model, private-holdout, network, or external-publication action.
- **FR-011**: Repair the adjacent promotion-gate field mismatch: validation must read the runner's canonical `protocol_version`, accept the bounded legacy alias only when consistent, and reject conflicting identities.

## Success Criteria

- **SC-001**: The schema bundle is valid deterministic JSON with a stable digest reported by the audit.
- **SC-002**: Current public coverage is reported exactly and strict mode fails while the migration is incomplete.
- **SC-003**: Synthetic complete coverage passes strict mode; malformed and incomplete fixtures fail with stable finding codes.
- **SC-004**: Current compliant scorer/evaluator/fingerprint behavior remains unchanged, and its baseline-registry regression suite passes with the bounded protocol-field fix.
- **SC-005**: Complete public validation and workflow/diff gates pass without touching the dirty main checkout or external state.

## Non-Goals

- Activating v2 evaluation or promotion.
- Editing the remaining 19 vulnerable task manifests.
- Changing weighted scores or removing the historical safety subscore.
- Claiming JSON Schema conformance through an unavailable third-party engine.
- Running Kiro, models, Docker, or private holdouts.
