# Publish Checklist

Publish only from a clean, scrubbed working tree after local validation. The
intended public host is the public `github.com` account.

## Pre-Publish Gate

- [ ] `python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke`
- [ ] `python3 -Wd -m unittest discover -s tests`
- [ ] `python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'`
- [ ] `python3 scripts/validate_baseline_registry.py`
- [ ] `python3 scripts/validate_v0_release.py --allow-incomplete` for
      alpha/pre-v0 status reporting
- [ ] `python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json' --require-source-summary`
- [ ] `python3 -m compileall -q authzbench apps tests scripts`
- [ ] `docker compose config`
- [ ] `python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/scripted-baseline --timeout-seconds 10 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent scripted_baseline_agent --model deterministic-script --harness-type scripted`
- [ ] scripted baseline summary in `baselines/` matches the latest verified run
- [ ] tracked leaderboard example rows point to source run summaries and validate
      against them
- [ ] release-candidate eligible leaderboard rows live under
      `leaderboard_submissions/**/*.json` or an equivalent protected submission
      bundle, not as repurposed public harness-check examples
- [ ] baseline registry reports `v0_baseline_ready: true` before any real `v0`
      tag; alpha tags may keep it false if the docs clearly say why
- [ ] for any real `v0` tag, rerun strict
      `python3 scripts/validate_v0_release.py` and require `v0_ready: true`
- [ ] for any real `v0` tag, update `docs/release-evidence.json` only after the
      matching local validation, fresh-clone validation, remote CI, Docker smoke,
      privacy scan, release-note separation, and protected holdout execution
      evidence is actually available
- [ ] if a private pack exists locally, `python3 scripts/validate_holdout_pack.py`
      passes and no private manifests are staged
- [ ] private holdout validation reports `leaderboard_suitable: true` for any
      real holdout pack; rehearsal packs must remain `leaderboard_suitable: false`
- [ ] if using the rehearsal generator, confirm it is treated only as a workflow
      test and not as private leaderboard evidence
- [ ] older model/live baseline snapshots are clearly labeled, or rerun before a
      tagged release
- [ ] Docker daemon running; if debugging manually, `python3 scripts/container_smoke.py`
      passes against `docker compose up --build -d`
- [ ] `docs/launch-report.md` updated with the latest verified baseline results
- [ ] `docs/status.md` has no stale claims
- [ ] private holdout manifests are absent from Git and ignored by `.gitignore`
- [ ] secrets, personal paths, personal emails, browser artifacts, and unrelated local data are absent from the Git index
- [ ] `python3 scripts/validate_public.py --fresh-clone https://github.com/bmendonca3/authzbench-saas.git --include-scripted-baseline --include-container-smoke`
- [ ] GitHub Actions public-validation workflow exists and remote CI status is
      explicit and passing before any real v0 tag

## Suggested Repository Settings

- Repository name: `authzbench-saas`
- Visibility: public, after the pre-publish gate passes
- Default branch: `main`
- License: MIT
- Topics: `ai-agents`, `benchmark`, `appsec`, `authorization`, `saas-security`, `owasp-api`

## Suggested Alpha Tag

Tag: `alpha-0.0.1-public-scaffold`

Release notes:

- 6 Docker-ready intentionally vulnerable SaaS targets
- 44 public seeded tasks
- deterministic scorer with backend replay transcripts
- secure-control tasks for false-positive measurement
- scripted baseline and two initial model baselines
- baseline registry that labels legacy snapshots and current release readiness
- leaderboard submission validator and ineligible public harness-check example
- draft launch methodology and leaderboard schema

Do not use the plain `v0` label until the release gates in
[`v0-release-plan.md`](v0-release-plan.md) are satisfied.
