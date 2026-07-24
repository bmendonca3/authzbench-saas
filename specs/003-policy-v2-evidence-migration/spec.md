# Policy-v2 Evidence Migration and Gemini Rerun Specification

Status: locally verified implementation; external publication not performed
Classification: full Spec Kit workflow

## Outcome

Produce traceable score-policy-v2 evidence without rewriting policy-v1 artifacts,
then execute two complete 63-task Gemini API rows only after migration, adapter,
fingerprint, and promotion gates pass.

## Functional Requirements

- **FR-001**: Define a machine-validated re-score artifact with source policy,
  source artifact digest, target policy, tool version, and
  `rescored_from_policy_v1` status.
- **FR-002**: Re-score only provenance-complete retained submissions and preserve
  every source summary byte-for-byte.
- **FR-003**: Classify incomplete or unbound evidence as rerun-required without
  reconstructing missing submissions.
- **FR-004**: Prevent validators, registries, charts, and aggregate analysis from
  comparing or averaging policy-v1 and policy-v2 evidence.
- **FR-005**: Regenerate policy-v2 views only from digest-bound inputs and prove
  deterministic reproduction.
- **FR-006**: Add a Gemini API-key adapter that keeps the key environment-only,
  fails closed, verifies the returned model identity when available, and writes
  one model-output artifact per task.
- **FR-007**: Run one bounded control before the matrix; proceed to two 63-task
  executions only with zero adapter failures and zero invalid submissions.
- **FR-008**: Promote a Gemini row only when its fingerprint, source provenance,
  policy version, completeness, repeated-run, and registry guards pass.

## Constraints and Non-goals

- Never modify policy-v1 summaries or present re-scoring as fresh execution.
- Never print, persist, copy, or place the Gemini API key in commands, artifacts,
  specs, logs, or source files.
- Use the Gemini Developer API with API-key authentication, not Vertex AI or
  Google Cloud authentication.
- Preserve all staged, unstaged, and untracked user work. Local commits are
  allowed only by the current worktree-reconciliation request; do not push,
  reset, or delete preserved scratch artifacts.
- Do not register incomplete or failed runs as current evidence.

## Success Criteria

- **SC-001**: Migration schema and adversarial validators pass focused tests.
- **SC-002**: Source digests reproduce and source policy-v1 artifacts remain
  unchanged after migration tests.
- **SC-003**: Cross-policy registry/chart mixing is rejected by tests.
- **SC-004**: A Gemini control request completes through the benchmark adapter.
- **SC-005**: Each eligible full run contains 63 task rows, 63 model-output
  artifacts, verified policy-v2 fingerprinting, zero adapter failures, and zero
  invalid submissions.
- **SC-006**: Full local public validation, generated-artifact checks, registry
  checks, and staged/unstaged whitespace checks pass before any current-row claim.
