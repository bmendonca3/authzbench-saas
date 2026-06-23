# CI Validation Panel Summary

Date: 2026-06-05

Section reviewed:

- GitHub Actions public-validation workflow
- local workflow guard test
- CI-related roadmap/status/checklist wording

Question:

Does the new CI workflow make meaningful progress toward the v0 public
validation gate without overclaiming that remote CI has already passed?

## Reviewer Coverage

Counted reviewers:

- Gemini 3.5 Flash (High), verified from the panel log.
- Gemini 3.1 Pro (High), verified from the panel log.
- panel reviewer, run as a separate scoped reviewer.

Unavailable or limited reviewers:

- Claude Sonnet 4.6 (Thinking) label was verified from the panel log, but the
  run did not return usable final findings.
- Claude Opus 4.6 (Thinking) label was verified from the panel log, but the run
  did not return usable final findings.
- Kiro was skipped for this bounded review.

Raw panel logs are intentionally not committed.

## Findings And Disposition

### Clean: workflow runs the intended public validation gate

Reviewers agreed that `.github/workflows/validate.yml` runs:

```bash
python scripts/validate_public.py --include-scripted-baseline
```

That public gate covers unit tests, manifest validation, compile checks, Docker
Compose config validation, the Git-tracked privacy scan, and the scripted
baseline.

### Clean: triggers and permissions are appropriate

Reviewers found the triggers appropriate for a public benchmark repository:
pushes to `main`, pull requests, and manual dispatch. Permissions are limited to
`contents: read`, and no workflow secrets are referenced.

### Accepted: local workflow test should assert triggers

The panel reviewer noted that the first version of `tests/test_ci_workflow.py`
checked the validation command and permissions but did not guard the trigger
set.

Disposition:

- Updated the workflow test to assert `push`, `pull_request`,
  `workflow_dispatch`, the `main` branch, and the workflow timeout.
- Made the Python version assertion tolerant of common quote formatting.

### Deferred: Docker runtime smoke in CI

Gemini 3.5 recommended adding `docker compose up --build -d`,
`python scripts/container_smoke.py`, and `docker compose down` to CI.

Disposition:

- Deferred for this checkpoint. The current milestone item was public CI for
  unit tests, manifests, compile checks, and Docker Compose config.
- Docker runtime smoke remains an explicit v0 blocker and release-checklist
  item.
- Remote CI should be checked after pushing this workflow before any release
  tag.

### Clean: docs avoid remote-CI overclaiming

Reviewers agreed that the docs say the workflow exists while keeping remote
passing CI as a release-tag gate.

## Local Verification

After accepting panel findings and staging the workflow files so the privacy
scan covered them, the parent reviewer ran:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_ci_workflow.py'
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- focused workflow test passed
- public validation passed with 46 tests, manifest validation, compile checks,
  Docker Compose config validation, Git-tracked privacy scan, and a scripted
  baseline

## Remaining Risks

- Remote GitHub Actions status still has to be checked after push.
- Docker runtime smoke is still not part of the workflow and remains a real v0
  blocker.
- CI alone does not prove private holdout protection, repeated model baselines,
  or final release readiness.
