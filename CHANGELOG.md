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
- Added v0-candidate runner metrics for exploit proof, boundary reasoning,
  secure-control false reports, secure-control execution, and target-request
  coverage, while keeping the legacy alpha `mean_score` for compatibility.
- Added invalid-submission summary metrics and made vulnerable-task
  `v0_mean_score` require control replay as an integrity gate without giving
  vulnerable tasks separate agent-independent control credit.
- Added a GitHub Actions public-validation workflow for pushes, pull requests,
  and manual dispatch, now including Docker container smoke validation.
- Hardened private-holdout validation with non-empty route/decoy variant
  metadata checks and behavioral public-task structural-copy detection.
- Added a baseline registry and validator so legacy snapshots, harness checks,
  repeated runs, and leaderboard eligibility are machine-checkable.
- Added leaderboard submission validation plus a schema-valid public harness
  example that is explicitly not leaderboard eligible.
- Added artifact-backed leaderboard validation so tracked examples can be
  checked against source run summaries instead of trusting hand-entered rows.
- Added a v0 release-gate audit script and review registry so the repository can
  report `v0_ready: false` with explicit unmet gates during alpha/pre-v0 work.
- Added a release evidence registry and release-candidate leaderboard submission
  gate so strict v0 readiness cannot pass from public examples alone.
- Reran the live HTTP scripted baseline on the current 44-task public split and
  updated the baseline registry to treat it as a current harness check, while
  keeping it non-eligible for leaderboard claims.
- Added a heuristic live HTTP prober harness check with per-task probe artifacts
  and 44/44 target-request correlation, while keeping it out of the v0
  tool-agent baseline gate.
- Added two current 44-task Kiro `qwen3-coder-next` no-tools model baseline
  summaries and registered them as the first repeated public model family.
- Added two current 44-task Kiro `claude-sonnet-4.6` no-tools model baseline
  summaries and registered them as the second repeated public model family.
- Added two current 44-task Kiro `deepseek-3.2` no-tools model baseline
  summaries and registered them as the third repeated public model family.
- Hardened public validation so lightweight checks do not require Docker
  Compose unless container smoke validation is requested.
- Added a public-safe private holdout summary utility so maintainers can produce
  count-level release evidence without publishing private task bodies, seeds,
  routes, or oracle details.
- Added a prototype project-management route alias and billing decoy endpoint,
  both exercised by public task controls.
- Expanded route aliases and decoy endpoint controls across all six public
  target apps while keeping route randomization as future private-holdout work.
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
