# Bearer Replay Scorer Context

Question: Does the API-token scorer replay now treat seeded bearer-token
evidence as first-class proof while preserving legacy actor-compatible replay?

Reviewed section:

- `authzbench/core.py`
- `authzbench/score.py`
- `tests/test_harness.py`
- `docs/result-schema.md`
- `README.md`
- `docs/status.md`
- `ROADMAP.md`
- `docs/benchmark-card.md`
- `docs/launch-report.md`

Parent-verified facts:

- `authzbench.core.replay_request()` now reads optional
  `request.headers.Authorization`.
- A seeded `Authorization: Bearer ...` value is resolved against the app's
  seeded public actors.
- If `actor` and bearer token are both supplied, they must resolve to the same
  seeded actor.
- Unknown bearer tokens fail closed during replay.
- Actor-only replay remains supported for existing public tasks, controls, and
  scripted baselines.
- The result schema now documents optional replay headers and bearer-token
  mismatch semantics.

Verification already run:

```bash
python3.11 -Wd -m unittest tests.test_harness
python3.11 scripts/validate_public.py --include-scripted-baseline
python3.11 -m authzbench.score tasks/api_tokens/tok_cross_tenant_secret_read.json examples/submissions/secure_control.no_findings.json
```

Manual replay smoke:

```python
replay_request(
    task,
    {
        "method": "GET",
        "path": f"/api/secrets/{HELIO_SECRET_ID}",
        "headers": {"Authorization": f"Bearer {MERIDIAN_READ_TOKEN}"},
    },
)
```

The smoke returned HTTP-style status `200` with token actor
`meridian_read_token` in the replay body.

Known remaining gaps:

- This is scorer-side deterministic replay, not a substitute for Docker-backed
  live-agent isolation.
- Route alias/randomization, real private holdouts, and protected holdout
  execution remain required before real v0 leaderboard claims.
