# Qwen/Cline Executor Harness Traceability

| Requirement | Acceptance observation | Direct evidence | Status |
| --- | --- | --- | --- |
| FR-001 | Cline-visible repository instructions distinguish parent and executor modes | `AGENTS.md`; final live read call | verified |
| FR-002 | Invalid/unsafe/hash-drifted contracts reject before run | focused contract tests | verified |
| FR-003 / FR-005 | Only named inputs materialize; symlink/hardlink/traversal/collision inputs reject | focused workspace tests | verified |
| FR-004 / SC-001 / SC-004 | Hook cancels private, outside-root, unlisted tool/read/write payloads | direct tests; final `hook-self-test.json` | verified |
| FR-006 | Post-run manifest rejects extra/missing/mode-changed/out-of-scope mutations | focused manifest tests | verified |
| FR-007 | Accepted run exports a patch while the canonical target remains absent | final live evidence and canonical readback | verified |
| FR-008 | Raw stream tolerates warning lines and compact stream groups coherent reasoning | parser tests; final live logs | verified |
| FR-009 / FR-013 | Wrong/missing model, ledger mismatch, malformed terminal, output-hash mismatch, and repetition reject | focused tests; newline-mismatch rejection evidence | verified |
| FR-010 | No commit, push, credential, external message, or publication action occurs | exact tool ledger and status/process audit | verified |
| FR-011 | Sandbox allows named workspace/bridge and denies outside content/write/second listener | final live `sandbox_checks` | verified |
| FR-012 | Exact runtime and control hashes are retained | final live `summary.json` | verified |
| SC-002 | Allowed and rejected fake-Cline runs behave deterministically | 20 focused tests | verified |
| SC-003 | Live accepted smoke uses exact provider/model and exact admitted output hash | `<local-harness-state>/20260729T170003Z-qwen38-harness-smoke-dgutab3b/summary.json` | verified |
| SC-005 | Focused and strongest repository gates pass | 20 focused tests; `<local-gate-evidence-logs>/1785344663807_evidence.log` | verified |
