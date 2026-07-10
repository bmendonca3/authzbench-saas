# Kaggle follow-up action ledger

Status: current working ledger for the June 2026 Google/Kaggle AuthZBench-SaaS thread. This is not a platform acceptance record, hosted leaderboard claim, external validation record, or evidence of completed Kaggle setup.

## Email-derived requests

- Ivan Leo's June 25, 2026 note asks for a Kaggle organization account and benchmark share in the correct format before Kaggle can start porting toward a Harbor-compatible hosted spec.
- Kaggle expects the organization/setup step to take about 24 hours for approval after submission.
- Kaggle can then review how to port AuthZBench-SaaS toward a Harbor-compatible spec for hosting.
- Latest Gmail scope checked: `in:anywhere subject:"AuthZBench-SaaS" newer_than:30d -in:spam -in:trash`.
- Latest actionable message: Ivan's June 25, 2026 follow-up. Meg's later message in the same thread is a reaction, not a new request.

## Access note for future email

Include this note in the next Kaggle reply unless access is fixed first:

> I tried opening the published setup document while signed in as `brian.mendonca6@gmail.com`, but Google shows: "You need permission to access this published document. You are signed in as brian.mendonca6@gmail.com, but you don't have permission to access this published document. You may need to sign in as a different user." If there is a different account I should use, or if access can be granted to this address, I can complete that setup step.

## Draft reply

Do not send without explicit approval.

```text
Hi Ivan,

Thanks again. I started the Kaggle setup path, but the published setup doc is blocked for me at the moment. When I open it while signed in as brian.mendonca6@gmail.com, Google says I need permission to access it and may need to sign in as a different user. Could you grant access to that address, or tell me which account I should use?

In the meantime, I cleaned up the host-review package so the public-facing Kaggle materials match the current repo state: 63 public tasks, 48 private holdout tasks summarized publicly, and 111 total public/private tasks. I also kept the wording conservative: this is a Kaggle/Harbor review package, not an accepted or hosted benchmark. The current public evidence includes the deterministic scripted sanity check and offline policy-v2 rescores of saved full-63-task model/tool-agent submissions; the models were not rerun under v2 and harness failures remain explicit.

Once I can access the setup instructions, I can finish the org/share step and then adapt the repo to the Docker/Harbor shape Kaggle prefers.

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

1. Get access to the Google setup document or ask Kaggle which account should be used.
2. Complete the Kaggle organization/share step only after explicit user approval.
3. Reconcile any setup-doc requirements with `platform/kaggle/` sample submission and dry-run bundle artifacts.
4. Refresh host-facing candidate metadata once exact-head validation and CI are available.
5. Keep the next email short: confirm the repo package, mention the document-access blocker, ask for the preferred account/access path, and offer to align the repo to Kaggle's Docker/Harbor spec once shared.

## Verification ledger

- Gmail thread read: the most recent actionable messages confirm Ivan's June 25 request and the onboarding alias.
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
