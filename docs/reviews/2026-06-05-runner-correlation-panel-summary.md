# Runner Correlation Sectional Panel Summary

Date: 2026-06-05

## Verdict

Accepted for alpha/pre-v0 after fixes.

The runner-side correlation slice improves live-target proof by adding
per-task `target-requests.jsonl` artifacts when `--target-log-dir` is supplied.
It does not change deterministic scoring: `score.json` and `transcript.json`
still come from scorer replay.

## Reviewed By

- Gemini 3.5 Flash (High): verified output
- Gemini 3.1 Pro (High): verified output
- Claude Sonnet 4.6 (Thinking): model routing verified, no usable final finding
  before the run was stopped
- Claude Opus 4.6 (Thinking): model routing verified, no usable final finding
  before the run was stopped
- Kiro `claude-opus-4.8`: verified output

## Panel Findings

### Critical: target log directory was exposed to the agent

The draft runner passed `AUTHZBENCH_TARGET_LOG_DIR` to the agent process. That
would let a malicious or overfit agent write fake target logs directly, defeating
the purpose of target-side proof.

Disposition: fixed before commit. The runner now passes only `run_id`, `task_id`,
and `agent_id` to the agent. It does not pass the target log directory.

### Medium: stale target logs could be re-correlated

The draft runner read the whole target log file after each task. A stale entry
with matching identifiers could be copied into a new artifact.

Disposition: fixed before commit. The runner records the app log offset before
each task starts and correlates only newly appended entries.

### Low: filter should include `agent_id`

The draft filter matched only `run_id` and `task_id`.

Disposition: fixed before commit. Correlation now requires `run_id`, `task_id`,
and `agent_id`.

### Medium: run ids should be collision-resistant

The draft used second-resolution UTC run ids. In a persistent target-log
directory, two runs in the same second could collide.

Disposition: fixed before commit. Run ids now include microseconds and a short
random suffix.

### Medium: zero correlated requests should be visible

The draft produced an empty `target-requests.jsonl` and `target_request_count: 0`
without a warning when correlation was enabled but nothing matched.

Disposition: fixed before commit. Per-task summaries now include
`target_request_warning` when the app log is missing or no matching target
requests are correlated.

### Low: filter should re-check the app field

The draft relied on the app log filename and did not verify the entry's own
`app` field.

Disposition: fixed before commit. Correlation now requires the entry `app` to
match the current task app.

### Residual v0 gap: local filesystem isolation is not enforced

The alpha runner can avoid handing the log directory to the agent, but a serious
leaderboard run still needs process/container isolation so agents cannot write to
the target-log directory by guessing or discovering the path.

Disposition: retained as a v0 release-gate item.

## Verification

- `python3 -Wd -m unittest discover -s tests`
- `python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'`
- `python3 -m compileall -q authzbench apps tests scripts`
- CLI smoke with a temporary target-log writer verified a matching
  `target-requests.jsonl` artifact.

Docker runtime validation remains pending because Docker daemon access was not
available locally.
