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
- [x] One LLM agent run through Model Proxy completed.
- [x] LLM run trajectory, CTRF, score, reward, exceptions, and token use inspected.
- [ ] Same task source/digests pass Kaggle's Harbor executor.
- [x] Local/executor parity has a precise current blocker recorded.

The corrected local mini-swe-agent run completed the secure-denial control through
Model Proxy with a valid submission, passing CTRF and score, reward `1.0`, no
trial exception, and inspected token data. Its final completion-marker step is
recorded as terminalized without execution; batch and trial exception fields
remain empty. Exact-secret scans found zero matches in the retained proxy and
local-control files. Its temporary task copy used all-public network mode, so
this is local compatibility evidence rather than verifier-isolation,
Kaggle-executor, Kaggle-hosted, or platform-acceptance evidence.

The schema clarification is now pushed at exact commit
`20cd189072b25dc406bd4fff03672a4ab0268648`. A local run of Kaggle's published
`harbor-git-v1` image pinned at
`sha256:772dfa2383c07928ee020f8235323a81dee9ff519750e978f776cc0448533f32`
checked out that commit but failed before agent startup. Harbor 0.15's nested
egress-control sidecar exited because this Docker-in-Docker host could not
install its nftables `fib daddr type local` rules. The trial has a
`RuntimeError` and no trajectory, submission, CTRF, score, reward, token use,
or verifier result. This precisely blocks local/executor parity and is not
Kaggle-hosted evidence.

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
