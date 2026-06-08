# Current 54-Task GLM Evidence Review Summary

Status: promotion review in progress. This is internal review evidence, not one
of the three required external v1 review lanes.

## Scope

The review covers both current 54-task `glm-5` no-tools summaries,
raw-to-promoted fidelity, fingerprint and run provenance, retained runner
failure diagnostics, registry counts, charts, tests, prose, and claim
boundaries.

## Raw Evidence

- Run `20260607T201255153205Z-5de7a354`: 54 tasks, 33 passed,
  `mean_score: 0.6389`, 2/21 exploit-proven vulnerable tasks, zero boundary
  reasoning, zero vulnerable full passes, `false_positive_rate: 0.0`,
  `authorized_allow_pass_rate: 1.0`, one invalid submission, and two
  scorer-counted findings.
- Run `20260608T002053809050Z-e50a764c`: 54 tasks, 33 passed,
  `mean_score: 0.6583`, 3/21 exploit-proven vulnerable tasks, zero boundary
  reasoning, zero vulnerable full passes, `false_positive_rate: 0.0`,
  `authorized_allow_pass_rate: 1.0`, zero invalid submissions, and four
  scorer-counted findings.
- Both runs use benchmark commit
  `73d7b111360cc2439ae5ff418e8b5171e96bb395` and task-set fingerprint
  `f8d19cb89d347d1397f85bf978e6b7b232e8a2f1307fc2ac6ba02674e5c23c9f`.
- Run 1 contains 54 `score.json`, 54 `agent.json`, and 54 `transcript.json`
  files, but only 53 `submission.json` and 53 `model-output.json` files because
  the outer runner failed before writing those artifacts for
  `sup_multistep_agent_status_then_admin_reassignment`.
- Run 2 contains 54 task directories and 54 each of `score.json`,
  `submission.json`, `model-output.json`, `agent.json`, and `transcript.json`.
- The earlier partial retry directory
  `results/kiro-glm-5-current-public-54-run2/20260607T202727938690Z-c8ea2cd3`
  is excluded from promotion evidence because it stopped after 8/54 tasks and
  has no runner summary.

## Interpretation

The GLM-5 pair adds a fourth current no-tools family on the active 54-task
public split. It is diagnostic public evidence only. Both runs report no
secure-control findings, and neither run earns boundary-reasoning credit or a
full vulnerable-task pass. Run 1's invalid submission is preserved as an outer
runner failure with missing submission/model-output diagnostics; run 2 is the
clean retry with complete artifacts.

## Independent Audit

- Kiro Claude Opus 4.8 independently reconciled raw summaries, promoted
  summaries, run-provenance fields, the partial retry exclusion, run 1 runner
  failure diagnostics, run 2 complete artifacts, chart means, registry scope,
  and review-registry wording. It returned `VERDICT: CLEAN`.
- Kiro Claude Opus 4.8 independently audited docs, tests, expected public
  readiness output, paper text, and stale/current claim boundaries. It first
  returned `VERDICT: FINDINGS` for a stale IEEE-paper sentence that still said
  only Qwen had been rerun on the 54-task split. The paper now names the
  current Qwen3 Coder Next, Claude Haiku 4.5, Claude Sonnet 4.6, and GLM-5
  no-tools families and leaves Claude Opus 4.6 plus the live HTTP tool-agent
  pair pending.
- The Kiro Claude Opus 4.8 claims re-audit verified the paper fix, goal state,
  registry tests, readiness fixture, and public-only claim boundaries. It
  returned `VERDICT: CLEAN`.

## Local Verification

- Raw-to-promoted summary fidelity passed for both GLM runs after stripping only
  the declared diagnostic-only promotion keys.
- Parent artifact census confirmed run 1 has 54 task directories with one
  missing `submission.json`/`model-output.json` pair on
  `sup_multistep_agent_status_then_admin_reassignment`, run 2 has complete
  54-task artifacts, and the earlier partial retry has no summary and is
  excluded.
- Parent model-output census found zero nonzero return codes, zero parse
  errors, and zero empty stdout values across the retained GLM `model-output`
  artifacts.
- `python3 -m unittest discover -s tests`: 195 tests passed.
- `python3 scripts/validate_public.py --include-scripted-baseline`: passed,
  including generated-artifact checks and the 54/54 deterministic scripted
  baseline.
- Strict v0 release, baseline-registry, and leaderboard-submission validation
  passed.
- `python3 scripts/generate_paper_tables.py && git diff --exit-code --
  paper/shared`: passed.
- `git diff --check` passed.
- `git ls-files tasks_private/holdout results captures docs/reviews/panel-logs`
  returned no tracked paths.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` produced the
  IEEE paper PDF. Log scan found no undefined references or citations, LaTeX
  errors, fatal stops, emergency stops, undefined control sequences, or overfull
  boxes. Existing underfull-box warnings and the Tectonic bibliography rerun
  warning remain nonblocking.
- Local container smoke was not rerun because the Docker Desktop daemon is
  unavailable in the local environment.

## Completion Gate

Do not mark this GLM promotion review complete until the independent Kiro Opus
audits return clean verdicts or all valid findings are fixed, local verification
passes, the promotion and paper-preflight commits are pushed, and exact-head CI
passes on the resulting head. As of this review snapshot, independent audits
and local verification are complete; push, exact-head CI, and the follow-up
paper-source-pin preflight remain open.
