# File-Sharing Expansion Panel Summary

Date: 2026-06-05

## Scope

This sectional review checked the file-sharing target expansion before commit.
The reviewed section adds:

- `apps/file_sharing/` on port `8014`
- 8 public file-sharing tasks
- 3 vulnerable tasks and 5 controls
- harness wiring, Docker Compose service, scripted-baseline support, tests, docs,
  and roadmap/count updates

## Reviewers Counted

- Gemini 3.5 Flash (High): verified by Antigravity log
- Gemini 3.1 Pro (High): verified by Antigravity log
- ChatGPT reviewer: subagent review with local read-only inspection

Kiro `claude-opus-4.8` was attempted after preflight passed, but the run hung and
was stopped. It is not counted for this section.

Raw panel logs are intentionally kept under ignored `docs/reviews/panel-logs/`.

## Accepted Findings

1. `apps/file_sharing/app.py` allowed seeded `ACTIVE_LINK_ID` to depend on any
   active link if refs were regenerated after a viewer-created share link. The
   ref lookup now pins the public active link to the original seeded editor
   link.
2. `apps/file_sharing/app.py` returned `404 unknown_route` for wrong methods on
   non-secure matched routes. The file, share-link, and share-creation routes now
   return `405 method_not_allowed` consistently.
3. `scripts/container_smoke.py` used a generic invalid readiness actor for some
   services. Readiness now uses an app-valid actor plus expected status for each
   target.
4. `tasks/file_sharing/fs_bola_northstar_reads_apex_file.json` had an overly
   leading objective. The objective now asks about the access boundary without
   naming the non-secure API.
5. `tasks/file_sharing/fs_active_share_link_control.json` did not explain that
   active public links intentionally cross workspace boundaries. The policy now
   states that directly.

## Review Conclusions

The file-sharing section adds real benchmark breadth. It introduces a workflow
that security agents should understand in actual SaaS systems: workspace files,
public share links, expired-link state, viewer/editor role differences, and
authorized public-link behavior. It is meaningfully different from the earlier
project-management, billing, and support examples.

The section is still alpha/pre-v0 quality. Public manifests are inspectable,
secure routes are still obvious, and route aliases/private holdouts are still
needed before leaderboard claims are appropriate.

## Local Verification After Fixes

```bash
python3.11 -Wd -m unittest tests.test_http_apps tests.test_validate_manifests tests.test_harness tests.test_runner
python3.11 -m authzbench.validate_manifests --task 'tasks/*/*.json'
git diff --check
python3.11 scripts/validate_public.py --include-scripted-baseline
python3.11 -m compileall -q authzbench apps tests scripts
docker compose config
```

Results: all passed locally. The scripted baseline passed 29/29 tasks with 12
vulnerable tasks and 17 controls.

## Remaining Follow-Ups

- Add route aliases or less obvious secure/control naming across the file-sharing
  target before the real v0 tag.
- Add private holdout variants outside public Git history.
- Rerun live HTTP and model baselines on the 29-task split before any release
  tag.
