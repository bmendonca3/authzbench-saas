# AuthZBench-SaaS Improvement Roadmap — July 2026

Status: evidence-backed implementation plan; no benchmark or platform changes
were made as part of this audit.

## Verdict

AuthZBench-SaaS already has the bones of an unusually credible authorization
benchmark: deterministic backend replay, a strong secure-control mix, careful
claim boundaries, protected-holdout governance, and a substantial hardening
branch. The next jump in quality will not come from adding another broad model
row. It will come from making one clean source tree authoritative, freezing the
blinded measurement contract, closing the remaining safety/evidence/isolation
gaps, generating less memorizable task instances, and then running a
pre-registered multi-seed calibration study.

The clean `improve/evidence-backed-hardening` worktree at `aae81c0f` is the
right implementation base. It already fixes several severe defects still
visible in the named `main` checkout: participant-visible class labels,
exact-claim-gated boundary scoring, adapter failures that could become empty
findings, unverified empty control answers, and incomplete executable-source
provenance. Reimplementing those fixes would waste effort. The immediate task
is to review and land that work cleanly, then build the next protocol version
on top of it.

A fresh full Kiro run is **not warranted now**. Four comparable 63-task blinded
Kiro diagnostics already establish that the new protocol executes end to end,
while the audit found more consequential unresolved questions in the benchmark
itself. The next Kiro spend should occur only after the task/evidence/sandbox
contract changes and should begin with one bounded admission smoke per model
family.

## Evidence boundary

This plan distinguishes two repository states:

| Surface | State | How it is used here |
| --- | --- | --- |
| Named checkout | `main` at `f5c6a17`, with 38 pre-existing changed/untracked entries | Exact audit target and evidence of staged-document/baseline drift. Existing work is user-owned and must not be cleaned or overwritten. |
| Clean candidate | `improve/evidence-backed-hardening` at `aae81c0f`, clean and 18 commits ahead of `main` | Latest implementation candidate and source for scorer-v2, blinded evaluation, fail-closed adapters, provenance, Harbor packaging, and current validation. |
| Private split | 48 tasks, public-safe summaries only | Count, fingerprints, lifecycle, and governance may be audited; raw task bodies and raw private results remain out of scope. |
| External status | Gmail and Drive read-only checks through 2026-07-14 | No Kaggle reply after the 2026-07-10 follow-up; no acceptance, hosting approval, setup approval, or Gemini feedback is inferred. |

The public split contains 63 tasks across six synthetic SaaS apps: 27
vulnerable cases, 21 denial controls, and 15 authorized-allow controls. The
private count is 48, for a public-safe total scale of 111.

## What is already strong

- Backend replay verifies status and response evidence instead of trusting
  prose or a model grader.
- Controls are the majority of the public split and include both correct
  denial and correct allow behavior.
- Score-policy v2 removes the undeclared exact claim-string gate, uses bounded
  structured boundary normalization, rejects shotgun boundary lists, and keeps
  policy-v1 evidence historical.
- `authzbench.evaluate` uses opaque per-run case IDs, removes authored outcome
  labels from participant context, requires participant-selected control
  verification, separates completion from performance, and hashes the
  evaluator, scorer, runner, apps, and adapter source.
- Adapter, timeout, model-label, and parse failures fail closed in the clean
  candidate rather than becoming a successful empty submission.
- The repository is unusually disciplined about public/private, local/hosted,
  internal/external, and requested/effective-model claim boundaries.
- The host-review packet, Harbor package, validation scripts, and external
  reviewer intake structure are substantial and useful.

## Do not re-propose completed hardening

Several serious findings are real in the dirty `main` checkout but are already
addressed in the clean candidate. They should be treated as integration gates,
not new design work.

| Finding in staged `main` | Clean-candidate disposition | Remaining work |
| --- | --- | --- |
| Task IDs such as `*_control` reveal the class; the legacy runner exposes canonical IDs. | Fixed in `authzbench.evaluate` with opaque per-run IDs and neutral context. | Make the blinded evaluator the only promotable protocol and add a CI canary that an ID-only classifier has no signal. |
| Empty findings can receive control credit without participant evidence. | Fixed by required participant-selected control request and predicted-status verification; the empty-only regression test exists. | Deprecate legacy control accuracy for capability comparison. |
| Exact hidden claim text gates boundary credit. | Fixed by `score-policy-v2-boundary-normalization`; claim equality is diagnostic, not weighted. | Add a structured vulnerability taxonomy for analysis and task generation, not another fuzzy prose scorer. |
| Kiro/AGY command or parse failure can become `{"findings": []}` and exit successfully. | Fixed by fail-closed adapters/runners and offline v2 rescoring that preserves adapter/infrastructure failures. | Keep structural admission smokes and require complete failure telemetry for promoted rows. |
| Benchmark commit alone does not identify adapter/evaluator source. | Improved by protocol/source manifests and content hashes. | Add task-generator/schema/container digests to one explicit comparability key. |
| Current 63-task staged scores are distorted by the policy-v1 boundary defect. | Fourteen saved full-split submissions were rescored offline under v2 with derivation hashes; model execution was not repeated. | Land and independently verify the hardening candidate; never describe the rescores as fresh v2 executions. |

## Remaining measurement risks

These gaps remain material after the existing hardening work.

1. **Safety is not observed.** The 10% safety subscore still depends primarily
   on the participant voluntarily listing `out_of_scope_actions`. Target logs
   cover the synthetic targets but do not prove that all filesystem, process,
   or network behavior was in scope. Per-task working directories are not an
   operating-system sandbox.
2. **Evidence contracts are sparse.** Only 8 of 27 vulnerable tasks declare
   explicit `evidence_requirements`; 19 can still be credited from a single
   final request. The current structural quality gate reports no flags despite
   this measured gap.
3. **Public instances are memorizable.** All public seeds are fixed, manifests
   and app logic are public, and many vulnerability routes follow closely
   related alias/check-omission patterns.
4. **The effective sample is smaller than 63.** Tasks are nested in six apps,
   several claim families repeat, and mirrored variants are correlated. Simple
   task-level intervals overstate independence.
5. **Current empirical evidence is diagnostic.** The 14 tracked policy-v2 rows
   are offline rescores of preserved executions. The four newer blinded Kiro
   rows are single, dirty-source, requested-label-only diagnostics and all use
   Claude models. They are not a cross-family ranking study.
6. **Host integrations stop short of platform evidence.** Harbor has packaged
   local execution and six-task empty-findings parity, not full representative
   parity or platform acceptance. The repository has a Kaggle-like competition
   packet but no native `kaggle_benchmarks` / `@kbench.task` implementation.
7. **The research narrative is stale.** The IEEE paper, technical report,
   roadmap, citation metadata, host copy, and several readiness surfaces mix
   54-, 60-, 63-, and 111-task states and policy-v1/v2 semantics.
8. **Independent validation has not happened.** The AppSec,
   benchmark-methodology, and AI-agent/tooling lanes are all still pending; no
   SaaS-provider scenario validation is recorded.

## Priority roadmap

### P0 — Establish one publishable source and measurement contract

#### P0.1 Reconcile and land the hardening candidate

Owner: benchmark maintainer.

Affected surfaces: branch history, `authzbench/`, adapters, `baselines/`,
readiness artifacts, documentation, and CI.

Dependencies: preserve the dirty `main` checkout; review the complete candidate
delta from `b04751b` through `aae81c0f`.

Work:

- Treat the hardening worktree as the proposed source, not as automatically
  accepted merely because it is newer.
- Review score-policy-v2, the blinded evaluator, fail-closed adapters, offline
  rescore derivation, Harbor packaging, and source-provenance changes as one
  coherent measurement release.
- Reconcile the staged `main` baselines and untracked analyses against that
  release. Mark `docs/boundary-scoring-defect.md` resolved only after the
  corrected source and derived summaries are canonical. Update or archive the
  stale `docs/benchmark-quality-analysis.md`; it still claims that full-63
  model evidence does not exist and describes policy-v1 behavior as current.
- Repair and execute-test the baseline rerun runbook. The staged instructions
  still mix `no-tools` with the canonical `no-tools-model` harness label and
  contain a wildcard copy pattern that can collapse multiple summaries into
  one destination. Generate promotion commands from the registry schema
  instead of maintaining hand-copied shell snippets.
- Require a content-addressed run-bundle manifest for promoted evidence,
  including task results, submissions, model-output/failure records, target-log
  coverage, source manifests, and analysis outputs. A checksum manifest is an
  integrity handle, not an independent signature or attestation.
- Do not commit the untracked `test.sh` debug probe as a release artifact. If
  its scenario is valuable, convert it to a deterministic test that derives
  synthetic credentials and IDs from fixtures.

Acceptance:

- One clean candidate commit is the explicit benchmark source of truth.
- The complete public validator passes from that clean source, including all
  loopback and protected-evaluation tests.
- Registry validation recomputes every tracked aggregate and derivation hash.
- Every current result points to its source-execution SHA, target benchmark
  SHA, score policy, evidence contract, source hashes, and derivation method.
- The rerun runbook completes a fixture promotion without overwriting another
  run, and its harness labels validate against the registry enum.
- Old policy-v1/staged rows are visibly historical or superseded; no chart or
  public status page silently mixes policy versions.

Non-claim: landing this work does not turn offline rescores into fresh model
runs, make the benchmark externally validated, or establish platform
acceptance.

#### P0.2 Freeze `blinded-control-evidence-v2`

Owner: scorer/evaluator maintainer, with AppSec and evals review.

Affected surfaces: task schema, participant schema, scorer, evaluator,
container/runtime policy, run bundle, fingerprint, and tests.

Dependencies: P0.1.

Work:

- Publish canonical JSON Schemas for task manifests, participant submissions,
  control verification, vulnerable evidence chains, and run summaries. Generate
  participant documentation and examples from those schemas.
- Make the blinded evaluator the only path eligible for new comparison or
  registry promotion. Preserve the legacy runner for historical reproduction,
  with an explicit legacy label.
- Give all 27 vulnerable tasks an explicit proof contract. Each contract should
  state required actor, request sequence, state transition or postcondition,
  and permitted alternatives. Use deny-then-bypass evidence where it proves the
  causal boundary; use same-state postconditions for mutation tasks.
- Treat malformed proof entries as invalid instead of silently skipping them.
  Separate the concise submitted proof chain from the full exploration log so
  valid exploration is auditable without rewarding shotgun evidence.
- Move safety out of the weighted accuracy score until it is host-observed.
  In v2, report it as a protocol-compliance gate derived from sandbox, proxy,
  filesystem, process, and target-request telemetry. Retain participant
  self-report only as an honesty diagnostic.
- Execute agents in an OS-isolated environment with read-only benchmark source,
  a writable opaque task directory, a target-only network allowlist, resource
  limits, and complete egress/process telemetry. Add a malicious fixture that
  attempts source reads, parent-directory traversal, unapproved network access,
  and destructive methods.
- Extend the comparability key to include task-generator version, seed-set hash,
  task/participant JSON Schema hashes, score/evidence policy, evaluator and app
  source hashes, container image digest, adapter source, harness capabilities,
  CLI version, and requested model/effort. Record an effective backend model ID
  only when independently returned by the provider.

Acceptance:

- `27/27` vulnerable tasks have validated evidence contracts or a reviewed,
  machine-readable waiver; the target is zero waivers for promotion.
- Always-empty, ID-only, report-all, magic-claim, malformed-prefix,
  duplicate-proof, wrong-actor, wrong-victim, shotgun-boundary, valid-JSON-then-
  nonzero-exit, timeout, parse-failure, and malicious-escape canaries all yield
  their predeclared outcomes.
- An omitted self-report cannot earn safety; one observed out-of-scope action
  fails protocol compliance; a fully observed in-scope run passes.
- Any semantic mutation to the task generator, schema, scorer, evaluator, app,
  container, or adapter changes the comparability key.
- Documentation examples validate and round-trip through the production scorer.

Non-claim: an isolated local protocol is still not evidence of hosted operation
or real-production-SaaS safety.

#### P0.3 Create a single generated status and claim surface

Owner: release/documentation maintainer.

Affected surfaces: machine status, README, claim ledger, readiness checklist,
roadmap, host packet, charts, and paper tables.

Dependencies: P0.1 and the frozen v2 terminology from P0.2.

Work:

- Generate one versioned status snapshot from the task registry, baseline
  registry, readiness fixture, Harbor parity artifact, external-review tracker,
  and source commit.
- Make all public status surfaces consume that snapshot or fail CI when they
  disagree. Add semantic drift checks for task counts, policy version,
  evidence derivation, model families, Harbor level, external-review status,
  and source commit.
- Define a clear hierarchy:
  `README orientation -> docs/index role router -> generated status -> claim
  ledger -> forward roadmap`.
- Label historical goals, checkpoints, calibration plans, and release snapshots
  with the date and task/policy version they describe.

Acceptance:

- A deliberate task-count, score-policy, or external-status mismatch breaks CI.
- README, status, claim ledger, host packet, charts, and paper evidence table
  agree on `63 public / 48 private-summary / 111 total`, policy v2 disposition,
  current vs diagnostic rows, and Harbor/Kaggle status.
- The readiness validator distinguishes a fixture match from actual readiness
  in both exit behavior and user-facing output.

Non-claim: generated consistency proves internal coherence, not that the claims
have been independently validated.

### P1 — Increase construct validity and resistance to gaming

#### P1.1 Replace frozen public instances with versioned task generators

Owner: task-set maintainer.

Affected surfaces: all six apps, task manifests, public/private split tooling,
fingerprints, and contamination policy.

Dependencies: P0.2 schema and isolation contract.

Work:

- Separate task logic from run instances. Generate actor, tenant, object,
  route-alias, content, and decoy values from a host-held run seed.
- Keep stable public templates for reproducibility while withholding the scored
  instance seed until the run closes. Publish the seed and generated manifest
  after the public diagnostic window when appropriate.
- Ensure participant IDs, filenames, objective wording, and route names do not
  encode vulnerable/control class. Add semantic, not merely suffix-based,
  leakage tests.
- Add a structured task taxonomy: app, authorization dimension, vulnerability
  class, mechanism, statefulness, proof-chain type, control type, and cluster ID.
- Expand beyond alias routes and omitted checks into IDOR/predictable reference,
  nested-object authorization, search/pagination leakage, mass assignment,
  token/audience/scope confusion, indirect membership, stale sharing state,
  path normalization, and state-transition/TOCTOU families.
- Introduce variable-cardinality suites only after the scorer supports them:
  zero, one, and multiple valid findings among plausible decoys.

Acceptance:

- At least three generated instances per task template preserve the oracle while
  changing all participant-visible identifiers and content.
- A held-out leakage classifier using only prompt text, IDs, filenames, and
  route names has balanced accuracy whose 95% upper bound is no greater than
  `0.55` on generated instances.
- The quality gate reports evidence coverage, taxonomy/cluster coverage,
  mirrored variants, decoy strength, and reviewed waivers; it no longer returns
  “no flags” for the known 19-task evidence gap.
- Every task has an explicit cluster ID so analysis does not count mirrored
  cases as independent.

Non-claim: more generated variants do not automatically create more independent
constructs or establish real-world representativeness.

#### P1.2 Calibrate the task set before ranking models

Owner: evaluation lead and independent statistics reviewer.

Affected surfaces: study protocol, baseline registry, analysis scripts, charts,
and paper.

Dependencies: P0.2 and P1.1.

Work:

- Pre-register the population, hypotheses, primary metrics, cluster structure,
  model/harness inclusion criteria, retries, missing-run policy, and promotion
  threshold before execution.
- Treat infrastructure-invalid cells as missing execution evidence, never as an
  accuracy zero or control pass. Report completeness separately and do not
  impute missing accuracy.
- Use paired generated instances across models. Estimate uncertainty over task
  family and run seed, not only over 63 task rows. Report app-stratified results
  and use a cluster-aware bootstrap or hierarchical model; keep Wilson intervals
  as descriptive per-row diagnostics.
- Use a metric suite rather than one opaque rank: exploit-proven vulnerable
  recall, full-boundary recall, verified denial specificity, verified
  authorized-allow specificity, balanced authorization accuracy, discrimination
  index, invalid/infrastructure rate, protocol-compliance rate, and probe cost.
- Run deterministic negative controls first: oracle/scripted, always-empty,
  report-all, label/ID-only, shotgun, malformed output, deliberate timeout, and
  escape-attempt agents. Every control gets a predeclared expected profile.
- Pilot enough generated seeds and stochastic repeats to estimate variance,
  then choose the full matrix from a power/precision target. As a practical
  starting design, test three generated task-set seeds and two invocation
  repeats per admitted configuration, but expand or stop based on the
  predeclared interval-width criterion rather than that number alone.
- Adjust or avoid claims for multiple model comparisons. Do not publish ordinal
  rankings when paired intervals substantially overlap.

Acceptance:

- The study protocol is timestamped before model execution.
- All negative controls match their expected profiles.
- Every promoted model/harness row is complete on identical task-instance and
  protocol hashes, or is explicitly excluded with infrastructure evidence.
- Analysis can reproduce every point estimate and interval from task-level
  public-safe results.
- Tasks with persistent ceiling, floor, leakage, or near-zero discrimination
  are retired, revised, or retained with a documented purpose.

Non-claim: a small synthetic, clustered study should not be described as a
population-wide ranking of frontier security capability.

### P1 — Build real host paths without conflating them

#### P1.3 Native Kaggle Benchmarks task

Owner: platform integration maintainer.

Affected surfaces: new native Kaggle task package, local tests, host docs, and
release bundle.

Dependencies: frozen evaluator/schema; current Kaggle clarification is helpful
but local prototyping does not require an external write.

Work:

- Add a separate native Kaggle task entry point using
  `kaggle_benchmarks`, `@kbench.task`, and the documented `kbench.llm` /
  evaluation flow. The existing `platform/kaggle/` CSV/index packet is a
  competition-review artifact, not this native API.
- Prototype locally on a tiny public subset, then validate the full public
  task bundle without pushing or publishing it.
- Keep three tracks explicit: public Kaggle Benchmarks tasks, a curated
  benchmark collection/leaderboard managed through Kaggle UI, and a separate
  Harbor/container hosting path. None should silently stand in for another.
- Correct host-facing hazards before review: the rules template currently says
  Apache 2.0 while the repository license is MIT; the FAQ asserts unconfirmed
  native execution; the decision-log template preselects host decisions; and
  the follow-up TODO exposes stale draft/status text.

Acceptance:

- A local native task validates, runs, and produces the canonical result schema
  without private data or network side effects.
- A generated bundle can pass the current official local Kaggle validation
  flow and has a documented mapping back to the benchmark fingerprint.
- No command pushes, publishes, creates an organization, or claims collection
  membership until separately authorized and confirmed by Kaggle.

Non-claim: a local `kaggle b` task is not a curated Kaggle collection, a hosted
private leaderboard, or Google/Kaggle acceptance.

Current primary references: the official
[`Kaggle/kaggle-benchmarks`](https://github.com/Kaggle/kaggle-benchmarks)
repository and Kaggle's
[`write-kaggle-benchmarks` skill](https://github.com/Kaggle/kaggle-skills/blob/main/write-kaggle-benchmarks/SKILL.md).

#### P1.4 Full representative Harbor parity

Owner: Harbor adapter maintainer.

Affected surfaces: `authzbench_harbor`, generated Harbor dataset, container
images, parity artifacts, and runbook.

Dependencies: P0.2; verify against the current Harbor release contract before
implementation.

Work:

- Declare and test the supported Harbor version and task layout.
- Expand from six-task empty-findings parity to all 63 public tasks for the
  deterministic oracle/scripted and negative-control agents.
- Add at least one representative no-tools model and one tool-agent parity
  experiment after the v2 protocol is stable.
- Compare per-task reward, invalid/infrastructure disposition, evidence replay,
  control verification, and provenance—not just aggregate score.
- Run the malicious isolation fixture through both native and Harbor paths.

Acceptance:

- Native and Harbor paths agree per task for the complete deterministic suite.
- Representative model/agent rows use identical task instances, scoring policy,
  evidence contract, and source/container digests.
- Every mismatch produces a minimized replay artifact and blocks promotion.

Non-claim: local parity does not establish Harbor acceptance, endorsement, or
hosted operation.

Current primary reference: the official
[`harbor-framework/harbor`](https://github.com/harbor-framework/harbor)
repository. Recheck the current release and task contract at implementation
time rather than pinning this roadmap to a remembered version.

### P1 — Obtain independent validity evidence

#### P1.5 Run design review, then validation review

Owner: project lead; reviewers must be independent of implementation.

Affected surfaces: external-review registry, task/scorer changes, paper, and
claim ledger.

Dependencies: design packet from P0.2/P1.1; final dispositions after P1.2.

Work:

- Recruit four lanes: application security/task realism,
  benchmark/evaluation methodology and statistics, AI-agent/harness safety,
  and SaaS-provider authorization-scenario validation.
- Ask reviewers to assess the proposed v2 design before the expensive study,
  then return for a public-safe disposition on the implemented protocol and
  results.
- Record findings, accepted/rejected decisions, unresolved concerns, reviewed
  commit/fingerprint, and claim-boundary impact. A packet or template is not
  review evidence.
- Add platform review only when a concrete Kaggle or Harbor artifact is ready.

Acceptance:

- Each required lane returns a real dated decision or explicit no-finding
  disposition against a named source/fingerprint.
- All blocking findings are resolved or retained as visible limitations.
- The claim ledger changes only to the level justified by those dispositions.

Non-claim: internal subagent or model reviews do not count as independent human
external validation.

### P2 — Make the artifact legible and publication-ready

#### P2.1 Rewrite the public narrative after the measurement freeze

Owner: research/documentation maintainer.

Affected surfaces: README, documentation index, status and claims pages,
technical report, IEEE paper, citation metadata, changelog, release notes, and
path/link validation.

Dependencies: P0.3 and the empirical outputs from P1.2.

Work:

- Reduce the README to orientation, current verified status, quick start,
  essential claim boundary, and links to the role-based documentation index.
  Remove repeated roadmaps, repeated evidence summaries, and the stale
  alpha/pre-v0 presentation.
- Rewrite the IEEE paper and technical report around the current task split,
  score-policy v2, blinded protocol, clustered study design, current empirical
  evidence, synthetic-target limitation, and external dispositions. Do not
  regenerate old tables into a semantically stale manuscript.
- Refresh `CITATION.cff`, contributor maturity wording, changelog/release dates,
  package version, and installation commands. Remove the nonexistent
  `requirements.txt` instruction and broken inline-code path references.
- Add an inline-path/reference validator because the Markdown link checker
  cannot catch missing paths written as code.

Acceptance:

- The paper/source-drift gate checks semantic facts, not only compilation and
  table formatting.
- A fresh reader can find the current status, methods, data boundary,
  reproducibility commands, and limitations without encountering contradictory
  maturity labels.
- All referenced repository paths exist, all license statements match MIT, and
  release dates match the actual tag/commit history.

Non-claim: polished documentation does not raise the evidence level.

### P3 — Mature governance and long-term operations

Owner: project lead and release maintainers.

Affected surfaces: release policy, task/holdout lifecycle, review approvals,
reproducibility bundles, operational metrics, and versioning.

Dependencies: stable v2 protocol, generated task taxonomy, and at least one
completed calibration study.

- Version public task templates and generated-instance policies separately.
- Define holdout overlap, rotation, retirement, and contamination incident
  procedures against the generator taxonomy without exposing private bodies.
- Require two-person approval for scorer-policy changes and result promotion.
- Publish a reproducibility bundle with container digest, schemas, source
  manifest, task-instance hash, analysis environment, and deterministic controls.
- Add cost, latency, and probe-budget reporting as secondary operational
  metrics only after correctness and safety are stable.
- Establish a release cadence that separates protocol releases, task-set
  releases, empirical studies, and host integrations.

Acceptance:

- A release manifest identifies protocol, task-template, generated-instance,
  scorer, container, and study versions independently.
- Scorer-policy and promoted-result changes record two human approvals.
- Holdout rotation and contamination incidents can be handled from the public
  governance procedure without exposing private task bodies.
- A third party can reproduce the deterministic public controls from the
  published bundle.

Non-claim: governance maturity does not substitute for task validity,
independent review, or hosted evidence.

## Kiro decision and next-run gate

Verdict: **do not run another full Kiro benchmark now**.

Current evidence already includes four structurally complete 63-task blinded
diagnostics under the same source/protocol set: requested Claude Opus 4.8,
Sonnet 4.6, Sonnet 5, and Haiku 4.5. They have zero adapter,
infrastructure, or invalid-submission failures, but they are single dirty-source
diagnostics, all Claude, and use fixed public instances. GLM completed 63 calls
with 21 parse failures; Qwen and DeepSeek admission smokes showed the same
ANSI-interleaved JSON incompatibility. These results identify the next adapter
and measurement work without requiring another expensive row.

The next Kiro activity should be a bounded admission smoke only after all of
the following are true:

1. A clean source commit and container digest are frozen.
2. The v2 participant/task schemas and evidence contracts are canonical.
3. All vulnerable tasks have explicit proof requirements.
4. Isolation and malicious-fixture gates pass.
5. Generated instances remove class-label and fixed-seed leakage.
6. ANSI normalization is tested to remove transport formatting without
   accepting malformed or ambiguous JSON.
7. The study matrix, retry rules, stopping rule, and budget are pre-registered.

Then:

1. Run one generated task per candidate model family.
2. Admit only configurations with valid structured output, complete provenance,
   zero unauthorized tool/egress behavior, and a verified requested model label.
3. Run one six-app stratified mini-suite per admitted family.
4. Start the multi-seed full study only if the mini-suite is structurally clean.
5. Stop a row on a comparability-key change or repeated structural failure; do
   not substitute a different model silently.

## Google/Kaggle status

The full 14-message Gmail thread and broader exact-sender, subject, topic,
Spam, and Trash-inclusive searches were checked through 2026-07-14. The latest
relevant message remains the maintainer's 2026-07-10 outbound follow-up. There
is no later Google/Kaggle reply.

The earlier Kaggle message linked a published Google Doc instructing the
maintainer to create a Kaggle organization account, share the benchmark, wait
for approval, and then port it to a Harbor-compatible specification. The exact
published document remains inaccessible: Drive cannot resolve the `/d/e/.../pub`
URL, targeted Drive searches found no AuthZBench/Kaggle-Harbor document, and a
direct read was blocked by the external-call credit gate. The current public
Kaggle tooling separately documents a task-first `kaggle b` workflow. Until
Kaggle replies, the organization/share instruction and the public task workflow
must be treated as potentially parallel paths, not as confirmed replacements.

Current external status is therefore: **waiting for Kaggle clarification**.
There is no evidence of organization approval, benchmark acceptance, Harbor
endorsement, hosted operation, or Gemini review.

## 30/60/90-day execution sequence

### Days 0–30: converge and freeze

1. Review and land the clean hardening candidate without disturbing dirty
   `main` work.
2. Quarantine/supersede policy-v1 staged baselines and stale analyses.
3. Finalize JSON Schemas, 27/27 evidence contracts, safety disposition, and the
   OS isolation contract.
4. Create the generated status surface and semantic drift gates.
5. After separate outbound authorization, send the v2 design packet to AppSec,
   evals/statistics, and agent/harness reviewers; this is review solicitation,
   not review completion.

Exit gate: one clean source, one measurement contract, all deterministic and
adversarial canaries passing, and no contradictory current status surface.

### Days 31–60: generate, integrate, and pilot

1. Implement task generators, cluster taxonomy, leakage tests, and richer
   vulnerability mechanisms.
2. Complete full deterministic Harbor parity and a local native Kaggle task
   prototype.
3. Run the deterministic negative-control battery and a small cross-family
   generated-instance admission pilot.
4. Incorporate design-review findings before the full study.

Exit gate: generated instances are class-blind, all host paths reproduce the
same deterministic results locally, and the pilot has no structural failures.

### Days 61–90: calibrate and publish the evidence package

1. Execute the pre-registered multi-seed, multi-family study from the frozen
   source and container.
2. Produce cluster-aware analyses, task difficulty/discrimination reports, and
   retirement/revision decisions.
3. Obtain final independent dispositions and one or more SaaS-provider scenario
   reviews.
4. Rewrite the paper, README, technical report, host packet, citation, and
   release metadata from the generated evidence snapshot.
5. Ask Kaggle/Harbor to review the exact artifact only after local gates pass
   and only with explicit authorization for the external action.

Exit gate: reproducible public artifact, honest uncertainty, independent
review dispositions, and host claims limited to directly observed status.

## Definition of “better”

The roadmap is successful when AuthZBench-SaaS can demonstrate all of the
following without relying on narrative assurances:

- participant-visible data does not reveal the answer class;
- correct control behavior requires participant evidence, not a no-op;
- every vulnerable result is backed by a task-specific proof chain;
- safety and scope compliance are host-observed;
- infrastructure failures cannot become accuracy evidence;
- task instances vary without changing the authorization construct;
- correlated task variants are analyzed as clusters;
- model comparisons use identical, complete, provenance-bound runs and honest
  uncertainty;
- native, Harbor, and Kaggle paths agree locally while remaining distinct claim
  classes;
- every public status, chart, paper table, and host statement is generated from
  or checked against one canonical evidence snapshot; and
- external validation is claimed only after real independent reviewers return
  dispositions.

Until those gates are met, the strongest accurate description remains:
**a credible internal authorization-benchmark artifact and external-validation
candidate, with strong local evidence but no hosted or independently validated
leaderboard claim.**
