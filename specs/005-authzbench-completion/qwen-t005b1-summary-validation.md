# Execute Now: T005B1 Public-Safe Summary Validation

Do not ask a question. Edit the two named files now, run the checks, and
report. Do not delegate.

Repository: `<canonical-checkout>`

Edit only:

- `scripts/validate_scored_cohort_contract.py`
- `tests/test_scored_cohort_contract.py`

Do not edit any other path.

## Validator Change

Add an optional `summary_root` argument to `validate_contract`; default it to
`tasks_dir.parent`.

Require `source_bindings.public_safe_summary_paths` to equal exactly these four
paths:

```text
artifact/private-holdout-active-public-summary.json
artifact/private-holdout-shadow-public-summary.json
artifact/v1-task-scale-roadmap.json
artifact/private-holdout-operation-blocker.json
```

Load them under `summary_root`, fail closed on missing/malformed data, and
validate without reading `tasks_private/`.

For active and shadow summaries require:

```text
schema_version = holdout-public-safe-summary-v1
public_safe_summary = true
passed = true
private_holdouts_untracked = true
every publication_safety value = false
private_holdout_count = 24
vulnerable_count = 12
control_count = 12
denial_control_count = 6
authorized_allow_control_count = 6
public_structure_overlap_count = 0
```

Derive combined totals:

```text
private=48
vulnerable=24
controls=24
denial=12
authorized_allow=12
overlap=0
```

Require those to match
`private_scored_cohort_candidate.aggregate_private_summary_counts` and
`negative_control_requirements.aggregate_observed_private_summary_counts`.
Add any missing aggregate fields to the contract comparison only; do not edit
the contract unless its existing aggregates cannot represent these values.

Require `artifact/v1-task-scale-roadmap.json` to report
`current_validated_private_holdout_task_count=48` and
`artifact/private-holdout-operation-blocker.json` to report
`count_level_public_evidence.validated_private_holdout_task_count=48`.

Include the six derived private totals in validator/CLI structured output.

## Tests

Preserve all 18 tests. Add a helper that copies only the four public-safe
artifacts to a temporary `artifact/` tree and passes that directory as
`summary_root`.

Add fail-closed tests for:

- a wrong source-summary path list;
- `public_safe_summary=false`;
- any publication-safety flag set true; and
- a wrong active summary count.

The real contract must still pass.

Run:

```text
python3 scripts/validate_scored_cohort_contract.py
python3 -m pytest -q tests/test_scored_cohort_contract.py
git diff --check
```

Return public totals 63/27/21/15, private totals 48/24/24/12/12/0, test count,
and confirmation that only the validator and its test changed during this job.
