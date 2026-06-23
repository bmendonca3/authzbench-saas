# Sectional Panel Summary: v0 Roadmap And Alpha Positioning

This review checked whether the repo-level roadmap and v0 plan move
AuthZBench-SaaS toward a top benchmark while honestly keeping the current release
at alpha/pre-v0.

## Reviewers Counted

| Reviewer | Status |
| --- | --- |
| Gemini 3.5 Flash (High) | verified by parent from local panel log |
| Gemini 3.1 Pro (High) | verified by parent from local panel log |
| Claude Sonnet 4.6 (Thinking) | verified label; no usable final findings returned in captured output |
| Claude Opus 4.6 (Thinking) | verified by parent from local panel log |
| Kiro `claude-opus-4.8` | verified by model catalog and captured output |
| panel reviewer | verified |

Local evidence filenames, not committed because raw panel logs can contain local
account metadata:

- `gemini-3-5-flash-high-20260605-013133.log`
- `gemini-3-1-pro-high-20260605-013133.log`
- `claude-sonnet-4-6-thinking-20260605-013133.log`
- `claude-opus-4-6-thinking-20260605-013133.log`
- `kiro-claude-opus-4-8-20260605-013244.out.txt`
- `kiro-claude-opus-4-8-20260605-013244.models.json`

## Section 1: Roadmap Quality

Findings accepted:

- Holdout task counts were inconsistent across roadmap and holdout docs.
- Milestones needed clearer `v0` prerequisite grouping.
- Version-label convention was too scattered.
- The roadmap needed a v0 task build-matrix item.
- CI status needed clearer alpha versus v0 treatment.

Disposition:

- `docs/holdout-and-contamination.md` now aligns on a 20-30 private holdout
  target, with 24 preferred for balanced coverage.
- `ROADMAP.md` now states that Milestones 2, 3, and 4 are prerequisites for the
  real `v0` tag and adds a version-label section.
- `ROADMAP.md` now includes a v0 task build-matrix action.
- `docs/publish-checklist.md` now says CI is required for v0 and optional for
  alpha tags when workflow-scoped credentials are unavailable.

## Section 2: Benchmark And Scoring Credibility

Findings accepted:

- Private holdouts need a protected execution model, not just hidden local JSON.
- Request logs should come from the target container or proxy sidecar, not from
  self-reported agent logs.
- Leaderboard sorting by lowest false-positive rate first can reward do-nothing
  agents.
- Leaderboard metadata needed split, commit, harness type, repeated-run, and
  boundary-reasoning fields.
- At least one tool-equipped agent baseline should be required for v0.
- Route aliases, decoys, and multi-seed holdouts should be v0 gates, not vague
  future preferences.

Disposition:

- `docs/holdout-and-contamination.md` now defines hosted, maintainer-run, and
  encrypted/local holdout execution options.
- `docs/v0-release-plan.md` now gates v0 on protected holdout execution,
  route-alias support, decoys, proxy/container-side request logs, two seeds per
  private holdout task, a tool-equipped baseline, and independent review.
- `docs/leaderboard-schema.md` now changes ranking to require a false-positive
  threshold before sorting by exploit-proven success.
- `docs/leaderboard-schema.md` now adds split, public/private counts, commit SHA,
  harness type, boundary-reasoning, control, repeated-run, and variance fields.
- `authzbench/run.py` now emits benchmark version, agent, model, and harness type
  fields natively.

## Section 3: Release And Documentation Posture

Findings accepted:

- Baseline summaries still used a premature `v0` benchmark-version string.
- README mixed harness sanity checks with model results.
- README omitted the Qwen baseline command despite listing the result.
- The launch report undersold the current alpha split as only inspectable, rather
  than immediately useful for local agent integration.
- `docs/publish-checklist.md` included an unnecessary institutional reference.

Disposition:

- Baseline summaries now use `alpha-0.0.1-public-scaffold-local`.
- README now separates harness sanity checks from no-tools model baselines.
- README now includes the Qwen baseline command.
- `docs/launch-report.md` now states the alpha is already useful as a local
  integration and regression suite.
- `docs/publish-checklist.md` now says public `github.com` account.

## Remaining Open Items

- Implement CI.
- Expand route aliases and decoy endpoints beyond the alpha prototype.
- Harden target/proxy-side request logging with Docker CI and isolated
  live-agent validation.
- Add a protected private-holdout execution path.
- Run tool-equipped and repeated model baselines.
