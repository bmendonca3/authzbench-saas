# Run-Bundle Integrity Traceability

| Requirement | Implementation / evidence | Status |
| --- | --- | --- |
| FR-001–FR-003 deterministic safe inventory | `authzbench/run_bundle.py`; `test_manifest_is_deterministic_and_contains_metadata_only` | verified |
| FR-004 no overwrite | build CLI; `test_refuses_to_overwrite_existing_manifest` | verified |
| FR-005–FR-007 fail-closed validation and requirements | validator functions; focused adversarial suite (22 passing tests with submission regression) | verified |
| FR-008 metadata-only privacy boundary | manifest serialization test; `artifact/run-bundle.md`; claim-boundary checks | verified |
| FR-009 stable local CLIs | `test_cli_build_and_validate_exit_contract`; standard-library import/compile check | verified |
| FR-010 documentation integration/no score drift | runbook diff; baseline/runner regression slice; complete public and host gates | verified |
| SC-001 deterministic output | byte-identical independent-directory test | verified |
| SC-002 adversarial mutations | tamper, deletion, late file, symlink, FIFO, missing evidence, unsafe paths, malformed hash, duplicate path/key, and claim-tamper controls | verified |
| SC-003 repository gates | focused tests; `validate_host_presentation.py --allow-dirty` including complete public validation | verified |
| SC-004 claim/timing documentation | final documentation readback; claim, overclaim, and Markdown-link checks | verified |
| SC-005 state preservation | final branch/HEAD/status review; dirty `main` remains at 40 entries and original HEAD | verified |
