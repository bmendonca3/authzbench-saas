# Review Artifacts

This directory keeps the lightweight review trail for benchmark sections.

Each context packet is a point-in-time snapshot. Older files may mention earlier
task counts, app counts, or open blockers that changed in later commits. Treat
the newest status files, roadmap, release plan, and validation output as the
current state.

For release claims, a section is not ready just because a review artifact
exists. The section should have:

- a clear review question
- the files and commands supplied to reviewers
- counted reviewers or a clear unavailable-reviewer note
- accepted findings with follow-up commits or decisions
- rejected findings with reasons when relevant
- remaining release risks

Raw model, CLI, account, and local-system logs should stay out of the public
repo. Summaries should preserve the useful findings without exposing private
metadata.

For external v1/community readiness review, use
`external-review-response.template.json` only as a starting shape for real
reviewer responses. The template is public-safe scaffolding, not review
evidence, and the v1 readiness validator rejects it if it is copied unchanged
into `external-review-summary.json`.
The same validator also rejects unresolved placeholders embedded in pending or
completed review fields, including `TBD`, `TODO`, `pending`, `unknown`, `n/a`,
and angle-bracket placeholders, and scans completed external-review evidence
for sensitive private-path markers, sensitive private-evidence keys, and local
absolute paths.
