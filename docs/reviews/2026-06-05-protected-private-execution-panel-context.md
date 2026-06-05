# Protected Private Execution Panel Context

Section: holdout, contamination, anti-gaming, and release evidence.

AuthZBench-SaaS remains alpha/pre-v0. This slice adds a protected
maintainer-run private evaluation path and a redacted execution artifact. It
must not be treated as a finished private live/tool-agent leaderboard launch.

## Change Under Review

- Added `scripts/protected_private_eval.py`.
- Added `tests/test_protected_private_eval.py`.
- Added `docs/protected-private-execution-2026-06-05.redacted.json`.
- Updated `docs/release-evidence.json` so
  `protected_private_holdout_execution_available` is true.
- Updated README, status, roadmap, and changelog wording.

## Execution Evidence

The protected evaluator loaded the ignored private holdout pack, rendered each
task context, and ran the Kiro Haiku no-tools adapter from a temporary empty
agent workspace. Raw submissions, model outputs, scores, and transcripts remain
ignored under `results/`.

The tracked redacted artifact contains only aggregate counts and metrics:

- 24 private-holdout tasks
- 12 vulnerable tasks
- 12 controls
- 6 denial controls
- 6 authorized-allow controls
- 12 v0-passed controls
- zero exploit-proven vulnerable tasks
- zero false-positive controls
- zero invalid submissions
- `agent_received`: `rendered-context-only`
- `private_manifests_readable_in_agent_workspace`: false
- `tracked_private_manifest_count`: 0
- `raw_private_artifacts_tracked`: false

## Privacy Boundary

Tracked artifacts must not include private task IDs, seeds, route paths, refs,
oracle bodies, prompt text, transcripts, raw Kiro output, local result paths, or
private filesystem details.

## Current Validation

```bash
python3 -Wd -m unittest discover -s tests -p 'test_protected_private_eval.py'
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_v0_release.py --allow-incomplete
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

Current strict audit result:

- release evidence fields: all true
- `v0_ready`: false
- remaining blocker: not all required sectional reviews are marked v0-ready

## Known Limitation

This is a protected maintainer-run no-tools evaluation. It is not a hosted
leaderboard service, not a malicious-agent sandbox, and not private live
tool-agent execution with target-request correlation.
