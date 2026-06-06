# AuthZBench-SaaS v0.0

Draft release notes. These notes are intended for the `v0.0` GitHub Release
after the final tag target has passed post-push CI.

AuthZBench-SaaS v0.0 is the first evidence-backed release snapshot of a SaaS
authorization benchmark for evaluating whether AI agents can prove
authorization failures with backend replay evidence while avoiding false
positives on secure controls.

Included:

- 6 synthetic SaaS apps
- 46 public tasks
- 19 vulnerable tasks and 27 secure-control tasks
- deterministic backend replay scoring
- public baseline summaries
- repeated current public model/tool-agent baseline evidence
- protected private-holdout evidence summarized without private task leakage
- leaderboard-submission schema and validation
- release-gate, privacy, Docker smoke, fresh-clone, and CI evidence

Not included:

- hosted public leaderboard
- rotating private holdout packs
- v1/community-scale benchmark claims
- production vulnerability discovery claims
