# Run Bundle And Attestation Guidance

This guide describes what a public or maintainer run bundle should contain
before it is treated as comparable benchmark evidence. It does not create a
hosted leaderboard and does not replace the validator.

## Bundle Contents

A reviewable run bundle should include:

- run `summary.json`;
- per-task `score.json`;
- per-task `submission.json`;
- per-task `agent.json`;
- agent, model, harness type, and tool-access metadata;
- benchmark version and exact commit SHA;
- runner-emitted `benchmark_fingerprint`;
- `comparability_key` when the run is converted into a leaderboard submission;
- repeated-run source summaries when a row claims repeated provenance;
- a short note declaring whether the run is a harness check, no-tools model
  baseline, tool-agent baseline, or private-holdout submission candidate.

## Fingerprint Verification

The runner-emitted `benchmark_fingerprint` binds the task set, task paths,
score policy, scorer contract, evidence contract, and task counts. A row should
be considered directly comparable only when the validator accepts its
`comparability_key`.

Use:

```bash
python3 scripts/validate_leaderboard_submission.py \
  --submission 'leaderboard_submissions/**/*.json' \
  --require-source-summary
```

The validator is authoritative for schema consistency, source-summary checks,
repeat evidence, eligibility flags, and recomputed aggregate metrics.

## Eligibility Rules

For the current v0.0 schema, a row marked `leaderboard_eligible: true` must:

- use `leaderboard_schema_version: leaderboard-submission-v1`;
- use `eligibility_policy_version: leaderboard-eligibility-v1`;
- target the private-holdout split;
- include repeated source summaries;
- use a runner-emitted fingerprint, not a reconstructed historical one;
- include vulnerable tasks and secure controls;
- pass false-positive and evidence gates;
- include protected execution evidence showing private paths were denied for
  private-holdout runs.

Public-split runs can be useful diagnostic evidence, but they are not
leaderboard eligible under the current policy.

## Repeated-Run Provenance

Repeated rows should use `repeat_evidence.aggregation: primary_run`. Published
metrics come from the named primary run, while `source_run_ids` and
`source_run_summaries` preserve the repeated-run context. `run_count` must match
the number of unique source run IDs.

Before accepting a repeated row, check:

- every source summary has the same task split, score policy, evidence contract,
  benchmark fingerprint, agent, model, and harness type expected for comparison;
- the primary run ID appears in `source_run_ids`;
- `variance_or_ci` matches the configured `variance_metric`;
- stale 44-task, frozen v0.0 46-task, or legacy 15-task artifacts are not mixed
  with current v1 evidence.

## Exclusions

Do not include credentials, local absolute paths, raw captures, raw private
holdout bodies, private routes, private seeds, or raw review logs in public run
bundles. Public packets should contain summaries and validator-checkable
metadata, not private execution internals.

## Maintainer Review Flow

1. Validate the run bundle schema and source summaries.
2. Check benchmark fingerprint and comparability key.
3. Confirm split, task count, harness type, model label, and commit SHA.
4. Confirm repeated-run provenance and primary-run selection.
5. Check false-positive, exploit-proof, boundary-reasoning, invalid-submission,
   and target-request coverage metrics.
6. Confirm private-path protections for any private-holdout candidate.
7. Record the decision as non-eligible evidence, needs rerun, parked, or
   eligible candidate.

Any change to task count, task bodies, score policy, evidence contract, or
fingerprint should mark older baselines stale for current comparison until they
are rerun.
