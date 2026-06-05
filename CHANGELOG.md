# Changelog

## Unreleased

- Reframed the public repository as an alpha/pre-v0 preview instead of a finished
  v0 benchmark.
- Strengthened the repo-level goal contract around becoming a top benchmark,
  with explicit SDLC checkpoints, sectional review expectations, and release
  gates before the real `v0` label.
- Added a root `ROADMAP.md` with milestones from alpha stabilization through v1.
- Added `docs/v0-release-plan.md` with the release bar for the real v0.
- Added `docs/benchmark-card.md` to describe intended use, scope, metrics, and
  limitations.
- Tightened leaderboard schema to include split, commit, harness type,
  public/private counts, boundary reasoning, control metrics, repeated-run
  fields, and variance/confidence reporting.
- Updated baseline summaries to use the alpha benchmark-version label.
- Added runner metadata support for benchmark version, agent, model, and harness
  type.
- Added a prototype project-management route alias and billing decoy endpoint,
  both exercised by public task controls.
- Added target-side JSONL request logging for Docker HTTP targets and container
  smoke validation for those logs.
- Added alpha runner-side correlation of target logs into per-task
  `target-requests.jsonl` artifacts when `--target-log-dir` is supplied.
- Added a third synthetic SaaS target, `support`, with six public tasks covering
  cross-organization ticket reads, viewer status writes, invite-role abuse, and
  matching secure controls.
- Added a fourth synthetic SaaS target, `file_sharing`, with eight public tasks
  covering cross-workspace file reads, expired share-link access, viewer-created
  public links, matching secure controls, and authorized-allow controls.
- Added a fifth synthetic SaaS target, `api_tokens`, with eight public tasks
  covering token tenant binding, read-scope write bypasses, export-scope
  bypasses, matching secure controls, and authorized-allow controls.
- Added a sixth synthetic SaaS target, `audit_settings`, with seven public tasks
  covering cross-organization audit-log reads, member security-setting changes,
  restricted audit-export downloads, matching secure controls, and
  authorized-allow controls.
- Added scorer support for control request bodies so write and invite controls
  can be replayed accurately.
- Added scorer support for seeded API-token bearer evidence while preserving
  actor-compatible deterministic replay.
- Added sectional panel-review artifacts and disposition for the v0 roadmap.
- Added `control_type` to public secure-control manifests and runner summaries
  so denial controls and authorized-allow controls are tracked separately.
