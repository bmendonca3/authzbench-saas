# Validation Commands

This page consolidates the bounded public validation set, the maintainer-only
strict set, and the privacy check. It is intentionally a copy-paste friendly
reference; see the linked scripts for full flag documentation.

## Validation Levels

Reviewers and hosts should use the appropriate validation level:

### Public No-Docker Reviewer Validation
Run this from a clean clone to verify public tests and registry states:
```bash
python3 scripts/validate_public.py --include-scripted-baseline
```

### Full CI/Container-Smoke Validation
Run this to include full container smoke testing (requires Docker to be running):
```bash
python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke
```

### Host-Presentation Validation
To run the aggregate validation checking all host-facing artifacts, markdown links, templates, and schemas:
```bash
python3 scripts/validate_host_presentation.py
```
Or, to run the aggregate checks including Docker container smoke:
```bash
python3 scripts/validate_host_presentation.py --include-container-smoke
```

`artifact/run-public-validation.sh` wraps the core of the public set and also runs the tracked-path privacy check. It is the recommended one-line entrypoint.

## Maintainer-Only Strict Set

Maintainers with the private holdout pack should additionally run:

```bash
python3 scripts/validate_v0_release.py
python3 scripts/validate_v1_readiness.py
```

These do not publish private evidence; they enforce strict gates against
local holdout contents.

## Privacy Check

A public commit must not track private/raw artifact paths. Run:

```bash
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs harbor-jobs .harbor .handoff
```

The command must print nothing.

## Harbor Local Preflight

To check whether the local checkout is ready to attempt a future Harbor run:

```bash
python3 scripts/check_harbor_local_execution.py
```

This generates and validates a temporary public skeleton and records whether
the `harbor` CLI is on `PATH`. It does not invoke `harbor run`. In a checkout
without Harbor installed, the local execution gate is recorded as blocked on
the missing CLI.

## Harbor Local Smoke

To create a redacted local smoke summary without committing raw
`harbor-jobs/` output:

```bash
python3 scripts/run_harbor_local_smoke.py
python3 scripts/validate_harbor_local_evidence.py
```

The checked-in smoke summary proves only local task/agent/verifier
execution for the generated public skeleton and records
`parity_verified: false` until a public-safe adapter can produce valid
submissions across vulnerable and secure-control tasks and a multi-task
`parity_experiment.json` is computed from matching Harbor and native run
artifacts.

## Generated Charts And Tables

Paper and chart reproducibility:

```bash
python3 scripts/generate_benchmark_charts.py
python3 scripts/generate_paper_tables.py
git diff --exit-code -- paper/shared docs/assets/benchmark-charts
```

The diff should be empty for a release-candidate commit unless charts or
tables were intentionally refreshed.

## When A Check Fails

- `validate_public.py`: manifest, scoring, or privacy regression. Inspect
  the failure context; do not weaken validators to clear a check.
- `validate_baseline_registry.py`: baseline registry drift. Refresh the
  affected baseline or update the registry contract.
- `validate_harbor_parity_experiment.py`: parity evidence drift. Refresh
  the parity evidence or correct the methodology field.
- `validate_harbor_adapter_templates.py`: adapter template drift. Refresh
  the affected template.
- `validate_v1_readiness.py --public-view`: public-view readiness drift.
  Refresh the public-view fixture only if a tracked gate intentionally
  changed; do not weaken readiness truth conditions.
- `git diff --check`: whitespace or conflict-marker regression.
- Privacy check: investigate the tracked file before unstaging.
