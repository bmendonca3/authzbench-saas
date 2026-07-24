# Implementation Plan

## Source And Gates

- Implementation worktree: this repository root.
- Branch: `feature/kaggle-harbor-pilot`.
- Base: `aae81c0f5aa3e998f001b0a1d754fc3068a237ae`.
- Both pre-existing worktrees remain untouched and retain their user-owned changes.
- Private data, credentials, remote actions, and platform/launch claims are excluded.

## Approach

1. Freeze the compact design contract and label unresolved Kaggle decisions.
2. Select one public API-token task for each of vulnerable, denial-control, and
   authorized-allow behavior.
3. Add a fail-closed public pilot Oracle mode that generates a substantive
   replayable vulnerable submission and correct control submissions.
4. Preserve the default non-Oracle skeleton behavior and reject unsupported
   tasks in the pilot mode.
5. Validate generated task structure, NOP, Oracle, deterministic output,
   adversarial evidence, verifier isolation, and public safety.
6. Attempt actual local Harbor execution only when the local Docker runtime is available.
7. Converge the Spec Kit packet and leave hosted/external actions explicitly gated.

## Verification Strategy

- Unit: reference-solution construction and builder mode behavior.
- Controls: NOP `0.0`; Oracle `1.0`; repeated deterministic scoring.
- Adversarial: malformed, forged, wrong actor/boundary, and unsupported task.
- Structure/privacy: generated dataset validator, redaction/public-safety checks,
  and direct artifact readback.
- Integration: real `harbor run --agent nop` and `--agent oracle` when Docker is available.
- Final: focused regression suite, strongest feasible public gate, `git diff --check`, and traceability convergence.
