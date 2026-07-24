# Tasks: OpenAI Model-Effort Benchmark Matrix

**Input**: [spec.md](spec.md), [plan.md](plan.md)
**Organization**: Tasks are grouped by independently verifiable user outcome.

## Phase 1 - Protocol And Matrix Foundation

- [x] T001 Define the 27 supported non-delegating configurations in `artifact/openai-codex-model-effort-matrix-2026-07-12.json` and bind them to a public-safe normalized source catalog.
- [x] T002 Add generic CLI/schema/tool telemetry support in `authzbench/evaluate.py`.
- [x] T003 Add the ephemeral no-tools invocation and public-safe metadata boundary in `scripts/codex_baseline_agent.py`.
- [x] T004 Add smoke/full orchestration and source-binding policy in `scripts/run_codex_model_matrix.py`.

## Phase 2 - Fail-Closed Admission

- [x] T005 Enforce ordered JSONL lifecycle validation and strict exact-key submission normalization in `scripts/codex_baseline_agent.py`.
- [x] T006 Enforce nonexisting run/report destinations, evaluator return codes, full 27-row admission coverage, current source binding, prompt-hash/runtime-context scope, and unique configuration coverage in `scripts/run_codex_model_matrix.py`.
- [x] T007 Preserve legitimate model/parse failures as scored results while rejecting infrastructure or provenance failures from completed comparison rows.
- [x] T008 Add a run-level exact hosted-credit blocker sentinel and verify that it prevents later remote calls.
- [x] T009 Add adversarial fixture tests for T005-T008 in `tests/test_codex_baseline_adapter.py` and `tests/test_codex_model_matrix.py`.

## Phase 3 - Public Evidence And Documentation

- [x] T010 Add `artifact/openai-codex-credit-blocker-2026-07-12.json` from the preserved public-safe real preflight hashes with an explicit no-quality-claim boundary.
- [x] T011 Reconcile README, artifact index, benchmark quality plan, matrix artifact, and this traceability set.
- [x] T012 Run focused tests, the full public validator, privacy/claim checks, workflow checks, and diff review.
- [x] T013 Obtain an independent changed-file audit and close every blocker or record it explicitly.

## Phase 4 - Hosted Execution And Publication

- [x] T014 Establish a committed clean source boundary with `bmendonca3` authorship and push only after the upstream publication gate.
- [x] T015 Retry the 27 one-task smokes serially when workspace credits are available; validate exact complete coverage.
- [ ] T016 Run all 63 public tasks for every admitted configuration serially and preserve raw ignored evidence.
- [x] T017 Publish only complete public-safe comparison artifacts and refresh PR state/CI without merging.
- [x] T018 Migrate host-review artifact upload from the deprecated Node 20 action line to `actions/upload-artifact@v7` and verify fresh exact-head GitHub CI.
- [x] T019 Replace deprecated web-search feature flags with the current top-level disabled config, preserve rejection of pre-turn item events, and verify one clean hosted admission smoke before resuming the matrix.
- [x] T020 Add the current exact workspace-credit wording to the top-level failure allowlist after the full run exposed classifier drift; preserve model-text spoof resistance and matrix-wide short-circuit tests.
- [x] T021 Publish a public-safe admission/full-phase aggregate with source/report hashes, one complete diagnostic row, incomplete-row counts, and an explicit no-ranking boundary.

## Blocked Task

- T016 remains externally blocked after credits were exhausted during the full phase. One configuration completed 63/63; 23 admitted configurations are incomplete and excluded from comparison, while three `gpt-5.4` efforts were excluded during admission on direct capacity failures. Do not retry until the exact workspace-credit sentinel is absent.
