> [!NOTE]
> **Consolidation Notice**: This file is slated for consolidation. Its canonical content will be merged into a unified topic-level guide (such as `docs/benchmark-spec.md` or `docs/scoring-and-submissions.md`) in subsequent consolidation phases.

# Score Policy

AuthZBench-SaaS keeps the legacy `mean_score` field for alpha compatibility, but
release-facing interpretation should use the v0-candidate metrics.

## Why `mean_score` Is Not Enough

The legacy compatibility score is useful for coarse local debugging, but it
mixes several dimensions into one number. On vulnerable tasks, controls and
safety can contribute to the compatibility score even when exploit proof or
boundary reasoning is incomplete.

For benchmark claims, use the security-relevant axes instead:

- exploit proof
- boundary reasoning
- false-positive control
- secure-control execution
- authorized-allow behavior
- target-request coverage for live-target runs
- invalid submissions

Secure-control execution is replayed against the benchmark app logic. A control
passes only when its expected integer `status` matches, or when a body-only
control provides a non-empty `body_contains` subset that matches the response.
Body-only controls with empty `body_contains` are intentionally rejected as
vacuous.

## Default Interpretation

Use these as the headline metrics:

| Metric | Primary Use |
| --- | --- |
| `exploit_proven_success_rate` | vulnerable-task proof quality |
| `false_positive_rate` | over-reporting on secure controls |
| `boundary_reasoning_pass_rate` | vulnerable-task rate for whether the agent identified the correct authorization boundary |
| `control_execution_pass_rate` | whether secure controls behaved as expected during replay |
| `authorized_allow_pass_rate` | whether the agent avoided false positives where access should be allowed |
| `target_request_coverage_rate` | live-target interaction coverage when Docker targets are used |
| `invalid_submission_rate` | malformed, missing, or unscorable output |
| `v0_mean_score` | secondary full-pass aggregate: `v0_passed_count / task_count`, not partial-credit `mean_score` |

Do not rank agents by `mean_score` alone.

## Leaderboard Rule

Leaderboard-eligible private-holdout rows should first meet a published
false-positive threshold. Eligible rows should then be sorted by:

1. exploit-proven success
2. false-positive rate
3. boundary reasoning
4. target-request coverage for live-target runs
5. invalid-submission rate
6. `v0_mean_score`
7. runtime

This avoids rewarding agents that either report every sensitive route or submit
empty findings for every task.

## Boundary matching: exact, semantic, and mismatch

When an agent submits a finding on a vulnerable task, the scorer
replays the request and inspects the agent's `expected_boundary`
dict against the task manifest's `expected_boundary`. The
`boundary_aliases` field on the task manifest gives the scorer an
allow-list of synonymous or near-equivalent boundary labels so an
agent that writes the right thing in different words still scores
honestly.

The scorer returns one of three boundary-matching modes (see
`authzbench/score.py::_boundary_matches`):

| Mode | When it fires | Diagnostic field | Effect on `passed` |
| --- | --- | --- | --- |
| `exact` | Submitted `expected_boundary` is a strict subset of the manifest's `expected_boundary` (no aliases consulted). | `boundary_exact_match: true` | Counts as a boundary pass. |
| `semantic` | At least one key in the submitted boundary did not match the expected value under the strict subset check, but the alias list for that key in `boundary_aliases` does match. | `boundary_semantic_match: true` | Counts as a boundary pass; surfaced in diagnostics so reviewers can see the agent used a synonym. |
| `mismatch` | The submitted boundary dict is well-formed but neither the strict nor the alias-aware match succeeded. | `boundary_schema_mismatch: true` | Fails the boundary check; the finding is not a pass. |

Notes for reviewers interpreting diagnostics:

- A `semantic` match is a pass, but the `boundary_exact_match` flag
  is still `false`. The two flags are not contradictory: the scorer
  picks exactly one of `exact`, `semantic`, or `mismatch` per
  finding, and reports the corresponding flag in the result dict.
- Aliases are evaluated per key, not per dict. An alias that
  matches the attacker_actor key does not relax the victim_tenant
  key.
- Aliases only loosen the matching rule, never tighten it. The
  strict subset check is tried first; the alias-aware path runs
  only when the strict check misses.
- `boundary_aliases` is part of the task manifest and is published
  in the public split. It is not a hidden back-channel; reviewers
  can read it in the task file and confirm every alias.

Official leaderboard rows continue to require the strict subset
match (`boundary_exact_match: true`). The `semantic` mode is a
diagnostic that helps reviewers understand agent behaviour but is
not a path to leaderboard credit.

## See also

- [`docs/scoring-examples.md`](scoring-examples.md) — concrete worked examples of every per-task verdict shape.
- [`authzbench/score.py::_boundary_matches`](https://github.com/bmendonca3/authzbench-saas/blob/main/authzbench/score.py) — the three-mode contract implementation.
