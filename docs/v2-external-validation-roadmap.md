# V2 External Validation Roadmap

> **See also:** [`docs/current-claim-boundary.md`](current-claim-boundary.md) for the canonical claim table that names these v2 / external gates.

External review and platform acceptance are not v1 gates.
They are preserved here as v2 validation tracks.

v1 does not claim external review, hosted public leaderboard readiness,
SaaS-provider validation, or platform acceptance.
Those are tracked below as v2 gates.

## Deferred v2 Validation Tracks

### Application Security Review

- Goal: independent AppSec reviewer assesses task realism, authorization
  boundary quality, false-positive controls, and unsafe/ambiguous task flags.
- Review packet: `docs/reviews/external-review-packet.md`,
  `docs/task-quality-matrix.md`, representative public tasks, scorer controls,
  `docs/evidence-and-claims.md`.
- Acceptance criteria: reviewer can confirm BOLA/BFLA, role, token-scope,
  sharing, and admin-action tasks are realistic enough for a benchmark paper;
  false-positive controls are meaningful; no unsafe or ambiguous tasks remain.
- Status: v2 deferred — not a v1 gate.

### Benchmark and Evals Methodology Review

- Goal: independent benchmark/evals reviewer evaluates task split design,
  scoring semantics, repeated-run evidence, and claim boundary.
- Review packet: `docs/reviews/external-review-packet.md`, technical reports,
  paper scaffold, `baselines/baseline-registry.json`,
  `docs/baseline-variance-analysis.md`, validation commands.
- Acceptance criteria: reviewer judges that task split, scoring semantics,
  repeated-run evidence, and claim boundary support the paper's stated claims
  without implying private leaderboard readiness.
- Status: v2 deferred — not a v1 gate.

### AI-Agent and Tooling Review

- Goal: independent AI-agent/tooling reviewer assesses harness types, tool
  access, target-request correlation, and comparability keys.
- Review packet: `docs/reviews/external-review-packet.md`, public baseline
  summaries, live HTTP tool-agent summaries, runner/scorer docs,
  `docs/leaderboard-schema.md`,
  `docs/boundary-reasoning-calibration-study.md`.
- Acceptance criteria: reviewer can assess whether harness assumptions, tool
  access, and agent comparability keys are described well enough for
  agent-to-agent comparison.
- Status: v2 deferred — not a v1 gate.

### SaaS-Provider Scenario Validation

- Goal: validation from one or more SaaS authorization providers that
  benchmark task scenarios, boundary definitions, and oracle logic accurately
  reflect real SaaS authorization patterns.
- Status: v2 deferred — not a v1 gate.

### Optional Platform Review: Kaggle and Harbor Acceptance

- Harbor-compatible execution path is scaffolded and locally smoked.
  Full Harbor adapter parity, platform publishing, and platform review are v2.
- Kaggle or other public platform acceptance is not claimed for v1.
- Status: v2 deferred — not a v1 gate.

## v1 Harbor Boundary Statement

Harbor-compatible execution path is scaffolded and locally smoked.
Full Harbor adapter parity and platform or publishing review are v2.
v1 does not claim Harbor acceptance.

## How to Trigger v2 External Validation

1. Recruit independent reviewers for each lane above.
2. Use `docs/reviews/external-review-packet.md` as the intake packet.
3. Use `docs/reviews/external-review-intake.md` as the human-facing response form.
4. When a reviewer returns a lane, record findings in
   `docs/reviews/external-review-summary.json` using real evidence
   (not placeholders or templates).
5. Update `docs/reviews/external-review-summary.md` to reflect the completed lane.
6. Do not mark v2 external-validation release complete until all three required
   lanes (AppSec, benchmark/evals, AI-agent/tooling) record real human decisions.
