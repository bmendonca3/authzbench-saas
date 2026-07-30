# Qwen Phase 0 Remediation Packet

## Objective

Implement the documentation and regression portion of AuthZBench-SaaS
T001-T004 after the parent/DAD's source-binding decision.

The desired outcome is that the repository distinguishes the completed
historical `v1.0-internal` snapshot from the readiness of current `main`, and
states the exact evidence refresh needed before current `main` can become a
new release candidate.

## Parent/DAD Decision

Do **not** make the readiness gate pass by expanding the post-source allowlist,
re-pinning a SHA, editing historical evidence, or weakening validation.

Direct parent evidence at canonical HEAD
`acb6434c4bb25cce53a1a9f4eb31c869986743ca` shows:

- public-view readiness is honestly 9/10;
- `paper_and_artifact_readiness` is the one failed gate;
- the source evidence is pinned to
  `54e87b04ce67a5cbc163dfb64cd2c8f63c6bdeef`;
- 263 paths changed after that source and are outside
  `PAPER_POST_SOURCE_EVIDENCE_ONLY_PATHS` and
  `POST_SOURCE_EVIDENCE_ONLY_PREFIXES`;
- those paths include canonical runner, core, score-policy, baseline, schema,
  test, and validation changes, not merely documentation or generated Harbor
  evidence; and
- the old source SHA is also bound to historical submission-runner smoke and
  repeated private leaderboard rows, so changing the SHA without fresh runs
  would fabricate evidence.

Therefore the validator and expected public-view fixture are behaving
correctly. The proper local repair is to make the current status/roadmap
truthful and regression-test that distinction. A future source freeze and
evidence refresh remains required work.

## Target And Baseline

- Repository: `/Users/brianmendonca/Documents/authzbench-saas`
- Branch: `main`
- Required HEAD and `origin/main`:
  `acb6434c4bb25cce53a1a9f4eb31c869986743ca`
- The only pre-existing worktree entry is the untracked
  `specs/005-authzbench-completion/` packet. Preserve it and do not edit it.
- Do not touch linked worktrees.

Stop without editing if tracked files are already modified or the baseline
does not match.

## Role And Boundaries

- Qwen is the sole implementation executor; Codex is parent/DAD and final
  verifier.
- Use no nested delegation.
- Writes are allowed only to:
  - `docs/status.md`
  - `ROADMAP.md`
  - `tests/test_v1_ready_doc_alignment.py`
- Inspect other tracked repository files read-only as needed.
- Do not edit the validator, paper-readiness JSON, expected-output fixture,
  smoke/private evidence, source/task/scorer/baseline files, or the completion
  packet.
- Do not commit, push, publish, install dependencies, access credentials or
  private task bodies, use external services, or perform destructive cleanup.

## Required Implementation

1. Update `docs/status.md` as of 2026-07-28 so its opening/current-state
   language says all of the following without overclaiming:
   - `v1.0-internal` remains a completed historical internal/non-external
     snapshot;
   - current `main` is not a freshly validated release candidate;
   - current public-view readiness is 9/10 at the audited HEAD because
     `paper_and_artifact_readiness` correctly rejects release-affecting changes
     after the old benchmark source pin;
   - the old source, smoke, private rows, paper verification, and CI remain
     historical evidence, not current-HEAD evidence; and
   - a new current candidate requires an explicit source freeze plus fresh,
     matching local/container smoke, private rows, paper tables/charts/LaTeX,
     expected-output, and CI/release evidence. External/Kaggle/launch gates
     remain separate and incomplete.
2. Reconcile the corresponding current-state and Milestone 5 wording in
   `ROADMAP.md`. Preserve the historical milestone, but add an explicit open
   current-HEAD evidence-refresh item/dependency. Do not relabel external v2
   gates as local work.
3. Add narrow assertions in `tests/test_v1_ready_doc_alignment.py` that prevent
   the status and roadmap from again presenting the historical milestone as
   proof that current `main` is fully ready. Prefer durable semantic phrases
   over asserting the transient count of changed paths.
4. Keep the edit concise and consistent with the existing docs' voice. Do not
   duplicate large readiness inventories.

## Required Verification

At minimum run:

```text
python3 -m pytest -q tests/test_v1_ready_doc_alignment.py
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view --expected-output artifact/expected-output/v1-readiness-public-view.json
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
git diff --check
```

The readiness command must continue to match the expected 9/10 incomplete
fixture. A change that makes all ten gates pass is a failure of this packet.

Before returning, inspect the complete diff and confirm that only the three
allowed tracked files changed.

## Return Contract

Return:

1. verdict (`completed`, `partial`, or `blocked`);
2. every changed file;
3. concise rationale for the historical-snapshot/current-HEAD distinction;
4. exact commands and results;
5. any skipped check and reason;
6. blockers/residual risk; and
7. confirmation that no other file, linked worktree, external resource,
   commit, or remote changed.
