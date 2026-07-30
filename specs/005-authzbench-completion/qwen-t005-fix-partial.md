# Execute Now: Repair And Complete The Partial T005 Lane

Do not ask for context. All paths and decisions are below. Edit now, run the
checks, inspect the diff, and report. Do not delegate.

## Current Partial State

The canonical repository is
`<canonical-checkout>`, branch `main`, HEAD
`acb6434c4bb25cce53a1a9f4eb31c869986743ca`.

The prior T005 attempt created:

- `artifact/scored-cohort-contract.v1.json`
- `scripts/validate_scored_cohort_contract.py`
- `tests/test_scored_cohort_contract.py`

It did not update:

- `docs/kaggle-benchmark-design-contract.md`
- `scripts/validate_public.py`

The three accepted Phase 0 edits in `ROADMAP.md`, `docs/status.md`, and
`tests/test_v1_ready_doc_alignment.py` must remain byte-for-byte unchanged.
The completion packet is parent-owned and must not be edited.

Only the five T005 paths above may be created/edited.

## Parent-Rejected Defects To Fix

1. The contract's public behavior counts are wrong. For example, authorized
   operations are labeled `vulnerable`. Derive each public task's behavior
   exactly as:

   ```text
   vulnerable       if expected_vulnerable is true
   denial           if expected_vulnerable is false and control_type == denial
   authorized_allow if expected_vulnerable is false and control_type == authorized_allow
   ```

   Regenerate every cluster's behavior counts from the actual public
   manifests. Across all clusters the exact totals must be 27 vulnerable,
   21 denial, and 15 authorized-allow. Remove the redundant `behaviors` field
   or make the schema use only one canonical `behavior_counts` field.
2. The validator currently checks that behavior/app fields exist but does not
   verify them against the manifests. It must derive task ID, app, and behavior
   from every public manifest and require each cluster's:
   - `task_count`;
   - sorted unique `apps`;
   - `app_count`; and
   - `behavior_counts`
   to equal the derived values. Also require aggregate 27/21/15 behavior
   totals and 63 tasks.
3. Cluster ID validation is too weak. Require a stable kebab-case semantic ID
   regex and reject task-ID-like or empty IDs.
4. The validator hard-codes private totals without loading the public-safe
   summaries. It must load the two exact source paths listed in the contract,
   require each summary to be `public_safe_summary=true`, `passed=true`,
   `private_holdouts_untracked=true`, contain no publication-safety leak flag,
   and report 24 tasks, 12 vulnerable, 6 denial, and 6 authorized-allow.
   Derive the combined 48/24/12/12 totals and compare them to the contract.
   Do not read `tasks_private/` or any private body.
5. Private-detail rejection is too narrow. Under
   `private_scored_cohort_candidate`, recursively reject any added key whose
   normalized name contains task ID, seed, route, oracle, body, manifest path,
   raw result, or diagnostic detail. Continue to allow only aggregate/public
   summary metadata. Add a mutation test that injects a
   `private_task_ids` field; do not rely only on inserting the literal
   `tasks_private/` string into prose.
6. Require source binding paths to equal the tracked public manifest paths and
   the allowed four public-safe source paths. Require the audited baseline
   commit to exist and be an ancestor of current HEAD; do not require current
   HEAD equality after a future commit.
7. For required rule/analysis/review fields, validate nonempty values and exact
   pending/null/false state, not mere key presence.

## Complete The Missing Work

1. Update `docs/kaggle-benchmark-design-contract.md` only in Section 3 and its
   directly related observable check:
   - link `artifact/scored-cohort-contract.v1.json`;
   - show `python3 scripts/validate_scored_cohort_contract.py`;
   - state that all 63 public calibration tasks are assigned to candidate
     semantic clusters;
   - state that private cluster assignment, cluster-disjoint proof, numeric
     minimum, and independent methodology decision remain pending;
   - state admitted scored tasks remain zero and launch readiness false.
   Do not change executor/platform evidence.
2. Add the standalone validator to `scripts/validate_public.py` as a structural
   public gate. A valid pending candidate exits 0; this must not claim review,
   scored-cohort freeze, or launch readiness.
3. Complete `tests/test_scored_cohort_contract.py` so it covers:
   - the real contract and exact 63 / 27 / 21 / 15 derived totals;
   - duplicate and missing mapping;
   - digest mismatch;
   - wrong cluster app or behavior count;
   - unsafe/malformed public-safe summary using a temporary repo fixture or
     injectable summary-root argument;
   - injected `private_task_ids`;
   - nonzero admitted count;
   - invented/complete review;
   - numeric minimum with pending status; and
   - launch-ready true.

Use repository-native Python/pytest and no new dependency. Keep the CLI output
compact and structured.

## Boundaries

Do not edit source pins, readiness evidence, expected readiness fixture,
private files, benchmark/scorer/baseline files, or any path outside the five
T005 allowlisted files. Do not read private bodies, commit, push, publish,
install dependencies, use external services, or touch linked worktrees.

## Verification

Run:

```text
python3 scripts/validate_scored_cohort_contract.py
python3 -m pytest -q tests/test_scored_cohort_contract.py
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
git diff --check
```

Before returning, inspect the full five-file T005 diff and confirm Phase 0
files are unchanged from the start of this job. Report the cluster count,
derived 63/27/21/15 totals, pending-review state, exact check results, and any
remaining risk.
