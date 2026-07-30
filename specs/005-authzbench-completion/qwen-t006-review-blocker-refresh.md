# Qwen T006 — Review And External-Blocker Handoff Refresh

## Role

You are the bounded implementation executor. Codex is the parent/DAD and will
inspect every edit, run the integrated gates, and decide whether to accept the
lane.

## Objective

Refresh the local, public-safe external-blocker and reviewer handoff surfaces
to the current AuthZBench-SaaS source facts. This is preparation only: do not
send, publish, complete, or imply completion of any external review or Kaggle
action.

## Exact Write Scope

You may edit only these seven files:

1. `artifact/external-blockers-issue-tracker.json`
2. `docs/reviews/external-review-packet.md`
3. `docs/reviews/external-review-summary.md`
4. `docs/reviews/external-review-summary.json`
5. `docs/reviews/external-review-response.template.json`
6. `docs/reviews/benchmark-methodology-review-packet.md`
7. `docs/reviews/saas-provider-review-packet.md`

Use Cline's editor tool for every write. Use command tools only for bounded,
read-only inspection and validation. Do not write through Python, shell
redirection, `sed -i`, or generated rewrites.

## Authoritative Facts

- Current base `HEAD` and `origin/main` are
  `acb6434c4bb25cce53a1a9f4eb31c869986743ca`.
- Completion-packet evidence is dated 2026-07-28. This local refresh is being
  generated at `2026-07-29T15:42:10Z`.
- The exact benchmark source requested by the current Kaggle runner attempt is
  parent commit `20cd189072b25dc406bd4fff03672a4ab0268648`.
- Kaggle's pinned published runner digest remains
  `sha256:772dfa2383c07928ee020f8235323a81dee9ff519750e978f776cc0448533f32`.
- The attempted exact-source run stopped before agent startup because the
  nested Harbor 0.15 egress sidecar could not install required nftables `fib`
  rules. Local Docker-in-Docker failure is not Kaggle-hosted evidence.
- KQ-005 now needs either a Kaggle-supported host/kernel where that egress
  sidecar starts or a corrected supported runner image with equivalent network
  isolation, followed by exact-source/digest parity evidence.
- The public set has 63 tasks across 6 apps: 27 vulnerable and 36 secure
  controls (21 denial, 15 authorized-allow).
- Public-safe private summary metadata has 48 tasks: 24 vulnerable and 24
  controls. Do not inspect private task bodies, raw private results, private
  routes, or private seeds.
- `artifact/scored-cohort-contract.v1.json` is a draft candidate with 17
  public semantic clusters. Private cluster assignment/disjointness, the
  minimum discriminating cohort size, independent methodology review, cohort
  admission, and launch eligibility all remain pending.
- Historical evidence must be described distinctly: stale 44-task, frozen
  46-task, historical 49-task, stale 54-task and 60-task, and current 63-task
  evidence. The current 63-task model/tool rows are offline policy-v2 rescores
  of saved full-split submissions, not fresh repeated model execution under
  policy v2.
- The formal `external-review-registry.json` contains exactly three pending
  independent lanes: AppSec, benchmark/evals, and agent/tooling. Do not add a
  fourth lane and do not mark any lane complete.
- SaaS-provider/product-security validation is a separate fourth realism lane.
  `docs/reviews/review-registry.json` is the historical/internal registry and
  is not the submission target for this lane.

## Required Changes

1. Refresh `artifact/external-blockers-issue-tracker.json` metadata to the
   current base commit and generation timestamp above.
2. Replace stale EXT-001 wording with the precise KQ-005 supported
   host/kernel-or-corrected-image dependency, exact source/digest, observed
   pre-agent nftables failure, and the exact parity evidence still needed.
3. Keep EXT-003's six-task local Harbor parity explicitly historical/local and
   distinct from the still-missing exact-source hosted executor parity and
   external Harbor review/publishing.
4. Keep EXT-004 through EXT-007 pending. For the methodology blocker, include
   the draft scored-cohort contract and its unresolved review decisions.
5. Refresh the three-lane reviewer handoff materials and questions with the
   current 63-task evidence separation. Add the scored-cohort contract and
   Kaggle design contract to benchmark/evals requested materials, and ask the
   reviewer to decide cluster disjointness and minimum-count methodology.
6. Update the Markdown summary, structured pending summary, and response
   template consistently. Preserve exactly three pending formal lanes; do not
   invent reviewer identity, dates, findings, dispositions, or reviewed SHAs.
7. Correct the methodology packet's submission target to
   `docs/reviews/external-review-registry.json` plus the public-safe external
   review summary.
8. Correct the SaaS packet's submission instructions. A returned public-safe
   SaaS/product-security response must be retained as a dedicated tracked
   review artifact and cited from the claim/evidence surface; it must not be
   placed in the historical `review-registry.json` or silently added to the
   three-lane external registry. Until a real response and an appropriate
   validated record exist, EXT-004 and the SaaS-validation claim remain
   pending.

## Prohibited Actions

- Do not read `tasks_private/` or any raw/ignored private evidence.
- Do not use credentials, network access, email, browsers, external services,
  or platform APIs.
- Do not edit any file outside the exact write scope.
- Do not install dependencies, commit, push, publish, create issues, send
  review packets, reset, clean, delete, or modify linked worktrees.
- Do not change benchmark tasks, apps, scorer behavior, readiness policy,
  review status, or claim-boundary enforcement.

## Required Verification

Run only after editing:

```bash
python3 -m json.tool artifact/external-blockers-issue-tracker.json >/dev/null
python3 -m json.tool docs/reviews/external-review-summary.json >/dev/null
python3 -m json.tool docs/reviews/external-review-response.template.json >/dev/null
python3 scripts/validate_external_review_summary.py --json
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
git diff --check
git status --short
```

The external-review validator must keep all three lanes pending and
`v2_external_validation_complete=false`. Public readiness may remain 9/10 with
only the already documented paper/source-binding gate unmet.

## Final Report

Report:

- the exact files changed;
- the facts refreshed;
- every verification command and result;
- confirmation that all external lanes remain pending;
- confirmation that no private data, credential, network, external action,
  commit, or push occurred.
