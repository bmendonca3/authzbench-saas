# AuthZBench-SaaS Panel Context

Repository: https://github.com/bmendonca3/authzbench-saas

Current public state:

- 3 Dockerized synthetic SaaS target apps: `project_mgmt`, `billing`, and `support`
- 21 public task manifests under `tasks/`
- 9 vulnerable tasks and 12 secure-control tasks
- Covered bug classes: BOLA / cross-tenant object reads, BFLA / non-admin billing access, support-ticket invite abuse, secure controls for same-tenant allowed behavior and cross-tenant denial
- Task manifests use seeds to derive tenant IDs, object IDs, org IDs, invoice IDs, and actor tokens
- Private holdout manifests are intentionally excluded from the public repo; `tasks_private/holdout/` is ignored
- Runner writes `context.json`, `submission.json`, `agent.json`, `score.json`, `transcript.json`, and run `summary.json`
- Scorer replays HTTP-style evidence against backend app logic and checks proof responses plus secure controls
- Current baselines:
  - scripted sanity baseline: 21/21, exploit-proven success 1.0, false-positive rate 0.0
  - Kiro `claude-sonnet-4.6`: legacy 15-task alpha snapshot
  - Kiro `qwen3-coder-next`: legacy 15-task alpha snapshot
- Docker config validates locally; full Docker smoke depends on an available Docker daemon
- README now embeds `assets/authzbench-saas-infographic.svg`

Relevant files:

- `README.md`
- `assets/authzbench-saas-infographic.svg`
- `authzbench/score.py`
- `authzbench/run.py`
- `authzbench/validate_manifests.py`
- `apps/project_mgmt/app.py`
- `apps/billing/app.py`
- `apps/support/app.py`
- `tasks/`
- `scripts/scripted_baseline_agent.py`
- `scripts/kiro_baseline_agent.py`
- `docs/methodology.md`
- `docs/leaderboard-schema.md`
- `docs/holdout-and-contamination.md`
- `docs/launch-report.md`
- `docs/result-schema.md`
- `baselines/`

Known limits already documented:

- Larger private holdout pack is still needed for a serious leaderboard
- Route aliases are not randomized yet
- Runner executes trusted local commands and is not yet a containerized leaderboard runner
- Browser HAR capture is not implemented; backend replay transcripts are implemented

Decision criteria:

1. Improve public benchmark value for AI/security researchers.
2. Prioritize changes that are implementable in this repo now.
3. Preserve personal-info and secret cleanliness.
4. Avoid overclaiming leaderboard readiness.
5. Prefer objective verification over prose-only polish.
