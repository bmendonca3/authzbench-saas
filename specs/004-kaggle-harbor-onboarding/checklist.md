# Kaggle / Harbor Onboarding Requirements Checklist

## Source And Relationship

- [x] Newest Google/Kaggle email and thread history reviewed.
- [x] Email attachment metadata distinguished from linked sources.
- [x] Complete onboarding DOCX reviewed page by page.
- [x] Current public Harbor starter README and dataset manifest reviewed.
- [x] Consult pathway recorded; no FDE assignment or acceptance inferred.

## Design Document

- [x] Single capability and public-evaluation gap defined.
- [x] Standardized versus multiple harnesses decided.
- [x] Single-task input and correct-solution contract defined.
- [x] Public/private split and contamination boundary described.
- [ ] Minimum discriminating task count fixed and independently reviewed.
- [x] Runtime, services, network, compute, and timeout stated.
- [x] Agent input, tools, interaction loop, and final artifact stated.
- [x] Model Proxy routing boundary stated.
- [x] Metric, deterministic verifier, alternatives, anti-gaming, and isolation stated.
- [x] Primary maintenance owner and proposed launch tier stated.
- [ ] Backup maintainer and target launch date agreed.

## Current Starter Compatibility

- [x] Dataset manifest uses `[dataset]`, `[[dataset.authors]]`, and digest-backed `[[tasks]]`.
- [x] Generated task digests match Harbor 0.13.2 `harbor add`.
- [x] Pilot task trees contain environment, instruction, solution, tests, and task metadata.
- [x] NOP expected reward is `0.0`.
- [x] Oracle expected reward is `1.0`.
- [x] Verifier emits `/logs/verifier/ctrf.json`.
- [x] Fresh NOP and Oracle jobs have inspected `trial.log`, CTRF, score, and reward artifacts.
- [x] Public-safety/secret scan passes after current-starter regeneration.

## Credentialed Runtime And Platform

- [x] Kaggle CLI authentication completed.
- [x] Short-lived Model Proxy credentials minted and direct health verified.
- [ ] One LLM agent run through Model Proxy completed.
- [ ] LLM run trajectory, CTRF, score, and reward inspected.
- [ ] Same task source/digests pass Kaggle's Harbor executor.
- [x] Local/executor parity has a precise current blocker recorded.

The authenticated Harbor smoke reached 22 proxy-backed model steps but timed
out before submission and scored `0.0`; it is routing evidence, not a completed
LLM benchmark result. A corrected `no_tools` instruction is tracked and locally
validated, but its proxy rerun is blocked by the current DNS outage. The Kaggle
executor requires the exact source at a remote repository URL and commit; the
current source is intentionally uncommitted/unpushed pending separate authority.

## Scale, Review, And Launch

- [ ] Scored cohort count and cluster-disjoint public/private split frozen.
- [ ] Independent methodology review complete.
- [ ] Independent AppSec review complete.
- [ ] Independent agent/tooling review complete.
- [ ] SaaS-provider realism/credibility review complete.
- [ ] Kaggle organization approved.
- [ ] Launch tier, date, messaging, technical summary, and social assets approved.
- [ ] Privacy and private-synchronization plan approved if private repo sync is used.
- [ ] Public leaderboard and publication evidence recorded.

## Completion Guard

- [x] Local, Model Proxy, Kaggle executor, platform acceptance, independent validation,
  organization, and launch states are tracked separately.
- [x] External and credentialed actions remain explicit approval gates.
- [x] Every requirement is `verified`, `partial`, `blocked`, or `not-run` in traceability.
