# Publish Checklist

Publish only from a clean, scrubbed working tree after local validation. The
intended public host is non-Gatech `github.com`.

## Pre-Publish Gate

- [ ] `python3 -Wd -m unittest discover -s tests`
- [ ] `python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'`
- [ ] `python3 -m compileall -q authzbench apps tests scripts`
- [ ] `docker compose config`
- [ ] `python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/scripted-baseline --timeout-seconds 10`
- [ ] model baseline summaries in `baselines/` match the latest verified runs
- [ ] Docker daemon running and `python3 scripts/container_smoke.py` passes against `docker compose up --build -d`
- [ ] `docs/launch-report.md` updated with the latest verified baseline results
- [ ] `docs/status.md` has no stale claims
- [ ] private holdout manifests are absent from Git and ignored by `.gitignore`
- [ ] secrets, personal paths, personal emails, browser artifacts, and unrelated local data are absent from the Git index
- [ ] a fresh clone from public `github.com` passes the non-Docker checks
- [ ] optional GitHub Actions workflow is added with credentials that have `workflow` scope

## Suggested Repository Settings

- Repository name: `authzbench-saas`
- Visibility: public, after the pre-publish gate passes
- Default branch: `main`
- License: MIT
- Topics: `ai-agents`, `benchmark`, `appsec`, `authorization`, `saas-security`, `owasp-api`

## Suggested First Release

Tag: `v0.0.1-public-scaffold`

Release notes:

- 2 Docker-ready intentionally vulnerable SaaS targets
- 15 public seeded tasks
- deterministic scorer with backend replay transcripts
- secure-control tasks for false-positive measurement
- scripted baseline and two initial model baselines
- draft launch methodology and leaderboard schema
