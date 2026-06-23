# Sectional Panel Summary: Audit/settings Surface And v0 Goal Refresh

This review checked whether the sixth SaaS surface, the seven-task
audit/settings public slice, and the roadmap/goal refresh make AuthZBench-SaaS
more credible as a future top SaaS authorization benchmark while keeping the
current repo honestly labeled alpha/pre-v0.

## Reviewed Files

- `apps/audit_settings/app.py`
- `tasks/audit_settings/*.json`
- `authzbench/core.py`
- `scripts/scripted_baseline_agent.py`
- `scripts/container_smoke.py`
- `tests/test_http_apps.py`
- `tests/test_harness.py`
- `README.md`
- `ROADMAP.md`
- `docs/goal.md`
- `docs/status.md`
- `docs/benchmark-card.md`
- `docs/v0-release-plan.md`
- `docs/v0-task-build-matrix.md`
- `docs/launch-report.md`

## Verified Reviewers

- Gemini 3.5 Flash (High), verified from panel log model evidence.
- Gemini 3.1 Pro (High), verified from panel log model evidence.
- Claude Sonnet 4.6 (Thinking), verified from panel log model evidence.
- Claude Opus 4.6 (Thinking), verified from panel log model evidence.
- Kiro CLI `claude-opus-4.8`, verified from the live model catalog and output.
- panel reviewer, read-only review.

Raw model logs were written under ignored `docs/reviews/panel-logs/`.

## Decision

Accepted for the alpha/pre-v0 checkpoint after fixes.

The panel consensus was that the audit/settings slice improves the benchmark:
it adds realistic admin-settings, audit-log, restricted-export, denial-control,
and authorized-allow behavior. Reviewers also found that the goal and roadmap
communicate a serious path toward a top benchmark without claiming the current
repo is already v0 or leaderboard-ready.

## Accepted Findings And Fixes

### Audit BOLA Proof Could Use A Mismatched Path Org

Finding: the non-secure audit-log route originally allowed
`/api/orgs/{NIMBUS_ORG_ID}/audit-logs/{QUASAR_AUDIT_LOG_ID}` to return the
Quasar log. The task intended a cross-org actor boundary, not a mismatched
path/resource boundary, and the oracle did not reject that weaker proof.

Disposition: fixed.

- `apps/audit_settings/app.py` now requires the path org to match the audit
  log's org before returning the non-secure audit-log response.
- `tests/test_http_apps.py` now checks the mismatched path returns `404`.
- `tests/test_harness.py` now verifies a forged submission using the wrong path
  org does not pass exploit proof.

### Rendered API Docs Were Too Leading

Finding: reviewers noted that rendered `api_docs` used phrases such as
"non-secure" and described exact protected-route boundaries. That made public
tasks easier to solve by route wording instead of authorization reasoning.

Disposition: fixed for the public alpha surface.

- Public API descriptions across all six apps now use neutral wording such as
  "alternate route" instead of labeling routes as vulnerable, secure, protected,
  or enforcing a specific missing boundary.
- The public split still exposes route names and remains inspectable, so this is
  an alpha anti-gaming improvement, not a private-holdout substitute.

### v0 Matrix Looked Like It Reduced Public Authorized-Allow Coverage

Finding: the v0 target matrix briefly showed fewer public authorized-allow
controls than the current alpha already has.

Disposition: fixed.

- `docs/v0-task-build-matrix.md` now preserves a target of 10 public
  authorized-allow controls and 27 public controls total.
- The v0 target is now roughly 70-75 total tasks, still inside the intended
  public/private release shape.

### Docker Runtime Smoke Was Worded Too Strongly

Finding: `docs/launch-report.md` could be read as claiming Docker runtime smoke
currently passed, even though only Docker Compose config was verified in this
local run.

Disposition: fixed.

- The launch report now says Docker Compose config validation passes and Docker
  runtime smoke requires an available local Docker daemon before release tags.

## Accepted Residual v0 Work

### Alpha Subscore Naming Can Inflate Mean Score

Finding: on vulnerable tasks, the compatibility `false_positive_control`
subscore replays fixed task controls and can give agent-independent credit. The
headline false-positive rate remains correctly computed over secure-control
tasks, and docs already de-emphasize `mean_score`, but the subscore naming is
not ideal for a mature leaderboard.

Disposition: retained as v0 scoring hardening.

- `ROADMAP.md` now includes a v0 item to replace alpha compatibility subscores
  with metrics that avoid agent-independent control credit on vulnerable tasks.

### Legacy Model Baselines Need Reruns

Finding: no-tools model baselines remain legacy snapshots from the earlier
15-task split.

Disposition: retained as v0/before-tag work.

- README, status, and launch docs continue to label those snapshots as legacy
  and require reruns on the 44-task split before release tags.

## Verification After Fixes

```bash
python3.11 -Wd -m unittest tests.test_http_apps tests.test_validate_manifests tests.test_harness tests.test_runner
python3.11 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3.11 -m compileall -q authzbench apps tests scripts
docker compose config
```

Result: all passed locally.

Docker runtime smoke was not run in this verification step because it depends on
an available Docker daemon.

## Remaining Risks

- Public tasks are still inspectable; private holdouts remain required for real
  leaderboard claims.
- Route names still reveal some structure, even after API description wording
  was softened.
- CI workflow is still blocked by unavailable workflow-scoped GitHub
  credentials.
- Legacy Kiro/model baselines need reruns on the 44-task split.
- Docker-backed live-agent/request-log validation is still required before any
  real v0 tag.
