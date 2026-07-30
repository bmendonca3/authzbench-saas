# Execute T005 Now: Scored-Cohort And Contamination Candidate

Do not ask a question and do not return an analysis-only response. Implement
this one bounded lane, run its checks, inspect the diff, and report. Codex is
the parent/DAD and final verifier; do not delegate.

## Target

- Repository: `<canonical-checkout>`
- Branch/HEAD: `main` at
  `acb6434c4bb25cce53a1a9f4eb31c869986743ca`
- Existing accepted tracked edits are limited to `ROADMAP.md`,
  `docs/status.md`, and `tests/test_v1_ready_doc_alignment.py`. Preserve them
  exactly.
- Existing untracked `specs/005-authzbench-completion/` is parent-owned. Do not
  edit it.
- Do not touch linked worktrees.

Stop if any other tracked file is already modified.

## Objective

Implement T005 only: a versioned, machine-checkable scored-cohort and
contamination **candidate** that an independent benchmark/evals methodology
reviewer can accept, reject, or amend.

This lane must not claim that a scored cohort is frozen, launch-ready, or
independently reviewed. It must not choose an unsupported numeric minimum.

## Allowed Reads

- All 63 tracked public manifests under `tasks/*/*.json`.
- Public documentation and public source/tests needed to implement and verify
  the contract.
- Only these public-safe private summary surfaces:
  - `artifact/private-holdout-active-public-summary.json`
  - `artifact/private-holdout-shadow-public-summary.json`
  - `artifact/v1-task-scale-roadmap.json`
  - `artifact/private-holdout-operation-blocker.json`

Do not read `tasks_private/`, private task bodies/IDs/seeds/routes/oracles, raw
private results, captures, credentials, or local secret material.

## Allowed Writes

Only:

- new `artifact/scored-cohort-contract.v1.json`
- new `scripts/validate_scored_cohort_contract.py`
- new `tests/test_scored_cohort_contract.py`
- `docs/kaggle-benchmark-design-contract.md`
- `scripts/validate_public.py`

If a correct implementation requires another file, stop and report it instead
of widening scope.

## Required Contract Semantics

Use only public and public-safe metadata. The JSON contract must include:

1. A stable schema/version and status such as
   `candidate_pending_independent_review`, an evidence date of `2026-07-28`,
   and an explicit public claim boundary.
2. Source bindings:
   - audited baseline commit `acb6434c4bb25cce53a1a9f4eb31c869986743ca`;
   - public manifest count `63`;
   - public-manifest-set SHA-256 computed deterministically from sorted
     relative paths and exact bytes;
   - public-safe private summary count `48`;
   - active scoring policy ID `score-policy-v2-boundary-normalization`; and
   - the exact public/public-safe source paths used.
3. A public calibration inventory that maps every current public task ID
   exactly once into a semantic scenario `cluster_id`. Cluster IDs must be
   stable semantic names, not seeds or task IDs. Include app and behavior
   counts. Public tasks and the three-task pilot are calibration/development
   material and are not scored leaderboard tasks.
4. A private scored-candidate section that publishes no private task IDs,
   seeds, routes, oracle details, bodies, or paths. It may cite only the
   allowed public-safe summaries and aggregate counts. It must state:
   - private cluster assignment is pending maintainer-private work;
   - cluster-disjointness cannot yet be verified from public-safe summaries;
   - admitted scored task count is `0`;
   - launch/scored-cohort readiness is `false`.
5. Cluster-disjoint rules:
   - no semantic cluster may cross calibration and scored cohorts;
   - aliases, route variants, seeds, decoys, and multistep variants of the same
     authorization scenario keep the same cluster ID;
   - suspected overlap quarantines the scored cluster until review;
   - scores from incompatible pack/cluster versions are not merged.
6. Negative-control requirements for vulnerable, denial-control, and
   authorized-allow behavior. Record only aggregate observed private-summary
   counts; do not claim per-cluster private coverage.
7. Seed/variant and contamination handling, including rotation, retirement or
   invalidation, reruns, and public-safe incident reporting.
8. A `minimum_discriminating_cohort` object whose numeric task/cluster minimums
   are `null`, status is exactly `pending-review`, and whose required analysis
   covers discriminability/power, uncertainty or bootstrap intervals,
   false-positive sensitivity, per-cluster balance, and ranking stability.
   Do not reuse the old v0 shape minimum as the scored-cohort minimum.
9. An independent methodology review gate with status `pending`, decision
   `null`, no invented reviewer, explicit review questions/acceptance fields,
   and launch readiness `false`.

The private summaries' aggregate `public_structure_overlap_count=0` does not
prove semantic cluster-disjointness. Preserve that distinction.

## Required Validator

`scripts/validate_scored_cohort_contract.py` must use repository-native Python
and no new dependency. It must fail closed and at minimum verify:

- exact schema/status and required claim-boundary fields;
- all 63 tracked public task IDs appear exactly once in the public cluster
  inventory, with matching app/behavior totals;
- cluster ID syntax and nonempty semantic grouping;
- deterministic public-manifest-set SHA-256;
- both public-safe private summaries are safe/passing, total 48, and the
  contract does not expose forbidden private detail;
- admitted private scored count is zero and cluster verification/readiness are
  pending/false;
- numeric minimums are null with `pending-review`;
- independent review is pending with null decision/reviewer evidence;
- required disjointness, negative-control, contamination, and versioning rules
  are present; and
- launch readiness remains false.

The CLI should print a compact structured result and exit 0 for a structurally
valid pending candidate, nonzero for malformed or overclaiming contracts.

Add the validator to `scripts/validate_public.py` as a public structural gate.
Pending review is valid candidate state; it must not make v1/public launch
claims pass.

## Required Tests

`tests/test_scored_cohort_contract.py` must cover the real contract plus
fail-closed mutations, including at least:

- duplicate/missing public task mapping;
- manifest-set digest mismatch;
- leaked private task identifiers or forbidden private-detail fields;
- nonzero admitted scored tasks while cluster verification is pending;
- invented/complete independent review;
- numeric minimum supplied while status is `pending-review`; and
- `launch_ready=true`.

Use temporary copies/objects; never inspect private bodies.

## Documentation

Update only the cohort/contamination section and directly related observable
check in `docs/kaggle-benchmark-design-contract.md`:

- link the new contract and validator command;
- state that public calibration clusters are inventoried;
- state that the private mapping, minimum, cluster-disjoint proof, and
  independent decision remain pending;
- do not alter Kaggle executor evidence or claim platform/review completion.

## Required Verification

Run:

```text
python3 scripts/validate_scored_cohort_contract.py
python3 -m pytest -q tests/test_scored_cohort_contract.py
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
git diff --check
```

Before returning, inspect the full diff. Confirm the only newly changed tracked
files are the five T005 allowlisted paths and that the three pre-existing
Phase 0 edits are unchanged.

Return every changed file, the public cluster count and coverage result, exact
check results, pending-review fields, blockers/residual risk, and confirmation
that no private body, external resource, commit, remote, or linked worktree was
accessed or changed.
