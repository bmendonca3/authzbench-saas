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
- Current 54-task no-tools public model families restored: 4/5
  (`qwen3-coder-next`, `claude-haiku-4.5`, `claude-sonnet-4.6`, and
  `glm-5`).
- Remaining 54-task no-tools public family: `claude-opus-4.6`.
- Current 54-task live HTTP tool-agent family: not yet restored.
- External review lanes: open.
- Active plus shadow/candidate private holdout packs: open.
- Release-grade hosted/containerized private execution: open.
- Correct claim: stable `v1-prep`, not `v1-ready`.

### Next Immediate Checkpoint

The next public checkpoint is complete when:

- `glm-5` has two runner-emitted 54-task no-tools summaries;
- `claude-opus-4.6` has two runner-emitted 54-task no-tools summaries;
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
  54-task v1-prep public split, deterministic scoring, current no-tools
  public baselines in progress, and clear public/private claim boundaries.
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

- [ ] Restore stable public model/tool-agent evidence for the active 54-task
  fingerprint.
  Current evidence:
  - the 54-task scripted sanity baseline is current and passes 54/54;
  - the repeated 54-task no-tools public families currently restored are
    `qwen3-coder-next`, `claude-haiku-4.5`, `claude-sonnet-4.6`, and `glm-5`,
    each with two runner-emitted summaries, matching active fingerprints,
    retained task bundles, and public-safe failure diagnostics;
  - `python3 scripts/validate_baseline_registry.py` currently reports
    `current_public_model_family_count: 4` and
    `has_current_public_tool_agent_baseline: false`;
  - the readiness gate is therefore correctly red even though the historical
    49-task checkpoint above was green.
  Completion is tracked by `Refresh model evidence after the 54-task
  promotion` below; do not mark this item complete until its repeated model and
  live HTTP acceptance evidence is satisfied.

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

- [ ] Complete the Application Security review lane.
  Acceptance evidence:
  - structured review evidence exists in
    `docs/reviews/external-review-summary.json`;
  - reviewer role/scope and review date recorded;
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
    review date, reviewer role/scope, reviewed artifacts, disposition, decisions,
    follow-up artifact for accepted/unresolved findings, and claim-boundary
    impact;
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
  - smoke evidence records command, commit SHA, runner image or hosted-runner
    version, private-pack version label, isolation model, expected denial of
    private manifest reads by submitter code, pass/fail result, and cleanup;
  - smoke evidence `benchmark_source_sha` matches the benchmark source SHA in
    the external release evidence;
  - smoke evidence `private_pack_fingerprint_sha256` matches the active private
    holdout pack fingerprint computed from validated private manifests;
  - public output excludes private task bodies, private routes, private seeds,
    raw private results, captures, credentials, and local absolute paths.

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
  - pack directories are versioned by role and pack label;
  - active and shadow/candidate labels are documented without exposing task
    bodies publicly;
  - each pack has manifest validation evidence;
  - the active pack fingerprint is computed from canonical private manifest
    content plus manifest paths and is recorded in release, hosted-smoke, source
    summary, and eligible leaderboard evidence;
  - compatibility, retirement trigger, and rerun policy are documented.

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

- [ ] Refresh model evidence after the 54-task promotion.
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
  - [ ] `claude-opus-4.6` no-tools family has two runner-emitted 54-task
    summaries;
  - the live HTTP `claude-sonnet-4.6` tool-agent family has two 54-task runs
    with one plan/probe artifact per task and full target-request correlation;
  - registry rows use the live fingerprint and are no longer marked stale;
  - variance, calibration, charts, status, report, and paper wording are
    refreshed from the 54-task artifacts;
  - no 49-task result is presented as a current comparison.

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
  - structured evidence exists at `docs/v1-paper-readiness.json`;
  - paper distinguishes frozen v0.0, current v1-prep, and true v1 claims;
  - figures and tables label current/stale/legacy evidence clearly;
  - `python3 scripts/generate_paper_tables.py` leaves no diff under
    `paper/shared`;
  - `latexmk -pdf -interaction=nonstopmode -halt-on-error
    paper/ieee-sp/main.tex` passes;
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
  - the structured evidence records the current release commit SHA, the
    benchmark source SHA used for hosted/paper/private-run evidence, every
    required command above with `passed: true`, exact-head CI conclusion, active
    private-pack fingerprint, and pushed commit status;
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
