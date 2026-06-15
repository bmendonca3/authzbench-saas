# AuthZBench-SaaS External Validation and Coverage Expansion Goal

> Source of truth. Re-read at the start of every turn.

## Purpose

After the v1.0-internal release, the next milestone for AuthZBench-SaaS is to
move toward a community-grade benchmark with external validation and broader
coverage. This goal defines the core objectives and deliverables for the next
pull request. The focus is on adding rigor, realism, and reviewer-ready
artefacts while preserving the strong claim-boundary discipline established in
the v1 release.

## Claim Boundary

- This goal does NOT authorize a claim of external acceptance, third-party
  endorsement, hosted production leaderboard, or production vulnerability
  discovery.
- All artifacts remain community-grade preparation, not external validation.
- `v1_ready` stays `false` until strict release evidence exists.
- v1 release-candidate gates (see `docs/goal.md`) remain unchanged.

## Objectives

### 1. Refresh and expand baselines
- Rerun the full 60-task public split across at least three no-tools models
  (e.g., GPT-4-o, Claude 3, Gemini) and two distinct tool-agent scaffolds.
- Capture per-task scores, mean +/- standard error and confidence intervals.
- Mark every existing baseline as `historical` if it does not come from
  fresh runs.
- Add a script and CI gate that fails if a baseline entry lacks
  `model_name`, `model_version`, `scaffold_name`, `run_date`, or
  `evidence_status`.

### 2. Publish the task taxonomy and oracle audit artefacts
- Finalize the taxonomy generator to produce JSON and Markdown overviews
  listing each task by app/domain, vulnerability type, boundary type, control
  type, route pattern and difficulty.
- Finalize the oracle audit generator to flag any task missing an objective,
  oracle status/body, expected boundary, denial control, or authorised-allow
  control.
- Commit both artefacts and make them part of the public validation workflow.
- Add a CI test that fails when a task is missing any mandatory field.

### 3. Implement adversarial scorer tests
- Create a comprehensive test suite for negative submissions, including
  empty findings on vulnerable tasks, report-all-routes strategies, wrong
  actor/tenant proofs, malformed JSON and mixed valid/invalid findings.
- Extend the scorer to expose diagnostic fields such as `exploit_proven`,
  `boundary_semantic_match`, and `boundary_schema_mismatch` and assert that
  each case is classified correctly.
- Add a CI gate so that any future change to the scorer cannot break these
  tests unnoticed.

### 4. Add boundary-synonym support
- Introduce a `boundary_aliases` field in task manifests to allow alternate,
  semantically equivalent boundary labels (e.g., tenant <-> cross-tenant,
  alpha tenant <-> tenant_alpha).
- Update the scorer to mark a submission as `boundary_semantic_match` when
  an alias is used while still enforcing the official evaluation keys.
- Document this behaviour in `docs/score-policy.md` to help reviewers
  interpret diagnostic outputs.

### 5. Define and document the private holdout lifecycle
- Write `docs/private-holdout-lifecycle.md` to describe how private task
  packs are created, validated, rotated and retired. Include roles (active,
  shadow, retired), who can inspect them, and how fingerprints are
  generated.
- Introduce JSON metadata fields for each pack (e.g., `pack_id`, `role`,
  `created_at`, `activated_at`, `retire_after_submissions`, `fingerprint`).
- Add a CI gate that ensures only active packs are used for scoring private
  submissions.

### 6. Prepare external review packets
- Generate three reviewer packets: one for AppSec reviewers (focusing on
  task realism and oracle correctness), one for benchmark/evals reviewers
  (focusing on methodology, leakage policy and scoring), and one for
  agent/tooling reviewers (focusing on harness fairness and tool budgets).
- Create structured review forms as JSON schemas to capture reviewer
  comments and ratings.
- Document the review process and how reviewer feedback will be incorporated
  into future releases.

### 7. Clarify leaderboard and submission governance
- Finalize `docs/leaderboard-schema.md` with eligibility tiers (sanity,
  public diagnostic, private candidate, private eligible, external
  verified) and anti-gaming rules.
- Implement a submission bundle validator that checks for transcripts,
  environment metadata and tool-budget compliance. Submissions lacking
  these fields or exceeding defined limits should fail.
- Add documentation explaining how to prepare and submit a run for each
  tier, emphasising that only private-eligible runs are considered for the
  private leaderboard.

### 8. Extend the task suite for deeper coverage
- Design and implement at least six new tasks: two multi-step discovery
  tasks where the agent must discover IDs through authorised calls; two
  stateful tasks involving invites, reassignments or token rotation; and
  two new vulnerability categories (e.g., team membership boundary,
  entitlement downgrade, share-link expiry).
- For each new task, provide a realism note mapping it to a real SaaS
  pattern and an OWASP/CWE reference.
- Update the taxonomy and oracle audit scripts to include the new tasks.

## Status (Net-New Items)

| # | Item                                                       | Status |
|---|------------------------------------------------------------|--------|
| 1 | Baseline CI gate for required fields                       | TBD    |
| 2 | Task taxonomy + oracle audit artifacts + pytest gate       | TBD    |
| 3 | Adversarial scorer tests + diagnostic fields + CI gate    | TBD    |
| 4 | boundary_aliases + score-policy tightening                | TBD    |
| 5 | Private-holdout lifecycle doc + metadata + CI gate         | TBD    |
| 6 | Three external review packets + JSON review forms          | TBD    |
| 7 | Leaderboard governance + submission bundle validator + howto | TBD |
| 8 | Six new tasks (discovery x2, stateful x2, vuln-cats x2) with realism/OWASP/CWE notes | TBD |

## Deliverables

The next pull request is considered complete when the following artefacts
and changes are delivered:

1. An updated baseline registry containing fresh runs with variance reporting
   and historical entries marked accordingly.
2. Published taxonomy and oracle audit artefacts included in the public
   validation process.
3. A comprehensive adversarial scorer test suite that passes under CI.
4. A revised scorer emitting diagnostic fields and supporting boundary
   synonyms.
5. A documented private holdout lifecycle with metadata and CI enforcement.
6. External review packets and structured review forms ready for independent
   reviewers.
7. A clear leaderboard governance document and a submission bundle
   validator.
8. An expanded task suite with corresponding documentation and updated
   audit scripts.

## Operating Rules

- Maintain `bmendonca3` authorship on all commits and authored-by
  references.
- Do not insert coding-agent-specific branding (`[codex]`, etc.) in code,
  commits, PRs, issues, or GitHub comments.
- Use a feature branch (`v1-claim-boundary-fixes` is the current
  candidate). Do not create new branches prefixed with `codex/`.
- Do not push, do not open a PR, do not commit unless the user explicitly
  asks.
- Use `humanizer` for any user-facing copy.
- All new artifacts must remain within the established claim boundary.
- Preserve determinism and reproducibility across public and private splits.
- Keep private task bodies, private manifests, raw private evidence,
  captures, credentials, and absolute local paths out of public commits.

## Verification Ladder

After every material change:

1. Run focused tests for the changed behavior.
2. Run the relevant validator for the affected gate.
3. Run `python3 scripts/validate_public.py` after shared validator, task,
   scorer, Harbor, artifact, or claim-boundary changes.
4. Run public-view v1 readiness and confirm `v1_ready: false` until strict
   release evidence exists.
5. Run `git diff --check`.
6. Run private-source and overclaim scans before public artifact handoff.
7. Confirm tracked private/raw path scan is empty.

## Reference Files (Existing Public Evidence)

- 49-task checkpoint:
  `docs/checkpoints/2026-06-07-49-task-v1-prep-checkpoint.md`
- v1 hardening history:
  `docs/checkpoints/2026-06-08-v1-readiness-hardening-history.md`
- External review packet (v1): `docs/reviews/external-review-packet.md`
- External review tracker: `docs/reviews/external-review-summary.json`
- Private holdout blocker/runbook: `artifact/private-holdout-operation-blocker.json`,
  `artifact/private-holdout-operation-runbook.json`
- Hosted submission smoke blocker/runbook: `artifact/submission-runner-smoke.json`,
  `artifact/hosted-submission-execution-runbook.json`
- Task scale roadmap: `artifact/v1-task-scale-roadmap.json`
- v1 internal goal: `docs/goal.md`
- v2 external-validation roadmap: `docs/v2-external-validation-roadmap.md`
