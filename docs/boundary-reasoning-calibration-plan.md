# Boundary-Reasoning Calibration Plan

Status: completed by `docs/boundary-reasoning-calibration-study.md`.

This plan and the completed study are a historical/public-safe calibration artifact based on 49-task live HTTP runs, not current 63-task public model/tool-agent capability evidence and not a blocker to the v1.0-internal label.

The historical public evidence shows a sharp gap between exploit proof and
boundary reasoning. The then-current 49-task live HTTP tool-agent repeated runs
prove 15 of 20 vulnerable public tasks but still record `0.0000`
`boundary_reasoning_pass_rate` and zero vulnerable full passes. The completed
study uses a full census of those exploit-proven vulnerable task-run cases.

## Study Question

When a run has `exploit_proof: 1` and `boundary_reasoning: 0`, what failed?

Possible categories:

- true boundary misunderstanding: the finding proves a route but names the wrong
  actor, tenant, role, object, or scope boundary;
- missing field: the finding omits a required boundary key even though the prose
  claim implies it;
- synonym or schema mismatch: the finding uses a reasonable alternate key or
  value that the scorer does not accept;
- insufficient task instruction: the task objective or output schema does not
  make the required boundary field obvious enough;
- scorer strictness: the oracle accepts only one representation where multiple
  public-safe representations would preserve the same claim.

## Public-Safe Sample

Use public tasks only. Start with tasks where the live HTTP tool-agent has
`exploit_proof: 1`, `boundary_reasoning: 0`, and `invalid_submission: false`.
Candidate examples can be selected from
`baselines/kiro-live-tool-agent-sonnet-current-public-49-run1-summary.json` and
`baselines/kiro-live-tool-agent-sonnet-current-public-49-run2-summary.json`.

For each sampled task, record:

| Field | Source |
| --- | --- |
| Task id | baseline summary `tasks[].task_id` |
| Expected boundary keys | public task `expected_boundary` |
| Submitted boundary keys | per-task `submission.json`, when available in the run bundle |
| Exploit proof status | baseline summary `tasks[].exploit_proof` |
| Boundary score | baseline summary `tasks[].boundary_reasoning` |
| Category | manual audit using the taxonomy above |
| Proposed action | none, task wording change, schema hint, scorer normalization, or doc note |

Do not use private holdout bodies, raw private run bundles, captures, or
reviewer logs in this public calibration file. This calibration is public-safe,
does not use private holdouts, raw private bundles, or reviewer logs, and is not hosted leaderboard operation, not platform acceptance, and not external validation.

## Audit Procedure

1. Select 8 to 12 public vulnerable tasks across at least four app families.
2. Require `exploit_proof: 1` and `invalid_submission: false` so the sample is
   about boundary reasoning rather than missing proof or malformed JSON.
3. Read the public task's `expected_boundary` keys and the submitted boundary
   object from the associated run bundle.
4. Classify each failure into exactly one primary category and optional
   secondary notes.
5. Count categories and list examples with public task IDs only.
6. Propose changes only after the sample is reviewed. Do not relax scoring based
   on one anecdote.

## Decision Rules

- If most failures are true boundary misunderstandings, keep scoring strict and
  emphasize the result in the paper.
- If most failures are missing fields with correct prose, consider clearer
  output-schema instructions but keep the v0.0 result boundary unchanged.
- If most failures are synonym or representation mismatches, add a scorer
  normalization proposal for v1 and rerun baselines before comparing scores.
- If task wording is ambiguous, patch public task wording only in a future
  benchmark version and mark old baselines stale.
- If scorer strictness changes, bump the score-policy or evidence-contract
  version before producing new current comparisons.

## Verification Commands

```bash
rg -n "expected_boundary" tasks
rg -n "boundary_reasoning" baselines/kiro-live-tool-agent-sonnet-current-public-49*.json
python3 scripts/validate_baseline_registry.py
```
