# v0.0 Technical Report Panel Summary

Date: 2026-06-06

Scope: public-safe review of the v0.0 technical report draft, evidence map, and
release-facing status docs. Reviewers were asked to look for factual
contradictions, unsupported claims, stale v0-candidate wording, baseline-number
mismatches, privacy/leak risks, and reviewer objections. Raw panel logs were not
committed.

## Reviewers

- panel reviewer: local file and validation review.
- read-only reviewer: read-only public-safe file review.
- Kiro `claude-opus-4.8`: read-only review using `fs_read` only.

## Accepted Findings

1. Private leaderboard eligibility wording was contradictory because docs mixed
   an older reconstructed historical private row with a newer runner-emitted
   private row.
   - Disposition: accepted and patched. Current wording distinguishes the two:
     the newer source-backed private no-tools row is release-candidate eligible
     because its benchmark fingerprint provenance is runner-emitted, while the
     older reconstructed historical row remains non-eligible.

2. Released-state prose still used some v0-candidate wording.
   - Disposition: accepted and patched where it described current release state.
     The literal artifact metric profile `v0-candidate-authz-evidence` remains
     where it names stored result fields.

3. The stale 44-task live HTTP tool-agent row was omitted from the status table.
   - Disposition: accepted and patched.

4. The private holdout count should be treated as count-level redacted evidence,
   not as hidden task detail.
   - Disposition: accepted. README and roadmap now make clear that count-level
     summaries may be public while private task bodies, seeds, routes, oracles,
     raw captures, and per-task private rows must stay private.

## Rejected Or Narrowed Findings

- The phrase "five repeated model/agent families" is retained because the
  registry intentionally counts harness families, not only distinct base model
  names. Docs describe this as four no-tools model families plus one live HTTP
  tool-agent family to avoid implying five distinct base models.

## Remaining Reviewer Risks

- The benchmark is still small for v1/community claims.
- Public tasks remain inspectable and should not be used for private leaderboard
  rankings.
- Boundary-reasoning failures may need calibration or ablation in future work.
- Hosted or fully containerized third-party submission infrastructure is still
  future work.
