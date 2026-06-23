# Leaderboard Submission Panel Summary

Date: 2026-06-05

Section: leaderboard submission schema and eligibility validation.

## Verdict

Approved for this alpha/pre-v0 checkpoint after fixes.

The validator improves benchmark credibility by making leaderboard submissions
machine-checkable while keeping the current public scripted example explicitly
ineligible. The section does not claim v0 readiness or leaderboard readiness.

## Reviewers Counted

- internal read-only auditor: usable findings returned.
- Gemini 3.5 Flash (High): usable findings returned; model label verified in
  runner log.
- Gemini 3.1 Pro (High): usable findings returned; model label verified in
  runner log.

## Reviewers Not Counted For Content

- Claude Sonnet 4.6 (Thinking): model label verified, but output file was empty.
- Claude Opus 4.6 (Thinking): model label verified, but output file was empty.

Raw logs are intentionally kept under ignored `docs/reviews/panel-logs/` and
are not part of the public repo.

## Accepted Findings And Fixes

- Combined public/private rows can no longer be marked leaderboard eligible.
  They remain schema-valid evidence, but eligibility now requires
  `split: private-holdout` until private-only combined metrics exist.
- Leaderboard-eligible rows now require at least 20 private-holdout tasks.
- `baseline_kind` and `harness_type` must agree:
  - `harness_check`: `scripted` or `scripted-live-http`
  - `model_baseline`: `no-tools-model`
  - `tool_agent_baseline`: `tool-agent`
- Placeholder variance text no longer counts as repeat evidence. Eligible rows
  must use parseable `stddev=...`, `variance=...`, or `ci95=[low,high]`.

## Must Fix Before Commit

None remaining after the fixes above.

## Should Fix Before v0

- Cross-validate submitted leaderboard rows against raw result artifacts, not
  only summary-level JSON.
- Add private-only metrics if combined public/private rows should ever become
  leaderboard eligible.
- Add a secure private-holdout task-count reference that proves count
  expectations without exposing private manifests.
- Add real private-holdout leaderboard submissions only after protected
  execution exists.

## Verification After Fixes

```bash
python3 -Wd -m unittest discover -s tests -p 'test_leaderboard_submission.py'
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json'
git diff --check
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- leaderboard submission tests: 12 passed
- public validation integration tests: 5 passed
- leaderboard submission validator: passed with 1 schema-valid example and
  0 leaderboard-eligible examples
- diff check: passed
- full public validation: 74 tests passed, manifest validation passed, baseline
  registry validation passed with `v0_baseline_ready: false`, leaderboard
  submission validation passed, compile checks passed, Docker Compose config
  passed, privacy scan passed, scripted baseline passed 44/44
