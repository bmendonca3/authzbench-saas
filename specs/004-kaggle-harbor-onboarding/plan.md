# Implementation Plan

## Source And Gates

- Integrated and executed benchmark source: this repository root on `main` at
  `20cd189072b25dc406bd4fff03672a4ab0268648`; later documentation-only
  evidence updates do not change its task contract or digests.
- Preserved pilot checkpoint: `7f3da26d9b0240fae2e0f324d91a10e02380a66b`
  on `feature/kaggle-harbor-pilot`, based on
  `aae81c0f5aa3e998f001b0a1d754fc3068a237ae`.
- The original worktrees were preserved during reconciliation; the verified
  pilot is now integrated into the canonical clean `main` checkout.
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

## Current-Starter Completion Slice

1. Replace the legacy internal `dataset.toml` shape with the current Harbor
   `[dataset]`, author, and digest-backed task-reference structure.
2. Compute task content digests with the same ordered path/file-hash contract
   used by Harbor 0.13.2 and compare the result to `harbor add`.
3. Emit a minimal standard CTRF result for both missing-submission and scored
   verifier paths without adding a network-time dependency to the verifier.
4. Extend validators and focused tests for manifest structure, digest drift,
   CTRF output, and claim boundaries.
5. Regenerate the three-task public pilot, run fresh NOP and Oracle controls,
   and inspect `trial.log`, CTRF, score, and reward artifacts.
6. Update compact evidence, design status, Spec Kit traceability, and durable
   state without claiming Model Proxy, Kaggle executor, platform acceptance,
   scaled-cohort validity, independent review, organization approval, or launch.

## External Continuation

Kaggle authentication, direct Model Proxy health, and one local admitted LLM
agent/verifier completion are verified. The coherent schema clarification was
committed and pushed at `20cd189`, and Kaggle's pinned published runner checked
out that exact commit locally. Harbor 0.15 then failed before agent startup
because its mandatory nested egress sidecar requires nftables `fib` support
absent from the local Docker-in-Docker host. Obtain a Kaggle-supported
host/image contract and complete the same-digest run before scaling; this local
runner attempt is not Kaggle-hosted evidence.
Organization forms, invitations, private synchronization, uploads, messages,
publication, and launch remain separately gated.

## Verification Strategy

- Unit: reference-solution construction and builder mode behavior.
- Controls: NOP `0.0`; Oracle `1.0`; repeated deterministic scoring.
- Adversarial: malformed, forged, wrong actor/boundary, and unsupported task.
- Structure/privacy: generated dataset validator, redaction/public-safety checks,
  and direct artifact readback.
- Integration: real `harbor run --agent nop` and `--agent oracle` when Docker is available.
- Final: focused regression suite, strongest feasible public gate, `git diff --check`, and traceability convergence.
