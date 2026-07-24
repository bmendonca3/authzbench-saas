# Requirement-To-Evidence Traceability

| Requirement | Evidence / verification | Status |
| --- | --- | --- |
| FR-001 exact target and dirty-state preservation | `git status --short --branch`; no reset/cleanup; final diff review | verified |
| FR-002 reconcile hardening candidate | `git worktree list`; `git rev-list main...improve/evidence-backed-hardening`; candidate code/docs; roadmap “Do not re-propose completed hardening” table | verified |
| FR-003 cover all material benchmark lanes | Two complete independent audits, runner/baseline interim evidence, parent statistics/reconciliation, and final roadmap risk/work-package coverage | verified-with-gap |
| FR-004 current Gmail status | Full 14-message thread; exact-sender, subject, topic, Spam, and Trash-inclusive searches | verified |
| FR-005 current Kaggle/Harbor contracts | Primary `Kaggle/kaggle-benchmarks`, `Kaggle/kaggle-skills`, `Kaggle/kaggle-cli`, `harbor-framework/harbor` sources | verified |
| FR-006 evidence-ranked priorities | `docs/improvement-roadmap-2026-07.md` P0-P3 packages and 30/60/90 sequence | verified |
| FR-007 owner/dependency/acceptance/non-claim | Every P0-P3 work package in the final roadmap | verified |
| FR-008 explicit Kiro decision | Runner evidence, existing diagnostic summaries, bounded validation, and roadmap “Kiro decision and next-run gate” | verified |
| FR-009 privacy and no external writes | Final diff/readback; Gmail/Drive read-only; no raw private holdout bodies/results; no send/publish/push/benchmark run | verified |
| FR-010 durable continuation | `GOAL_STATE.md`, this Spec Kit packet, and final roadmap | verified |
| SC-001 lane completeness | Final task ledger, roadmap risk inventory, two complete independent audits, runner interim, and parent reconciliation; post-synthesis reread credit-blocked | verified-with-gap |
| SC-002 P0/P1 direct evidence | Final roadmap evidence boundary, fixed/open reconciliation, acceptance gates, and repository/source references | verified |
| SC-003 no duplicate hardening work | Parent reconciliation against `aae81c0f` and explicit fixed/open table | verified |
| SC-004 current external status | July 14 Gmail and primary-source checks | verified |
| SC-005 gated Kiro decision | Explicit no-run verdict, seven prerequisites, smoke/mini-suite/full sequence | verified |
| SC-006 independent completion gate | Two complete independent audit verdicts were incorporated; post-synthesis subagent reread failed at workspace credit gate and is not claimed | partial |
