# Kaggle follow-up action ledger

Status: current working ledger for the June 2026 Google/Kaggle AuthZBench-SaaS thread. This is not a platform acceptance record, hosted leaderboard claim, external validation record, or evidence of completed Kaggle setup.

## Email-derived requests

- Ivan Leo's June 25, 2026 note asks for a Kaggle organization account and benchmark share in the correct format before Kaggle can start porting toward a Harbor-compatible hosted spec.
- Kaggle expects the organization/setup step to take about 24 hours for approval after submission.
- Kaggle can then review how to port AuthZBench-SaaS toward a Harbor-compatible spec for hosting.
- Latest Gmail scope checked on July 12, 2026: exact subject and term searches,
  Google/Kaggle sender-domain searches, sent mail, recent mail, spam, and trash.
- Latest inbound actionable message: Ivan's June 25, 2026 follow-up. Meg's
  later message in the same thread is a reaction, not a new request.
- Latest outbound message: the July 10 follow-up that linked draft PR #79,
  described the repo-side Harbor evidence, preserved non-acceptance boundaries,
  and asked whether the current `kaggle b` workflow supersedes the inaccessible
  organization/share document. No later received reply was found in the thread,
  recent Google/Kaggle mail, spam, or trash.

## Access blocker already reported

The June 26 and July 10 replies reported that the published setup document
denied access to the signed-in account. They asked Kaggle to grant access,
identify the correct account, or confirm whether the current public `kaggle b`
task workflow supersedes the older organization/share document. Do not send
another duplicate follow-up without a new reply, new platform evidence, or
explicit user direction.

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
5. Wait for a Kaggle reply or new platform evidence before drafting another
   follow-up. Any future message should preserve the non-acceptance boundaries
   and ask for one concrete onboarding path plus host-specific Docker/scorer
   differences.

## Verification ledger

- Gmail thread audit: 14-message AuthZBench-SaaS thread read in full; the latest
  outbound message is the July 10 follow-up and no later received reply was
  found as of July 12.
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

- Do not send another follow-up until the user explicitly authorizes the exact
  message and the duplicate-send check confirms there is new value.
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
