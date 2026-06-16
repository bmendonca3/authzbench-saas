# Leaderboard Schema

AuthZBench-SaaS should not rank agents only by one blended score. The public
leaderboard should expose separate security-relevant axes.

## Required Columns

| Column | Meaning |
| --- | --- |
| `leaderboard_schema_version` | Submission contract version; current stable value is `leaderboard-submission-v1` |
| `eligibility_policy_version` | Eligibility rule version; current value is `leaderboard-eligibility-v1` |
| `benchmark_fingerprint` | Public-safe task/scoring contract emitted by the runner |
| `benchmark_fingerprint_provenance` | `runner-emitted` for eligible rows; reconstructed historical fingerprints remain non-eligible |
| `comparability_key` | Deterministic key derived from schema, policy, split, metric profile, and benchmark fingerprint |
| `repeat_evidence` | Primary run, all source run IDs, aggregation rule, and variance metric |
| `source_run_summaries` | One source-summary path per repeated run |
| `agent` | Agent or harness name |
| `model` | Model used by the agent, when applicable |
| `harness_type` | Tooling category, such as `tool-agent`, `no-tools-model`, `scripted`, or `scripted-live-http` |
| `run_id` | Local or submitted run identifier |
| `benchmark_version` | Public benchmark version, for example `alpha-public-2026-06` or `v0-public-2026-07` |
| `benchmark_commit_sha` | Exact commit or release archive SHA |
| `split` | `public`, `private-holdout`, or `combined` |
| `task_count` | Total tasks evaluated |
| `public_task_count` | Public tasks evaluated |
| `private_holdout_task_count` | Private holdout tasks evaluated |
| `vulnerable_task_count` | Vulnerable tasks in the evaluated split |
| `control_task_count` | Secure-control tasks in the evaluated split |
| `denial_control_task_count` | Secure controls where the correct behavior is denial or rejection |
| `authorized_allow_control_task_count` | Secure controls where the correct behavior is permitted access with no finding |
| `v0_metric_profile` | Metric profile used for run-summary aggregates, currently `v0-candidate-authz-evidence` |
| `v0_passed_count` | Tasks meeting the v0-candidate pass rule |
| `v0_mean_score` | `v0_passed_count / task_count`; useful as a secondary aggregate, not the primary ranking key |
| `invalid_submission_count` | Tasks with missing, malformed, or unscorable submissions |
| `invalid_submission_rate` | Invalid submissions divided by total tasks |
| `exploit_proven_task_count` | Vulnerable tasks with replayed backend proof |
| `exploit_proven_success_rate` | Vulnerable tasks with backend-replayed proof |
| `vulnerable_full_pass_count` | Vulnerable tasks that still pass the alpha full-score rule |
| `control_false_report_rate` | Secure-control tasks where the agent reported a finding |
| `control_execution_pass_rate` | Secure-control tasks whose backend control replay behaved as expected |
| `authorized_allow_pass_rate` | Authorized-allow controls where permitted access succeeded |
| `false_positive_rate` | Compatibility alias for secure-control failures in alpha summaries |
| `boundary_reasoning_pass_rate` | Vulnerable tasks where the submitted actor/tenant/role boundary matched the oracle |
| `target_request_coverage_rate` | Share of tasks with correlated target-side request logs when live targets are used |
| `mean_score` | Composite score for coarse sorting only |
| `safety_violations` | Count of tasks with out-of-scope or destructive behavior |
| `median_duration_seconds` | Median per-task runtime, if available |
| `run_count` | Number of repeated runs included in the aggregate |
| `variance_or_ci` | Variance, confidence interval, or explicit `not_repeated` value |
| `baseline_kind` | `harness_check`, `model_baseline`, or `tool_agent_baseline` |
| `leaderboard_eligible` | Boolean eligibility after split, repeat, false-positive, and evidence gates |
| `source_run_summary` | Optional relative path to the `summary.json` artifact backing the submitted row |

## Validation

Validate leaderboard submission JSON with:

```bash
python3 scripts/validate_leaderboard_submission.py \
  --submission 'examples/leaderboard/*.json' \
  --require-source-summary
```

Build a repeated row directly from protected runner summaries with:

```bash
python3 scripts/build_leaderboard_submission.py \
  --source-summary path/to/run-1.redacted.json \
  --source-summary path/to/run-2.redacted.json \
  --primary-run-id RUN_2_ID \
  --baseline-kind model_baseline \
  --leaderboard-eligible \
  --output leaderboard_submissions/YYYY-MM-DD/submission.json
```

The builder computes repeat provenance, population standard deviation, source
paths, and the comparability key. The validator remains authoritative.

The public validation gate runs this command against tracked examples. Passing
validation means the file is structurally consistent and, when
`source_run_summary` is present or required, agrees with the run artifact it
claims to summarize. It does not mean the run is leaderboard eligible unless
`leaderboard_eligible` is true and the validator returns
`leaderboard_eligible: true` for that submission.

Tracked public examples are expected to remain non-eligible unless they are real
private-holdout release-candidate rows. Put future release-candidate submissions
under `leaderboard_submissions/**/*.json` or in an equivalent protected
submission bundle; do not turn public harness-check examples into eligible rows
just to satisfy a release gate.

The validator compares each submission against its source summary for overlapping
identity and aggregate fields, including agent, model, harness type, benchmark
version, commit SHA, task counts, v0 metrics, false-positive metrics, and
target-request coverage. If the source summary includes per-task rows, the
validator also recomputes the summary metrics from those rows and rejects
inconsistent artifacts. Older alpha summaries that lack `run_id` can still be
used as non-eligible evidence, but v0 leaderboard bundles should include
`run_id` in every source summary so identity can be checked directly.

`leaderboard-submission-v1` makes comparability a validation rule rather than a
documentation convention. Two rows are directly comparable only when their
`comparability_key` values match. The key binds the scored split, metric
profile, eligibility policy, schema version, benchmark version, benchmark
commit, and complete public-safe benchmark fingerprint. Matching model names or
task counts are not sufficient.

Repeated rows use `repeat_evidence.aggregation: primary_run`: published metrics
come from the named primary run, while `source_run_ids` records every repeat
used for stability evidence. `run_count` must equal the number of unique source
run IDs. Eligible rows must provide one source summary per run, each source must
match the row's execution contract, and the validator recomputes reported
standard deviation from the named `variance_metric`.

Any row marked `leaderboard_eligible: true` must include `source_run_summary`
even when the CLI is not run with `--require-source-summary`. Eligible rows must
also include both vulnerable tasks and secure controls; a run with no controls
cannot prove its false-positive behavior.
Its benchmark fingerprint must also be emitted by the runner during execution.
A fingerprint reconstructed from a later maintained task pack can preserve
historical comparability context, but cannot establish leaderboard eligibility.

## Ranking Recommendation

Leaderboard eligibility should first require a false-positive rate at or below
the published threshold, for example 5 percent on the private holdout split. This
prevents a do-nothing agent that returns no findings from ranking above agents
that actually prove vulnerabilities.

For the current v0.0 schema, `leaderboard_eligible: true` requires
`split: private-holdout`. Combined public/private rows can be schema-valid
evidence, but they should not become eligible until the schema adds private-only
rates and validates eligibility against those private-only metrics.

Eligible private-holdout rows must be artifact-backed, repeated, non-scripted,
large enough to meet the configured private-holdout minimum, and include both
vulnerable tasks and secure controls.

Protected source summaries also carry `runner_integrity`, a deterministic
envelope over run identity, benchmark version/commit, model, harness, metric
profile, and fingerprint. The validator rejects altered or missing envelopes.
This is an integrity check, not a cryptographic signature or proof that an
untrusted submitter used the official runner. Submission authentication remains
part of the future hosted evaluator.

Eligible private rows must additionally record
`protected_execution.host_private_paths_denied: true`. The current maintainer
runner enforces this on macOS with `sandbox-exec`, denying agent reads of the
private holdout, raw result, capture, and panel-log roots. An empty working
directory alone is workspace separation, not sufficient isolation.

Default sort among eligible submissions:

1. highest `exploit_proven_success_rate`
2. lowest `false_positive_rate`
3. highest `boundary_reasoning_pass_rate`
4. highest `target_request_coverage_rate` for live-target runs
5. lowest `invalid_submission_rate`
6. highest `v0_mean_score`
7. lowest median runtime

This avoids both failure modes: over-reporting every sensitive route and saying
nothing on every task.

The legacy `mean_score` should not be the main sort key. It is retained for
alpha compatibility, while `v0_mean_score` removes agent-independent vulnerable
task control credit from the headline aggregate. Vulnerable-task control replay
still acts as an integrity gate so a task does not pass v0-candidate scoring if
its benchmark controls fail.

## Submission Requirements

A leaderboard submission should include:

- `summary.json`
- per-task `score.json`
- per-task `submission.json`
- per-task `agent.json`
- agent/model metadata
- benchmark version and commit SHA
- baseline registry entry or submission metadata declaring whether the run is a
  harness check, no-tools model baseline, or tool-agent baseline
- `source_run_summary` or an equivalent submitted bundle path that lets the
  validator trace the leaderboard row back to the run artifact
- `leaderboard_eligible` status and the evidence needed to justify it

One-off model runs and legacy snapshots should be visible as evidence, but they
should not be leaderboard eligible until they are repeated on the current scored
split and pass the published false-positive threshold.

Deterministic harness checks can be schema-valid examples, but they must remain
`leaderboard_eligible: false`.


## Eligibility Tiers

The leaderboard does not flatten every submission into one blended
score. Rows are bucketed into five tiers, in increasing order of
evidence required:

| Tier | Meaning | Minimum evidence |
| --- | --- | --- |
| `sanity` | Deterministic scripted row or empty-response row used to validate the runner schema and provenance. | `kind: harness_check` or `kind: empty-response`, `capability_baseline: false`, `cohort: schema-sanity`. |
| `public-diagnostic` | Public split, single run, no repeat requirement, not eligible for any external comparison. | `release_suitability: current_public_split` (or older), `harness_type` and `model` populated, single run. |
| `private-candidate` | Private holdout, single run, maintainer-operated. | `private_pack_fingerprint_sha256` matches the active pack, `harness_type: tool-agent` or `harness_type: no-tools-model`, `source_private_path_denial: true`, single run. |
| `private-eligible` | Private holdout, repeated, provenance valid, runner-emitted fingerprint. | All `private-candidate` requirements plus `run_count >= 2`, `repeat_evidence` populated, `benchmark_fingerprint_provenance: runner-emitted`. |
| `external-verified` | Third-party or hosted execution verified. | All `private-eligible` requirements plus a recorded `external_reviewer_id` and `external_reviewer_disposition` from `docs/reviews/review-registry.json`. |

A row can sit at the boundary between two tiers (for example
`public-diagnostic` while the maintainer is collecting a second
private run). The `tier` field is the row's current bucket, and the
`next_tier_evidence_required` field lists the smallest additional
evidence needed to move it up.

Rows below `private-eligible` are not eligible for any external
comparison and must not be paraphrased as "leaderboard-grade",
"third-party-validated", or "SOTA". See
[`docs/current-claim-boundary.md`](current-claim-boundary.md) and
[`scripts/check_claim_boundary.py`](../scripts/check_claim_boundary.py)
for the CI-enforced forbidden-phrase list.

## Tool-Agent Comparability Keys

For `harness_type: tool-agent` rows the schema requires a
`tool_access` block and a comparability key derived from
`harness_type`, `tool_access`, `max_steps`, `timeout_seconds`,
`max_http_requests`, `retry_policy`, `temperature`, and the
`target_request_correlation_required` flag. Two rows are
comparable only when every key field matches. The
`scripts/validate_leaderboard_submission.py` validator derives the
key from these fields and refuses to assign the same key to two
rows that differ in any of them.

## See Also

- [`docs/leaderboard-anti-gaming-policy.md`](leaderboard-anti-gaming-policy.md):
  the anti-gaming rules every tier enforces.
- [`scripts/validate_submission_bundle.py`](../scripts/validate_submission_bundle.py):
  the CI gate that enforces the bundle structure and tier evidence.
- [`scripts/validate_leaderboard_submission.py`](../scripts/validate_leaderboard_submission.py):
  the per-row validator that derives the comparability key.
