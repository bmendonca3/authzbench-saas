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

## Historical 49-Task Perfection Pass

Status: preserved checkpoint record as of 2026-06-07. The active source of
truth is `Active v1 Readiness Goal` below.

This section records the verification state reached by the preceding 49-task
v1-prep checkpoint. It is intentionally retained for auditability, but its
baseline counts and commit evidence must not be read as the current 54-task
comparison state.

### Checkpoint Objective

Keep `main` honest as post-v0 active development: frozen v0.0 evidence remains
auditable, the 49-task v1-prep checkpoint remains inspectable, the active
54-task split does not treat those model runs as current, and every remaining
v1/community-benchmark gap is visible rather than implied away.

### Verification Checklist

- [x] Active goal/checklist in this file names the exact perfection criteria.
  Evidence: this section defines the pass objective, verification checklist, and
  open gaps that must remain unchecked until real evidence exists.
- [x] Docker smoke fails clearly when Docker CLI exists but the daemon is not
  available locally.
  Evidence: direct local call to `run_container_smoke(ROOT)` prints Docker client
  information and exits with `docker daemon is required for
  --include-container-smoke; start Docker and rerun validation` when the daemon
  socket is unavailable.
- [x] GitHub Actions no longer relies on the deprecated Node 20 default for
  JavaScript actions.
  Evidence: workflow opts into Node 24 and uses Node-24-native
  `actions/checkout@v6` and `actions/setup-python@v6`; GitHub Actions run
  `27083608925` passed on `main` with no Node 20 annotation in the watch output.
- [x] Focused tests for changed validation behavior pass.
  Evidence: `python3 -m unittest discover -s tests -p
  'test_validate_public.py'` and the full test suite pass.
- [x] Full public validation without local Docker smoke passes.
  Evidence: `python3 scripts/validate_public.py --include-scripted-baseline`
  passed on commit `ede97d01ecb708feb24985dec0fc3b51d37ac7d1` for the then-current
  49-task public split.
- [x] Docker-backed public validation is confirmed by GitHub Actions on `main`.
  Evidence: GitHub Actions run `27083952334` passed on `main` for commit
  `ede97d01ecb708feb24985dec0fc3b51d37ac7d1`.
- [x] Privacy scan shows no tracked private holdouts, raw results, captures, or
  panel logs.
  Evidence: `git ls-files tasks_private/holdout results captures
  docs/reviews/panel-logs` returns no tracked paths.
- [x] Tracked working tree is clean after generated validation artifacts are
  removed.
  Evidence: generated `results/validation-scripted-baseline/...` output was
  removed after validation, leaving no tracked working-tree changes before the
  pushed implementation commit.
- [x] Commit is authored as `bmendonca3` and pushed to `main`.
  Evidence: commit `ede97d01ecb708feb24985dec0fc3b51d37ac7d1` is authored and
  committed as `bmendonca3 <bmendonca3@users.noreply.github.com>` and is present
  on both `origin/main` and `origin/v1-task-expansion`.
- [x] The 49-task checkpoint had one repeated no-tools model-family baseline.
  Evidence: `kiro-claude-haiku-4-5-current-public-49` is registered with two
  then-current public split Haiku runs, `task_count: 49`, `run_count: 2`,
  `harness_type: no-tools-model`, and explicit non-leaderboard claim-boundary
  text.
- [x] The 49-task checkpoint had five repeated no-tools model families.
  Evidence: `kiro-claude-haiku-4-5-current-public-49`,
  `kiro-claude-sonnet-4-6-current-public-49`,
  `kiro-qwen3-coder-next-current-public-49`, `kiro-glm-5-current-public-49`,
  and `kiro-claude-opus-4-6-current-public-49` were registered as current public
  split no-tools model baselines at that checkpoint, with `run_count: 2`, distinct
  `run_artifacts`, `task_count: 49`, matching model labels, benchmark commit
  `1eaac973ffe5229dad5796b9a5b144fa3af37a3a`, and non-leaderboard
  claim-boundary notes.
- [x] The 49-task checkpoint had repeated live HTTP tool-agent runs with
  target-request correlation.
  Evidence: `kiro-live-tool-agent-sonnet-current-public-49` was registered as a
  current public split tool-agent baseline at that checkpoint, with two
  `claude-sonnet-4.6` Kiro live HTTP runs from benchmark commit
  `3d4293cd24305ad410ddad8cb68654bf10adc9ff`. Run
  `20260607T071431380750Z-fc6636f1` reports `task_count: 49`,
  `model_tool_plan_artifact_count: 49`, `per_task_tool_probe_artifact_count:
  49`, `target_request_correlated_task_count: 49`,
  `target_request_coverage_rate: 1.0`, `planner_failure_count: 0`,
  `planner_parse_error_count: 0`, and `executed_tool_probe_total: 124`. Run
  `20260607T072056877797Z-2be17ca0` reports the same 49/49 artifact and
  correlation counts, `target_request_coverage_rate: 1.0`, zero planner/parser
  failures, and `executed_tool_probe_total: 126`.
- [x] Baseline registry and release gates recognized the 49-task checkpoint.
  Evidence: `python3 scripts/validate_baseline_registry.py` passes with
  `baseline_count: 23`, `current_public_model_family_count: 6`,
  `repeated_model_baseline_count: 6`, `has_current_public_tool_agent_baseline:
  true`, `v0_baseline_ready: true`, `v0_release_snapshot_ready: true`, and no
  unmet baseline requirements. Strict `python3 scripts/validate_v0_release.py`
  passes with all 8 gates green and `v0_ready: true` in this maintainer checkout.
- [x] The 49-task public tool-agent checkpoint was committed, pushed, and CI
  verified.
  Evidence: commit `fd0bfcb41e0f8db0b52a0a7f56106c9c2e2e416b` (`Add current
  public tool-agent baseline evidence`) is authored as `bmendonca3`, pushed to
  both `origin/v1-task-expansion` and `origin/main`, and GitHub Actions run
  `27086361745` passed the `Validate AuthZBench-SaaS` workflow on `main`.

### Open Perfection Gaps

These remain intentionally open until real evidence exists:

- [x] Boundary-reasoning calibration study completed and reflected in the paper.
  Evidence: `docs/boundary-reasoning-calibration-study.md` audits both
  then-current 49-task live HTTP `claude-sonnet-4.6` tool-agent runs, covering all 30
  exploit-proven vulnerable task-run cases where boundary reasoning failed.
  `docs/authzbench-saas-v1-prep-technical-report.md` and
  `paper/ieee-sp/main.tex` now state the calibrated interpretation: exploit
  replay often succeeded, but submitted boundaries did not preserve the
  oracle-compatible vocabulary required by `score-policy-v1`.
- [ ] External AppSec, benchmark/evals, and AI-agent/tooling review lanes
  completed.
- [x] Rotating private holdout and hosted or fully containerized submission
  governance defined for v1/community use.
  Evidence: `docs/v1-community-submission-governance.md` defines submission
  states, eligibility gates, hosted-runner flow, fully containerized flow,
  private-pack rotation, stale-score handling, tie policy, attestation,
  appeals, deprecation, and the minimum v1 launch bar. It links to
  `docs/holdout-rotation-protocol.md` and `artifact/run-bundle.md` while
  preserving the claim boundary that hosted/containerized execution is specified
  but not yet implemented.

### Externally Blocked Gap

- External review remains open. Evidence packet:
  `docs/reviews/external-review-packet.md`. Tracker:
  `docs/reviews/external-review-summary.md`. Blocker: completion requires real
  independent AppSec, benchmark/evals, and AI-agent/tooling reviewers to return
  findings or explicit no-finding dispositions; local repository work cannot
  honestly manufacture that evidence.
- Release-grade hosted/containerized execution also remains infrastructure
  dependent. Repository and CI work can prove the submitter-isolation mechanism
  with a rehearsal pack, but the release gate requires the same path to run on
  the intended maintainer platform against the real active private-pack
  fingerprint. Rehearsal evidence must not be promoted into release evidence.

## Active v1 Readiness Goal

Status: active as of 2026-06-07. This is the current source of truth for the
remaining work needed before any `v1`, hosted leaderboard, or community-ready
claim is fair.

Do not mark this goal complete until every checklist item below is checked with
fresh evidence, and until strict `python3 scripts/validate_v1_readiness.py
--release-evidence <external-json>` exits successfully on the release candidate
commit. Until then, the correct claim is stable `v1-prep`, not `v1-ready`.

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
    status 0 and reports two passed gates plus nine unmet gates after the
    54-task expansion invalidates current-comparison status for 49-task model
    and tool-agent rows;
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
  - `python3 scripts/validate_baseline_registry.py` currently reports
    `current_public_model_family_count: 0` and
    `has_current_public_tool_agent_baseline: false`;
  - the readiness gate is therefore correctly red even though the historical
    49-task checkpoint above was green.
  Completion is tracked by `Refresh model evidence after the 54-task
  promotion` below; do not mark this item complete until its repeated model and
  live HTTP acceptance evidence is satisfied.

### External Review Gate

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
  - public validation uses `--public-view` so ignored private checkout state
    cannot change clean-clone expected output;
  - focused rotation, duplicate-path, fingerprint, and public-view tests pass in
    `tests/test_v1_readiness_validator.py`.

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
  - `claude-haiku-4.5`, `claude-sonnet-4.6`, `qwen3-coder-next`, `glm-5`, and
    `claude-opus-4.6` no-tools families each have two runner-emitted 54-task
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
  - benchmark source commit:
    `ac020ad75e31c5b1c525a0fc52778bcfce89fafe`;
  - `python3 scripts/generate_paper_tables.py && git diff --exit-code --
    paper/shared` passed;
  - `python3 scripts/generate_benchmark_charts.py && git diff --exit-code --
    docs/assets/benchmark-charts` passed;
  - `latexmk -pdf -interaction=nonstopmode -halt-on-error
    paper/ieee-sp/main.tex` exited zero and generated `main.pdf`;
  - the LaTeX log contained non-fatal font and underfull-box warnings, but no
    unresolved citation/reference, LaTeX error, fatal stop, or overfull-box
    match;
  - two independent Kiro Opus 4.8 read-only audits reviewed validator safety
    and goal completeness; their valid findings were incorporated;
  - `scripts/validate_v1_readiness.py` requires `evidence_scope:
    release_candidate` and
    `upstream_review_and_infrastructure_complete: true` before the final paper
    gate can pass, and independently cross-checks the live external-review,
    hosted-execution, and private-rotation gates instead of trusting that
    evidence field alone.
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
  - `artifact/expected-output/v1-readiness-public-view.json` records the
    deterministic clean-clone state with two passed and nine unmet gates after
    the 54-task expansion made 49-task model/tool-agent evidence stale;
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

## Current Goal Statement

Build AuthZBench-SaaS into a public benchmark that serious AI-agent and
application-security researchers can trust for SaaS authorization testing. The
work should move through normal SDLC checkpoints: goal and roadmap design,
target/task expansion, scorer and runner hardening, baseline refreshes,
sectional panel review, privacy validation, fresh-clone validation, and
release-readiness review. The repository should include a clear roadmap and
should use commits that match those checkpoints instead of burying the work in
one large change.

The ambition is to become a top benchmark, but the label has to be earned. The
current repo has crossed the v0.0 release threshold with protected private
evidence, live-target proof, repeated real model and agent baselines,
anti-gaming controls, clean packaging, and review artifacts. It still needs v1
scale, rotating holdouts, external review, and hosted or fully containerized
submission infrastructure before stronger community-benchmark claims are fair.

## Operating Contract

### Outcome

Turn AuthZBench-SaaS from a promising alpha into one of the strongest public
benchmarks for multi-tenant SaaS authorization reasoning. A strong score should
mean an agent can reason through actors, roles, tenants, organizations, objects,
API tokens, audit logs, admin settings, sharing links, secure controls, and
replayable HTTP evidence.

The benchmark should reward agents that:

- prove vulnerable behavior with replayable backend evidence
- name the correct actor, role, tenant, organization, object, and scope boundary
- distinguish allowed access from broken authorization
- avoid findings on secure controls
- stay inside the benchmark policy and target scope

The benchmark should penalize agents that:

- guess from route names or task wording alone
- submit polished prose without replayable proof
- over-report every sensitive endpoint
- rely on memorized public manifests instead of live reasoning
- ignore tenant, role, token, or object boundaries

### Verification Surface

Progress toward a release-worthy benchmark must be backed by concrete evidence:

- unit tests, manifest validation, compile checks, and Docker Compose validation
- deterministic scorer transcripts and scripted sanity baselines
- live HTTP target smoke tests and target-side request-log correlation when
  Docker is available
- repeated real model or agent baselines with exact commands, model labels,
  commit SHAs, result bundles, and variance notes
- private holdout validation outside public Git history
- privacy scans proving no secrets, personal paths, private holdouts, cookies,
  tokens, or unrelated local data are committed
- sectional panel review notes under `docs/reviews/` for major benchmark areas
- fresh public-clone validation before public release claims

### Top-Benchmark Bar

To be worth citing, AuthZBench-SaaS has to do more than run. It has to be
harder to game than a task list, clearer than a demo repo, and fair enough that
model comparisons mean something.

The benchmark should be judged on five qualities:

- realism: tasks should resemble real SaaS authorization mistakes without using
  real customer, employer, school, bounty, or personal data
- proof: successful findings should replay against the backend, not just read
  well as vulnerability reports
- controls: safe behavior should be tested as carefully as vulnerable behavior
- comparability: model and agent runs should preserve exact commands, settings,
  commit SHAs, result bundles, and repeated-run notes
- resilience: private holdouts, seeds, route aliases, decoys, and protected
  execution should reduce the value of memorizing public manifests

### Constraints

- Keep the public repo honest as a released v0.0 artifact until v1 gates pass.
- Keep the benchmark focused on SaaS authorization, not generic CTF coverage.
- Keep synthetic data synthetic; do not copy real customer, employer, bug bounty,
  school, or personal data.
- Keep private holdouts out of public Git history.
- Do not let headline scores hide false-positive behavior.
- Do not present one-off model runs as stable leaderboard results.
- Do not commit raw panel logs, local captures, result bundles, secrets, or
  personal/private information.

### Boundaries

Work should stay inside the benchmark repo and its ignored local evidence
folders. Public-facing changes belong in docs, tasks, apps, scorer/harness code,
tests, baseline summaries, and release artifacts. Externally visible GitHub work
must use the public `github.com` repo, the configured maintainer author identity,
and normal commits at meaningful SDLC checkpoints.

High-blast-radius actions require explicit review before proceeding: publishing
a release tag, changing leaderboard scoring semantics, exposing private holdouts,
rewriting public history, adding real-world data, or changing external GitHub
state beyond ordinary commits and pushes for this repo.

### Iteration Policy

Improve the benchmark section by section:

1. Define the section's purpose and threat model.
2. Add or update target behavior, tasks, scorer logic, docs, and tests.
3. Run focused local verification.
4. Run sectional panel review and record accepted/rejected findings.
5. Fix valid findings.
6. Refresh baselines or status docs when behavior changes.
7. Commit at a natural SDLC checkpoint with a clear message.
8. Re-run public validation and privacy scans before pushing.

If a section cannot be fully validated because Docker, model quota, credentials,
or private holdout infrastructure is unavailable, record the gap plainly and
continue with the strongest safe local work.

### Blocked Stop Condition

Do not claim the benchmark is leaderboard-ready, v1, community-scale, or
top-tier if any core proof surface is missing: rotating private holdouts,
third-party runs, repeated private tool-agent evidence, hosted/containerized
submission handling, variance analysis, external review, or public-clone
validation for the relevant release. If a blocker requires unavailable
infrastructure or user action, record the exact blocker, preserve the evidence
gathered, and keep the goal active rather than downgrading the standard.

## v0 Release Goal

The real `v0` goal was to ship the first version that other researchers can use
without mentally discounting every headline score. The `v0.0` release now
satisfies this Level 1 goal while leaving v1/community-benchmark work open.

To call the project `v0`, the repo should have:

- 6 synthetic SaaS apps
- 40-50 public tasks
- 20-30 private holdout tasks outside public Git history
- at least 40 percent secure controls, counting both denial controls and
  authorized-allow controls
- at least 10 authorized-allow controls that prevent "everything is a bug"
  strategies
- route aliases, decoys, seeded IDs, and multi-seed private holdouts
- target/proxy-side request logs correlated into per-task result artifacts
- repeated baselines across at least five real model or agent families
- one or more tool-equipped agent baselines, not only no-tools model runs
- CI, live Docker validation, and fresh public-clone validation
- sectional panel review for goal, roadmap, and release criteria; task realism
  and vulnerability/control mix; scorer, runner, request-log correlation, and
  live-target proof; baseline methodology and leaderboard schema; holdout,
  contamination, and anti-gaming design; and privacy scan, packaging, and final
  release readiness
- public docs that clearly separate alpha results, public-split development
  results, and private-holdout leaderboard results

Those gates are now met for the v0.0 release. The honest next label remains
released v0.0 until v1-scale evidence is added.
