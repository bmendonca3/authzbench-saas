# External Review Summary

**External review is no longer a v1 gate.**
It is preserved as a v2 validation track and is not claimed for v1.
v1 does not claim external review, hosted public leaderboard readiness,
SaaS-provider validation, or platform acceptance.
Those are tracked as v2 gates in `docs/claims-and-evidence.md`.

Status: intake tracker for v2 external review preparation. The public-safe
handoff candidate was refreshed from base commit
`acb6434c4bb25cce53a1a9f4eb31c869986743ca` with evidence through
2026-07-28, but it has not been sent and no review commit has been frozen.
Independent external review is blocked until real human lane reviewers return
intake results. This is not a v1 prerequisite.

No independent external review is claimed yet. This file tracks planned review
lanes, reviewer questions, requested evidence, and acceptance criteria without
publishing private reviewer identity or private holdout details.
The machine-readable pending-review tracker lives in
`docs/reviews/external-review-summary.json`; it records the three required
lanes, requested artifacts, reviewer questions, blockers, and next actions, but
keeps `review_status` as `pending` for every lane.
When a reviewer returns a lane, use
`docs/reviews/external-review-intake.md` as the human-facing response form and
`docs/reviews/external-review-response.template.json` only as the machine-shape
starting point for the completed response. Replace every placeholder with real
reviewer evidence before updating `external-review-summary.json`; the validator
rejects the unchanged template and unresolved placeholder text embedded inside
otherwise non-empty pending or completed lane fields.

Current blocker: the repository can prepare and validate the review packet, but
it cannot honestly mark review complete without independent AppSec,
benchmark/evals, and AI-agent/tooling reviewers returning findings or explicit
no-finding dispositions.

The review candidate covers 63 public tasks across 6 apps: 27 vulnerable tasks
and 36 secure controls (21 denial and 15 authorized-allow). Public-safe private
summary metadata covers 48 holdout tasks (24 vulnerable and 24 controls);
private task bodies and raw private evidence remain excluded. The draft scored
cohort maps the public set into 17 semantic clusters, but private cluster
assignment and disjointness, minimum discriminating task and cluster counts,
methodology approval, cohort admission, and launch eligibility remain
unresolved.

This is an external blocker, not a missing public-repo checklist item. The
public repo has the packet, intake form, response template, pending structured
summary, and validator checks. This v2 tracker updates only when independent reviewers
return real review evidence and maintainers copy public-safe summaries into
`docs/reviews/external-review-summary.json`.

## Review Lanes

| Lane | Reviewer status | Requested evidence | Acceptance criteria | Next action |
| --- | --- | --- | --- | --- |
| Application security | Handoff candidate refreshed; reviewer not yet engaged | `docs/reviews/external-review-packet.md`, `docs/task-quality-matrix.md`, representative public tasks, scorer controls, `docs/claims-and-evidence.md` | Reviewer can identify whether BOLA/BFLA, role, token-scope, sharing, and admin-action tasks are realistic enough for a benchmark paper; false-positive controls are meaningful; unsafe or ambiguous tasks are flagged. | Freeze the review commit, then recruit a reviewer for task realism, authorization-boundary quality, and control quality. |
| Benchmark/evals methodology | Handoff candidate refreshed; reviewer not yet engaged | `docs/reviews/external-review-packet.md`, `docs/kaggle-benchmark-design-contract.md`, `artifact/scored-cohort-contract.v1.json`, technical reports, paper scaffold, `baselines/baseline-registry.json`, `docs/baseline-variance-analysis.md`, validation commands | Reviewer can judge whether task split, cluster-disjoint cohort design, minimum-count methodology, scoring semantics, repeated-run evidence, and claim boundary support the paper's stated claims without implying private leaderboard readiness. | Freeze the review commit, then recruit a reviewer for split design, cohort methodology, scoring validity, variance framing, and release claim limits. |
| AI-agent/tooling | Handoff candidate refreshed; reviewer not yet engaged | `docs/reviews/external-review-packet.md`, public baseline summaries, live HTTP tool-agent summaries, runner/scorer docs, `docs/scoring-and-submissions.md`, `docs/boundary-reasoning-calibration-study.md` | Reviewer can assess whether harness types, tool access, target-request correlation, and comparability keys are described well enough for agent-to-agent comparison. | Freeze the review commit, then recruit a reviewer for harness assumptions, tool access, and agent comparability. |

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
  `docs/claims-and-evidence.md`?
- Are `v0_mean_score`, exploit proof, boundary reasoning, false-positive rate,
  and target-request coverage separated clearly enough?
- Are two-run ranges framed as descriptive evidence rather than statistical
  certainty?
- Are stale 44-task, frozen 46-task, historical 49-task, stale 54-task and
  60-task, and current 63-task evidence clearly separated?
- Is it clear that the current 63-task model/tool rows are offline policy-v2
  rescores of saved full-split submissions, not fresh repeated model execution
  under policy v2?
- Does the draft 17-cluster contract define defensible semantic clusters and
  cluster-disjoint split rules, and what analysis should determine the minimum
  discriminating task and cluster counts?
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
- Update `docs/claims-and-evidence.md` if a review changes the supported claim
  boundary.

## Completion Gate

Do not mark the external-review goal complete until each lane records a real
human decision process. A public-safe packet and a machine-checked structure for
pending-review evidence are useful v2 preparation, but neither is external review. The
response template is also not review evidence. Pending and completed lane
fields must use concrete wording; unresolved markers such as `TBD`, `TODO`,
`pending`, `unknown`, `n/a`, and `<placeholder>` are rejected even when embedded
inside longer strings.

## Finding Log Template

| Date | Lane | Reviewer role | Finding | Decision | Follow-up artifact |
| --- | --- | --- | --- | --- | --- |
| Use ISO date | Required lane | Role and scope only | Public-safe finding summary | accepted, rejected, or unresolved | Tracked file path or existing commit SHA |
