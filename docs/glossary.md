# Glossary

Canonical definitions for the terms used in the AuthZBench-SaaS docs,
artifacts, and review packets. When a term is used in a public-facing
context, prefer the definition here over a local paraphrase.

## Authorization terms

- **BOLA (Broken Object Level Authorization)**: an authenticated user
  can read or modify an object they do not own by knowing or guessing
  its id. OWASP API1:2023. See
  `tasks/project_mgmt/pm_bola_read_alpha_from_beta.json` for a
  canonical example.
- **BFLA (Broken Function Level Authorization)**: an authenticated
  user can invoke a function (route or mutation) reserved for a
  different role. OWASP API5:2023. See
  `tasks/file_sharing/fs_bfla_viewer_creates_public_link.json` for a
  canonical example.
- **Tenant boundary**: the boundary between two customers (tenants) of
  a multi-tenant SaaS app. Crossing this boundary is BOLA at the
  tenant level.
- **Object boundary**: the boundary between two objects owned by the
  same tenant. Crossing this boundary is BOLA at the object level.
- **Role boundary**: the boundary between two roles in the same
  tenant (e.g., `viewer` vs `editor`). Crossing this boundary is BFLA.
- **Token scope**: the permission set attached to an API token
  (e.g., `read` vs `write`, or `audit:read` vs `audit:export`).
  Crossing the scope boundary is a scope-bypass vulnerability.

## Control and oracle terms

- **Authorized-allow control**: a secure-control task that asserts
  the correct behavior is to permit access with no finding. Tests
  that an agent does not over-report.
- **Denial control**: a secure-control task that asserts the correct
  behavior is to deny or reject the request. Tests that an agent
  does not under-report or confuse a denial with a vulnerability.
- **False positive**: a finding that the scorer rejects as incorrect
  because the underlying request was either denied, permitted, or
  out of scope. See
  [`docs/scoring-and-submissions.md`](scoring-and-submissions.md#3-leaderboard--anti-gaming-policy).
- **Exploit proof**: the recorded request/response that demonstrates
  a vulnerability actually exists in the target app. The scorer's
  `exploit_proven: true` field is set when the final evidence
  request satisfies the backend oracle.
- **Scorer-owned replay**: the property that the scorer, not the
  agent, is the only path that produces a `proof` response. See
  `authzbench/score.py::_request_requirement_matches`.
- **Target-request correlation**: the property that every HTTP
  request the harness issues is reflected in the on-target request
  log. Enforced via the `target_request_coverage_rate` field for
  tool-agent rows.

## Benchmark lifecycle terms

- **Private holdout**: the set of tasks not published in the public
  split. The private holdout protects against memorization and is
  the source of truth for v1.0-internal scoring. See
  [`docs/private-holdout-lifecycle.md`](private-holdout-lifecycle.md).
- **Public split**: the 63 public task manifests under `tasks/`
  (6 apps; 27 vulnerable tasks and 36 secure controls). Inspectable by reviewers; not leaderboard-grade
  by itself.
- **v1.0-internal**: the internal release tag the project carries
  today. The `v1_ready: true` field in
  `artifact/expected-output/v1-readiness-public-view.json` is scoped
  to internal/public-view readiness only. See
  [`docs/claims-and-evidence.md`](claims-and-evidence.md).
- **External validation**: the v2 readiness state in which all three
  external review lanes (AppSec, benchmark / evals, agent / tooling)
  are in `complete` status with real reviewer records. Not claimed
  today.
- **Harbor adapter**: the local adapter package at
  `authzbench_harbor/` that ships the public tasks in a Harbor-
  compatible dataset shape. Distinct from Harbor platform
  acceptance, which is not claimed.
- **Platform acceptance**: any third-party platform (Harbor, Kaggle,
  or other) accepting the project as a public benchmark. Not claimed
  today. The `harbor_acceptance_claimed`,
  `kaggle_acceptance_claimed`, and `platform_acceptance_claimed`
  fields in
  `artifact/harbor-adapter-readiness-blockers.json` are explicitly
  `false`.

## Leaderboard and submission terms

- **Eligibility tier**: the bucket a leaderboard-candidate row sits in
  (`sanity`, `public-diagnostic`, `private-candidate`,
  `private-eligible`, `external-verified`). See
  [`docs/scoring-and-submissions.md`](scoring-and-submissions.md#2-result-and-submission-schema).
- **Comparability key**: the deterministic key derived from
  `harness_type`, `tool_access`, `max_steps`, `timeout_seconds`,
  `max_http_requests`, `retry_policy`, `temperature`, and the
  `target_request_correlation_required` flag. Two rows are
  comparable only when every key field matches.
- **Submission bundle**: a directory containing `submission.json`,
  `score.json`, `summary.json`, `transcript.json`,
  `target-requests.jsonl` (tool-agent only), `metadata.json`, and
  `environment.json`. See
  [`scripts/validate_submission_bundle.py`](../scripts/validate_submission_bundle.py).
- **Active private pack**: the private holdout pack currently
  scoring against. The `private_pack_fingerprint_sha256` field in
  any submission must match the active pack's fingerprint.
