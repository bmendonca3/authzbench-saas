# Run-Bundle Integrity Implementation Plan

## Technical Context

- Python standard library only.
- Existing result directories contain `summary.json` plus per-task artifacts.
- Outer wrappers may add logs after the evaluator exits, so manifest creation is
  an explicit post-run promotion step.
- Existing submission-bundle and leaderboard validators remain separate.

## Design

1. Add `authzbench/run_bundle.py` with pure build and validate functions.
2. Use the fixed filename `run-bundle-manifest.json`; exclude only that file.
3. Hash sorted regular files, reject all symlinks, and encode only relative POSIX paths.
4. Store exact and glob requirements inside the bundle-digest payload.
5. Parse validation input with duplicate-key rejection and return structured finding codes.
6. Add thin scripts for build and validate CLI behavior.
7. Add adversarial tests and update the rerun/attestation docs.

## Files

- `authzbench/run_bundle.py`
- `scripts/build_run_bundle_manifest.py`
- `scripts/validate_run_bundle_manifest.py`
- `tests/test_run_bundle_manifest.py`
- `tests/test_submission_bundle_validator.py`
- `artifact/run-bundle.md`
- `docs/baseline-rerun-readiness-runbook.md`

## Verification

- Focused: `python3 -m pytest -q tests/test_run_bundle_manifest.py tests/test_submission_bundle_validator.py`
- Regression: relevant bundle, runner, evaluator, and registry tests.
- Final: `python3 scripts/validate_public.py --include-scripted-baseline` plus claim, link, workflow, and diff checks.

## Complexity And Safety Gates

- No dependency or lockfile changes.
- No implicit overwrite or deletion.
- No raw file contents in the manifest.
- No external or private execution.
