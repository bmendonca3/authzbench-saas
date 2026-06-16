# Contributing

AuthZBench-SaaS is alpha/pre-v0. Contributions are welcome, but public changes
must preserve the benchmark's separation between public rehearsal material and
private holdout evidence.

## Good Public Contributions

- new public tasks that use synthetic tenants, users, roles, objects, and tokens
- new synthetic SaaS fixture apps or endpoints
- scorer, runner, and validator improvements
- documentation that makes the benchmark easier to run or audit
- baseline adapters or example submissions that are clearly labeled public-split
  evidence
- tests that improve manifest, scoring, privacy, or release-gate coverage

## Do Not Contribute

- private holdout task IDs, seeds, route aliases, or oracle bodies
- raw private-run results, captures, transcripts, target logs, or panel logs
- real customer data, production SaaS credentials, tokens, cookies, or secrets
- claims that the repo is tagged v0, hosted-leaderboard-ready, or a validated
  model benchmark before a maintainer publishes that release state
- third-party product logos or screenshots that imply the fixtures are real SaaS
  integrations

## Add or Update Public Tasks

1. Put public task manifests under `tasks/<app>/`.
2. Keep all data synthetic and deterministic from the task seed.
3. Mark vulnerable tasks with `expected_vulnerable: true`.
4. Mark secure controls with `expected_vulnerable: false` and `control_type` set
   to `denial` or `authorized_allow`.
5. Include enough oracle and control information for deterministic backend
   replay, but do not copy private holdout material into public tasks.
6. Keep `allowed_hosts` limited to local benchmark fixture app names.
7. Review the task family with [`docs/task-quality-rubric.md`](docs/task-quality-rubric.md).
8. Run:

```bash
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3 scripts/validate_task_quality_gate.py --contract artifact/task-quality-gate-contract.json --task 'tasks/*/*.json'
python3 scripts/validate_public.py --include-scripted-baseline
```

## Add Baseline Evidence

Baseline summaries should be artifact-backed and labeled by split:

- `public-split`: useful for methodology review and sanity checks
- `private-holdout`: maintainer-only release-candidate evidence
- `leaderboard_eligible: true`: only when the leaderboard schema and source-run
  checks pass

Do not present public-split baseline numbers as final model rankings.

For release-facing metric interpretation, follow
[`docs/score-policy.md`](docs/score-policy.md) and avoid ranking by legacy
`mean_score` alone.

When task or scorer changes affect comparability, follow
[`docs/score-stability-policy.md`](docs/score-stability-policy.md) and mark old
results as legacy or deprecated instead of mixing them with current runs.

## Local Validation

Before opening a PR or publishing a release-candidate change, run the strongest
checks that apply:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_v0_release.py --allow-incomplete
git diff --check
```

Maintainers with the private holdout pack should also run strict:

```bash
python3 scripts/validate_v0_release.py
```

## Privacy Check

Before committing, check that private paths are not tracked:

```bash
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs harbor-jobs .harbor .handoff
```

The command should print nothing for public commits.

Ignored public-safe paths include:

- `tasks_private/holdout/` — maintainer-only private holdout bodies, seeds,
  routes, and oracles
- `results/` — local run result bundles
- `captures/` — local capture artifacts
- `docs/reviews/panel-logs/` — raw model or CLI review logs
- `harbor-jobs/`, `.harbor/` — raw Harbor job output
- `.handoff/` — local Codex agent scratch (handoff packets, run logs)

If you need to add a tracked public-safe example under one of these paths,
update `.gitignore` carefully and re-run the privacy check.
