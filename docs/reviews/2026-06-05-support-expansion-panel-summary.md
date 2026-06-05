# Sectional Panel Summary: Support Expansion And Goal Refresh

This review checked whether the support-app expansion and project-goal refresh
are worth committing as an alpha/pre-v0 checkpoint.

## Reviewers Counted

| Reviewer | Status |
| --- | --- |
| Gemini 3.5 Flash (High) | verified label and usable findings |
| Gemini 3.1 Pro (High) | verified label and usable findings |
| Claude Sonnet 4.6 (Thinking) | verified label; no usable final findings returned |
| Claude Opus 4.6 (Thinking) | verified label; no usable final findings returned |
| Kiro `claude-opus-4.8` | verified model catalog and usable findings |
| ChatGPT reviewer | usable findings |

Raw panel logs are intentionally not committed because they can contain local
environment metadata. They were written under `docs/reviews/panel-logs/`, which
is ignored by Git.

## Decision

Accepted as an alpha/pre-v0 improvement after fixes.

The support app adds useful benchmark breadth: one more SaaS workflow, a
three-role support model, JSON-body mutation tasks, and an invite-role abuse
case that is meaningfully different from the original object-read and billing
admin tasks. It is still too small and too public to support leaderboard claims.

## Findings Accepted

- The support secure routes needed explicit HTTP method checks.
- Malformed JSON request bodies should return a bounded error instead of risking
  handler-thread crashes.
- Secure-control scoring should verify the expected response body subset when
  an oracle provides one, not only the status code.
- The infographic overclaimed model false-positive performance because one
  legacy model snapshot has a nonzero false-positive rate.
- The v0 scope table needed to list invite abuse in the alpha-preview class set.

## Disposition

- `apps/support/app.py` now rejects wrong methods on secure ticket read and
  secure ticket-status routes with `405 method_not_allowed`.
- `apps/support/app.py` now returns `400 invalid_json` for malformed or
  non-object JSON bodies on `PATCH` and `POST`.
- `authzbench/score.py` now checks control response body subsets when provided
  by the control or by the secure-control task oracle.
- `tests/test_http_apps.py` covers wrong-method and invalid-JSON behavior.
- `tests/test_harness.py` covers secure-control body-oracle enforcement.
- `assets/authzbench-saas-infographic.svg` now labels the `0.0`
  false-positive metric as the scripted sanity baseline, not current model
  baselines.
- `docs/v0-release-plan.md` now lists invite abuse in the alpha-preview
  vulnerability class set.

## Remaining Open Items

- Public secure routes are still signposted with `/secure/`; broader route alias
  masking and decoys remain v0 work.
- Token authentication is still simplified through benchmark actor headers.
- Invite abuse proves unauthorized invite creation, not full invite acceptance.
- Private holdouts, repeated model baselines, Docker CI, and isolated
  live-agent validation are still required before any real `v0` tag.

## Verification Performed For This Section

```bash
python3 -Wd -m unittest discover -s tests -p 'test_http_apps.py'
python3 -Wd -m unittest discover -s tests -p 'test_harness.py'
```

Both focused suites passed after the accepted fixes.
