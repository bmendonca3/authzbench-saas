# Kaggle follow-up action ledger

Status: current working ledger for the June 2026 Google/Kaggle AuthZBench-SaaS thread. This is not a platform acceptance record, hosted leaderboard claim, external validation record, or evidence of completed Kaggle setup.

## Email-derived requests

- Ivan Leo's June 25, 2026 note asks for a Kaggle organization account and benchmark share in the correct format before Kaggle can start porting toward a Harbor-compatible hosted spec.
- Kaggle expects the organization/setup step to take about 24 hours for approval after submission.
- Kaggle can then review how to port AuthZBench-SaaS toward a Harbor-compatible spec for hosting.
- Latest Gmail scope checked on July 10, 2026: exact subject and term searches,
  Google/Kaggle sender-domain searches, sent mail, recent mail, spam, and trash.
- Latest inbound actionable message: Ivan's June 25, 2026 follow-up. Meg's
  later message in the same thread is a reaction, not a new request.
- Latest outbound message: the June 26 access request below. No later reply was
  found in the thread, the onboarding alias, spam, or trash.

## Access note for future email

Include this note in the next Kaggle reply unless access is fixed first. Also
ask whether the current public `kaggle b` task workflow supersedes the older
organization/share document, because the public Kaggle tooling has evolved
since the June 25 note.

> I tried opening the published setup document while signed in as `brian.mendonca6@gmail.com`, but Google shows: "You need permission to access this published document. You are signed in as brian.mendonca6@gmail.com, but you don't have permission to access this published document. You may need to sign in as a different user." If there is a different account I should use, or if access can be granted to this address, I can complete that setup step.

## Draft reply

Do not send without explicit approval.

```text
Hi Ivan,

Quick follow-up on AuthZBench-SaaS. The published setup document is still blocked for brian.mendonca6@gmail.com. Could you grant access, tell me which account to use, or confirm whether the newer public `kaggle b` task workflow replaces that organization/share step?

The repo now has a packaged Harbor adapter, an isolated wheel/CLI/scorer smoke, a real local Harbor execution smoke, and exact per-task native/Harbor reward parity on a six-task public subset. Draft PR #79 consolidates the scorer, manifest, provenance, packaging, and host-review changes: https://github.com/bmendonca3/authzbench-saas/pull/79

The public package remains intentionally conservative: it is not presented as Kaggle-accepted, Harbor-accepted, hosted, externally validated, or release-ready. The fourteen current model/tool-agent summaries are offline re-scores of saved submissions; model execution was not repeated.

Once the setup path is clear, I can complete the required organization/share or `kaggle b` step and provide the generated Harbor package for review. If your hosted Docker/Harbor contract differs from the public CLI flow, the expected container, artifact, and scorer interface would be the most useful next input.

Thanks,
bmendonca3
```

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
4. Use draft PR #79 as the remotely inspectable integration candidate; do not
   close its source drafts until exact-head CI and the integrated diff are confirmed.
5. Keep the next email short: link PR #79, state the completed repo-side Harbor
   evidence, preserve the non-acceptance boundaries, and ask for one concrete
   onboarding path plus any host-specific Docker/scorer differences.

## Verification ledger

- Gmail thread audit: 13-message AuthZBench-SaaS thread read in full; the latest
  outbound message is the June 26 access request and no later reply was found.
- Remote integration candidate: draft PR #79 at publication HEAD
  `1c089d1a378d617faf5261dd842fb1712bd48b0a`; exact-head Public validation and
  Host presentation checks passed on GitHub Actions.
- Count checks: 63 public task manifests in `tasks/`; 48 validated private holdout tasks in `artifact/v1-task-scale-roadmap.json`.
- Claim-boundary validation: `python3 scripts/check_claim_boundary.py`.
- Markdown link validation: `python3 scripts/check_markdown_links.py`.
- Host docs validation: `python3 scripts/validate_host_review_docs.py`.
- Full public validation, including scripted baseline: `python3 scripts/validate_public.py --include-scripted-baseline`.
- Host presentation validation on the local checkout: `python3 scripts/validate_host_presentation.py --skip-public-validation --timeout-seconds 120`.
- Kaggle artifact validators: `python3 scripts/validate_kaggle_sample_submission.py`, `python3 scripts/validate_kaggle_dry_run_bundle.py`, and `python3 scripts/validate_kaggle_toy_solution_file.py`.
- Stale-wording inventory: `python3 scripts/generate_docs_alignment_inventory.py` produced 304 hits, 12 `replace`, 6 `keep-forbidden`, 132 `keep-negated`, 154 `keep-historical`, and 0 `needs-dad`. The remaining exact 60-task hit in current docs is the historical sentence that 49-task, 54-task, and 60-task public splits are stale after the 63-task expansion.
- Whitespace sanity: `git diff --check`.

## Remaining approval gates

- Do not send the draft reply until the user explicitly approves sending.
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
