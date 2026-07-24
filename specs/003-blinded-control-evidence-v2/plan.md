# Blinded Control Evidence V2 Foundation Plan

## Technical Context

- Python 3.10+ standard library only; `jsonschema` is not a project dependency.
- Existing runtime validation is distributed across `score.py`, `evaluate.py`,
  and `validate_manifests.py`.
- The current fingerprint binds task bodies, score policy, and
  `evidence-requirements-v1`.
- The foundation must be inspectable without becoming an active scoring path.

## Design

1. Add one Draft 2020-12 JSON Schema bundle with reusable `$defs` and explicit
   draft/non-promotable metadata.
2. Add a small standard-library contract module that loads duplicate-key-safe
   JSON, checks the schema bundle identity/required definitions, and audits
   task evidence coverage using the existing manifest validator.
3. Add a CLI with report-only default and `--require-complete` migration gate.
4. Add synthetic/adversarial tests plus current-coverage assertions.
5. Document version activation and comparability requirements without changing
   current scorer, evaluator, tasks, fingerprints, baselines, or registry rows.

## Planned Files

- `schemas/blinded-control-evidence-v2.schema.json`
- `authzbench/protocol_contracts.py`
- `scripts/audit_evidence_contracts.py`
- `tests/test_protocol_contracts.py`
- `docs/blinded-control-evidence-v2-migration.md`
- `specs/003-blinded-control-evidence-v2/*`

## Verification

- Focused contract/audit tests and CLI exit-contract tests.
- Current scorer/evaluator/fingerprint/promotion regression slice.
- Complete public validation, workflow check, compile, and diff checks.

## Complexity And Safety Gates

- No dependency or lockfile changes.
- No runtime protocol activation in this slice.
- No task-manifest or score-policy mutation.
- No remote, model, private, or destructive action.
