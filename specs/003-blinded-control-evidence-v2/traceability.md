# Blinded Control Evidence V2 Foundation Traceability

| Requirement | Planned implementation / evidence | Status |
| --- | --- | --- |
| FR-001–FR-002 canonical contracts and identity | pinned schema bundle; contract module; deterministic digest and identity tests | verified |
| FR-003–FR-005 deterministic migration audit | replay-validating module/CLI; current, synthetic, empty, narrowed, and adversarial coverage tests | verified |
| FR-006 proof/transcript separation | exclusive participant modes in schema/manual validator; migration guide | verified |
| FR-007 compatibility boundary | evaluator diff clean; 160-test regression slice; full suite/public gate | verified |
| FR-008 activation gates | migration guide and durable remaining-work ledger | verified |
| FR-009 malformed/ambiguous inputs | 23 focused protocol-contract tests with stable finding codes | verified |
| FR-010 local standard-library scope | dependency/diff/state audit; no model/private/network/external action | verified |
| FR-011 adjacent promotion field mismatch | real runner-shaped, conflicting, unsupported, and missing runner protocol regressions | verified |
| SC-001–SC-003 schema/audit behavior | 23 focused tests; default 8/27 exit 0; strict 8/27 exit 1 | verified |
| SC-004 current behavior | 28 registry + 12 blinded protocol tests; 557-pass full suite | verified |
| SC-005 complete convergence | host/public presentation gate; workflow, compile, diff, and preservation checks | verified |
