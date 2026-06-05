# Protected Private Execution Panel Summary

Section: holdout, contamination, anti-gaming, and release evidence.

Disposition: accepted for the alpha/pre-v0 protected private-execution
checkpoint.

The panel accepted `scripts/protected_private_eval.py` and
`docs/protected-private-execution-2026-06-05.redacted.json` as honest evidence
that maintainers can run private holdouts without handing readable private
manifests to the agent workspace. The tracked artifact is aggregate-only and
does not publish private task IDs, seeds, routes, refs, oracle bodies, prompt
text, transcripts, raw model output, local result paths, or private filesystem
details.

This does not make the whole benchmark v0-ready.

## Verified Reviewers

- Gemini 3.5 Flash (High): accepted with one required test update. Verified
  propagated label in panel log.
- Gemini 3.1 Pro (High): accepted and recommended keeping the
  holdout/anti-gaming section blocked. Verified propagated label in panel log.
- Claude Sonnet 4.6 (Thinking): label verified, but the run produced an empty
  review output, so it is not counted for substantive findings.
- Claude Opus 4.6 (Thinking): label verified, but the run produced an empty
  review output, so it is not counted for substantive findings.
- ChatGPT reviewer: parent-review fallback.

Raw panel logs are intentionally untracked under `docs/reviews/panel-logs/`.

## Accepted Evidence

- Protected evaluator:
  - `scripts/protected_private_eval.py`
- Focused tests:
  - `tests/test_protected_private_eval.py`
- Redacted execution artifact:
  - `docs/protected-private-execution-2026-06-05.redacted.json`
- Release evidence:
  - `docs/release-evidence.json`

Current redacted execution evidence:

- 24 private-holdout tasks
- 12 vulnerable tasks
- 12 controls
- 6 denial controls
- 6 authorized-allow controls
- 12 v0-passed controls
- zero exploit-proven vulnerable tasks
- zero false-positive controls
- zero invalid submissions
- agent workspace: temporary empty workspace
- agent input: rendered context only
- tracked private manifests: 0
- tracked raw private artifacts: false

## Findings And Disposition

1. High: the protected execution evidence satisfies the release-evidence field
   for alpha/pre-v0.
   Disposition: accepted. The evaluator loads private manifests only in the
   maintainer process, renders task contexts, runs the agent from a temporary
   empty workspace, and keeps raw result bundles ignored.

2. High: the redacted artifact preserves the private holdout boundary.
   Disposition: accepted. It contains aggregate metrics and protection metadata
   only. It does not include task rows or raw model artifacts.

3. High: release-validator tests needed updating after the release-evidence
   field became true.
   Disposition: fixed in `tests/test_v0_release_validator.py`.

4. Medium: this is not a private live/tool-agent leaderboard run.
   Disposition: documented. `target_request_coverage_rate` remains null and the
   harness is `no-tools-model`.

5. Medium: the holdout/anti-gaming section should remain blocked.
   Disposition: accepted. The section still needs private live/tool-agent
   evidence with target-request correlation, multi-seed coverage, and final
   anti-gaming review before it can be marked v0-ready.

## Section Readiness

The release-evidence field `protected_private_holdout_execution_available` can
be true for this alpha/pre-v0 checkpoint.

The `holdout_contamination_anti_gaming` section remains not v0-ready.

## Residual v0 Blockers

- Not all required review sections are marked v0-ready.
- Private live/tool-agent holdout execution with target-request correlation is
  not complete.
- Multi-seed private holdout scoring is not complete.
- Final anti-gaming and final release-readiness reviews are still required.
