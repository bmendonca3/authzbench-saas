# Qwen Current 46-Task Baseline Panel Summary

Date: 2026-06-06

Scope: two Kiro `qwen3-coder-next` no-tools runs on the current 46-task public
split, the baseline registry update that counts them as one current repeated
model-family baseline, and the README/status/chart framing around that evidence.

## Reviewers Counted

- Gemini 3.5 Flash (High), verified by the panel runner run log.
- Gemini 3.1 Pro (High), verified by the panel runner run log.
- Kiro `claude-opus-4.8`, verified against the live Kiro model catalog.
- Kiro `claude-sonnet-4.6`, verified against the live Kiro model catalog.
- Kiro `deepseek-3.2`, verified against the live Kiro model catalog.
- panel reviewer.

the panel runner Claude Sonnet and Opus labels propagated, but returned no
substantive review output in the fast runner. Kiro `qwen3-coder-next` was
rate-limited in the balanced Kiro pass and was not counted.

## Consensus

The checkpoint improves benchmark credibility, but only by one narrow step:
AuthZBench-SaaS now has one repeated current public no-tools model-family
baseline on the 46-task split. It still does not have five current repeated
families, a current public tool-agent baseline, broad private-holdout leaderboard
coverage, or hosted leaderboard readiness.

Reviewers agreed that the Qwen evidence is honestly weak capability evidence:

- both runs passed 27 of 46 tasks
- run 1 proved 0 of 19 vulnerable tasks
- run 2 proved 1 of 19 vulnerable tasks
- both runs had `false_positive_rate: 0.0`
- both runs had `authorized_allow_pass_rate: 1.0`
- both runs had `boundary_reasoning_pass_rate: 0.0`

The useful signal is control restraint plus repeatability variance, not strong
exploit-finding performance.

## Accepted Findings

1. The registry framing is correct: the Qwen run pair counts as one current
   repeated public model-family baseline and keeps `v0_baseline_ready: false`.
2. Docs should make the `boundary_reasoning_pass_rate` denominator clearer.
   Accepted. `docs/baseline-credibility.md` and `docs/score-policy.md` now state
   that the headline rate is vulnerable-task scoped.
3. Docs should make the `v0_mean_score` vs. partial-credit `mean_score`
   distinction clearer. Accepted. `docs/score-policy.md` and `docs/status.md`
   now state that `v0_mean_score` is `v0_passed_count / task_count`.
4. Run 2's invalid vulnerable-task submission should be visible in narrative
   docs, not only raw JSON. Accepted. `docs/status.md` now calls this out.
5. Release-gate wording should avoid implying strict v0 readiness. Accepted.
   `docs/evidence-and-claims.md` now frames the strict gate as an
   `--allow-incomplete` reporting gate until all v0 blockers clear.

## Rejected Or Resolved Findings

- One reviewer suspected run 2's `v0_mean_score: 0.587` was stale because
  `mean_score` is `0.6033`. Parent verification found the field is correct:
  `authzbench/run.py` defines `v0_mean_score` as full-pass `v0_passed_count /
  task_count`, while `mean_score` keeps partial credit. Run 2 has 27 full passes
  on 46 tasks, so `0.587` is expected.
- A duplicate current-Qwen entry was reported in `baselines/README.md`, but the
  second Qwen entry is the stale 44-task run pair. No duplicate current entry was
  present.
- A stale private-holdout sentence was reported in `docs/launch-report.md`, but
  the checked text already states that protected private-holdout evidence is
  summarized in redacted public-safe form and that no hosted public leaderboard
  exists.

## Verification Used

- `python3 -Wd -m unittest discover -s tests -p 'test_*.py'`
- `python3 scripts/validate_baseline_registry.py`
- `python3 scripts/validate_v0_release.py --allow-incomplete`
- Parent inspection of `authzbench/run.py` for `v0_mean_score` semantics
- Parent inspection of both Qwen 46-task summary JSON files

The public validation chart-drift guard was not expected to pass before this
checkpoint was staged/committed because the generated chart assets changed. It
should be rerun after the chart assets are staged with the checkpoint.
