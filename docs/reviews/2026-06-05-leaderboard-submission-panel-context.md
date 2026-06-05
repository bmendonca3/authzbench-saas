# Leaderboard Submission Panel Context

Date: 2026-06-05

Section: leaderboard submission schema and eligibility validation.

## Review Question

Does the new leaderboard submission validator make AuthZBench-SaaS more credible
without pretending the current alpha/pre-v0 public split is a real leaderboard?

## Changed Files

- `scripts/validate_leaderboard_submission.py`
- `examples/leaderboard/scripted-sanity-public.leaderboard.json`
- `tests/test_leaderboard_submission.py`
- `scripts/validate_public.py`
- `tests/test_validate_public.py`
- `README.md`
- `ROADMAP.md`
- `docs/leaderboard-schema.md`
- `docs/status.md`
- `docs/v0-release-plan.md`
- `docs/benchmark-card.md`
- `docs/launch-report.md`
- `docs/publish-checklist.md`
- `CHANGELOG.md`

## Parent-Verified Facts

- The validator requires the leaderboard columns documented in
  `docs/leaderboard-schema.md`.
- The tracked public example is a deterministic scripted harness check.
- The tracked public example validates as schema-valid evidence but reports
  `leaderboard_eligible: false`.
- A leaderboard-eligible submission must:
  - use `split: private-holdout` until private-only combined metrics exist
  - include at least 20 private-holdout tasks
  - avoid deterministic harness-check status
  - include at least two runs
  - include parseable variance or confidence evidence instead of placeholder
    text
  - pass false-positive and invalid-submission thresholds
  - meet target-request coverage when using a live/tool harness
- The validator rejects:
  - missing required fields
  - public-only submissions marked leaderboard eligible
  - combined submissions marked leaderboard eligible before private-only
    combined metrics exist
  - harness checks marked leaderboard eligible
  - one-off submissions marked leaderboard eligible
  - inconsistent public/private task counts
  - inconsistent vulnerable/control task counts
  - inconsistent v0 mean score, invalid-submission rate, and exploit-proven rate
  - live/tool submissions that claim eligibility without target-request coverage
- `scripts/validate_public.py` now runs the leaderboard submission validator
  against `examples/leaderboard/*.json`.

## Verification Run

Focused checks:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_leaderboard_submission.py'
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json'
python3 -m compileall -q scripts tests
```

Results:

- leaderboard submission tests: 12 passed
- public validation integration tests: 5 passed
- leaderboard submission validator: passed, 1 schema-valid submission,
  0 leaderboard-eligible submissions
- compile checks: passed

Full local gate:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- 74 tests passed
- manifest validation passed
- baseline registry validation passed with `v0_baseline_ready: false`
- leaderboard submission validation passed with 0 eligible examples
- compile checks passed
- Docker Compose config passed
- Git-tracked privacy scan passed
- deterministic scripted baseline passed 44/44

## Known Remaining v0 Gaps

- The validator proves submission shape and eligibility gates, not the existence
  of real private-holdout results.
- There is still no current private-holdout leaderboard submission.
- There is still no current public tool-agent baseline.
- There are still no repeated real model or agent baseline families on the
  current public split.
- Protected private-holdout execution and final release-readiness review are
  still required before any real `v0` or leaderboard claim.
