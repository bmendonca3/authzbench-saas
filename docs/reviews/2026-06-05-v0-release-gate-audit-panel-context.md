# v0 Release Gate Audit Panel Context

Date: 2026-06-05

Section under review: privacy, packaging, and final release readiness, focused
on the new machine-readable v0 release-gate audit.

## Objective

AuthZBench-SaaS should not rely on prose alone to decide whether it is ready for
the real `v0` label. This slice adds a strict release-gate validator that returns
success only when the benchmark is actually v0-ready, plus an explicit
`--allow-incomplete` mode for alpha/pre-v0 public validation.

## Files Changed

- `scripts/validate_v0_release.py`
- `docs/reviews/review-registry.json`
- `tests/test_v0_release_validator.py`
- `scripts/validate_public.py`
- `tests/test_validate_public.py`
- `README.md`
- `ROADMAP.md`
- `docs/status.md`
- `docs/v0-release-plan.md`
- `docs/publish-checklist.md`
- `CHANGELOG.md`

## Current Behavior

- Strict command:

```bash
python3 scripts/validate_v0_release.py
```

returns non-zero while `v0_ready: false`.

- Alpha/pre-v0 audit command:

```bash
python3 scripts/validate_v0_release.py --allow-incomplete
```

returns success while still printing the same `v0_ready: false` result.

- `scripts/validate_public.py` runs the audit command in
  `--allow-incomplete` mode so public alpha validation continuously checks the
  readiness auditor without pretending the benchmark is v0.

## Gates Checked

- public split scope
- private holdout pack
- task/control mix
- baseline credibility
- leaderboard submissions
- sectional reviews
- documentation and packaging

The current local audit reports `v0_ready: false` with these major gaps:

- private holdout pack is not leaderboard-suitable; local rehearsal manifests do
  not count as real private leaderboard tasks
- total secure controls are below the v0 target when unsuitable holdouts are
  excluded
- baseline registry still reports `v0_baseline_ready: false`
- no tracked leaderboard submission is eligible
- only one required review section is currently marked `v0_ready`

## Verification Already Run

```bash
python3 -Wd -m unittest discover -s tests -p 'test_v0_release_validator.py'
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 scripts/validate_v0_release.py --allow-incomplete
python3 scripts/validate_v0_release.py
git diff --check
```

The first three checks passed, strict mode intentionally failed with
`v0_ready: false`, and `git diff --check` passed.

## Known Limits

- This audit does not run fresh-clone validation by itself. The public validation
  script and publish checklist still cover fresh-clone validation separately.
- This audit depends on the review registry for section status instead of trying
  to infer readiness from filenames.
- The current result is intentionally not v0-ready.
