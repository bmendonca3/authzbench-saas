# Live Baseline Refresh Panel Summary

Date: 2026-06-05

Section: scorer, runner, request-log correlation, and live-target proof.

## Verdict

Approved for this alpha/pre-v0 checkpoint after one validator-hardening fix.

The refreshed live HTTP scripted baseline is correctly represented as a current
44-task public harness check, not as an AI model baseline and not as leaderboard
evidence. The docs consistently keep the repo in alpha/pre-v0 status and state
that strict v0 readiness remains false.

## Reviewers Counted

- Gemini 3.5 Flash (High): usable grounded findings returned; model label
  verified in runner log.
- Gemini 3.1 Pro (High): usable grounded findings returned; model label
  verified in runner log.
- panel reviewer: performed the integration and disposition review in
  this main thread.

## Reviewers Not Counted For Content

- Claude Sonnet 4.6 (Thinking): model label verified, but output file was empty.
- Claude Opus 4.6 (Thinking): model label verified, but output file was empty.
- read-only reviewer: unavailable because the local reviewer thread pool was
  already occupied by prior shutdown reviewers.

Raw Antigravity outputs and logs are intentionally kept under ignored
`docs/reviews/panel-logs/` and are not part of the public repo.

## Accepted Findings And Fixes

- The live scripted baseline is now registered as `live-scripted-public-44` with
  `kind: "harness_check"`, `release_suitability:
  "current_public_harness_check"`, and `leaderboard_eligible: false`.
- The tracked summary reports 44 tasks passed, 18 vulnerable tasks, 26 secure
  controls, 10 authorized-allow controls, and 18/44 target-side request
  correlation.
- Docs now explicitly say the deterministic live scripted agent exercises
  submitted vulnerable findings, while secure controls are evaluated without
  live agent-side requests. This prevents overclaiming the 18/44 target-log
  coverage.
- `scripts/validate_public.py` no longer requires `docker compose config` for
  lightweight public validation. Compose config is still checked when
  `--include-container-smoke` is requested.
- `tests/test_validate_public.py` now covers that lightweight validation does
  not run Compose checks, while container smoke still validates Compose before
  startup.

## Findings Rejected Or Deferred

- The panel noted that `benchmark_commit_sha` records the commit evaluated by
  the live baseline run, not the future commit that will add this review and doc
  metadata. That is acceptable for an alpha harness-check artifact. A v0 release
  candidate must rerun baselines against the release commit or tag.
- The panel suggested validating target-request correlation in the baseline
  registry validator. Deferred for a later baseline-hardening slice because the
  current registry already treats this run as non-leaderboard harness evidence,
  and the tracked summary contains the correlation metrics.

## Must Fix Before Commit

None remaining after the validator-hardening fix.

## Should Fix Before v0

- Replace deterministic harness checks with repeated real model or agent
  baselines across at least five model or agent families.
- Add at least one real tool-agent baseline.
- Add private holdout tasks outside public Git history.
- Require leaderboard submissions to include artifact-backed live evidence and
  target-log correlation appropriate to their claimed harness type.
- Rerun the strict release gate and baseline registry after the final v0
  baseline artifacts exist.

## Verification After Fixes

```bash
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'
python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke
```

Results:

- public validator tests: 7 passed
- baseline registry tests: 6 passed
- full public validation: 86 tests passed, manifest validation passed, baseline
  registry validation passed with `v0_baseline_ready: false`, release gate
  passed in allow-incomplete mode with `v0_ready: false`, leaderboard example
  validation passed, compile checks passed, scripted baseline passed 44/44, and
  Docker container smoke passed
