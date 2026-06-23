# API-Tokens Expansion Panel Summary

Date: 2026-06-05

## Scope

This sectional review checked the API-token target expansion before commit. The
reviewed section adds:

- `apps/api_tokens/` on port `8015`
- 8 public API-token tasks
- 3 vulnerable tasks and 5 controls
- harness wiring, Docker Compose service, scripted-baseline support, tests, docs,
  and roadmap/count updates

## Reviewers Counted

- Gemini 3.5 Flash (High): verified by Antigravity log
- Gemini 3.1 Pro (High): verified by Antigravity log
- panel reviewer: read-only local inspection

Kiro was deliberately skipped for this section after the previous file-sharing
Kiro review hung. Raw panel logs are intentionally kept under ignored
`docs/reviews/panel-logs/`.

## Accepted Findings

1. The original draft treated API tokens only as benchmark actor names. The HTTP
   handler now also accepts seeded `Authorization: Bearer ...` tokens when the
   benchmark actor header is absent.
2. The original secret values were static strings. Secret values now derive from
   the seed, and task manifests use resolved template refs for oracle matching.
3. Docker smoke originally covered only the cross-tenant token read path. It now
   also covers the read-token write bypass and missing-export-scope bypass.
4. API-token task and API-doc prose used overly leading "secure route" language.
   The API-token control objectives and API docs now say "protected API path" or
   "protected path" instead.
5. Public docs now distinguish the alpha implementation from the desired v0
   hardening: live HTTP supports bearer tokens, while scorer replay is still
   actor-compatible for deterministic local evaluation.

## Rejected Or Already Covered Findings

- A reviewer warned that control-task oracles using `no_vulnerability` conflict
  with `findings: []`. That is the benchmark convention: the scorer accepts
  empty findings for controls and uses the oracle only to validate the control
  replay response.
- A reviewer warned that expected token scopes would fail exact list matching.
  The scorer uses subset matching for lists, so expecting `secrets:write` passes
  when the token has both `secrets:read` and `secrets:write`.
- Route names still include `/api/secure/...`. This remains an acknowledged
  alpha/pre-v0 limitation. Route aliases and less obvious protected paths are
  still v0 hardening work.

## Review Conclusions

The API-token section adds meaningful benchmark breadth. It adds tenant-bound
token reasoning, read/write token-scope separation, export-scope checks, and
authorized-allow controls. This is distinct from the earlier user-role and
workspace examples and moves the public split closer to the real v0 target.

The section is still alpha/pre-v0 quality. Public manifests are inspectable,
protected paths are still easy to identify, and private holdouts plus first-class
scored bearer-token replay are needed before leaderboard claims are appropriate.

## Local Verification After Fixes

```bash
python3.11 -Wd -m unittest tests.test_http_apps tests.test_validate_manifests tests.test_harness tests.test_runner
python3.11 -m authzbench.validate_manifests --task 'tasks/*/*.json'
git diff --check
python3.11 -m compileall -q authzbench apps tests scripts
docker compose config
```

Results: all passed locally. The targeted suite passed 24 tests. Manifest
validation passed with 37 manifests, 15 vulnerable tasks, and 22 controls.

## Remaining Follow-Ups

- Add route aliases or less obvious protected-path naming across token tasks
  before the real v0 tag.
- Make bearer-token replay a first-class scored path instead of only an HTTP
  target capability.
- Add private holdout variants outside public Git history.
- Rerun live HTTP and model baselines on the 37-task split before any release
  tag.
