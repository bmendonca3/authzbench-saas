# Qwen execution packet — T005C docs and public-gate integration

You are the implementation executor. Codex is the DAD/orchestrator.

Repository:

`/Users/brianmendonca/Documents/authzbench-saas`

Use `apply_patch` for edits.

## Exact edit scope

Edit only:

- `docs/kaggle-benchmark-design-contract.md`
- `scripts/validate_public.py`
- `tests/test_scored_cohort_contract.py`

Do not edit the scored-cohort JSON or validator, status/roadmap, other tests,
task manifests, public-safe summary artifacts, Spec Kit files, or private
directories. Do not read `tasks_private/`.

## Required implementation

1. Update only the relevant material in Section 3, “Cohorts, Contamination,
   And Clusters,” of the Kaggle design contract.
   - Link the versioned candidate contract:
     `../artifact/scored-cohort-contract.v1.json`.
   - Give its validation command:
     `python3 scripts/validate_scored_cohort_contract.py`.
   - State precisely that the candidate maps all 63 public calibration tasks
     into 17 semantic clusters and derives the exact public behavior totals:
     27 vulnerable, 21 denial, and 15 authorized-allow.
   - State only public-safe aggregate private evidence: 48 total private
     holdouts (24 active and 24 shadow), comprising 24 vulnerable and
     24 controls (12 denial and 12 authorized-allow), with aggregate public
     structure overlap 0.
   - Preserve the distinction that aggregate overlap 0 is not proof of semantic
     cluster disjointness.
   - Explicitly preserve all pending gates: private cluster assignment pending,
     cluster disjointness unverified/false, numeric minimum task and cluster
     counts null with `pending-review`, independent methodology review pending,
     admitted scored tasks 0, and launch readiness false.
   - Describe the 17-cluster mapping as a candidate pending independent review,
     not accepted methodology or launch evidence.
   - Do not rewrite the historical Kaggle execution sections or upgrade their
     evidence date/claim layer.

2. Integrate the validator into the normal public validation path.
   - In `validate(cwd, ...)`, add:
     `run([sys.executable, "scripts/validate_scored_cohort_contract.py"], cwd)`
   - Place it alongside the other artifact/readiness validators, before claim
     boundary and overclaim checks.
   - Do not weaken, reorder materially, or remove any existing gate.

3. Add two compact regression tests to
   `tests/test_scored_cohort_contract.py`:
   - the public validation script invokes the scored-cohort validator exactly
     once;
   - Section 3 links the versioned contract, exposes the command and exact
     public totals, and retains explicit pending/false/zero/null launch
     boundaries.
   Keep all current 55 passing cases and unique function names.

## Verification

Run:

```bash
python3 scripts/validate_scored_cohort_contract.py
python3 -m pytest -q tests/test_scored_cohort_contract.py
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
python3 -m py_compile scripts/validate_public.py
git diff --check
git status --short
```

Do not run the full public validator in this executor lane; the parent will run
that strongest gate after inspecting the diff.

## Completion report

Return exact files changed, the factual claim boundary added, all command
results and pytest count, confirmation no private directory was read, and any
residual uncertainty. Implement now; do not return a plan-only answer.
