# Project Goal

AuthZBench-SaaS is being built to become a top benchmark for one narrow,
important question:

> Can an AI agent prove SaaS authorization failures with backend evidence, while
> avoiding false positives when the application is behaving correctly?

The current repository is a released v0.0 benchmark artifact. It is useful for
reviewing the idea, running the harness, and comparing early agents on a
medium-size public split. It is not a hosted leaderboard or community-scale
benchmark, and the project should not claim the `v1` label until the scale,
review, and submission-infrastructure gaps below are closed.

## Historical 49-Task v1-Prep Checkpoint

Status: preserved checkpoint record. Full evidence lives in
[`docs/checkpoints/2026-06-07-49-task-v1-prep-checkpoint.md`](checkpoints/2026-06-07-49-task-v1-prep-checkpoint.md).

Summary:

- The 49-task public split was verified before the later 54-task expansion.
- Five no-tools model families and one live HTTP tool-agent family had repeated
  evidence at that checkpoint.
- Those rows are historical and must not be used as current 54-task comparisons.
- Boundary-reasoning calibration from that checkpoint remains useful for scorer
  interpretation, but does not make old runs current.

## Active v1 Readiness Goal

Status: active as of 2026-06-07. This is the current source of truth for the
remaining work needed before any `v1`, hosted leaderboard, or community-ready
claim is fair.

Do not mark this goal complete until every checklist item below is checked with
fresh evidence, and until strict `python3 scripts/validate_v1_readiness.py
--release-evidence <external-json>` exits successfully on the release candidate
commit. Until then, the correct claim is stable `v1-prep`, not `v1-ready`.

### Current Active Snapshot

As of the current `main` checkpoint:

- Public split: 54 tasks.
- Current scripted sanity baseline: complete, 54/54.
- Current 54-task no-tools public model families restored: 5/5
  (`qwen3-coder-next`, `claude-haiku-4.5`, `claude-sonnet-4.6`, `glm-5`, and
  `claude-opus-4.6`).
- Remaining 54-task no-tools public family: none.
- Current 54-task live HTTP tool-agent family: restored with two public
  `claude-sonnet-4.6` runs and 54/54 target-request correlation in both runs.
- External review lanes: open.
- Active plus shadow/candidate private holdout packs: open.
- Release-grade hosted/containerized private execution: open.
- Correct claim: stable `v1-prep`, not `v1-ready`.

Recent repo-side hardening checkpoints:

- commit `fd461390bd2816ccb8f36d9a3a1979d3ded3ec64` hardened the
  external-review evidence contract so completed lanes must record concrete
  bounded questions reviewed and per-decision summaries;
- exact-head GitHub Actions run `27122244154` passed on that commit;
- commit `d74bf2af9e3148e7872a337652baf166864e0636` hardened the final
  release-candidate evidence contract so strict release evidence must record
  workflow name `Validate AuthZBench-SaaS` alongside exact-head CI run ID, URL,
  conclusion, and head SHA;
- exact-head GitHub Actions run `27124203762` passed on that commit;
- the release-evidence placeholder hardening checkpoint ensures a copied
  template cannot pass after only changing the schema version: angle bracket
  placeholders are rejected in release SHA, benchmark source SHA, private-pack
  fingerprint, and per-command evidence fields;
- the hosted-smoke placeholder hardening checkpoint ensures a copied
  release-candidate smoke template cannot pass after only changing the schema
  version: angle bracket placeholders are rejected in runner/version,
  private-pack version, isolation model, and command fields, including embedded
  placeholders such as `runner:<digest>` or `--private-pack <active-pack>`;
- the private-rotation metadata hardening checkpoint requires declared pack
  versions, declared SHA-256 fingerprints matching computed pack fingerprints,
  compatibility policy, retirement triggers, and rerun policy before an active
  plus shadow/candidate rotation can pass;
- the paper-readiness evidence hardening checkpoint requires final
  release-candidate paper evidence to include the exact table, chart, and
  `latexmk` verification commands plus concrete LaTeX result and verification
  date, rather than relying on booleans alone;
- the public blocker evidence refresh checkpoint records the hosted-smoke
  blocker and private-operation blocker as prior-public-checkpoint evidence
  tied to GitHub Actions run `27147339042` on merge commit
  `5fbe63d1c73031814582a2494e2cef44f1981279`, while keeping both gates red
  because release-candidate private inputs are still absent;
- the public blocker reference-scope hardening checkpoint requires both public
  blocker records to declare `reference_scope: prior_public_checkpoint`, so
  historical public CI references cannot be mistaken for release-candidate or
  exact-head private evidence;
- the external-review embedded-placeholder hardening checkpoint ensures
  completed or pending review lane fields cannot pass with unresolved text such
  as `TBD`, `TODO`, `unknown`, `n/a`, or `<review-artifact>` embedded inside
  otherwise non-empty reviewer questions, artifacts, decisions, or next actions;
- the containerized-submission smoke image checkpoint ensures exact-head CI does
  not depend on a preloaded `python:3.11-alpine` image: the smoke resolves the
  runner image identity after pulling the image when local Docker inspection
  reports it missing;
- the public blocker evidence current-head refresh ties both structured blocker
  records to exact-head GitHub Actions run `27151712736` on merge commit
  `5d76970ecefb0c4959834e4f7acd81e8b51e11d9`, while keeping hosted/private
  operation gates red because release-candidate private inputs are still absent;
- strict v1 readiness still correctly reports `v1_ready: false` because the
  external-review, private-operation, scale, paper, and release-candidate
  evidence gates remain open.

### Completed Public Checkpoint

The current public checkpoint is complete because:

- all five no-tools public model families have two runner-emitted 54-task
  summaries: `qwen3-coder-next`, `claude-haiku-4.5`, `claude-sonnet-4.6`,
  `glm-5`, and `claude-opus-4.6`;
- the live HTTP `claude-sonnet-4.6` tool-agent family has two 54-task runs with
  one plan/probe artifact per task and full target-request correlation;
- baseline registry, charts, variance docs, status docs, report, and paper text
  are refreshed from those 54-task artifacts;
- exact-head CI passes on the promotion commit;
- no 49-task result is presented as current.

### v1 Product Bar

The v1 product is not just more benchmark rows. It needs a reviewable operating
surface: external review evidence, reproducible run bundles, private-pack
rotation, submitter isolation, clear eligibility rules, and paper/report wording
that a reviewer can inspect without relying on maintainer memory.

### External Platform Meeting Framing

Use this framing for the upcoming external platform discussion:

- What we have: a released v0.0 SaaS authorization benchmark, a stable
  54-task v1-prep public split, deterministic scoring, complete current
  54-task public no-tools baselines for five model families, repeated current
  live HTTP tool-agent public evidence, and clear public/private claim
  boundaries.
- What we want feedback on: benchmark framing, hosted submission workflow,
  leaderboard eligibility, run-bundle evidence, private holdout rotation, and
  how hosted evaluation infrastructure could support secure SaaS-authz evaluation.
- What we should not claim yet: `v1-ready`, hosted leaderboard operation,
  private-holdout ranking readiness, external-review completion, or stable
  community-scale model comparisons.
- The near-term collaboration ask: turn interest into bounded review evidence
  and infrastructure design notes that can be traced to artifacts, findings,
  or implementation commits.

### Objective

Advance AuthZBench-SaaS from a validated v1-prep research artifact into a
reviewed, scaled, protected, and operational v1/community benchmark. The project
must preserve the frozen v0.0 evidence boundary while adding enough independent
review, private-holdout operation, submission infrastructure, and repeated
private evidence to support stronger claims.

### Non-Negotiable Completion Rule

The goal is complete only when all of these are true:

- every item in this section is checked;
- strict `python3 scripts/validate_v1_readiness.py --release-evidence
  <external-json>` passes without `--allow-incomplete`;
- `python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view
  --expected-output artifact/expected-output/v1-readiness-public-view.json`
  matches the tracked clean-clone readiness fixture;
- `python3 scripts/validate_public.py --include-scripted-baseline` passes on the
  exact commit;
- container smoke passes either locally or in exact-head CI, with any local
  Docker daemon limitation recorded as environment-only;
- `python3 scripts/validate_baseline_registry.py` and
  `python3 scripts/validate_leaderboard_submission.py --submission
  'leaderboard_submissions/**/*.json' --require-source-summary` pass;
- generated paper tables and chart artifacts are clean after regeneration;
- `git diff --check` passes;
- `git ls-files tasks_private/holdout results captures docs/reviews/panel-logs`
  returns no tracked paths;
- the release commit is pushed and exact-head CI is green.

### Remaining v1 Release Checklist

Status: open. This is the concise current list of work required before any
fair `v1`, hosted-leaderboard, or community-ready release claim. The public
54-task baseline evidence is complete; the remaining work is external review,
private operation, protected execution, scale, and release-candidate evidence.

- [ ] Convert external interest into real review evidence.
  Required evidence:
  - all three review lanes are complete: Application Security,
    Benchmark/Evals methodology, and AI-agent/tooling;
  - each lane records reviewer role/scope, review date, reviewed artifacts,
    bounded questions, findings or explicit no-finding disposition, decisions,
    and claim-boundary impact; reviewer identity is recorded only when the
    reviewer grants permission;
  - accepted or unresolved findings link to concrete follow-up commits, docs,
    tests, task changes, or other repo artifacts;
  - `docs/reviews/external-review-response.template.json` is used only as a
    public-safe starting shape and every placeholder is replaced before review
    evidence is recorded;
  - `docs/reviews/external-review-summary.json` moves every required lane from
    `pending` to complete evidence;
  - `python3 scripts/validate_v1_readiness.py --allow-incomplete` reports
    `external_review_completed` as passed.

- [ ] Build an executable release-candidate hosted/private submission path.
  Required evidence:
  - `artifact/submission-runner-smoke.json` is replaced by a passing
    `execution_scope: release_candidate` smoke record tied to the active private
    pack;
  - `artifact/hosted-submission-execution-runbook.json` remains public-safe
    runbook evidence only and is not counted as release-candidate smoke;
  - `artifact/submission-runner-smoke.template.json` is used only as a
    public-safe starting shape and every placeholder is replaced before hosted
    smoke evidence is recorded;
  - the smoke record includes command, commit SHA, runner image or hosted-runner
    version, private-pack version, active private-pack fingerprint, isolation
    model, expected submitter private-manifest denial, pass/fail result, and
    cleanup status;
  - `benchmark_source_sha` matches the release evidence;
  - `private_pack_fingerprint_sha256` matches the active pack fingerprint
    computed from validated private manifests;
  - public outputs contain only redacted summaries and exclude private task
    bodies, private routes, private seeds, raw private results, captures,
    credentials, and local absolute paths.
  Current blocker evidence:
  - `artifact/submission-runner-smoke.json` is only structured blocker evidence;
  - its public rehearsal reference is marked
    `reference_scope: prior_public_checkpoint` and includes an AuthZBench-SaaS
    Actions URL and matching numeric run ID, plus workflow name `Validate
    AuthZBench-SaaS`;
  - `artifact/hosted-submission-execution-runbook.json` defines the
    maintainer-hosted and fully containerized smoke procedure but does not
    satisfy the gate;
  - `artifact/submission-runner-smoke.template.json` defines the required
    release-candidate smoke evidence shape and is rejected by the validator if
    copied unchanged as evidence;
  - the public CI container rehearsal is valuable but cannot satisfy this gate.

- [ ] Prove protected execution on the intended maintainer platform.
  Required evidence:
  - submitter code cannot directly read private manifests or raw private
    artifacts;
  - scorer-controlled code can evaluate private tasks;
  - raw private evidence is written only to ignored or protected locations;
  - redacted source summaries and candidate rows are generated from protected
    evidence;
  - privacy scans confirm no private or raw paths are tracked.

- [ ] Implement rotating private holdout packs.
  Required evidence:
  - one active private pack and one shadow or candidate private pack exist in
    the maintainer-only holdout area;
  - `artifact/private-holdout-operation-runbook.json` remains public-safe
    runbook evidence only and is not counted as private-holdout evidence;
  - `artifact/private-holdout-rotation-metadata.template.json` is used only as a
    public-safe starting shape and every placeholder is replaced in the ignored
    maintainer-only rotation metadata file before validation;
  - `tasks_private/holdout/rotation-metadata.json` declares pack IDs, roles,
    safe relative paths, concrete version labels, declared fingerprints matching
    computed pack fingerprints, and exactly one active pack;
  - each pack validates with the holdout-pack validator and is
    leaderboard-suitable;
  - pack IDs, task IDs, paths, and fingerprints are unique where required;
  - active-pack fingerprint is recorded consistently in release evidence,
    hosted-smoke evidence, source summaries, and eligible leaderboard rows;
  - compatibility, retirement triggers, and rerun policy are documented and
    validator-enforced.
  Current blocker evidence:
  - `artifact/private-holdout-operation-blocker.json` is public-safe structured
    blocker evidence only;
  - its public readiness reference is marked
    `reference_scope: prior_public_checkpoint` and includes an AuthZBench-SaaS
    Actions URL and matching numeric run ID, plus workflow name `Validate
    AuthZBench-SaaS`;
  - `artifact/private-holdout-operation-runbook.json` defines required private
    inputs, operation steps, rotation metadata fields, acceptance checks, and
    publication rules but does not satisfy the gate;
  - `artifact/private-holdout-rotation-metadata.template.json` defines the
    required active plus shadow/candidate metadata shape and is rejected by the
    validator if copied unchanged as evidence;
  - rotation metadata validation exists, but public checkout has no active or
    shadow/candidate packs and must not pretend otherwise.

- [ ] Produce repeated private evidence.
  Required tool-agent evidence:
  - at least one private-holdout `tool-agent` candidate row has
    `leaderboard_eligible: true`, `run_count >= 2`, matching benchmark source
    SHA, matching active private-pack fingerprint, source summaries,
    runner-emitted fingerprint/comparability key, target-request coverage, and
    protected-execution metadata proving private-path denial.
  Required no-tools evidence:
  - at least one repeated private-holdout `no-tools-model` row is refreshed for
    comparison and tied to the same benchmark source SHA, active private-pack
    version, active private-pack fingerprint, and validated source summaries;
  - old private rows affected by task, scoring, private-pack, or
    evidence-contract changes are marked stale, legacy, or deprecated;
  - baseline registry and variance docs distinguish public diagnostics from
    private leaderboard candidates.

- [ ] Reach the v1 scale gate.
  Required evidence:
  - the benchmark reaches at least 100 validated tasks across public and
    protected private splits;
  - `artifact/v1-task-scale-roadmap.json` is treated only as public-safe
    planning evidence and not counted as validated task-scale evidence;
  - counts are recomputed from manifests;
  - vulnerable/control mix remains meaningful;
  - denial controls and authorized-allow controls are preserved;
  - new task families include scorer fixtures or equivalent replay evidence;
  - task-quality matrix, charts, tables, status docs, and report language are
    regenerated and clean;
  - old baselines are not compared as current after task or scoring changes.
  Candidate expansion families:
  - file-share revoke and stale-link access;
  - API-token scope changes and unauthorized export/read;
  - cross-org audit exports;
  - invitations, role downgrade, and stale-permission workflows;
  - additional billing, support, admin/config, and SaaS collaboration flows
    with denial and authorized-allow controls.
  Current planning evidence:
  - `artifact/v1-task-scale-roadmap.json` maps the current 54 public tasks plus
    planned active and shadow protected-private waves to more than 100 total
    tasks, but the `v1_task_scale` gate remains open until those planned tasks
    exist as validated manifests.

- [ ] Refresh the v1-prep technical report and IEEE scaffold after evidence
  gates close.
  Required evidence:
  - frozen v0.0, current v1-prep, and true v1 claims are clearly separated;
  - external-review and infrastructure findings are reflected in paper/report
    language;
  - generated tables and charts regenerate without diff;
  - the IEEE scaffold compiles cleanly.

- [ ] Run full release-candidate validation.
  Required evidence:
  - `artifact/v1-release-candidate-validation-runbook.json` remains passing
    runbook evidence only and is not treated as release-candidate validation
    evidence;
  - full unit suite passes;
  - public validation with scripted baseline passes;
  - v0 release validation, baseline registry validation, leaderboard
    submission validation, and v1 readiness validation pass;
  - release evidence records schema version, commit SHA, benchmark source SHA,
    active private-pack fingerprint, exact command outcomes, exact-head CI run
    ID, exact-head CI run URL, exact-head CI workflow name
    `Validate AuthZBench-SaaS`, exact-head CI head SHA matching the release
    commit, and privacy-scan results;
  - `artifact/v1-release-candidate-validation.template.json` is used only as a
    public-safe starting shape, copied outside tracked Git, and replaced with
    real values before strict validation;
  - the release-candidate runbook names every required input, command, evidence
    field, acceptance check, and publication rule for collecting the external
    evidence;
  - the external evidence records `exit_code: 0` and non-placeholder evidence
    for every required command, and copied template placeholders such as
    `<log-or-run-id>` are rejected even if the schema version is changed;
  - generated paper tables and chart artifacts are clean after regeneration;
  - `git diff --check` passes;
  - `git ls-files tasks_private/holdout results captures docs/reviews/panel-logs`
    returns no tracked paths and release evidence records this as exactly
    `empty output`;
  - strict `python3 scripts/validate_v1_readiness.py --release-evidence
    <external-json>` passes without `--allow-incomplete`.

- [ ] Push the final release candidate and verify exact-head CI.
  Required evidence:
  - release candidate is committed as `bmendonca3`;
  - intended public branches are pushed;
  - exact-head GitHub Actions passes for the release commit;
  - no docs, paper, registry, expected-output, or generated-artifact drift
    remains after the CI commit.

### Automated Readiness Gate

- [x] Add a v1 readiness validator that reports each major v1/community gate as
  `passed` or `unmet`.
  Acceptance evidence:
  - strict mode fails while true v1 gates are incomplete:
    `python3 scripts/validate_v1_readiness.py` exits with status 1 and reports
    `v1_ready: false`;
  - `--allow-incomplete` mode exits successfully for current v1-prep validation:
    `python3 scripts/validate_v1_readiness.py --allow-incomplete` exits with
    status 0 and reports `v1_ready: false` with explicit passed and unmet gates
    matching the tracked public-view fixture;
  - the gate is called from `scripts/validate_public.py` in
    `--allow-incomplete` mode;
  - focused unit tests assert the current expansion state is not misrepresented
    as v1-ready: `python3 -m unittest discover -s tests -p
    'test_v1_readiness_validator.py'` and `python3 -m unittest discover -s
    tests -p 'test_validate_public.py'` pass.

### Stable v1-Prep Checkpoint Gate

- [x] The 49-task checkpoint was a verified stable v1-prep artifact before the
  next task expansion changed the live fingerprint.
  Evidence:
  - exact-head CI passed on commit `8da35643b1685fbb31892793d7ab50de0a5ad6f3`;
  - local public validation, v0 release validation, baseline registry
    validation, leaderboard-submission validation, generated paper table check,
    whitespace check, and tracked-private-path scan passed;
  - local Docker container smoke was not rerun only because the Docker daemon
    was unavailable locally, while exact-head CI covered the Docker-backed public
    validation path.

- [x] Restore stable public model/tool-agent evidence for the active 54-task
  fingerprint.
  Current evidence:
  - the 54-task scripted sanity baseline is current and passes 54/54;
  - the repeated 54-task no-tools public families currently restored are
    `qwen3-coder-next`, `claude-haiku-4.5`, `claude-sonnet-4.6`, `glm-5`, and
    `claude-opus-4.6`, each with two runner-emitted summaries, matching active
    fingerprints, retained task bundles, and public-safe failure diagnostics;
  - the repeated 54-task live HTTP `claude-sonnet-4.6` tool-agent family has
    two runner-emitted summaries, one model-tool plan artifact and one
    tool-probe artifact per task, 54/54 target-request correlation in both
    runs, zero planner failures, zero planner parse errors, zero invalid
    submissions, and zero secure-control false reports;
  - `python3 scripts/validate_baseline_registry.py` currently reports
    `current_public_model_family_count: 6`,
    `has_current_public_tool_agent_baseline: true`, `v0_baseline_ready: true`,
    and no unmet baseline requirements;
  - `python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view`
    reports the stable v1-prep public-evidence gate as passed while the true v1
    gates remain red.
  This item closes only the active public v1-prep evidence gate. It does not
  close external review, private holdout, hosted/containerized execution,
  private repeated evidence, task-scale, paper, or release-candidate gates.

### External Review Gate

- [ ] Convert external interest into bounded review evidence.
  Acceptance evidence:
  - reviewer or collaborator name, role/scope, and date are recorded;
  - the reviewed artifact set is listed;
  - requested review questions are bounded, such as benchmark framing, scoring
    validity, agent/tooling usability, or submission infrastructure;
  - feedback is recorded as findings, no-finding disposition, or advisory notes;
  - accepted findings link to concrete commits, docs, tests, or task changes;
  - interest alone is not treated as completed external review.
  Current evidence:
  - `docs/reviews/external-review-packet.md` is ready to send;
  - `docs/reviews/external-review-summary.md` is the human-readable intake
    tracker;
  - `docs/reviews/external-review-summary.json` is now structured pending
    evidence for all three required lanes, with requested artifacts, review
    questions, blockers, and next actions;
  - `docs/reviews/external-review-response.template.json` defines the required
    completed-review response shape and is rejected by the validator if copied
    unchanged as evidence;
  - the v1 readiness validator accepts that structure but still keeps
    `external_review_completed` red until all lanes move from `pending` to real
    completed review evidence.

- [ ] Complete the Application Security review lane.
  Acceptance evidence:
  - structured review evidence exists in
    `docs/reviews/external-review-summary.json`;
  - reviewer role/scope and review date recorded;
  - bounded questions reviewed are recorded as concrete non-placeholder strings;
  - artifacts reviewed listed;
  - findings or explicit no-finding disposition recorded;
  - every finding has an accepted, rejected, or unresolved decision;
  - accepted findings link to follow-up commits, docs, tasks, or tests; issue or
    PR references must be mirrored by a real repo artifact or resolvable commit
    before strict validation passes;
  - claim-boundary impact is recorded.

- [ ] Complete the Benchmark/Evals methodology review lane.
  Acceptance evidence:
  - structured review evidence exists in
    `docs/reviews/external-review-summary.json`;
  - reviewer role/scope and review date recorded;
  - bounded questions reviewed are recorded as concrete non-placeholder strings;
  - split design, scoring semantics, variance framing, stale/current evidence
    separation, and paper claim boundary reviewed;
  - findings or explicit no-finding disposition recorded;
  - every finding has an accepted, rejected, or unresolved decision;
  - docs and paper language are updated for accepted findings.

- [ ] Complete the AI-agent/tooling review lane.
  Acceptance evidence:
  - structured review evidence exists in
    `docs/reviews/external-review-summary.json`;
  - reviewer role/scope and review date recorded;
  - bounded questions reviewed are recorded as concrete non-placeholder strings;
  - harness assumptions, tool access, target-request correlation, model/agent
    comparability, and run-bundle evidence reviewed;
  - findings or explicit no-finding disposition recorded;
  - every finding has an accepted, rejected, or unresolved decision;
  - accepted harness or evidence-packaging findings are implemented and tested.

- [ ] Re-run the external-review completion gate after all three lanes.
  Acceptance evidence:
  - `docs/reviews/external-review-summary.md` contains no placeholder `TBD`
    completion rows for required lanes;
  - `docs/reviews/external-review-summary.json` records all required lanes with
    review date, reviewer role/scope, bounded questions reviewed, reviewed
    artifacts, disposition, decisions, decision summaries, follow-up artifact
    for accepted/unresolved findings, and claim-boundary impact;
  - the response template has not been counted as review evidence; placeholders
    are replaced by real external review facts;
  - `python3 scripts/validate_v1_readiness.py --allow-incomplete` reports
    `external_review_completed` as passed.

### Hosted Or Fully Containerized Submission Gate

- [x] Prove the containerized submitter-isolation mechanism in exact-head CI.
  Acceptance evidence:
  - `scripts/containerized_submission_smoke.py` runs submitter code in a
    non-root container with no network, a read-only root filesystem, dropped
    capabilities, `no-new-privileges`, resource limits, and only rendered
    context plus an output mount;
  - private manifests remain host-side and the container's attempted private
    path reads are denied;
  - scorer-controlled evaluation completes outside the submitter container;
  - emitted evidence passes its public-safety scan and contains no private task
    IDs, seeds, routes, oracle data, raw results, or absolute host paths;
  - public CI uses an ephemeral `execution_scope: rehearsal` pack and exact-head
    Docker-backed validation passes;
  - the validator explicitly rejects rehearsal evidence as release-candidate
    hosted-execution evidence.
  Evidence:
  - commits `38339f4b053ffbce5d8fd4d48970a5162c72cc39` and
    `b1a01d9e271b331d0aa745fca9139c7cbcca211d` implement and harden the
    rehearsal path, including exact Docker-argv constraint validation, an
    exact mount allowlist, bounded outputs, explicit non-root bind-mount
    permissions, timeout cleanup, required container-emitted submission
    output, public-evidence redaction, and a Docker build-context denylist;
  - `python3 scripts/validate_public.py --include-scripted-baseline` passed
    locally on the hardened tree, including 179 tests and the 54-task scripted
    baseline;
  - exact-head GitHub Actions run `27099082635` passed the Docker-backed public
    validation on commit `b1a01d9e271b331d0aa745fca9139c7cbcca211d`;
  - independent Kiro Opus 4.8 security and completeness audits identified the
    build-context, command-attestation, mount, missing-output, umask, output
    bound, redaction, and cleanup-timeout gaps; each accepted finding was fixed
    and rerun through focused and full validation;
  - this check proves the public rehearsal mechanism only. It does not prove
    kernel-level isolation on the intended release platform, protection of the
    real active private pack, or release-candidate hosted execution; the two
    following gates remain open.

- [ ] Implement or document an executable hosted/containerized private
  submission smoke path.
  Acceptance evidence:
  - structured evidence exists at `artifact/submission-runner-smoke.json`;
  - the tracked hosted execution runbook has not been counted as release
    smoke evidence;
  - smoke evidence records command, commit SHA, runner image or hosted-runner
    version, private-pack version label, isolation model, expected denial of
    private manifest reads by submitter code, pass/fail result, and cleanup;
  - the tracked smoke template has not been counted as hosted execution
    evidence; placeholders are replaced by real maintainer-platform or
    containerized release-candidate facts, and copied angle bracket placeholders
    are rejected even if the schema version is changed;
  - smoke evidence `benchmark_source_sha` matches the benchmark source SHA in
    the external release evidence;
  - smoke evidence `private_pack_fingerprint_sha256` matches the active private
    holdout pack fingerprint computed from validated private manifests;
  - public output excludes private task bodies, private routes, private seeds,
    raw private results, captures, credentials, and local absolute paths.
  Current evidence:
  - `artifact/submission-runner-smoke.json` now exists as structured blocker
    evidence, not release-candidate smoke evidence;
  - the blocker record marks the prior public CI rehearsal as
    `reference_scope: prior_public_checkpoint` and cites the exact-head
    Docker-backed container-smoke run;
  - the v1 readiness validator accepts the blocker structure but still keeps
    `hosted_or_containerized_submission_execution` red until the blocker record
    is replaced by `execution_scope: release_candidate` smoke evidence tied to
    the active private-pack fingerprint.

- [ ] Prove protected execution on the intended maintainer platform.
  Acceptance evidence:
  - submitter process cannot read private manifests directly;
  - scorer-controlled process can evaluate private tasks;
  - raw private evidence is written only to ignored/protected locations;
  - redacted summary and candidate row are generated from source summaries;
  - privacy scan confirms no private or raw paths are tracked.

### Rotating Private Holdout Gate

- [ ] Implement at least one active and one shadow or candidate private holdout
  pack.
  Acceptance evidence:
  - structured rotation metadata exists at
    `tasks_private/holdout/rotation-metadata.json`;
  - the tracked private-holdout operation runbook has not been counted as
    private holdout evidence;
  - the tracked rotation metadata template has not been counted as private
    holdout evidence; placeholders are replaced by real maintainer-only pack
    facts;
  - pack directories are versioned by role and pack label;
  - active and shadow/candidate labels are documented without exposing task
    bodies publicly;
  - each pack has manifest validation evidence;
  - declared pack fingerprints match fingerprints computed from canonical
    private manifest content plus manifest paths;
  - the active pack fingerprint is recorded in release, hosted-smoke, source
    summary, and eligible leaderboard evidence;
  - compatibility, retirement trigger, and rerun policy are documented and
    validator-enforced.

- [x] Add validation for private-pack rotation metadata.
  Acceptance evidence:
  - validator checks active plus shadow/candidate pack presence and validates
    each declared pack's manifests in maintainer checkout;
  - validator fails clearly in strict mode when packs are absent or ambiguous;
  - public CI can still run without private manifests by using documented
    allow-incomplete behavior where appropriate.
  Verification:
  - `scripts/validate_v1_readiness.py` validates safe pack paths, unique pack
    IDs and task IDs, exactly one active pack, at least one shadow/candidate
    pack, manifest quality thresholds, and active-pack fingerprinting;
  - `scripts/validate_holdout_pack.py` rejects private-to-private structural
    overlap through `comparison_private_patterns`, and
    `scripts/validate_v1_readiness.py` validates each successive declared pack
    against all preceding private-pack fingerprints without emitting private
    task IDs, seeds, routes, oracle strings, or manifest bodies;
  - the standalone holdout validator exposes `--comparison-private-task` for
    manual cross-pack validation before any shadow or candidate pack is promoted;
  - public validation uses `--public-view` so ignored private checkout state
    cannot change clean-clone expected output;
  - focused rotation, duplicate-path, fingerprint, private-to-private overlap,
    and public-view tests pass in `tests/test_v1_readiness_validator.py` and
    `tests/test_holdout_validator.py`;
  - the independent review record in
    `docs/reviews/2026-06-07-private-holdout-overlap-review-summary.md`
    documents the bounded Kiro Opus passes, the accepted unique-fingerprint
    count correction, the post-fix `CLEAN` verdict, and the boundary that
    actual active plus shadow/candidate pack implementation remains open;
  - commit `47790857146f21ff52ef800dc92f75da205f29f9` implements the
    cross-pack overlap guard, and evidence-refresh commit
    `b163e90cc8c96a9b3c8e61f784f8999603c809ea` passed exact-head GitHub
    Actions run `27100247433`.

### Repeated Private Tool-Agent Evidence Gate

- [ ] Produce at least one repeated private-holdout tool-agent candidate row.
  Acceptance evidence:
  - `leaderboard_eligible: true`;
  - `split: private-holdout`;
  - `harness_type: tool-agent`;
  - `run_count >= 2`;
  - `benchmark_commit_sha` matches the benchmark source SHA declared in the
    external release evidence;
  - `private_pack_fingerprint_sha256` matches the active private holdout pack
    fingerprint declared in release evidence and source summaries;
  - source run summaries are present and validated;
  - benchmark fingerprint and comparability key are runner-emitted;
  - target-request coverage is present for live/tool runs;
  - protected execution metadata proves private-path denial;
  - `scripts/validate_leaderboard_submission.py --submission
    'leaderboard_submissions/**/*.json' --require-source-summary` passes.

- [ ] Refresh repeated private no-tools baseline evidence for comparison.
  Acceptance evidence:
  - repeated eligible private-holdout no-tools rows match the benchmark source
    SHA declared in the external release evidence;
  - the benchmark source SHA exists, is an ancestor of the release commit, and
    has no release-affecting file changes between source and release unless the
    changed path is an explicitly allowed evidence-only JSON record;
  - any future compatibility attestation is tied to the same benchmark
    fingerprint, active private-pack version, and active private-pack
    fingerprint;
  - source summaries are present and validate;
  - old rows affected by task, scoring, private-pack, or evidence-contract
    changes are marked stale, legacy, or deprecated;
  - baseline registry and variance docs distinguish public diagnostics from
    private leaderboard candidates.

### v1 Scale Gate

- [ ] Reach at least 100 tasks across public and protected private splits.
  Acceptance evidence:
  - task counts are recomputed from manifests;
  - the tracked scale roadmap has not been counted as manifest evidence;
  - vulnerable/control mix remains meaningful;
  - denial controls and authorized-allow controls are preserved;
  - task-quality matrix is regenerated and clean;
  - new tasks include scorer fixtures or equivalent replay evidence;
  - stale baselines are not compared as current after task/scoring changes.

- [x] Complete and promote the 54-task support-reassignment expansion wave.
  This item remains open until every child check below has direct evidence:
  - [x] Add one vulnerable ordered workflow that proves a normal same-org
    support status update followed by an unauthorized agent-driven ticket
    reassignment through an alias route.
  - [x] Add secure same-org agent denial, cross-org denial, secure admin allow,
    and agent status-only authorized-allow tasks.
  - [x] Require backend replay for every step, exact boundary vocabulary for
    the vulnerable task, `findings: []` for controls, and assignment-state
    preservation where the task does not authorize reassignment.
  - [x] Add target tests for canonical, alias, secure, cross-org, invalid
    assignee, authorized status-only, and authorized admin behavior.
  - [x] Add scorer tests proving missing, reordered, duplicated, or malformed
    multi-step evidence cannot receive exploit-proof credit.
  - [x] Extend container smoke so the new vulnerable, denial, and authorized
    paths are checked with target-request log correlation.
    Evidence: `scripts/container_smoke.py` covers the vulnerable canonical and
    alias reassignment routes, secure same-org denial, cross-org denial,
    authorized status update, and secure admin allow with per-request task IDs;
    exact-head GitHub Actions run `27089965403` passed the Docker-backed public
    validation on commit `c1c2b7d35ae8944d91d598361e80b4c9c857ee31`;
    final promotion commit `45670b0a62db97d2da8d16113eac9f182fa78175`
    also passed exact-head GitHub Actions run `27089985522`.
  - [x] Recompute the public split from manifests and verify the expected mix:
    54 total, 21 vulnerable, 33 controls, 19 denial controls, 14
    authorized-allow controls, and 2 explicit multi-step workflows.
  - [x] Regenerate the task-quality matrix, charts, paper tables, and public
    expected-output fixtures; generated-file checks must leave no diff.
  - [x] Rerun and register a clean deterministic 54-task scripted baseline.
    Evidence: `baselines/scripted-baseline-public-54-summary.json` is
    runner-emitted from benchmark source commit
    `3448564f84afbaba7841b52233e5404e86d81937`, passes all 54 tasks, and
    carries the live 54-task fingerprint.
  - [x] Mark every 49-task model and tool-agent row stale for current
    comparison before the task change is published.
  - [x] Update status, benchmark-card, evidence/claims, baseline, artifact, and
    paper language so the 49-task model evidence is described as historical
    v1-prep evidence pending 54-task reruns.
  - [x] Run focused tests, the full unit suite, manifest validation, baseline
    registry validation, public validation with the scripted baseline,
    leaderboard validation, compile checks, whitespace checks, and tracked
    private-path checks.
    Evidence on commit `247ef1cd9bb836866d012ce4872358c044b16bdf`:
    168 unit tests passed; `validate_public.py --include-scripted-baseline`,
    strict v0 release validation, baseline-registry validation, manifest
    validation, and leaderboard-submission validation passed; the 54-task
    scripted run passed 54/54 with zero false reports or invalid submissions;
    task-quality, chart, and paper-table regeneration left no tracked diff;
    the IEEE paper compiled successfully; `git diff --check` passed; and the
    tracked private/raw-path scan returned no paths. Local Docker-backed smoke
    remains assigned to the next child check because the installed Docker
    client could not reach the absent Docker Desktop daemon.
  - [x] Commit as `bmendonca3`, push the intended public branches, and confirm
    exact-head CI including Docker-backed container smoke.
    Evidence: final promotion commit
    `45670b0a62db97d2da8d16113eac9f182fa78175` is authored as
    `bmendonca3 <bmendonca3@users.noreply.github.com>`, is present on
    `origin/main` and `origin/v1-task-expansion`, and exact-head GitHub Actions
    run `27089985522` passed.

- [x] Refresh model evidence after the 54-task promotion.
  Acceptance evidence:
  - [x] Finding-total telemetry is unambiguous and aligned across public and
    protected runners.
    Evidence: commit `1dc264b1d54c0608102b52231b0663d007543a11`
    adds scorer-derived `scored_submission_finding_total` while preserving
    legacy adapter-reported `submitted_finding_total`, aligns protected
    `false_positive_rate` with the public runner and leaderboard validator, and
    adds divergent-total, redaction, and control-failure regression tests.
    Paper-preflight refresh commit
    `220ebd980a4cde4fd9661185b6dae1bbed42c3f6` is pushed to `main` and
    `v1-task-expansion`; exact-head GitHub Actions run `27102314090` passed.
    Independent Kiro Opus audits first identified missing protected-path test
    coverage and a pre-existing false-positive semantic mismatch; both were
    fixed, and the final audit returned `CLEAN`.
  - [x] `qwen3-coder-next` has two runner-emitted 54-task base summaries,
    promoted with distinct run IDs, the active fingerprint, and public-safe
    task-level command/output failure diagnostics;
    Evidence: promotion commit
    `ee5bf213048bb0848b0c184e69646b668784a616` and paper-preflight refresh
    commit `98645dd7a9682050a94206865608e8185a11cdce` are authored as
    `bmendonca3`, pushed to `main` and `v1-task-expansion`, and exact-head
    GitHub Actions run `27101631586` passed. Local verification included 190
    tests, public validation with the 54-task scripted baseline, strict v0
    validation, baseline-registry and leaderboard validation, deterministic
    chart/table regeneration, IEEE paper compilation, whitespace checks, and an
    empty tracked-private/raw-path scan. A Kiro Opus evidence audit first
    returned actionable disclosure findings; after fixes, an independent narrow
    replacement audit returned `CLEAN`. The broad intermediate audit that
    stalled without a verdict is explicitly excluded from review evidence.
  - [x] `claude-haiku-4.5` has two runner-emitted 54-task base summaries with
    distinct run IDs, the active fingerprint, complete 54-task artifacts, zero
    adapter/runner failures, and zero invalid submissions.
    Evidence: run `20260607T185502191241Z-ac053a0a` passes 32 tasks, proves 4 of
    21 vulnerable replays, and has 11 scorer-counted findings; run
    `20260607T190024255303Z-8f2cac6a` passes 32 tasks, proves 5 of 21 vulnerable
    replays, and has 12 scorer-counted findings. Both keep boundary reasoning at
    `0.0`, fully pass zero vulnerable tasks, and report the same
    authorized-allow support reassignment control as vulnerable. The promoted
    scorer-finding aggregates are exact sums of retained task rows because the
    base runs immediately predate the aggregate emitter. A broad Kiro Claude
    Opus 4.8 audit found one ambiguous Qwen safety-rate attribution and then
    stalled without a verdict; the attribution was fixed and that incomplete
    audit is excluded from completion evidence. A narrow replacement Kiro
    Claude Opus 4.6 audit returned `VERDICT: CLEAN`. Local checks include 193
    passing tests, exact raw artifact counts, zero return-code/parse failures
    across 108 model outputs, deterministic chart and paper-table regeneration,
    successful public, strict-v0, registry, and leaderboard validation, an
    empty tracked-private/raw-path scan, and successful IEEE paper compilation.
    Promotion commit `a1b8b000d1b4789d03f780c969224e69f08f7b2f` and
    paper-preflight commit `9cd06e2b017a3071ccb398026654c78e949fbe3f`
    are authored as `bmendonca3`, pushed to `main` and `v1-task-expansion`, and
    exact-head GitHub Actions run `27102791303` passed.
  - [x] `claude-sonnet-4.6` has two runner-emitted 54-task base summaries with
    distinct run IDs, the active fingerprint, complete 54-task artifacts, zero
    adapter/runner failures, and zero invalid submissions.
    Evidence: run `20260607T194520410841Z-23511868` passes 32 tasks, proves 15
    of 21 vulnerable replays, and has 22 scorer-counted findings; run
    `20260607T195114220157Z-ad7ce734` passes 32 tasks, proves 14 of 21 vulnerable
    replays, and has 21 scorer-counted findings. Both keep boundary reasoning at
    `0.0` and fully pass zero vulnerable tasks. Run 1 falsely reports the
    authorized-allow admin reassignment control; run 2 falsely reports the
    secure viewer-status denial control. Kiro Claude Opus 4.8 and 4.6 audits,
    plus a post-fix Opus 4.6 audit, returned `VERDICT: CLEAN`; the only
    low-severity test-coverage suggestion was fixed. Local verification
    included 194 passing tests, exact raw-to-promoted JSON fidelity after
    stripping declared review annotations, 54 complete task bundles per run,
    zero return-code/parse failures across 108 model outputs, public validation
    with the 54-task scripted baseline, strict v0, registry, leaderboard,
    deterministic chart/table, paper compile, whitespace, and privacy checks.
    Local container smoke remained unavailable because the Docker Desktop
    socket was absent. Promotion commit
    `e1b7dcf43338b8baa97c117493700b3dddbf0211` and paper-preflight commit
    `c3c3d702d1f8fd6eccfca76ad523da2651ac46aa` are authored as `bmendonca3`,
    pushed to `main` and `v1-task-expansion`, and exact-head GitHub Actions run
    `27103482713` passed.
  - [x] `glm-5` has two runner-emitted 54-task base summaries with distinct run
    IDs, the active fingerprint, and retained task artifacts.
    Evidence: run `20260607T201255153205Z-5de7a354` passes 33 tasks, proves 2
    of 21 vulnerable replays, has 2 scorer-counted findings, reports zero
    control false positives, and preserves one outer runner failure on
    `sup_multistep_agent_status_then_admin_reassignment` with missing
    submission/model-output diagnostics; run
    `20260608T002053809050Z-e50a764c` passes 33 tasks, proves 3 of 21 vulnerable
    replays, has 4 scorer-counted findings, reports zero control false
    positives, and has complete 54-task artifacts with zero invalid
    submissions. Promotion commit
    `f069fbd9eada73bcfd3f750a51528af084d2a5fb`, paper-preflight commit
    `90e514367231135eff557e08e268971b02f80b5f`, independent Kiro Claude Opus
    artifact and claims audits, full local public validation, and exact-head
    GitHub Actions run `27110222646` verify this subitem.
  - [x] `claude-opus-4.6` no-tools family has two runner-emitted 54-task
    summaries with distinct run IDs, the active fingerprint, complete task
    artifacts, zero adapter, runner, or invalid-submission failures, and zero
    control false positives.
    Evidence: run `20260608T010424615768Z-6ce73f0b` and run
    `20260608T011105635536Z-ae586ffd` each pass 33 tasks, prove 14 of 21
    vulnerable replays, have 21 scorer-counted findings, keep boundary
    reasoning at `0.0`, fully pass zero vulnerable tasks, report zero false
    positives, and retain 54 submissions, scores, transcripts, contexts, and
    model-output artifacts. Focused baseline-registry and v0-release-validator
    tests passed at the Opus-only checkpoint with all five no-tools families
    present, so the live HTTP tool-agent pair was the only then-open
    public-evidence item.
  - [x] The live HTTP `claude-sonnet-4.6` tool-agent family has two 54-task
    runs with one plan/probe artifact per task and full target-request
    correlation.
    Evidence: run `20260608T013814005961Z-9c4b9351` and run
    `20260608T014504973620Z-1a19b7fb` each pass 33 tasks, prove 15 of 21
    vulnerable replays, keep boundary reasoning at `0.0`, fully pass zero
    vulnerable tasks, report zero secure-control false positives, submit 20
    findings, retain 54 model-tool plan artifacts, retain 54 tool-probe
    artifacts, correlate target requests for 54/54 tasks, and report zero
    planner failures, zero planner parse errors, zero invalid submissions, and
    zero fallback probes. Run 1 executes 123 tool probes; run 2 executes 126.
  - [x] Registry rows use the live fingerprint and are no longer marked stale.
    Evidence: `python3 scripts/validate_baseline_registry.py` reports
    `baseline_count: 30`, `current_public_model_family_count: 6`,
    `repeated_model_baseline_count: 6`,
    `has_current_public_tool_agent_baseline: true`,
    `v0_baseline_ready: true`, `v0_release_snapshot_ready: true`, and no unmet
    requirements or warnings.
  - [x] Variance, charts, status, report, and paper wording are refreshed from
    the 54-task artifacts.
    Evidence: tracked docs and generated artifacts now describe the current
    54-task public evidence as five no-tools families plus one live HTTP
    tool-agent family; generated charts and paper/shared tables are regenerated
    from the registry.
  - [x] No 49-task result is presented as a current comparison.
    Evidence: the 49-task rows remain labeled historical/stale, while the
    current public tool-agent row is `current_public_split` with
    `requires_rerun_before_current_comparison: false`.

- [ ] Expand task families without weakening v0.0 claim boundaries.
  Candidate areas:
  - billing entitlement misuse;
  - support ticket reassignment;
  - file share revoke and stale-link access;
  - API token scope change and unauthorized export/read;
  - audit export cross-org access;
  - invitation, role downgrade, and stale-permission behavior;
  - admin setting, report export, object ownership, and cross-org workflow
    variations.

### Paper And Artifact Gate

- [x] Complete the local v1-prep paper reproducibility preflight without
  claiming final paper readiness.
  Acceptance evidence:
  - `docs/v1-paper-readiness.json` binds the preflight to an ancestor benchmark
    source SHA;
  - the evidence scope is `v1_prep_preflight`, not `release_candidate`;
  - the report and IEEE scaffold distinguish frozen v0.0 evidence, current
    54-task v1-prep state, stale 46/49-task comparisons, and true v1 claims;
  - paper tables and benchmark charts regenerate without tracked diffs;
  - the IEEE scaffold compiles to PDF;
  - the final paper gate remains red until independent review and release
    infrastructure are complete.
  Verification:
  - `docs/v1-paper-readiness.json` is the structured source of truth for the
    current paper-preflight benchmark source SHA, CI provenance, chart/table
    regeneration commands, and LaTeX result;
  - `artifact/v1-paper-readiness-runbook.json` is a public-safe final-refresh
    procedure only, and the validator checks that it names the upstream inputs,
    table/chart/LaTeX commands, acceptance checks, and publication rules needed
    before true paper readiness;
  - the current paper-preflight evidence remains `v1_prep_preflight`, not
    `release_candidate`;
  - final paper readiness remains incomplete until independent external review,
    private-holdout operation, and release infrastructure gates pass;
  - exact-head CI uses `actions/checkout` with `fetch-depth: 0`, and
    `tests/test_ci_workflow.py` enforces that history requirement so the
    ancestor source SHA remains resolvable in a clean runner.

- [ ] Update the v1-prep technical report and IEEE scaffold after review and
  infrastructure gates change.
  Acceptance evidence:
  - `artifact/v1-paper-readiness-runbook.json` remains passing runbook evidence
    only and is not treated as release-candidate paper readiness;
  - structured evidence exists at `docs/v1-paper-readiness.json`;
  - paper distinguishes frozen v0.0, current v1-prep, and true v1 claims;
  - figures and tables label current/stale/legacy evidence clearly;
  - `python3 scripts/generate_paper_tables.py` leaves no diff under
    `paper/shared`;
  - `latexmk -pdf -interaction=nonstopmode -halt-on-error
    paper/ieee-sp/main.tex` passes;
  - structured paper evidence records the exact table-generation, chart
    generation, chart diff, paper-table diff, and `latexmk` verification
    commands, plus concrete LaTeX result and verification date;
  - paper readiness evidence `benchmark_source_sha` matches the benchmark
    source SHA in the external release evidence.

- [x] Add expected outputs or fixture snapshots for the new v1 readiness gates.
  Acceptance evidence:
  - artifact README names how to inspect current v1-prep versus true v1
  readiness;
  - expected output does not imply v1 readiness while incomplete gates remain.
  Verification:
  - `artifact/expected-output/v1-readiness-public-view.json` is the structured
    source of truth for the deterministic clean-clone public readiness view,
    including the current passed and unmet gates;
  - `scripts/validate_public.py` requires the current public view to match that
    fixture exactly;
  - fixture mismatch exits nonzero even when `--allow-incomplete` is used.

### Final Release Candidate Gate

- [ ] Run full exact-head local validation.
  Required commands:
  - `python3 -m unittest discover -s tests`
  - `python3 scripts/validate_public.py --include-scripted-baseline`
  - `python3 scripts/validate_public.py --include-scripted-baseline
    --include-container-smoke`
  - `python3 scripts/validate_v0_release.py`
  - `python3 scripts/validate_baseline_registry.py`
  - `python3 scripts/validate_leaderboard_submission.py --submission
    'leaderboard_submissions/**/*.json' --require-source-summary`
  - `python3 scripts/generate_paper_tables.py`
  - `git diff --exit-code -- paper/shared`
  - `git diff --check`
  - `git ls-files tasks_private/holdout results captures
    docs/reviews/panel-logs`
  Acceptance evidence:
  - structured release evidence exists outside tracked Git history and is passed
    to strict validation with `--release-evidence`;
  - `artifact/v1-release-candidate-validation-runbook.json` remains
    procedure-only evidence and is not counted as the external release evidence
    file;
  - the tracked template
    `artifact/v1-release-candidate-validation.template.json` remains
    template-only and is rejected if passed directly as release evidence;
  - the structured evidence records the current release commit SHA, the
    benchmark source SHA used for hosted/paper/private-run evidence, every
    required command above with `passed: true`, `exit_code: 0`, and
    non-placeholder evidence, exact-head CI conclusion, URL, numeric run ID,
    workflow name `Validate AuthZBench-SaaS`, head SHA matching the release
    commit, active private-pack fingerprint, and pushed commit status;
  - strict `python3 scripts/validate_v1_readiness.py --release-evidence
    <external-json>` passes from a clean working tree.

- [ ] Push release candidate and confirm exact-head CI.
  Acceptance evidence:
  - commit authored as `bmendonca3`;
  - pushed to the intended public remote;
  - exact-head GitHub Actions workflow passes;
  - no open validator gate remains;
  - this section is updated with final evidence and only then marked complete.

## Operating Principles

Keep the tracker focused on evidence that moves the project toward v1:

- Reward replayable backend proof, correct authorization-boundary reasoning,
  safe scope behavior, and silence on secure controls.
- Penalize route-name guessing, polished but unreplayable reports, blanket
  over-reporting, and confusion between allowed access and broken authorization.
- Keep public, stale, protected-private, and release-candidate evidence clearly
  labeled.
- Keep private holdouts, raw captures, secrets, local paths, and panel logs out
  of public Git history.
- Treat every stronger claim as gated by artifacts: repeated runs, exact commit
  SHAs, run bundles, privacy scans, external review, hosted/containerized
  execution evidence, and exact-head CI.
- Do not call the benchmark leaderboard-ready, v1, community-scale, or top-tier
  while rotating private holdouts, third-party review, repeated private
  evidence, hosted execution, or strict release validation remain open.

## Released v0.0 Boundary

The v0.0 release is complete and preserved as historical evidence: six
synthetic SaaS apps, a frozen public split, protected private evidence,
anti-gaming controls, live-target proof, repeated baselines, clean packaging,
and review artifacts. The active work above is the path from released v0.0 to
true v1/community readiness; do not blur those labels.
