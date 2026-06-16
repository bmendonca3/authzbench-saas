# Container Image Digests

This document records the container image digests the
AuthZBench-SaaS maintainer tracks for the v1.0-internal release.
The digests are not a hosted-leaderboard claim and are not a
Harbor / Kaggle / platform acceptance claim. They are the
reviewer-side image identity the maintainer uses when reproducing
the public validation surface.

## Reviewer-side image

| Image | Purpose | Digest |
| --- | --- | --- |
| `authzbench-saas/runner` | Reviewer-side image that runs `scripts/validate_public.py --include-scripted-baseline` on a clean clone. | See `artifact/expected-output/v1-readiness-public-view.json` for the recorded SHA (the `benchmark_source_sha` field, used as the public-view identity key for the readiness fixture). |

## Target-app images

| Image | Port | Digest | Notes |
| --- | --- | --- | --- |
| `authzbench-saas/project_mgmt` | 8011 | See `docker-compose.yml` `services.project_mgmt.build` | The synthetic project-mgmt target. |
| `authzbench-saas/billing` | 8012 | See `docker-compose.yml` `services.billing.build` | The synthetic billing target. |
| `authzbench-saas/support` | 8013 | See `docker-compose.yml` `services.support.build` | The synthetic support target. |
| `authzbench-saas/file_sharing` | 8014 | See `docker-compose.yml` `services.file_sharing.build` | The synthetic file-sharing target. |
| `authzbench-saas/api_tokens` | 8015 | See `docker-compose.yml` `services.api_tokens.build` | The synthetic api-tokens target. |
| `authzbench-saas/audit_settings` | 8016 | See `docker-compose.yml` `services.audit_settings.build` | The synthetic audit-settings target. |

## How to record a new digest

When the maintainer ships a new public-validation runner image, the
digest is recorded in
`artifact/expected-output/v1-readiness-public-view.json` and cross-
referenced from the release notes
(`docs/releases/v1.0-internal.md`). The maintainer does not promise
the digest is portable across hosts; the `Dockerfile` builds from
the local source tree and the per-app `apps/*/Dockerfile` files
build the synthetic fixtures.

## See also

- `docs/harbor-integration-runbook.md`: the four-level Harbor
  status table (repo-side adapter / local smoke / public parity /
  platform acceptance).
- `docs/hosted-evaluation-integration-sketch.md`: the v2 hosted
  submission execution runbook.
- `artifact/harbor-adapter-readiness-blockers.json`: the current
  blockers for Harbor / platform acceptance, with
  `harbor_acceptance_claimed: false`,
  `hosted_public_leaderboard_claimed: false`, and
  `kaggle_acceptance_claimed: false` explicit.
