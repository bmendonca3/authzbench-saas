# Requirement-To-Evidence Traceability

| Requirement | Implementation / artifact | Verification | Status |
| --- | --- | --- | --- |
| FR-001 | Matrix plus normalized catalog artifacts | Catalog digest/derivation, matrix schema, and exact configuration-set tests | Verified |
| FR-002 | `scripts/run_codex_model_matrix.py` | Full smoke coverage/duplicate/omission tests; 27-configuration hosted smoke report | Verified |
| FR-003 | `scripts/run_codex_model_matrix.py`, `authzbench/evaluate.py` | Source-binding and forged-summary tests | Verified |
| FR-004 | `scripts/codex_baseline_agent.py` | Tool event, unknown event, malformed stream, lifecycle-order tests, current CLI config regression, and one hosted admission smoke | Verified |
| FR-005 | `scripts/codex_baseline_agent.py` | Extra-key, method, status, body, and boundary-shape tests | Verified |
| FR-006 | Adapter run-level blocker sentinel | Legacy/current exact-message tests, model-text spoof control, and matrix-wide one-call fixture | Verified |
| FR-007 | Adapter metadata and matrix completion policy | Fixture model failure remains scored; infra failure excludes completion | Verified |
| FR-008 | Full completion validator | 63-task/provenance/telemetry/infrastructure adversarial tests | Verified |
| FR-009 | Validated admitted-configuration loader | Stale/forged/incomplete admission report tests | Verified |
| FR-010 | Matrix destination preflight | Existing run/report refusal tests | Verified |
| FR-011 | `artifact/openai-codex-credit-blocker-2026-07-12.json` | Public contract test and direct ignored raw-hash reconciliation | Verified |
| FR-012 | Matrix CLI exit policy | Complete/incomplete/global-blocker exit-code tests | Verified |
| FR-013 | Adapter runtime-context metadata and matrix gates | Prompt-hash scope and profile-skill status propagation/admission tests | Verified |
| FR-014 | `.github/workflows/validate.yml` | Exact-head GitHub Actions public-validation and host-presentation jobs; action annotation audit | Verified |
| FR-015 | `artifact/openai-codex-hosted-diagnostic-2026-07-12.json` | Aggregate arithmetic, hash-shape, row-completion, registry, and ranking-boundary contract test | Verified |

## External Evidence Boundary

The original authenticated preflight reached Codex CLI execution but failed before model inference because the workspace was out of credits. A later clean-source admission completed all 27 configuration decisions, then the full phase exhausted credits after one complete 63-task row and 25 tasks of the next row. The remaining 23 full rows are incomplete and cannot be compared. The historic public blocker artifact remains bound to its ignored raw event/stderr hashes; the later raw run evidence also remains ignored, with only the reviewed aggregate in `artifact/openai-codex-hosted-diagnostic-2026-07-12.json` tracked publicly.

## Completion Rule

Change a row to `Verified` only after the named focused test or artifact check passes on the final source boundary. Hosted-only requirements remain `Blocked` until current direct execution evidence exists.
