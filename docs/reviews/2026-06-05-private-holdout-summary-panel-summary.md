# Private Holdout Summary Panel Summary

Date: 2026-06-05

Section: holdout, contamination, anti-gaming, and release evidence.

## Verdict

Approved for this alpha/pre-v0 checkpoint after fixes.

The checkpoint improves benchmark proof by adding a public-safe summary utility
for ignored private holdout packs and by validating a local 24-task private pack
without publishing task bodies. The repo still correctly reports `v0_ready:
false` because real model baselines, a tool-agent baseline, leaderboard
submissions, final release evidence, and remaining v0-ready reviews are still
missing.

## Reviewers Counted

- Gemini 3.5 Flash (High): usable grounded findings returned; model label
  verified in runner log.
- Gemini 3.1 Pro (High): usable grounded findings returned; model label
  verified in runner log.
- panel reviewer: performed integration, privacy, and disposition
  review in this main thread.

## Reviewers Not Counted For Content

- Claude Sonnet 4.6 (Thinking): model label verified, but output file was empty.
- Claude Opus 4.6 (Thinking): model label verified, but output file was empty.

Raw Antigravity outputs and logs are intentionally kept under ignored
`docs/reviews/panel-logs/` and are not part of the public repo.

## Accepted Findings And Fixes

- Added `scripts/summarize_holdout_pack.py`, which emits only count-level
  private-holdout evidence and explicitly omits private task IDs, seeds, routes,
  oracle bodies, local paths, and raw diagnostics.
- Added `tests/test_holdout_summary.py` coverage for passing summaries,
  Git-tracked holdout failure, invalid-pack redaction, unavailable Git checks,
  and CLI `--output` writing.
- Hardened `authzbench/validate_manifests.py` so malformed JSON manifests are
  reported as validation errors instead of raw stack traces.
- Made the redacted summary's Git-tracking check availability explicit, so
  non-Git environments fail conservatively and visibly.
- Updated `tests/test_v0_release_validator.py` to support both clean public
  clones with no private pack and maintainer checkouts with an ignored valid
  private pack.
- Fixed README/status validation wording so lightweight validation no longer
  claims to run Docker Compose config; Compose config belongs to
  `--include-container-smoke`.

## Local Private Evidence

An ignored local private holdout pack was validated but not committed:

- manifest count: 24
- vulnerable tasks: 12
- controls: 12
- denial controls: 6
- authorized-allow controls: 6
- apps covered: 6
- route variants: 24
- decoy variants: 24
- `leaderboard_suitable`: true
- `rehearsal_manifest_count`: 0
- `public_structure_overlap_count`: 0
- Git-tracked holdout manifests: 0
- private maintainer replay check: 24/24 passed

With that ignored private pack present, the strict v0 audit now passes the
`private_holdout_pack` and `task_mix` gates locally. It still reports
`v0_ready: false`.

## Deferred

- Do not mark release evidence true yet; final release evidence still needs
  repeated current model baselines, a tool-agent baseline, leaderboard
  submissions, fresh-clone validation for a release commit, remote CI, and final
  privacy/release checks.
- Do not publish the private task manifests or raw private validation
  diagnostics.

## Verification After Fixes

```bash
python3 -Wd -m unittest discover -s tests -p 'test_holdout_summary.py'
python3 -Wd -m unittest discover -s tests -p 'test_validate_manifests.py'
python3 -Wd -m unittest discover -s tests -p 'test_v0_release_validator.py'
python3 scripts/validate_holdout_pack.py
python3 scripts/summarize_holdout_pack.py
python3 scripts/validate_v0_release.py --allow-incomplete
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- holdout summary tests: 5 passed
- manifest validation tests: 5 passed
- v0 release validator tests: 4 passed
- local private holdout validator: passed with `leaderboard_suitable: true`
- redacted private holdout summary: passed
- strict v0 audit in allow-incomplete mode: `private_holdout_pack` and
  `task_mix` passed, `v0_ready: false`
- public validation: 91 tests passed and scripted baseline passed 44/44
