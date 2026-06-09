# Hosted Evaluation Integration Sketch

Status: public-safe v1-prep design sketch. This is not hosted-evaluation
evidence, external-review evidence, platform acceptance, or v1 readiness.

## Goal

Map the current AuthZBench-SaaS runner, scorer, task manifests,
source-summary records, run bundles, and future private-pack workflow onto a
hosted or framework-driven evaluation surface without weakening the current
claim boundary.

The integration should preserve the benchmark's core evidence rule: a submitted
finding is useful only when the scorer can replay backend evidence against the
right actor, tenant, object, role, token, and control expectation. Secure
controls still require `findings: []`.

## Current Public Surface

- Public task manifests define local SaaS authorization scenarios, expected
  vulnerable or secure-control behavior, and scorer-owned replay metadata.
- The runner renders task context for no-tools and tool-agent harnesses.
- The scorer validates structured submissions by replaying backend requests.
- Source summaries, benchmark fingerprints, comparability keys, and run-bundle
  guidance describe provenance for public leaderboard-style rows.
- Public Docker rehearsal proves the isolation mechanism only. It is not
  release-candidate private-pack evidence.

## Hosted-Compatible Shape

A hosted evaluation should package each task as rendered context plus a
scorer-owned replay contract. The submitter receives only the rendered context
and an output location. The scorer retains task internals, private manifests,
oracles, raw captures, and replay controls.

Required per-run metadata:

- benchmark source SHA;
- task split and benchmark fingerprint;
- comparability key;
- runner image digest or hosted-runner version;
- exact command or hosted invocation;
- source-summary references;
- target-request coverage for tool-agent runs;
- private-pack version and active private-pack fingerprint when private tasks
  are used;
- isolation model;
- private-manifest denial proof;
- scorer access proof;
- cleanup status;
- public-output redaction proof.

## Compatibility Notes

Current simple publication resources can support public split packaging,
source-summary validation, benchmark fingerprints, comparability keys, public
run-bundle checks, and redacted public result rows.

Future Docker or hosted-task support is still required for release-candidate
private execution. That support must prove rendered-context-only submitter
access, scorer-controlled private replay, active private-pack fingerprint
matching, private-manifest denial, and redacted public outputs.

## Evidence Boundary

This sketch records an implementation direction only. It does not close the
external platform/framework gate. Closing that gate requires either reviewed
implementation evidence or bounded external review records tied to concrete
artifacts, commands, commits, and follow-up decisions.

Any external platform, model-team, SaaS-provider, or product-security feedback
must be converted into the structured review evidence shape before it affects
readiness claims.
