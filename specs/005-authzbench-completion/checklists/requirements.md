# Completion Requirements Checklist

## Requirements Quality

- [x] The target repository, starting source, authorization boundary, and
  private-data boundary are explicit.
- [x] Local product/benchmark defects are separated from source-freeze,
  private-maintainer, human-review, Kaggle, and launch gates.
- [x] Counts and terminology have one canonical truth:
  63 public, 48 public-safe private-summary, 111 total; 27 vulnerable,
  21 denial controls, and 15 authorized-allow controls.
- [x] Pending structural artifacts cannot be interpreted as completed evidence.
- [x] Success criteria are directly testable and do not depend on a particular
  executor or harness.

## Completion Gates

- [ ] Every local P0/P1 task in `tasks.md` is verified or rejected with direct
  evidence and rationale.
- [ ] Focused adversarial tests pass for every validator/runtime defect.
- [ ] Full dependency-free unit discovery executes all intended tests.
- [ ] Generated docs, tables, charts, paper inputs, and tracked artifacts have
  no unexplained drift.
- [ ] Privacy and claim-boundary scans pass.
- [ ] Clean/source-materialized install and reproduction pass.
- [ ] Strongest feasible public validation passes.
- [ ] Independent post-change audits have no unresolved local P0/P1 finding.
- [ ] Readiness and external gates state exact blockers without fabricated
  evidence.

## External Evidence Gates

- [ ] Exact-source Kaggle executor parity exists.
- [ ] Three independent review lanes have real dispositions on one frozen SHA.
- [ ] Separate SaaS/product-security review has a real disposition on that SHA.
- [ ] Private cohort mapping/disjointness/minimum analysis and decision exist.
- [ ] Organization, hosted operation, ownership, privacy, launch, publication,
  and leaderboard evidence exist.

The external boxes are deliberately expected to remain open during local-only
work. Their existence prevents a locally excellent candidate from being
misrepresented as approved by external reviewers or launched.
