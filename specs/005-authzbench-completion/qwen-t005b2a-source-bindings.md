# Execute Now: T005B2A Source Bindings

Do not ask a question. Edit the validator and tests now, run the checks, and
report. Do not delegate.

Repository: `/Users/brianmendonca/Documents/authzbench-saas`

Edit only:

- `scripts/validate_scored_cohort_contract.py`
- `tests/test_scored_cohort_contract.py`

Do not edit any other file.

## Validator Changes

1. For every public manifest, read `app` from the JSON:
   - require a nonempty string;
   - require it to equal the manifest parent-directory name; and
   - use that manifest value, not only the directory, when deriving cluster
     apps.
2. Require `source_bindings.public_manifest_paths` to equal the exact sorted
   63 paths derived from `tasks/*/*.json`.
3. Require each cluster ID to match:
   `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`.
   Continue to reject task-ID-like cluster names.
4. Validate `audited_baseline_commit` with local Git:
   - exactly 40 lowercase hex characters;
   - commit object exists; and
   - is an ancestor of current HEAD.
   Preserve the current contract's exact `acb6434...` value requirement for
   this v1 candidate.
5. Catch malformed/non-object task manifests, missing task IDs, duplicate
   manifest task IDs, and local Git command errors as structured validation
   errors instead of uncaught exceptions.

## Tests

Preserve all 23 tests and add fail-closed tests for:

- invalid kebab-case cluster ID such as `Bad Cluster`;
- a manifest `app` value that does not match its parent directory (use a
  temporary copy of the public tasks only);
- a wrong `public_manifest_paths` list; and
- a nonexistent audited baseline SHA.

Run:

```text
python3 scripts/validate_scored_cohort_contract.py
python3 -m pytest -q tests/test_scored_cohort_contract.py
git diff --check
```

Return test count and confirmation that only these two files changed during
this job.
