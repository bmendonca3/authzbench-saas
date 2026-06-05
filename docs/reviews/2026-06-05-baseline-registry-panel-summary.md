# Baseline Registry Panel Summary

Date: 2026-06-05

Section: baseline methodology and leaderboard schema.

## Verdict

Approved for this alpha/pre-v0 checkpoint after fixes.

The panel found that the baseline registry improves benchmark credibility by
making stale runs, deterministic harness checks, current public-split model
runs, repeated-run evidence, and leaderboard eligibility machine-checkable. The
section does not claim v0 readiness; the validator still reports
`v0_baseline_ready: false`.

## Reviewers Counted

- ChatGPT independent subagent auditor: usable findings returned.
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

- Repeated-run/leaderboard eligibility cannot rely on a self-declared
  `run_count`. The validator now requires a `run_artifacts` list for repeated
  or leaderboard baselines.
- Repeated-run artifacts must point to unique files and include distinct
  `run_id` values.
- `current_public_harness_check` is restricted to `harness_check` entries.
- Harness checks cannot use `current_public_split`; they must use
  `current_public_harness_check`.
- Legacy snapshots no longer have to be smaller than the current task count;
  staleness can also come from scorer, harness, task, or methodology changes.
  They still must set `requires_rerun_before_v0: true`.
- Baseline docs now describe the Kiro files as legacy 15-task alpha snapshots,
  not current full-split baselines.
- Launch docs now describe the model summaries as initial legacy 15-task
  public-alpha snapshots.

## Must Fix Before Commit

None remaining after the fixes above.

## Should Fix Before v0

- Rerun legacy model snapshots on the current 44-task public split.
- Add at least five real model or agent families.
- Add at least two runs per serious model or agent family, backed by distinct
  `run_artifacts` and `run_id` values.
- Add at least one tool-agent baseline.
- Rerun full validation after the commit so scripted validation uses the new
  commit SHA.
- Complete the remaining holdout, anti-gaming, private-execution, and final
  release-readiness reviews before any real `v0` tag.

## Verification After Fixes

```bash
python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 scripts/validate_baseline_registry.py
git diff --check
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- baseline registry tests: 6 passed
- public validation integration tests: 4 passed
- registry validator: passed with `v0_baseline_ready: false`
- diff check: passed
- full public validation: 61 tests passed, manifest validation passed, baseline
  registry validation passed, compile checks passed, Docker Compose config
  passed, privacy scan passed, scripted baseline passed 44/44
