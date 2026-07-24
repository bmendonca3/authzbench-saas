# AuthZBench-SaaS Improvement Roadmap Specification

Status: active audit specification
Classification: full Spec Kit workflow

## Purpose

Define an evidence-backed roadmap for improving AuthZBench-SaaS without
repeating work already present in the clean hardening candidate or overstating
public, private, hosted, or externally validated evidence.

## User Scenarios

### US-001 — Maintainer chooses the next high-leverage benchmark work

Given the current repository, preserved result artifacts, and hardening branch,
the maintainer can see which changes most improve measurement validity, why they
matter, what they depend on, and how to verify them.

### US-002 — Reviewer can audit every roadmap claim

An independent benchmark, AppSec, or agent-tooling reviewer can trace every
priority to repository paths, artifact fields, commands, or current external
status and can distinguish verified facts from recommendations.

### US-003 — Host integration work follows the current contract

The Kaggle/Harbor workstream distinguishes the public Kaggle Benchmarks task
workflow, Harbor container/task format, and host-specific onboarding decisions,
without claiming that one path supersedes another absent a Kaggle response.

### US-004 — Expensive evaluation runs are evidence-driven

The maintainer receives a bounded Kiro rerun decision: run only when a named
measurement question cannot be answered from current artifacts, with source,
protocol, model, seed, and stopping gates defined before execution.

## Functional Requirements

- **FR-001**: Audit the exact named checkout and preserve all pre-existing work.
- **FR-002**: Reconcile recommendations against the clean 18-commit-ahead hardening candidate so completed work is not re-proposed.
- **FR-003**: Cover task design, scorer semantics, runner/adapters, baselines, statistics, provenance, anti-gaming, tests, documentation, paper, external review, and host integration.
- **FR-004**: Verify current Google/Kaggle status from the complete relevant Gmail thread plus broader recent sender/topic searches, without mutating mail.
- **FR-005**: Compare repo host materials with current primary Kaggle Benchmarks, Kaggle CLI/skill, and Harbor contracts.
- **FR-006**: Rank improvements by benchmark-validity impact, external credibility, dependency order, risk, and verification cost.
- **FR-007**: Give every recommended work item an owner role, affected surface, dependency, acceptance condition, direct verification, and claim boundary.
- **FR-008**: Decide explicitly whether a fresh Kiro run is needed; do not run one when current evidence is sufficient.
- **FR-009**: Keep private holdout bodies, raw private evidence, secrets, credentials, and external writes outside scope.
- **FR-010**: Preserve a durable attempt ledger and requirement-to-evidence traceability for continuation.

## Edge Cases

- The named checkout is dirty while the latest candidate is a separate clean worktree.
- Documentation may describe historical 44/46/49/54/60-task states alongside the current 63-task split.
- Passing fixture or `--allow-incomplete` validation must not be reported as readiness or external acceptance.
- Offline rescoring must not be called fresh model execution.
- Requested model identity must not be treated as independently verified effective identity.
- Kaggle's public task CLI may coexist with a separate organization/Harbor onboarding path.
- A full benchmark command can exit nonzero because of model quality, infrastructure, or protocol failure; these must remain distinct.

## Success Criteria

- **SC-001**: Every material audit lane is complete or explicitly blocked with evidence.
- **SC-002**: Every P0/P1 roadmap item maps to at least one exact repository or external-status source and one acceptance check.
- **SC-003**: No P0/P1 item merely restates work already implemented on `improve/evidence-backed-hardening`.
- **SC-004**: Google/Kaggle status is current through July 14, 2026 and clearly labeled as read-only mailbox evidence.
- **SC-005**: The Kiro decision names the unresolved question, run/no-run verdict, and prerequisites; no expensive run is launched without satisfying that gate.
- **SC-006**: Independent completeness review finds no missing material requirement or undocumented evidence gap.

## Non-Goals

- Implementing benchmark changes in this audit turn.
- Reading raw private holdout manifests or raw private results.
- Sending email, creating Kaggle resources, publishing packages, changing PRs,
  committing, pushing, merging, or releasing.
- Declaring platform acceptance, external validation, hosted operation, or a
  research-grade leaderboard.
