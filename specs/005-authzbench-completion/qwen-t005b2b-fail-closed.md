# Qwen execution packet — T005B2B fail-closed contract hardening

You are the implementation executor. Codex is the DAD/orchestrator and will
independently inspect every diff and rerun all checks. Work only in:

`<canonical-checkout>`

## Exact edit scope

Edit only these three files:

- `artifact/scored-cohort-contract.v1.json`
- `scripts/validate_scored_cohort_contract.py`
- `tests/test_scored_cohort_contract.py`

Do not edit docs, status/roadmap files, Spec Kit files, other scripts, public
task manifests, public-safe summary artifacts, or any private task directory.
Do not read `tasks_private/` or any private task bodies. Preserve all accepted
behavior/source-binding checks and all existing test intent.

## Required implementation

1. Make private aggregate validation explicit and fail closed.
   - Add these exact fields to
     `private_scored_cohort_candidate.aggregate_private_summary_counts`:
     - `total_vulnerable_count`: `24`
     - `total_control_count`: `24`
     - `total_denial_control_count`: `12`
     - `total_authorized_allow_control_count`: `12`
   - Require every aggregate field to be present, have the exact expected
     integer value, and equal the totals derived from the two public-safe
     summaries.
   - Delete the current behavior that inserts missing aggregate fields into the
     in-memory contract. Validation must never repair or mutate input.

2. Reject private-detail keys recursively in
   `private_scored_cohort_candidate`.
   - Walk nested dictionaries and lists.
   - Normalize key case and hyphen/space separators.
   - Reject singular or plural forms for these private-detail concepts:
     `task_id`, `seed`, `route`, `oracle`, `body`, `manifest_path`,
     `raw_result`, and `diagnostic_detail`.
   - A nested key such as `private_task_ids`, `Task-IDs`, `oracle_bodies`, or
     `diagnostic_details` must fail with a structured error that identifies the
     offending key path.
   - Do not reject the approved aggregate/status/notes keys merely because the
     subtree is named `private_scored_cohort_candidate`.
   - Preserve the existing serialized-value checks for forbidden private path
     fragments.

3. Harden public-safe summary validation.
   - For both active and shadow summaries, `publication_safety` must be a
     non-empty JSON object.
   - Every value in it must be exactly JSON `false`; empty objects, lists,
     strings, null, integers, or any true/non-boolean value must fail cleanly.

4. Harden required-methodology fields without changing the candidate state.
   - Every required value in `cluster_disjoint_rules` and
     `seed_and_variant_handling` must be a non-empty string.
   - `minimum_discriminating_cohort.required_analysis` must be a JSON list with
     the exact five current non-empty string tokens, with no duplicates.
   - `independent_methodology_review_gate.review_questions` and
     `acceptance_criteria` must each be non-empty lists made entirely of
     non-empty strings.
   - Preserve numeric minimums as null, review status as pending, admitted
     scored task count as 0, cluster-disjointness as false, and launch readiness
     as false.
   - Add type checks for every object/list touched above so malformed JSON
     produces validation errors rather than uncaught exceptions.

5. Repair and expand the tests.
   - Remove the four duplicate test-function definitions introduced in T005B2A
     so every declared `test_*` function name is unique and all intended source
     binding cases still run.
   - Add focused mutation tests for:
     - each required aggregate field missing and at least one wrong aggregate;
     - a nested `private_task_ids` key and one differently normalized/plural
       forbidden key;
     - empty and non-object `publication_safety`;
     - empty required rule/policy strings;
     - malformed/duplicate `required_analysis`;
     - empty or non-string review questions/acceptance criteria.
   - Tests must mutate temporary contract/summary copies only.

## Verification

Run all of:

```bash
python3 scripts/validate_scored_cohort_contract.py
python3 -m pytest -q tests/test_scored_cohort_contract.py
python3 - <<'PY'
import ast
from collections import Counter
p = "tests/test_scored_cohort_contract.py"
t = ast.parse(open(p, encoding="utf-8").read())
names = [
    node.name for node in t.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name.startswith("test_")
]
dupes = {name: count for name, count in Counter(names).items() if count > 1}
assert not dupes, dupes
print(f"unique_test_functions={len(names)}")
PY
git diff --check
git status --short
```

## Completion report

Return:

- exact files changed;
- concise behavioral summary;
- test/validator results including collected pytest count;
- confirmation that no private task directory was read;
- any residual risk or uncertainty.

Do not merely analyze or propose changes. Implement them now.
