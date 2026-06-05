# Final Task-Mix Panel Summary

Section: task realism, vulnerable/control mix, and app coverage.

Disposition: accepted for the task-mix section only.

The panel accepted that the `task_realism_vulnerability_control_mix` review
section can be marked v0-ready. This does not make the full benchmark v0-ready,
does not make the public repo leaderboard-ready, and does not resolve holdout
anti-gaming, multi-seed private scoring, or final release-readiness blockers.

## Verified Reviewers

- Gemini 3.5 Flash (High): accepted. Verified propagated label in panel log.
- Gemini 3.1 Pro (High): accepted with one parent-verification note about
  billing and project-management review coverage. Verified propagated label in
  panel log.
- Claude Sonnet 4.6 (Thinking): label verified, but the run produced an empty
  review output, so it is not counted for substantive findings.
- Claude Opus 4.6 (Thinking): label verified, but the run produced an empty
  review output, so it is not counted for substantive findings.
- ChatGPT reviewer: independent subagent review accepted.

Raw panel logs are intentionally untracked under `docs/reviews/panel-logs/`.

## Evidence Accepted

Fresh validator evidence:

```bash
python3 scripts/validate_holdout_pack.py
python3 scripts/validate_v0_release.py --allow-incomplete
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
```

The current public split has:

- 44 public tasks
- 6 synthetic SaaS apps
- 18 vulnerable tasks
- 26 secure-control tasks
- 16 denial controls
- 10 authorized-allow controls

The current ignored private holdout pack has:

- 24 protected private holdout tasks
- 12 vulnerable tasks
- 12 secure-control tasks
- 6 denial controls
- 6 authorized-allow controls
- 4 tasks per app across all 6 apps
- 24 route variants
- 24 decoy variants
- `leaderboard_suitable: true`
- `rehearsal_manifest_count: 0`
- `public_structure_overlap_count: 0`
- `tracked_private_manifest_count: 0`

The combined v0 task-mix gate reports:

- 68 total tasks
- 30 vulnerable tasks
- 38 secure-control tasks
- 16 authorized-allow controls
- control ratio `0.5588`

This satisfies the explicit v0 task-mix thresholds: at least 25 vulnerable
tasks, at least 30 controls, at least 10 authorized-allow controls, a control
ratio of at least 40%, 40-50 public tasks, 6 apps, and 20-30 protected private
holdout tasks.

## Prior Review Coverage

The original grounded panel reviewed the first three apps:

- `project_mgmt`
- `billing`
- `support`

Later section reviews covered the expansion work:

- `2026-06-05-support-expansion-panel-summary.md`
- `2026-06-05-file-sharing-panel-summary.md`
- `2026-06-05-api-tokens-panel-summary.md`
- `2026-06-05-audit-settings-panel-summary.md`

The parent reviewer checked the prior summaries after Gemini 3.1 Pro flagged
that the final task-mix context listed only the four later expansion summaries.
That note is accepted as a useful review-quality check, but it is not a blocker:
the original panel summary covers the project-management and billing foundation,
and current manifest validation covers all six app task manifests.

## Section Readiness

`task_realism_vulnerability_control_mix` can be marked v0-ready.

## Wording Constraints

- Say the task-mix section is v0-ready, not that the benchmark is v0-ready.
- Keep the public repo language alpha/pre-v0 until the strict validator reports
  `v0_ready: true`.
- Describe private holdout evidence only in aggregate. Do not publish private
  task IDs, seeds, routes, oracle bodies, raw manifests, raw result bundles, or
  private filesystem details.
- Do not treat this section decision as resolving multi-seed private scoring,
  route-alias/decoy anti-gaming, or final release-readiness.

## Residual v0 Blockers

- `holdout_contamination_anti_gaming` remains not v0-ready.
- `privacy_packaging_final_release_readiness` remains not v0-ready.
- The strict local validator still reports `v0_ready: false`.
