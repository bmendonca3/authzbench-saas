# Execute Now: T005B Validator Hardening Only

Do not ask a question. Make these exact validator/test edits now, run the
checks, inspect the diff, and report. Do not delegate.

Repository: `<canonical-checkout>`

Edit only:

- `scripts/validate_scored_cohort_contract.py`
- `tests/test_scored_cohort_contract.py`
- `artifact/scored-cohort-contract.v1.json` only if a directly required
  structural correction is found

Do not edit docs, `scripts/validate_public.py`, Phase 0 files, private files, or
the completion packet.

## Required Hardening

1. Derive each task's app from its manifest `app` field, require it to be a
   nonempty string, and require it to match the manifest's parent directory.
2. Require every cluster ID to match stable kebab case:
   `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`. Continue to reject task-ID-like names.
3. Require `source_bindings.public_manifest_paths` to equal the exact sorted
   set of 63 tracked public manifest paths.
4. Require `source_bindings.public_safe_summary_paths` to equal exactly:
   - `artifact/private-holdout-active-public-summary.json`
   - `artifact/private-holdout-shadow-public-summary.json`
   - `artifact/v1-task-scale-roadmap.json`
   - `artifact/private-holdout-operation-blocker.json`
5. Require audited baseline commit
   `acb6434c4bb25cce53a1a9f4eb31c869986743ca` to exist and be an ancestor of
   current HEAD. Do not require HEAD equality.
6. Load the active and shadow public-safe summaries from their exact paths.
   For each require:
   - `schema_version=holdout-public-safe-summary-v1`;
   - `public_safe_summary=true`;
   - `passed=true`;
   - `private_holdouts_untracked=true`;
   - every value in `publication_safety` is exactly false;
   - counts: 24 private, 12 vulnerable, 12 controls, 6 denial, 6
     authorized-allow, and public-structure overlap 0.
   Derive and compare combined totals 48 private, 24 vulnerable, 24 controls,
   12 denial, 12 authorized-allow, and overlap 0 against both contract
   aggregate sections.
7. Load the scale roadmap and blocker paths named above. Require their
   public-safe count surfaces to agree on 48, without reading any private body.
8. Under `private_scored_cohort_candidate`, recursively reject keys whose
   normalized names contain any of:
   `task_id`, `seed`, `route`, `oracle`, `body`, `manifest_path`,
   `raw_result`, or `diagnostic_detail` (including plural forms). A new
   `private_task_ids` key must fail even if its value contains no path literal.
9. Required cluster-disjoint rule values, seed/variant policy values,
   minimum-analysis entries, review questions, and acceptance criteria must be
   nonempty strings/lists as applicable, not merely present.
10. Fail closed with structured errors instead of raising on malformed object,
    list, string, missing-file, JSON, or Git inputs.

For summary mutation tests, add an optional validator argument such as
`summary_root` that defaults to the repository root. Tests may copy only the
four public-safe files to a temporary `artifact/` tree and mutate those copies.
Do not access `tasks_private/`.

## Required Tests

Preserve all 18 existing tests and add fail-closed coverage for at least:

- invalid kebab-case cluster ID;
- manifest app mismatch;
- source manifest path mismatch;
- source summary path mismatch;
- unsafe public-safe summary flag or publication-safety field;
- wrong public-safe summary count;
- injected `private_task_ids`;
- empty required rule/policy/review text; and
- nonexistent or non-ancestor audited baseline SHA.

Run:

```text
python3 scripts/validate_scored_cohort_contract.py
python3 -m pytest -q tests/test_scored_cohort_contract.py
git diff --check
```

Return the validator's exact 63/27/21/15 and private 48/24/24/12/12 totals,
test count, and confirmation that no private body or out-of-scope file was
accessed or changed.
