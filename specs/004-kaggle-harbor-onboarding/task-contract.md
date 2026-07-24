# Shaped Task Contract — Kaggle / Harbor Onboarding Completion

Evidence date: 2026-07-23
Spec Kit classification: full
Durable state: `GOAL_STATE.md`

## Outcome

Turn the July Google/Kaggle onboarding handoff into a Kaggle-reviewable
AuthZBench-SaaS benchmark package that:

1. answers the onboarding guide's benchmark-design questions;
2. follows the current public Kaggle Harbor starter contract;
3. proves local NOP and Oracle controls with inspectable verifier artifacts;
4. distinguishes local evidence from Model Proxy, Kaggle executor, platform,
   independent-review, organization, and launch evidence; and
5. leaves every credentialed or external action as an explicit approval gate.

The final benchmark should measure one clear authorization capability, use a
versioned public/private dataset strategy, run deterministic protected
verification, and be ready for a staged public leaderboard launch without
exposing private holdouts, credentials, or verifier-only data.

## Current Sources Of Truth

In priority order:

1. The current user request and exact local repository
   `/Users/brianmendonca/Documents/authzbench-saas`.
2. Nicholas Kang's July 22 email. Gmail metadata confirms that the email did
   not contain a file attachment; it linked the onboarding guide, the public
   starter repository, and the dedicated Google Chat space.
3. The user-provided 12-page DOCX,
   `[Ext] Onboarding guide for Kaggle customer benchmarks.docx`.
4. The public
   `Kaggle/kaggle-benchmark-harbor-starter-template` repository as observed on
   2026-07-23.
5. The current AuthZBench-SaaS implementation, design contract, generated
   three-task public pilot, and retained local Harbor jobs.

The onboarding relationship is the consult/advisory pathway unless Kaggle
explicitly assigns a Forward Deployed Engineer. A Google Chat invitation is
not an FDE assignment, platform acceptance, or launch approval.

## Context And Definitions

- The onboarding guide defines three top-level goals: write a benchmark design
  document, implement a working benchmark on Kaggle, and launch a public
  leaderboard.
- The guide asks the benchmark owner to define the capability and gap,
  standardized versus multiple harnesses, dataset size and task semantics,
  contamination controls and public/private splits, runtime and network
  requirements, agent inputs/tools/loop, Model Proxy routing, metrics,
  deterministic verification, alternative-solution acceptance, verifier
  isolation, maintenance ownership, organization, and launch plan.
- The current Harbor starter adds an executable contract: initialize the
  dataset and tasks; generate short-lived Kaggle Model Proxy credentials; verify
  the proxy; run NOP for reward `0.0`; run Oracle for reward `1.0`; run an LLM
  agent through the proxy; inspect `trial.log` and `verifier/ctrf.json`; and run
  the task through Kaggle's published Harbor executor image.
- The existing local pilot contains one vulnerable, one secure-denial, and one
  authorized-allow task. Twelve retained local Harbor 0.13.2 cells recorded
  repeated NOP `0.0` and Oracle `1.0`.
- That pilot is calibration evidence only. Three public tasks do not establish
  a statistically discriminating private leaderboard cohort.

## Acceptance

### Local acceptance

- One named implementation source and preserved dirty-worktree boundary.
- A design contract that answers every guide topic or records a concrete Kaggle
  question with an observable acceptance check.
- Generated task directories with `environment/`, `instruction.md`,
  `solution/`, `tests/`, and `task.toml`.
- A current Harbor dataset manifest using `[dataset]`,
  `[[dataset.authors]]`, and digest-backed `[[tasks]]`.
- Local content digests match Harbor 0.13.2's `harbor add` computation for the
  exact generated task trees.
- Every verifier run writes reward/score artifacts and
  `/logs/verifier/ctrf.json`.
- Each pilot task repeats NOP `0.0` and real Oracle `1.0`; the resulting jobs
  contain inspectable logs and verifier artifacts.
- Focused tests, generated-dataset validation, public-safety/secret scanning,
  and the strongest feasible public repository gate pass.

### External acceptance

- Kaggle CLI authentication and Model Proxy credentials are generated only
  with current user authorization and remain secret and short-lived.
- A proxy health check and one admitted LLM-agent run succeed with inspectable
  trajectory/verifier evidence.
- The same versioned pilot passes Kaggle's published Harbor executor with
  explained local/executor parity.
- The scored cohort has a reviewed minimum task count, cluster-disjoint
  public/private strategy, contamination controls, and independent
  methodology/AppSec/agent-tooling/SaaS-provider validation.
- A Kaggle organization is approved, a backup maintainer and launch tier/date
  are agreed, required messaging/assets are complete, and Kaggle separately
  approves publication.

## Not Sufficient

- An email link, Chat invitation, organization request, or public repository.
- A structural skeleton or old-format `dataset.toml`.
- NOP/Oracle rewards without `trial.log` and CTRF/verifier artifact readback.
- A local-only Harbor pass presented as Kaggle-hosted execution.
- A three-task public pilot presented as a statistically valid leaderboard.
- Placeholder `solve.sh`, empty-findings-only parity, forged response bodies,
  superficial keyword checks, or agent-visible verifier/oracle material.
- Passing unrelated tests, elapsed effort, or a launch plan without platform
  and independent-review evidence.

## Boundaries And Constraints

- Preserve all staged, unstaged, untracked, linked-worktree, and retained job
  evidence. Do not reset, clean, revert, delete, stash, or overwrite unrelated
  user work.
- Local code, tests, generated public artifacts, specs, and durable state are
  in scope.
- Do not commit, push, publish, upload, share private data, invite users, submit
  a Kaggle organization form, mint credentials, call paid models, send email or
  Chat messages, or change external state without a current explicit gate.
- Keep credentials, tokens, cookies, private task bodies, raw private traces,
  and proprietary assets out of source, logs, specs, and public artifacts.
- Preserve fail-closed scoring, verifier isolation, deterministic reward,
  policy-version boundaries, and public/private claim separation.
- The private GitHub-to-Kaggle notebook synchronization procedure is optional
  and becomes required only if the launch architecture chooses a private
  repository-backed Kaggle dataset.

## Ordered Work Packages

### WP0 — Reconcile the source of truth

- Owner: benchmark maintainer.
- Dependency: newest email, complete DOCX, current starter, current worktree.
- Acceptance: sources are dated; the no-attachment/link distinction and
  consult-pathway status are recorded; current local and external evidence
  layers do not conflict.
- Verification: Gmail metadata readback, DOCX page review, starter README and
  manifest review, `git status`, durable-state readback.
- Non-claim: source reconciliation is not Kaggle acceptance.

### WP1 — Freeze the benchmark design

- Owner: benchmark maintainer; Kaggle reviews unresolved platform questions.
- Dependency: WP0.
- Acceptance: capability, gap, harness, dataset, contamination, runtime,
  network, interaction, Model Proxy, scoring, verifier, maintenance, and
  launch topics are decisions or named questions with checks.
- Verification: design-contract checklist and requirement traceability.
- Non-claim: a design document is not an implemented hosted benchmark.

### WP2 — Close current-starter local compatibility

- Owner: benchmark maintainer.
- Dependency: WP1 and preserved local pilot.
- Acceptance: current digest-backed dataset manifest; CTRF on NOP and Oracle;
  repeated declared rewards; inspected job artifacts; no public-safety leaks.
- Verification: focused unit tests, Harbor manifest comparison, generated
  dataset validation, real local Harbor runs, artifact readback, secret scan.
- Non-claim: local compatibility is not Model Proxy or Kaggle-executor parity.

### WP3 — Exercise Model Proxy and Kaggle executor

- Owner: benchmark maintainer; Kaggle for infrastructure defects.
- Dependency: WP2 and explicit authority for authentication/model calls.
- Acceptance: short-lived proxy credentials; proxy health; one LLM-agent run;
  same source/task digests on Kaggle executor; explained parity or a precise
  platform blocker.
- Verification: redacted command log, `trial.log`, trajectory, CTRF, reward,
  resource behavior, source/task fingerprint.
- Approval gate: credentials, model call, executor access, and any Chat handoff.

### WP4 — Scale and independently validate

- Owner: benchmark maintainer plus independent methodology, AppSec,
  agent/tooling, and SaaS-provider reviewers.
- Dependency: stable WP3 pilot.
- Acceptance: versioned scored-cohort design, minimum discriminating count,
  cluster-disjoint public/private split, contamination review, full-set
  representative parity, and resolved blocking review findings.
- Verification: cohort manifest/schema, statistical plan, review records, full
  regression/parity evidence.
- Non-claim: the public three-task pilot does not close this package.

### WP5 — Organization and public launch

- Owner: benchmark maintainer and Kaggle.
- Dependency: WP4 plus platform approval.
- Acceptance: approved organization; primary and backup maintainers; selected
  launch tier; target date; messaging, technical summary, and social assets;
  privacy review; publication and leaderboard evidence.
- Verification: organization approval, written launch checklist, platform
  run/leaderboard URL, and final claim review.
- Approval gate: forms, invitations, uploads, publication, and outbound
  messages.

## Evidence And Adversarial Checks

- Fast loop: unit tests for dataset digesting, manifest structure, CTRF
  generation, reference solutions, and dataset validation.
- Regression control: malformed, missing, forged, wrong-actor, wrong-boundary,
  superficial, and alternative-valid submissions.
- Runtime control: NOP `0.0`, Oracle `1.0`, repeated determinism, verifier
  isolation, no direct provider egress, and no verifier-only material in agent
  artifacts.
- Final local gate: generated-artifact diff/readback, current starter
  comparison, focused tests, full feasible public validation, secret/path scan,
  `git diff --check`, Spec Kit convergence, and durable-state update.
- Adversarial completion question: what evidence would prove that a claimed
  Kaggle-ready state is only a local proxy? Require the missing Model Proxy,
  executor, cohort, independent-review, organization, and launch evidence to
  remain separately `blocked` or `not-run`.

## Blocked Stop Condition

Stop with the strongest verified local evidence when the next step requires
credential minting, authenticated Model Proxy use, a paid/model call, Kaggle
executor access, private repository or Drive sharing, an invitation, a form
submission, an email or Chat message, upload, publication, organization
approval, independent participants, or a platform decision. Report the exact
missing evidence and the smallest authorization or external response that
would unblock the next package.
