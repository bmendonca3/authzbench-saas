# Multi-Step Evidence Contract Panel Summary

Date: 2026-06-06

Scope: uncommitted scorer, validator, test, and documentation changes for
optional vulnerable-task `evidence_requirements`.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by Antigravity CLI log
- Gemini 3.1 Pro (High), verified by Antigravity CLI log
- ChatGPT reviewer, read-only local-code review

Claude Antigravity labels were verified by logs but did not return substantive
review text for this checkpoint. The Kiro Opus 4.8 reviewer was started but was
terminated after exceeding the useful review window, so it is not counted.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Consensus

Reviewers agreed that explicit multi-step evidence support is a useful enabling
increment for workflow-real SaaS authorization tasks. It does not add public
tasks, does not change the current 44-task public split, and should not affect
existing baseline claims.

The main credibility benefit is that future vulnerable tasks can require a
sequence of scorer-owned backend replays instead of accepting a single final
request as proof.

## Accepted Finding

The first implementation allowed weak `evidence_requirements` that checked only
response status or body. Gemini 3.5 Flash identified that this could let an
agent repeat the final exploit request and satisfy a loosely written setup step.

Disposition: accepted and fixed.

Changes made:

- evidence requirements now require an expected request shape
- indexes must be contiguous starting at 0
- scorer checks the submitted request shape for each required step
- malformed evidence fails without crashing the scorer
- tests cover full-credit multi-step proof, missing-step failure,
  duplicate-final-step failure, malformed evidence, and manifest validation

## Remaining Boundaries

This checkpoint is not a v1 milestone by itself. It adds enforcement machinery
for future workflow tasks. Real benchmark-quality improvement still requires
public or private tasks that use the contract, plus baseline reruns if public
task behavior or task count changes.

## Verification

Required verification for this checkpoint:

- targeted scorer and manifest tests
- public manifest validation
- strict v0 release gate
- full public validation
- privacy check proving raw panel logs, private holdouts, results, and captures
  are untracked
- remote CI after commit
