# Qwen execution packet — finish T005B2B tests and type edges

You are the implementation executor. Codex is the DAD/orchestrator.

Repository:

`/Users/brianmendonca/Documents/authzbench-saas`

The previous lane already updated the contract and most validator logic before
its live stream was canceled. Preserve that accepted work.

## Exact edit scope

Edit only:

- `scripts/validate_scored_cohort_contract.py`
- `tests/test_scored_cohort_contract.py`

Do not edit the contract JSON, docs, status/roadmap, Spec Kit files, task
manifests, public-safe artifacts, or private directories. Do not read
`tasks_private/`.

## Required changes

1. In aggregate validation, require `type(value) is int`, not
   `isinstance(value, int)`, so JSON booleans cannot satisfy integer fields.
   In particular, `public_structure_overlap_count: false` must fail.

2. For the hardened fields from the prior packet, fail with structured errors
   instead of raising:
   - loaded active/shadow summary roots must be JSON objects;
   - their `counts` values must be JSON objects;
   - required contract objects must remain guarded before `.get`;
   - non-empty required strings/lists must reject whitespace-only strings.
   Do not broadly rewrite unrelated validator logic.

3. Delete the second definition of each currently duplicated test function:
   - `test_invalid_kebab_case_cluster_id_fails`
   - `test_manifest_app_mismatch_fails`
   - `test_wrong_public_manifest_paths_fails`
   - `test_nonexistent_audited_baseline_sha_fails`
   Preserve one effective test for each behavior. After the edit, every
   top-level `test_*` function name must be unique.

4. Add focused temporary-copy mutation tests for all of these:
   - parameterized missing required aggregate fields, covering all eight exact
     aggregate keys;
   - wrong aggregate value;
   - boolean `public_structure_overlap_count`;
   - nested `private_task_ids`;
   - normalized/plural forbidden key such as `Oracle-Bodies` or
     `diagnostic details`;
   - empty and non-object `publication_safety`;
   - empty/whitespace required cluster rule;
   - empty/whitespace seed/variant policy;
   - non-list, duplicate, and non-string `required_analysis`;
   - empty review questions and a non-string acceptance criterion;
   - malformed summary root/counts produces errors, not exceptions.
   Mutate only temporary contract and summary copies. Reuse existing fixtures.

5. Keep the valid contract behavior unchanged: 17 clusters, 63 tasks,
   27 vulnerable, 21 denial, 15 authorized-allow, private totals
   48/24/24/12/12/0, pending review, zero admitted scored tasks, and
   launch-ready false.

## Verification

Run:

```bash
python3 -m py_compile scripts/validate_scored_cohort_contract.py tests/test_scored_cohort_contract.py
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

Report exact files changed, validator result, pytest count/result, uniqueness
result, confirmation that no private directory was read, and residual risk.
Implement now; do not return a plan-only response.
