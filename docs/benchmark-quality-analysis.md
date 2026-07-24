# AuthZBench-SaaS — Benchmark Quality Analysis & Improvement Plan

Scope: this is a technical review of the benchmark as a *measurement instrument* —
how well it discriminates agent capability, resists gaming, and produces
trustworthy scores. It deliberately does not restate the process/roadmap items
already tracked in `ROADMAP.md`; it focuses on scoring, task design, and
anti-gaming properties. All claims below were checked against the code
(`authzbench/score.py`, `authzbench/run.py`, `authzbench/core.py`, the six apps,
and the 63 public task manifests).

## 1. What the benchmark does well

- **The core question is sharp and well-posed.** "Prove a boundary was crossed
  with a replayable backend request, and stay silent on secure controls" is a
  genuinely good stress test that separates fluent reporting from real proof.
- **False-positive discipline is built in.** 36 of 63 public tasks are secure
  controls (21 denial, 15 authorized-allow). Any finding on a secure task scores
  0. This is the single most valuable design choice and most security benchmarks
  lack it.
- **Deterministic, replayable oracle.** Scoring replays the agent's submitted
  request against fresh seed state and checks status + body subset. This is
  reproducible and hard to fake with prose.
- **Boundary reasoning is scored separately** from exploit proof, with an
  alias-aware semantic match so correct-but-differently-worded boundaries still
  count.
- **Honest claim boundaries.** The claim ledger + CI forbidden-phrase gate is
  unusually disciplined and is itself a credibility asset.

## 2. Highest-impact weaknesses (fix these first)

### 2.1 The safety subscore is self-reported and trivially gameable
`score.py` sets `safety = 1` unless the agent *voluntarily* populates
`finding.out_of_scope_actions`. The harness collects real target request logs
(`run.py:_target_requests`) but the scorer never reads them (`score.py` contains
zero references to logs). An agent that hammers disallowed hosts, brute-forces
IDs, or performs destructive writes gets full safety credit as long as it says
nothing. Safety is currently a self-graded honor system worth 10% of every task.

**Fix:** derive safety from evidence, not self-report. Score the actual request
log against `allowed_hosts`, an allowed-route/verb allowlist, and a
destructive-action denylist. Penalize any request outside scope. Keep the
self-report field as an *additional* honesty signal, not the sole input.

### 2.2 Claim scoring is an exact string match on a unique per-task label
Vulnerability claims are matched with `finding.claim != oracle.claim` — pure
exact-string equality, no alias support (unlike boundary matching). Each vuln has
a unique verbose label (e.g. `vault_alias_cross_tenant_secret_read`,
`token_without_export_scope_reads_export`). Two problems:

1. **Brittle:** a correct finding phrased slightly differently scores 0 on the
   45%-weighted exploit component even when the replayed proof is perfect.
2. **Answer-leaking / guessable:** the label string effectively *encodes the
   answer*. If the claim vocabulary is discoverable (it is, in the public repo),
   an agent can pattern-match the label to the objective rather than discover the
   bug.

**Fix:** replace the free-string claim with a small structured taxonomy —
`{vuln_class, actor, resource, mechanism}` drawn from controlled enums — and
score each field (with aliases, like boundary already does). This rewards
understanding the *shape* of the bug rather than reproducing a magic string.

### 2.3 Most vulnerable tasks require only a single lucky request
Only **8 of 27** vulnerable tasks define `evidence_requirements`. The other 19
pass if the final submitted request alone hits the oracle status+body. Because
the vulnerable route just returns 200 with the target content, an agent that
enumerates every documented route and submits them all can satisfy the oracle
without ever demonstrating it understood the boundary (the secure sibling route
denies; the alias route allows). There is no penalty for shotgun enumeration —
`executed_tool_probe_total` is reported but not scored.

**Fix:** require a two-step evidence chain on *every* vulnerable task: (a) a
baseline/negative step showing the secure route correctly denies, then (b) the
bypass step showing the alias/vulnerable route allows. This proves the agent
isolated the boundary rather than stumbling into a 200. Consider a
probe-efficiency signal that discounts brute-force submissions.

### 2.4 Public answers are fully deterministic and memorizable
Every public task uses a single fixed seed (`public-v0-001` … `-063`), and all
IDs/content are `sha256(seed:label)[:10]` — reproducible from public code. The
entire public answer key (route → status → body → boundary → claim label) is
derivable offline and is a candidate for training-data contamination over time.
The private holdout mitigates this for the leaderboard, but the public split
loses signal the moment it is memorized.

**Fix:** the harness already supports arbitrary seeds via the
`x-authzbench-seed` header. Rotate seeds per run so the same task *logic* yields
different IDs and content, forcing genuine probing instead of recalled
constants. Publish the task *generators*, not frozen instances, and freeze only
for a given scored run.

## 3. Discrimination and difficulty (can it tell models apart?)

- The scripted baseline scores a perfect 1.0 (it follows the oracle), so it
  validates the harness but says nothing about difficulty.
- Preserved full-63 public model and tool-agent rows exist, but they remain
  diagnostic rather than ranking evidence while the benchmark’s boundary policy,
  evidence contracts, and adapter-failure handling are corrected. The legacy AGY
  rows are specifically excluded from current comparison because their adapter
  could convert failures into empty findings.
- The benchmark still lacks a pre-registered, multi-seed, cross-family full-63
  study with uncertainty estimates, so its discriminative power and ceiling are
  not yet established.

**Fix:** run at least 3–5 models across the full 63 tasks, several seeds each,
and report mean ± confidence interval (a variance test scaffold already exists).
Publish a difficulty histogram per task; retire tasks that every model passes or
every model fails, since they carry no discriminative signal.

## 4. Task-design depth

- **Vuln patterns are template-y.** Most vulnerabilities are "an alias route
  skips the check that the secure route enforces." Real authorization testing
  spans predictable-ID IDOR, mass assignment / over-posting, scope/JWT
  confusion, path-normalization bypass, nested/indirect object references,
  pagination and search leakage, and TOCTOU on state transitions. Broadening the
  vuln class taxonomy raises the ceiling and reduces overfitting to one pattern.
- **Every vulnerable task has exactly one finding** (`len(findings) != 1`
  fails). Real audits surface a variable count. A task with two real bugs among
  decoys — or a "vulnerable app with zero findings on *this* route" — would test
  discrimination far more sharply than the current fixed-cardinality format.
- **Boundary schema is thin** (usually `{attacker_actor, victim_workspace}`).
  Adding the escalated privilege, the object, and the mechanism/route would test
  deeper reasoning and further reduce label-guessing.
- **Category balance is uneven** (billing 14 vs. the others at 9). Level the
  distribution as classes expand.

## 5. Score calibration

The headline `mean_score` under-penalizes a shotgun "always report" strategy:
such an agent wins the 27 vulnerable tasks and zeroes the 36 secure ones for a
mean around 0.43 — not obviously worse than a cautious agent. `false_positive_rate`
is tracked but not folded into the headline number.

**Fix:** publish a calibrated headline metric that applies an asymmetric penalty
for confident false reports on secure controls (e.g. subtract for a false
finding rather than merely awarding 0). This makes calibration — the benchmark's
stated purpose — the thing that actually moves the top-line score.

## 6. Prioritized recommendations

| # | Improvement | Why it matters | Effort |
| --- | --- | --- | --- |
| 1 | Score safety from request logs vs. allowed_hosts/verbs, not self-report | Closes a 10%-of-score gameable hole | Medium |
| 2 | Require a 2-step (deny-then-bypass) evidence chain on all 27 vuln tasks | Stops single-lucky-request passes | Medium |
| 3 | Replace exact-string claim match with a scored structured taxonomy + aliases | De-brittles and de-leaks the 45% component | Medium |
| 4 | Rotate seeds per run; ship generators not frozen instances | Kills memorization/contamination | Low–Med |
| 5 | Produce full-63 multi-model, multi-seed baselines with CIs | Establishes discriminative power (unknown today) | Medium |
| 6 | Add a calibrated headline metric penalizing false positives | Aligns the top-line number with the benchmark's purpose | Low |
| 7 | Broaden vuln classes beyond the alias-route pattern | Raises ceiling, reduces overfitting | High |
| 8 | Allow variable finding counts (0, 1, 2+ among decoys) | Tests discrimination realistically | Medium |
| 9 | Add a probe-efficiency signal to discount brute force | Rewards reasoning over enumeration | Low |

The first four are the ones that most change what the benchmark actually
measures; 5 and 6 make the results trustworthy and comparable; 7–9 extend
headroom for future model generations.
