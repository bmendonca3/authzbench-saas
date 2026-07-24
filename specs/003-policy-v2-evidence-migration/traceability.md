# Requirement Traceability

> Historical completion record: this table captures the opt-in
> score-policy-v2.1 experiment as it was verified. Its Gemini result bundles
> remain preserved, but the registry now classifies that evidence as stale and
> requires a rerun under the canonical
> `score-policy-v2-boundary-normalization` contract before current comparison.

| Requirement | Implementation boundary | Evidence | Status |
| --- | --- | --- | --- |
| FR-001 | `authzbench/evidence_migration.py`, `scripts/rescore_policy_v1_submission.py` | focused migration tests | verified |
| FR-002 | migration utility | source SHA-256 pre/post immutability test | verified |
| FR-003 | migration validator | missing submission and wrong-policy tests | verified |
| FR-004 | registry/chart validators | policy-isolation test suite and registry validation | verified |
| FR-005 | generated views | deterministic chart regeneration and readback | verified |
| FR-006 | Gemini adapter | adapter and runner adversarial tests | verified |
| FR-007 | runner and raw result bundle | control plus two 63/63 result bundles with 63 model-output artifacts each and zero adapter/invalid failures | verified |
| FR-008 | registry promotion guard | repeated-run registry and promotion validators | verified |
| SC-001 | focused test suites | 88-test migration/adapter/runner/registry/chart/scorer/manifest slice | verified |
| SC-002 | source artifacts | pre/post SHA-256 evidence and preserved policy-v1 summaries | verified |
| SC-003 | registry and charts | validator passed; policy mismatch tests pass | verified |
| SC-004 | control result bundle | `results/gemini-api-policy-v2-control` and adapter tests | verified |
| SC-005 | two raw result bundles | run ids `20260718T072322651520Z-35ced0bb` and `20260718T073022937546Z-bfc400fc`; tracked public-safe summaries | verified |
| SC-006 | repository gates | 577-test full non-Docker public gate, scripted 63/63 baseline, registry, generated-artifact, claim, privacy, and whitespace checks passed | verified |
