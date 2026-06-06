# Benchmark Fingerprint Panel Summary

Date: 2026-06-06

Scope:

- `benchmark_fingerprint` in runner summaries
- current-public baseline registry enforcement
- public docs for result schema and baseline credibility
- backfilled fingerprint metadata on tracked current 46-task public summaries

Reviewers counted:

- Gemini 3.5 Flash High
- Gemini 3.1 Pro High
- ChatGPT parent/subagent review

Antigravity also verified Claude Sonnet 4.6 Thinking and Claude Opus 4.6
Thinking routing labels for this panel run, but those reviewers did not return
substantive final findings, so they are not counted in the decision summary.

## Panel Decision

The panel agreed that the fingerprint checkpoint improves benchmark credibility.
It gives each current-public summary a machine-readable comparability contract
for the task set, score policy, scorer contract, evidence contract, and task
mix counts.

The panel also agreed that the docs do not overclaim. A matching fingerprint is
framed as comparability evidence, not leaderboard eligibility, v0 readiness, or
private-holdout proof.

## Accepted Finding

Reviewers found one blocker in the first implementation: runner fingerprints
were sensitive to the caller's current working directory and platform path
separator. The same task set could hash differently if invoked from a subfolder
or on a platform that renders paths with backslashes.

Fix accepted:

- runner fingerprint paths are now anchored to the benchmark repository root
- runner fingerprint paths use POSIX-style separators
- the baseline registry validator uses the same canonical path style
- the bundled runner executes agent commands from the benchmark root
- regression coverage verifies that an absolute task path run from another CWD
  produces the same fingerprint as the repo-root run

## Privacy Posture

The public fingerprint object uses whole task-set hashes and counts rather than
raw task IDs. This is appropriate for public-safe summaries and private holdout
comparison because the summary can prove sameness without publishing private
manifest names.

Caveat: a task-set hash is a comparability commitment, not a cryptographic
secret. If someone already has a candidate manifest set, they can hash it and
compare. That is acceptable for this use case.

## Local Verification After Fix

Commands run:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_runner.py'
python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'
python3 scripts/validate_baseline_registry.py
python3 -m py_compile authzbench/core.py authzbench/run.py scripts/validate_baseline_registry.py
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_v0_release.py --allow-incomplete
git diff --check
```

Result:

- public validation passed
- baseline registry validation passed
- v0 release audit remains intentionally not ready because baseline credibility
  still needs three more repeated current model/agent families and one current
  public tool-agent baseline

## Claim Boundary

This checkpoint supports:

> current-public score/version comparability is now machine-checked for tracked
> current 46-task public summaries.

It does not support:

> v0 ready, v1 ready, leaderboard ready, or private leaderboard validated.
