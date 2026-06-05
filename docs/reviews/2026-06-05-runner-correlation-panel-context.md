# Runner Correlation Sectional Panel Context

Date: 2026-06-05

AuthZBench-SaaS remains an alpha/pre-v0 public scaffold. The current public
split is two synthetic SaaS apps and fifteen tasks.

Previous checkpoint:

- Docker HTTP targets can emit target-side JSONL request logs under
  `captures/request-logs/`.
- Target logs include optional `run_id`, `agent_id`, and `task_id`.
- Request-log writes are best-effort and do not break target responses.

This slice adds alpha runner-side correlation:

- `python3 -m authzbench.run` accepts `--target-log-dir`.
- The runner passes `AUTHZBENCH_RUN_ID`, `AUTHZBENCH_TASK_ID`,
  and `AUTHZBENCH_AGENT_ID` to the agent process.
- The runner does not pass `AUTHZBENCH_TARGET_LOG_DIR` to the agent process.
- Before each task starts, the runner records the relevant target log offset.
  After scoring each task, the runner reads newly appended entries from
  `<target-log-dir>/<app>.jsonl`, filters entries matching the current `run_id`,
  `task_id`, and `agent_id`, and writes those entries to
  `results/<run_id>/<task_id>/target-requests.jsonl`.
- Each correlated entry receives a `correlation` object that records the match
  keys and source log path.
- Scoring still comes from deterministic backend replay; target request logs are
  interaction proof, not the scoring oracle.
- `scripts/live_scripted_baseline_agent.py` now sends runner-provided
  `run_id`, `agent_id`, and `task_id` headers.

Verification already run before this review packet:

- `python3 -Wd -m unittest discover -s tests` passed, 19 tests.
- `python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'` passed,
  15 manifests.
- `python3 -m compileall -q authzbench apps tests scripts` passed.
- `git diff --check` passed.
- A CLI smoke with a temporary target-logging agent passed and verified one
  matching target log entry was written to per-task `target-requests.jsonl`.
- Sectional panel review caught the initial log-directory exposure to the agent;
  that issue was fixed before commit.

Known limitations:

- Docker daemon access is unavailable locally, so Docker runtime correlation is
  still not verified on this machine.
- This is alpha correlation, not a complete leaderboard proof system.
- Real v0 still needs Docker-backed CI, isolated live-agent execution, broader
  live-agent header coverage, and stronger private holdouts.
