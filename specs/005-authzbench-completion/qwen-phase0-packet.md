# Qwen Phase 0 Execution Packet

## Objective

Implement only AuthZBench-SaaS tasks T001-T004 in the canonical checkout:

- reconcile the current authoritative local status against stale roadmap,
  paper-readiness, and generated readiness surfaces;
- repair only demonstrably stale local source/count/policy metadata;
- add the narrow regression coverage needed to prevent that drift; and
- run focused local checks and report their exact results.

The desired result is a truthful local readiness surface. It must not convert
missing external evidence into a pass.

## Target And Baseline

- Repository: `/Users/brianmendonca/Documents/authzbench-saas`
- Branch: `main`
- Required starting HEAD:
  `acb6434c4bb25cce53a1a9f4eb31c869986743ca`
- Required starting `origin/main`: the same SHA
- Pre-existing local work: the untracked
  `specs/005-authzbench-completion/` orchestration packet. Preserve it and do
  not edit it.
- Linked worktrees are out of scope and must not be touched:
  `/Users/brianmendonca/Documents/authzbench-saas-hardening` and
  `/Users/brianmendonca/Documents/authzbench-saas-kaggle-harbor`.

Stop without editing if the branch, HEAD, or starting tracked-file status does
not match this packet.

## Role And Runtime Contract

- Executor: Qwen Model Studio model `qwen3.7-plus`.
- Parent/DAD and final verifier: Codex.
- Sandbox: workspace-write in the canonical repository only.
- Context handoff: this self-contained packet; no inherited conversation.
- Concurrency: one executor.
- Descendants/nested delegation: forbidden.
- Qwen may make ordinary reversible edits inside the allowlist below and run
  local read-only checks. Qwen must not commit, push, publish, send messages,
  access credentials/private task bodies, install dependencies, start paid or
  hosted runs, edit remote resources, or perform destructive cleanup.

## Allowed Inspection And Write Surface

Qwen may inspect any relevant tracked repository file read-only. Writes are
limited to the smallest necessary subset of:

- `ROADMAP.md`
- `docs/status.md`
- `docs/v1-paper-readiness.json`
- `artifact/expected-output/v1-readiness-public-view.json`
- `scripts/validate_v1_readiness.py`
- `tests/test_v1_readiness_validator.py`
- `tests/test_v1_ready_doc_alignment.py`

Do not edit anything under `specs/005-authzbench-completion/`; the parent owns
task status, traceability, and durable orchestration state. If a correct fix
requires another file, stop and report the exact file and reason instead of
widening the write set.

## Truth And Evidence Constraints

- Determine the intended source-binding semantics from the validator, tests,
  generators, repository history, and current readiness documents before
  changing a SHA. Do not blindly replace the paper source SHA with `HEAD`.
- Preserve historical CI runs and their source bindings as historical
  evidence. Do not relabel an old run as validation of a newer commit.
- Do not invent, infer into existence, or promote evidence for CI, independent
  review, SaaS-provider review, Kaggle executor parity, organization/ownership,
  privacy/private sync, hosted operation, launch, publication, or leaderboard
  readiness.
- Preserve the public/private boundary: 63 public tasks, 48 private-summary
  tasks, 111 total.
- Treat current dates and SHAs as metadata only when directly supported by the
  repository state. A date refresh must not imply a newly completed review or
  run.
- Existing claims such as
  `upstream_review_and_infrastructure_complete` must be validated against their
  documented scope and current validator semantics; do not strengthen them.
- Preserve user work and safeguards. Do not weaken validators or tests merely
  to make readiness pass.

## Required Work

1. Verify the target/baseline and identify every concrete contradiction among
   the current source, `ROADMAP.md`, `docs/status.md`,
   `docs/v1-paper-readiness.json`, the expected public-view artifact, validator,
   and tests.
2. Implement the smallest truthful repair for T001-T002.
3. Add or update narrowly targeted regression coverage for the repaired drift
   (T003). The test must fail for the prior bad state and protect the intended
   semantics.
4. Regenerate or edit the expected-output artifact only through the repository's
   supported behavior and only when its new content is directly justified.
5. Run the focused verification below (T004). If an unrelated pre-existing
   failure blocks a command, record the exact failure without working around it.
6. Before returning, inspect `git status --short`, `git diff --check`, and the
   complete diff. Revert no user work. Stop and report if any file outside the
   write allowlist changed.

## Focused Verification

Use repository-native invocations where they differ, but at minimum attempt:

```text
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
python3 -m pytest -q tests/test_v1_readiness_validator.py tests/test_v1_ready_doc_alignment.py
git diff --check
```

Also run any narrow generator/fixture comparison required to prove the expected
public-view artifact matches actual validator output. Do not run a hosted,
credentialed, paid, private-data, or external-platform check.

## Return Contract

Return a concise implementation report containing:

1. verdict (`completed`, `partial`, or `blocked`);
2. every changed file;
3. the contradiction/root cause and why the chosen semantics are correct;
4. exact commands run and pass/fail results;
5. any check not run and why;
6. blockers and residual risk;
7. confirmation that no out-of-allowlist file, linked worktree, external
   resource, commit, or remote was changed.

Do not mark T001-T004 complete yourself. The parent will inspect the complete
diff, rerun the gates independently, and accept, correct, or reject the lane.
