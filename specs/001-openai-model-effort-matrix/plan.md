# Implementation Plan: OpenAI Model-Effort Benchmark Matrix

**Branch**: `improve/evidence-backed-hardening` | **Date**: 2026-07-12 | **Spec**: [spec.md](spec.md)

## Summary

Add a generic authenticated Codex no-tools adapter and a two-phase matrix orchestrator. Smoke every declared model/effort configuration under strict structured-output and provenance gates, then evaluate all 63 public tasks only for configurations admitted by a complete current report. Preserve hosted-service blockers separately from model performance.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: Python standard library and existing AuthZBench modules
**Storage**: JSON/JSONL run artifacts and public-safe JSON metadata
**Testing**: `unittest`, fixture CLIs, repository public validators
**Target Platform**: macOS/Linux CLI
**Project Type**: Benchmark runner and evaluation library
**Performance Goals**: At most one hosted call after a global blocker; serial full runs; bounded command output
**Constraints**: No callable tools, no new dependency, no private holdout access, no raw secrets or local paths in public artifacts
**Scale/Scope**: 27 admission configurations; 63 public tasks per admitted configuration

## Constitution Check

| Gate | Requirement | Status |
| --- | --- | --- |
| Measurement integrity | Compare only rows with identical source, protocol, schema, prompt class, and tool policy | Required |
| Fail closed | Reject malformed/unknown lifecycle and structured-output shapes | Required |
| Failure honesty | Separate infrastructure failure from model/scoring failure | Required |
| Privacy | Publish hashes and aggregate status, not raw prompts, traces, credentials, or local paths | Required |
| Reproducibility | Bind every row to explicit CLI/model/effort/source artifacts | Required |
| Resource control | Run serially and short-circuit a run-wide hosted blocker | Required |
| Claim boundary | Public split and requested-only identity remain diagnostic | Required |

No exception is approved. Any implementation that weakens one of these gates must be rejected.

## Technical Decisions

1. Use `codex exec --json --output-schema` in an ephemeral, read-only, no-tools invocation.
2. Validate event streams as an ordered lifecycle, not merely as a set containing a terminal event.
3. Normalize the model-facing schema to the benchmark submission contract with exact-key validation.
4. Hash raw event, stderr, prompt, schema, adapter source, protocol, and matrix inputs for audit without publishing raw content.
5. Create a run-level blocker sentinel only for exact global policy/credit classifiers; do not generalize arbitrary model errors into a global stop.
6. Treat model-output and parse failures as scored row content when infrastructure completed.
7. Require nonexisting destination run/report paths so stale evidence cannot be reused silently.
8. Make full admission depend on a complete 27-row smoke report that is itself validated against current source.
9. Record that `prompt_sha256` covers only the host-supplied user prompt. The current Codex CLI exposes no profile-skill loading disable, so that runtime context limitation is explicit and disqualifies rows from non-diagnostic promotion.
10. Preserve a public-safe normalized catalog and bind its digest and derived model/effort pairs into matrix loading and protocol provenance.
11. Disable web search through the current top-level `web_search="disabled"` CLI config. Do not pass the deprecated `web_search_cached` or `web_search_request` feature flags, because their pre-turn diagnostic events correctly fail the strict lifecycle gate.

## Project Structure

```text
artifact/
├── openai-codex-model-catalog-2026-07-12.json
├── openai-codex-model-effort-matrix-2026-07-12.json
└── openai-codex-credit-blocker-2026-07-12.json
authzbench/
└── evaluate.py
scripts/
├── codex_baseline_agent.py
└── run_codex_model_matrix.py
specs/001-openai-model-effort-matrix/
├── spec.md
├── plan.md
├── tasks.md
├── traceability.md
└── checklists/
    └── requirements.md
tests/
├── test_codex_baseline_adapter.py
├── test_codex_model_matrix.py
└── test_blinded_evaluation_protocol.py
```

## Verification Strategy

1. Run focused adapter/matrix/protocol unit tests with fixture CLIs.
2. Inspect generated metadata and lifecycle evidence from a real one-task authenticated preflight.
3. Validate matrix/source digests and public blocker artifact against the preserved raw evidence hashes.
4. Run the full public validator and all claim/privacy/provenance gates.
5. Run `git diff --check`, workflow checks, an independent changed-file review, and the upstream publication gate.
6. Retry hosted smokes once only after the external workspace-credit blocker is absent; do not infer that local tests prove hosted availability.

## Complexity Tracking

No additional dependency, persistent service, parallel hosted runner, or new package is justified. The two scripts isolate model invocation from matrix policy so each boundary can be tested independently.
