# Route Alias And Decoy Expansion Panel Summary

Date: 2026-06-05

Section reviewed:

- route aliases and decoy endpoints across the six public target apps
- scorer-replayed task controls that exercise representative aliases and decoys
- docs describing the current anti-gaming posture

Question:

Does this route-alias and decoy expansion materially improve the benchmark's
public anti-gaming posture while avoiding overclaiming full v0 anti-gaming
readiness?

## Reviewer Coverage

Counted reviewers:

- Gemini 3.5 Flash (High), verified from the panel log.
- Gemini 3.1 Pro (High), verified from the panel log.
- panel reviewer, run as a separate scoped reviewer.

Unavailable or limited reviewers:

- Claude Sonnet 4.6 (Thinking): model label was verified, but the captured
  output did not return usable final findings.
- Claude Opus 4.6 (Thinking): model label was verified, but the captured output
  started exploration and did not return usable final findings.
- Kiro CLI `claude-opus-4.8`: skipped for this bounded review because the
  previous Kiro route/roadmap review leg hung and had to be stopped. Kiro was
  not counted.

Raw panel logs are intentionally not committed.

## Findings And Disposition

### Clean: aliases preserve the intended vulnerable semantics

Gemini and panel reviewers agreed that the aliases mirror the intended public
vulnerabilities:

- project-management work-items preserve cross-tenant task read behavior
- billing entitlements preserve the non-admin plan-change/read BFLA behavior
- support cases preserve cross-organization ticket reads
- file-sharing documents preserve cross-workspace file reads
- API-token vault secrets preserve cross-tenant secret reads
- audit/settings events preserve cross-organization audit-log reads

Disposition:

- Accepted. The parent also verified these paths through targeted HTTP tests and
  scorer replay.

### Clean: decoys are harmless and correctly denied

Reviewers found the new decoys return harmless queue/report/preview metadata on
authorized access and deny unauthorized actors with `403`.

Disposition:

- Accepted. Targeted HTTP tests cover unauthorized denial and representative
  authorized success cases for the new decoys.

### Accepted: alias controls needed body-level assertions

The panel reviewer found that alias controls on vulnerable tasks were replayed
by the scorer, but most initially checked only `status: 200`. That proved the
path executed, but not that it returned the same protected object.

Disposition:

- Added `body_contains` to the alias controls for project management, billing,
  support, file sharing, API tokens, and audit/settings.
- Re-ran manifest validation and a scripted scorer smoke. Both passed.

### Clean: scorer controls replay the new paths

Reviewers confirmed that the scorer loops through manifest `controls`, and the
new alias/decoy checks live in task manifests rather than only in tests.

Disposition:

- Accepted. The scripted baseline passed all 44 tasks after the body-level alias
  assertions were added.

### Clean: docs avoid v0 anti-gaming overclaim

Reviewers found the public docs now say aliases and decoys exist across the
public target apps, while still naming route randomization, private holdouts,
protected holdout execution, Docker runtime proof, and model baselines as open
v0 work.

Disposition:

- Accepted. No additional wording change was needed after review.

### Rejected: Docker Compose failure as a repo blocker in this checkpoint

One Gemini reviewer reported a Docker Compose validation failure from its own
grounded environment. The parent-run public validation had already passed
`docker compose config` locally in this repo.

Disposition:

- Rejected as environment-specific for this checkpoint.
- Docker runtime smoke remains an open v0 blocker, but Docker Compose config
  validation passed in parent verification.

## Local Verification

The parent reviewer ran:

```bash
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3 -Wd -m unittest discover -s tests -p 'test_http_apps.py'
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/route-alias-scripted-smoke --timeout-seconds 10 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent scripted_baseline_agent --model deterministic-script --harness-type scripted
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- manifest validation passed with 44 tasks, 18 vulnerable tasks, 26 controls,
  16 denial controls, 10 authorized-allow controls, and 0 private holdouts
- targeted HTTP tests passed and exercised the new aliases and decoys
- scripted scorer smoke passed 44/44 after alias controls were hardened with
  `body_contains`
- public validation passed with 41 tests, compile checks, Docker Compose config,
  Git-tracked privacy scan, and 44/44 scripted baseline

## Remaining Risks

- Route aliases are broader but not randomized.
- Public task manifests remain inspectable.
- Real private holdouts and protected holdout execution are still required.
- Docker runtime smoke and Docker-backed request-log correlation still depend on
  Docker daemon availability.
