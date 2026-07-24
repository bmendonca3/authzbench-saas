# Run Bundle And Attestation Guidance

This guide describes what a public or maintainer run bundle should contain
before it is treated as comparable benchmark evidence. It does not create a
hosted leaderboard and does not replace the validator.

For v1/community operation, pair this bundle guidance with
`docs/v1-community-submission-governance.md`. This file defines the bundle;
the governance document defines states, eligibility, rotation, hosted or
containerized execution, appeals, and publication rules.

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

## Freeze The Complete Retained Directory

After the evaluator and any outer wrapper have finished writing files, create a
content manifest for the exact retained run directory. If a wrapper log is part
of the claimed evidence, place it inside that directory before this step. Files
kept elsewhere are outside the manifest's coverage.

```bash
RUN_ROOT="results/<result-family>/<run-id>"

python3 scripts/build_run_bundle_manifest.py "$RUN_ROOT" \
  --require summary.json \
  --require-glob '*/agent.json' \
  --require-glob '*/score.json' \
  --require-glob '*/submission.json' \
  --require-glob '*/transcript.json'

python3 scripts/validate_run_bundle_manifest.py "$RUN_ROOT"
```

The fixed `run-bundle-manifest.json` records every regular file in the run
directory except itself as a sorted relative path, byte size, and SHA-256. The
builder refuses to overwrite an existing manifest. Validation fails if a file
changes, disappears, appears later, or is replaced by a symlink or another
non-regular path. Build again only in a new clean run directory; do not edit or
replace a frozen manifest in place.

The exact-path and glob checks are evidence-presence guards, not task-count or
schema validators. A glob proves that at least one matching file exists. Keep
using the runner, submission, registry, and leaderboard validators for expected
cardinality, schema, scoring, comparability, and eligibility decisions.

The bundle digest is a deterministic local content-consistency checksum. It is
not a signature, timestamp, custody attestation, model-identity proof, platform
acceptance, or promotion approval. A party that can change both the files and
manifest can recompute it. Independent custody requires a separately authorized
signing, timestamping, or publication system.

The manifest contains no raw file bodies or absolute local paths, but relative
filenames can still expose task or private-pack identifiers. Keep private-run
manifests private unless their filenames and surrounding metadata have passed a
separate disclosure review.

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

1. Validate `run-bundle-manifest.json` against the complete retained directory.
2. Validate the run bundle schema and source summaries.
3. Check benchmark fingerprint and comparability key.
4. Confirm split, task count, harness type, model label, and commit SHA.
5. Confirm repeated-run provenance and primary-run selection.
6. Check false-positive, exploit-proof, boundary-reasoning, invalid-submission,
   and target-request coverage metrics.
   Treat `scored_submission_finding_total` as scorer-derived and
   `submitted_finding_total` as optional adapter telemetry; they are not
   interchangeable.
7. Confirm private-path protections for any private-holdout candidate.
8. Record the decision as non-eligible evidence, needs rerun, parked, or
   eligible candidate.

Any change to task count, task bodies, score policy, evidence contract, or
fingerprint should mark older baselines stale for current comparison until they
are rerun.
