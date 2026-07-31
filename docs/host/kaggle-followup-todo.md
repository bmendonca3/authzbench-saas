# Kaggle follow-up action ledger

Status: current working ledger for the June 2026 Google/Kaggle AuthZBench-SaaS thread. This is not a platform acceptance record, hosted leaderboard claim, external validation record, or evidence of completed Kaggle setup.

## Email-derived requests

- Ivan Leo's June 25, 2026 note asks for a Kaggle organization account and benchmark share in the correct format before Kaggle can start porting toward a Harbor-compatible hosted spec.
- Kaggle expects the organization/setup step to take about 24 hours for approval after submission.
- Kaggle can then review how to port AuthZBench-SaaS toward a Harbor-compatible spec for hosting.
- Latest Gmail scope checked on July 31, 2026 (full 16-message thread re-read):
  exact subject and term searches, Google/Kaggle sender-domain searches, sent
  mail, recent mail, spam, and trash.
- Latest inbound actionable message: Nicholas Kang (Nick), July 22, 2026 —
  apologized for the delay, pointed to a new onboarding document and the Harbor
  starter-template repository, and added the maintainer to a Google Chat space
  for faster communication ("let's chat there to help you get unblocked
  quickest"). This supersedes the older published setup document that denied
  account access. Meg's June 25 message in the thread is a reaction, not a new
  request.
- Latest outbound message: the July 16 follow-up (third access-blocker note),
  which reported the setup link now redirects to Google sign-in, described the
  deterministic tamper-checkable run bundle and draft versioned evidence
  contract, and again asked whether the organization/share instructions still
  apply or whether the current `kaggle b` / Harbor workflow has replaced that
  step. The July 10 follow-up (linking draft PR #79) preceded it.
- The maintainer has NOT yet posted in the Google Chat space Nick created
  (verified July 31, 2026); the thread has been idle on the email side since
  Nick's July 22 reply.

## Access blocker reported, then superseded by Kaggle's July 22 reply

The June 26, July 10, and July 16 replies reported that the published setup
document denied access to the signed-in account (brian.mendonca6@gmail.com) and
asked Kaggle to grant access, identify the correct account, or confirm whether
the current public `kaggle b` task workflow supersedes the older
organization/share document. Nick's July 22, 2026 reply effectively answered
this by supplying a NEW onboarding document and the Harbor starter-template
repository and by opening a Google Chat space, rather than granting access to
the old document. The old document's access blocker is therefore treated as
moot/superseded; the operative onboarding path is the new document + starter
repo + Chat space. The "new reply" condition that previously gated further
contact has been satisfied — the next action is to engage in the Chat space
(still requiring explicit user authorization before any external send).

## Repo-Verified Current State

- Current public split: 63 public tasks across 6 synthetic SaaS apps.
- Current public/private scale: 63 public tasks plus 48 maintainer-private holdout tasks, 111 total.
- Count evidence: `find tasks -name '*.json' -type f | wc -l` returns 63, and `artifact/v1-task-scale-roadmap.json` records `current_validated_private_holdout_task_count=48`.
- Claim boundary: v1.0-internal is internal/non-external only. Do not claim Kaggle acceptance, Harbor acceptance, hosted leaderboard operation, external validation, SaaS-provider validation, or third-party submissions.
- Fourteen saved full-63-task model/tool-agent runs have current policy-v2 offline rescores with explicit derivation and fail-closed execution metadata; older 60-task and smaller rows remain stale.
- Current stale-wording cleanup: host-facing Kaggle materials now say 63 public tasks and 111 public/private task scale. Historical 60-task baseline variance entries remain historical because they describe older `current_public_stale` rows.

## Maintainer todo

1. Get access to the Google setup document, learn which account should be used,
   or confirm that the current public `kaggle b` flow supersedes it.
2. Complete the Kaggle organization/share step only after explicit user approval.
3. Reconcile the confirmed onboarding path with `platform/kaggle/`, the packaged
   Harbor adapter, and the current public Kaggle task/run artifact model.
4. Use draft PR #79 at its current exact head as the remotely inspectable
   integration candidate. Superseded drafts #77 and #78 are already closed and
   linked to #79.
5. A Kaggle reply was received (Nick, July 22, 2026) opening a Google Chat
   space. The next action is to post there (after explicit user authorization),
   preserving the non-acceptance boundaries and asking for the concrete
   unblocking inputs: the exact Harbor 0.15 executor/host contract (the local
   Docker-in-Docker egress-sidecar nftables `fib` failure), the 0.13.2→0.15
   digest/schema/exec-shim reconciliation, the current organization-creation
   step, and the Consult-vs-FDE pathway. Refresh the 3-task pilot evidence and
   this ledger first so the message cites only current claims.

## Verification ledger

- Gmail thread audit: 16-message AuthZBench-SaaS thread re-read in full on
  July 31, 2026; the latest outbound message is the July 16 follow-up and the
  latest inbound is Nick's July 22, 2026 reply (new onboarding doc + starter
  repo + Google Chat space). (The earlier July 12 audit had recorded 14
  messages, latest outbound July 10, no later reply — now superseded.)
- Remote integration candidate: draft PR #79 at publication HEAD
  `1f73633587021c23f3a4774cf8d1de6ef66b6f58`; exact-head Public validation and
  Host presentation checks passed in GitHub Actions run `29216958371`.
- Count checks: 63 public task manifests in `tasks/`; 48 validated private holdout tasks in `artifact/v1-task-scale-roadmap.json`.
- Claim-boundary validation: `python3 scripts/check_claim_boundary.py`.
- Markdown link validation: `python3 scripts/check_markdown_links.py`.
- Host docs validation: `python3 scripts/validate_host_review_docs.py`.
- Full public validation, including scripted baseline: `python3 scripts/validate_public.py --include-scripted-baseline`.
- Host presentation validation on the local checkout: `python3 scripts/validate_host_presentation.py --skip-public-validation --timeout-seconds 120`.
- Kaggle artifact validators: `python3 scripts/validate_kaggle_sample_submission.py`, `python3 scripts/validate_kaggle_dry_run_bundle.py`, and `python3 scripts/validate_kaggle_toy_solution_file.py`.
- Stale-wording inventory: `python3 scripts/generate_docs_alignment_inventory.py` produced 314 hits, 11 `replace`, 6 `keep-forbidden`, 141 `keep-negated`, 156 `keep-historical`, and 0 `needs-dad`. The remaining exact 60-task hit in current docs is the historical sentence that 49-task, 54-task, and 60-task public splits are stale after the 63-task expansion.
- Whitespace sanity: `git diff --check`.

## Remaining approval gates

- Do not post the Chat-space message (or any follow-up) until the user
  explicitly authorizes the exact message. Nick's July 22 reply satisfies the
  prior "new reply" condition; the remaining gate is explicit send authorization
  plus a current (rebuilt) pilot so the message cites only current claims.
- Do not create/share the Kaggle organization benchmark package until the user explicitly approves the external setup step.
- Do not open a PR or publish a package until the user explicitly asks.
- Do not call the host-review package frozen until exact-head validation, privacy checks, and CI pass on a clean candidate commit.

## Verification commands

Run these before calling the host-review package ready to share:

```bash
git status --short --branch
python3 scripts/check_claim_boundary.py
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_host_presentation.py --timeout-seconds 120
```
