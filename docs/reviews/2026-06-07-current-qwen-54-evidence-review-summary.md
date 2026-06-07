# Current 54-Task Qwen Evidence Review Summary

Status: completed local independent-review loop for the current public Qwen
promotion. This is internal review evidence, not one of the three required
external v1 review lanes.

## Scope

The review covered:

- both current 54-task `qwen3-coder-next` no-tools summaries;
- the baseline registry row and current/stale semantics;
- adapter and runner failure behavior;
- numerical claims in the variance, credibility, status, launch, report, paper,
  evidence/claims, and goal documents;
- current public, stale public, private, leaderboard, and v1 claim boundaries.

## Reviewer Runs

1. Kiro `claude-opus-4.8`, read-only evidence audit:
   returned `NEEDS_FIXES`.
   It confirmed the headline metrics and fingerprint comparability, then flagged
   insufficient explanation of inner adapter failures, the invalid-submission
   source of run 1's `false_positive_rate`, the two timeout layers, and the
   vulnerable safety-rate dip.
2. Kiro `claude-opus-4.7`, read-only broad follow-up:
   read the scoped implementation and documentation but stopped emitting output
   and did not return a final verdict. The session was terminated and is not
   counted as review evidence.
3. Kiro `claude-opus-4.6`, read-only narrow replacement:
   returned `CLEAN` after directly checking `scripts/kiro_baseline_agent.py`,
   `authzbench/run.py`, both promoted summaries, the registry, variance
   analysis, status, and goal.

## Findings And Disposition

### Failure semantics

Disposition: accepted and fixed.

The adapter does not retry. An inner Kiro command failure or JSON-extraction
failure writes a valid `{"findings":[]}` fallback. That fallback remains in the
54-task scored denominator and can pass a secure control or fail a vulnerable
task. Outer runner failures instead produce invalid submissions.

Both summaries now record:

- task-level inner failure counts and task IDs;
- inner Kiro command versus missing-JSON breakdown;
- outer runner failure count;
- 60-second inner model-call timeout;
- 75-second outer per-task timeout;
- explicit fallback semantics.

### False-Positive And Safety Interpretation

Disposition: accepted and fixed.

Run 1's `false_positive_rate: 0.0303` is one failed secure control out of 33,
caused by an outer runner failure and invalid submission.
`control_false_report_rate` remains `0.0` because no finding was submitted on a
secure control. Its `vulnerable_safety_pass_rate: 0.9524` is likewise caused by
an invalid submission on one vulnerable task, not an unsafe or out-of-scope
action. The variance, credibility, and status documents now state this.

### Claim Boundary

Disposition: verified.

The two runs are current public-split diagnostic evidence for one no-tools
model family. They do not establish stable cross-model comparison, current
tool-agent coverage, private-holdout performance, leaderboard eligibility, or
v1 readiness. `docs/goal.md` remains active and incomplete.

## Final Verdict

The replacement Kiro Opus audit returned `CLEAN`. Parent-level validation,
generated-artifact checks, paper compilation, commit/push, and exact-head CI
remain separate completion gates for this promotion.
