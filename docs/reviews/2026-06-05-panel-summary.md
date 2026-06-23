# Panel Review Summary: 2026-06-05

This grounded panel reviewed AuthZBench-SaaS as a public benchmark for AI agents
testing multi-tenant SaaS authorization. Reviewers were instructed to perform
read-only inspection only.

## Reviewers Counted

| Reviewer | Status |
| --- | --- |
| Gemini 3.5 Flash (High) | verified |
| Gemini 3.1 Pro (High) | verified |
| Claude Sonnet 4.6 (Thinking) | verified |
| Claude Opus 4.6 (Thinking) | verified |
| panel reviewer | verified |
| Kiro `claude-opus-4.8` | not counted; non-interactive tool approval failure |

## Highest-Value Findings

1. Live Docker targets used a static `dev` seed while task contexts used
   per-task seeds, so live HTTP testing with rendered task IDs could fail.
2. Scorer replay was in-process and single-request oriented, which made the
   benchmark easier to game and blocked multi-step evidence.
3. Vulnerable-task scoring checked the claim and proof request but did not
   validate the submitted actor/tenant/role boundary.
4. Docker Compose published target ports on all interfaces instead of localhost
   only.
5. Public leaderboard claims still need private holdout tasks and stronger
   agent isolation.

## Implemented Follow-Ups

- Added `assets/authzbench-saas-infographic.svg` and embedded it in `README.md`.
- Added `target` metadata to rendered contexts: local base URL, Docker-network
  base URL, task seed, and `x-authzbench-seed` header.
- Updated both HTTP target apps to honor `x-authzbench-seed`, so live Docker
  requests can match rendered task contexts.
- Changed Docker Compose port bindings to `127.0.0.1`.
- Added `expected_boundary` to vulnerable tasks and scorer validation for
  attacker/tenant/role boundary reasoning.
- Updated scorer replay so multi-request evidence executes sequentially against
  one seeded state and the final proof response is checked against the oracle.
- Fixed vulnerable-task control scoring so all controls must pass before
  `false_positive_control` receives credit.
- Reran scripted and model baselines under the stricter scorer.
- Added a live HTTP scripted baseline that exercises vulnerable proof requests
  against the running Docker targets before writing submissions.

## Still Open

- Build a non-public private holdout pack with 20-30 tasks, with 24 preferred
  for balanced coverage.
- Add route alias randomization and decoy endpoints.
- Add an isolated/containerized agent runner for leaderboard-grade submissions.
- Correlate target-side request logs or HAR-backed verification into runner
  artifacts to prove the agent actually exercised the live target, not only
  submitted replayable evidence.
