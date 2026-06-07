# External Review Summary

Status: intake tracker for post-`v0.0` external review. Reviewer packet is
ready, but independent external review is still externally blocked until real
reviewers complete the lanes.

No independent external review is claimed yet. This file tracks planned review
lanes, reviewer questions, requested evidence, and acceptance criteria without
publishing private reviewer identity or private holdout details.

Current blocker: the repository can prepare and validate the review packet, but
it cannot honestly mark review complete without independent AppSec,
benchmark/evals, and AI-agent/tooling reviewers returning findings or explicit
no-finding dispositions.

## Review Lanes

| Lane | Reviewer status | Requested evidence | Acceptance criteria | Next action |
| --- | --- | --- | --- | --- |
| Application security | Packet ready; reviewer not yet completed | `docs/reviews/external-review-packet.md`, `docs/task-quality-matrix.md`, representative public tasks, scorer controls, `docs/evidence-and-claims.md` | Reviewer can identify whether BOLA/BFLA, role, token-scope, sharing, and admin-action tasks are realistic enough for a benchmark paper; false-positive controls are meaningful; unsafe or ambiguous tasks are flagged. | Recruit reviewer for task realism, authorization-boundary quality, and control quality. |
| Benchmark/evals methodology | Packet ready; reviewer not yet completed | `docs/reviews/external-review-packet.md`, technical reports, paper scaffold, `baselines/baseline-registry.json`, `docs/baseline-variance-analysis.md`, validation commands | Reviewer can judge whether task split, scoring semantics, repeated-run evidence, and claim boundary support the paper's stated claims without implying private leaderboard readiness. | Recruit reviewer for split design, scoring validity, variance framing, and release claim limits. |
| AI-agent/tooling | Packet ready; reviewer not yet completed | `docs/reviews/external-review-packet.md`, public baseline summaries, live HTTP tool-agent summaries, runner/scorer docs, `docs/leaderboard-schema.md`, `docs/boundary-reasoning-calibration-study.md` | Reviewer can assess whether harness types, tool access, target-request correlation, and comparability keys are described well enough for agent-to-agent comparison. | Recruit reviewer for harness assumptions, tool access, and agent comparability. |

## Reviewer Questions

### Application Security

- Do the public tasks exercise recognizable SaaS authorization boundaries rather
  than synthetic-only quirks?
- Are vulnerable tasks paired with controls that would catch over-reporting?
- Are boundary keys such as actor, tenant, role, object, and token scope clear
  enough for a reviewer to audit?
- Which task family is weakest or most ambiguous?
- Would any public task teach an unsafe real-world exploit pattern beyond normal
  authorization-testing knowledge?

### Benchmark And Evals Methodology

- Does the current claim boundary match the evidence in
  `docs/evidence-and-claims.md`?
- Are `v0_mean_score`, exploit proof, boundary reasoning, false-positive rate,
  and target-request coverage separated clearly enough?
- Are two-run ranges framed as descriptive evidence rather than statistical
  certainty?
- Are stale 44-task, frozen 46-task, historical 49-task, and current 54-task
  evidence clearly separated?
- Does the validation packet give enough public reproducibility without leaking
  private holdout internals?

### AI-Agent And Tooling

- Are no-tools model baselines and live HTTP tool-agent baselines comparable
  only where the docs say they are comparable?
- Does target-request correlation provide useful evidence without replacing
  scorer replay?
- Are model labels, harness type, benchmark fingerprint, and repeated-run
  provenance sufficient for future submissions?
- Are failure modes such as schema mismatch, missing boundary fields, and
  planner brittleness visible enough?
- What extra artifact would make the harness assumptions easier to inspect?

## Review Recording Rules

- Record reviewer role and scope, not private identity, unless explicit
  permission is granted.
- Keep raw private holdout details out of public review summaries.
- Track accepted changes, rejected changes, and unresolved concerns.
- Record whether each concern affects claims, scoring, task design, artifact
  packaging, or paper wording.
- Update `docs/evidence-and-claims.md` if a review changes the supported claim
  boundary.

## Completion Gate

Do not mark the external-review goal complete until each lane records a real
review date, reviewer role/scope, artifacts reviewed, findings or explicit
no-finding disposition, and accepted/rejected/unresolved decisions. Packet-ready
is useful evidence, but it is not external review.

## Finding Log Template

| Date | Lane | Reviewer role | Finding | Decision | Follow-up artifact |
| --- | --- | --- | --- | --- | --- |
| TBD | TBD | Role only | TBD | accepted, rejected, or unresolved | Path or issue reference |
