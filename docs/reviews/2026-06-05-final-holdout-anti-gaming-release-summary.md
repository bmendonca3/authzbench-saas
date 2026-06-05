# Final Holdout Anti-Gaming Release Summary

Date: 2026-06-05

Section reviewed: holdout, contamination, and anti-gaming design.

## Review Question

Can the holdout and anti-gaming section be treated as v0-candidate ready
without leaking private task material or relying on public-manifest rehearsal
tasks?

## Evidence Reviewed

- `python3 scripts/validate_holdout_pack.py`
- `python3 scripts/summarize_holdout_pack.py --output /tmp/authzbench-holdout-summary-check.json`
- `python3 scripts/validate_protected_private_evidence.py --summary docs/protected-private-execution-2026-06-05.redacted.json --summary docs/protected-private-live-kiro-sonnet-2026-06-05.redacted.json`
- `python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary`
- `git ls-files tasks_private/holdout results captures docs/reviews/panel-logs`

The private holdout evidence used for this review is count-level only. This
summary intentionally does not include private task IDs, seeds, routes, oracle
bodies, raw transcripts, private result-bundle paths, or target-log paths.

## Findings

### Accepted As v0-Candidate Evidence

1. The private holdout pack is not a rehearsal pack. The validator reports
   `leaderboard_suitable: true`, `rehearsal_manifest_count: 0`, and
   `public_structure_overlap_count: 0`.

2. The private split meets the v0 count and mix bar: 24 private tasks across
   all 6 apps, with 12 vulnerable tasks, 12 controls, 6 denial controls, and
   6 authorized-allow controls.

3. The private split has seed and variant diversity appropriate for a first
   protected v0 candidate: 24 unique private task IDs, 24 unique private seeds,
   24 route variants, and 24 decoy variants, with no missing variant metadata.

4. Protected execution evidence exists without exposing holdout manifests to
   the agent workspace. The redacted protected summaries validate two private
   runs, including one live tool-agent run with 24/24 target-request
   correlation.

5. The release-candidate leaderboard row is private-holdout backed,
   source-summary checked, and leaderboard eligible without publishing private
   task rows, seeds, routes, refs, oracle bodies, or raw result bundles.

6. The ignored sensitive paths remain untracked. The Git tracking check for
   `tasks_private/holdout`, `results`, `captures`, and `docs/reviews/panel-logs`
   returned no tracked files.

### Accepted With Explicit v0 Scope

1. Full dynamic multi-pack holdout rotation is deferred. For this v0 candidate,
   anti-gaming depends on a protected static private pack with 24 unique seeds,
   route variants, and decoy variants, plus protected execution. Rotating
   multiple private packs should be a v1 hardening item, not a hidden v0
   blocker.

2. Fully containerized external participant execution is deferred. For this v0
   candidate, the protected execution posture is temporary empty agent
   workspaces, rendered-context-only input, untracked private manifests, and
   redacted aggregate public artifacts. A hosted or fully containerized
   leaderboard service should be a later hardening milestone.

### Rejected

No final findings were rejected.

## Decision

This section is v0-candidate ready. The benchmark should still avoid claiming
to be a mature hosted leaderboard or a v1-scale anti-gaming system, but the
current protected holdout design is strong enough for a defensible v0 release
candidate when paired with the final privacy and packaging review.

