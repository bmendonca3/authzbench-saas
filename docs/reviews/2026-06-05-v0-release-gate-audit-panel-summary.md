# v0 Release-Gate Audit Panel Summary

Date: 2026-06-05

Section: privacy scan, packaging, and final release readiness.

## Reviewers Counted

- Parent/ChatGPT implementation reviewer
- ChatGPT independent read-only auditor
- Gemini 3.5 Flash (High), verified from Antigravity panel log
- Gemini 3.1 Pro (High), verified from Antigravity panel log

Claude Sonnet 4.6 (Thinking) and Claude Opus 4.6 (Thinking) labels were
verified in Antigravity logs, but their outputs were empty for this run, so they
were not counted as content reviewers.

Raw Antigravity logs are intentionally ignored under `docs/reviews/panel-logs/`.

## Question Reviewed

Does the new v0 release-gate audit let the public alpha/pre-v0 repository report
its real readiness honestly, while keeping strict v0 mode failing until the
release evidence is genuinely complete?

## Accepted Findings

1. The first audit draft did not cover enough release-plan evidence gates.

   Disposition: fixed. Added `docs/release-evidence.json` and a
   `release_verification_evidence` gate covering local public validation, fresh
   clone validation, remote CI, Docker smoke, privacy scan, release-note
   separation, and protected private-holdout execution. These fields are all
   false for the current alpha/pre-v0 repo, so strict v0 mode still fails.

2. Local private holdout rehearsals could be mistaken for real v0 task mix if
   the validator counted every ignored holdout manifest.

   Disposition: fixed. The task-mix gate counts private holdouts only when the
   holdout validator reports `leaderboard_suitable: true`. The local rehearsal
   generator remains useful for workflow testing, but it cannot satisfy real v0
   readiness.

3. The audit did not enforce a minimum vulnerable-task floor.

   Disposition: fixed. Added a `min_vulnerable_tasks` gate so the final task mix
   must contain at least 25 vulnerable tasks in addition to the secure-control
   requirements.

4. Requiring eligible leaderboard rows from public examples would create a bad
   incentive to publish private-holdout details.

   Disposition: fixed. Public examples are validated as non-eligible evidence.
   Release-candidate leaderboard submissions are checked separately under
   `leaderboard_submissions/**/*.json` and must be eligible before strict v0 can
   pass.

5. The private-holdout Git tracking check could crash outside a Git checkout.

   Disposition: fixed. The check now records a validator error instead of
   raising an exception if `git ls-files` cannot run.

6. The review registry did not yet reference this exact release-gate audit.

   Disposition: fixed in this checkpoint by adding this summary to
   `docs/reviews/review-registry.json` under the final release-readiness
   section.

7. The leaderboard-submission audit used caller-relative globs, so running the
   validator outside the repo root could miss public examples and future
   release-candidate submissions.

   Disposition: fixed. The v0 release validator now resolves leaderboard
   example and release-candidate globs from the repository root, keeps example
   and candidate result lists separate, and includes a regression test that
   calls `validate_v0_release()` after changing out of the repo directory.

## Verification After Fixes

The parent reviewer ran:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_v0_release_validator.py'
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 scripts/validate_v0_release.py --allow-incomplete
python3 scripts/validate_v0_release.py
python3 scripts/validate_public.py --include-scripted-baseline
git diff --check
```

Results:

- focused v0 release validator tests passed
- public validation routing tests passed
- `--allow-incomplete` returned success while reporting `v0_ready: false`
- strict `python3 scripts/validate_v0_release.py` returned non-zero with
  `v0_ready: false`, as intended
- full public validation passed with 84 tests and the deterministic scripted
  baseline
- `git diff --check` passed

## Remaining Release Risks

- No real private holdout pack exists outside public Git history yet.
- No release-candidate eligible leaderboard submission exists under
  `leaderboard_submissions/`.
- The baseline registry still reports `v0_baseline_ready: false`.
- Protected private-holdout execution is not implemented.
- Final release evidence remains false until local validation, fresh-clone
  validation, remote CI, Docker smoke, privacy scan, release-note separation,
  and protected holdout execution are all satisfied for a real v0 candidate.
