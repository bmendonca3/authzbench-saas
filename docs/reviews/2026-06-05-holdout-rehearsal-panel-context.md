# Holdout Rehearsal Workflow Panel Context

Question: Does the private-holdout rehearsal workflow improve v0 readiness
without misleading users into treating generated rehearsal tasks as real private
leaderboard holdouts?

Reviewed section:

- `scripts/generate_holdout_rehearsal_pack.py`
- `tests/test_holdout_rehearsal_generator.py`
- `scripts/validate_holdout_pack.py`
- `docs/holdout-and-contamination.md`
- `tasks_private/README.md`
- `ROADMAP.md`
- `docs/status.md`
- `docs/publish-checklist.md`
- `README.md`

Parent-verified facts:

- The generator writes 24 local tasks under `tasks_private/holdout/rehearsal/`.
- The generated pack covers six app families with four rehearsal tasks per app.
- The generated pack has 12 vulnerable tasks, 12 controls, 7 denial controls,
  and 5 authorized-allow controls.
- `leaderboard_suitable` is set to `false` in generator output.
- Generated rehearsal manifests set `leaderboard_suitable` to `false`, and the
  holdout validator reports rehearsal warnings when those manifests are present.
- Generated manifests set `split=private_holdout`, use non-public IDs and
  seeds, and pass `scripts/validate_holdout_pack.py`.
- `tasks_private/holdout/` is ignored by Git.
- The public repository still contains zero private holdout manifests.
- The docs state that the rehearsal pack is a workflow test only and must not be
  used for private leaderboard scoring or a `v0` release claim.

Verification already run:

```bash
python3.11 -Wd -m unittest tests.test_holdout_rehearsal_generator tests.test_holdout_validator
python3.11 scripts/generate_holdout_rehearsal_pack.py --dry-run
python3.11 scripts/generate_holdout_rehearsal_pack.py --force
python3.11 scripts/validate_holdout_pack.py
python3.11 scripts/validate_public.py --include-scripted-baseline
python3.11 scripts/validate_public.py --fresh-clone https://github.com/bmendonca3/authzbench-saas.git --include-scripted-baseline
git check-ignore -v tasks_private/holdout/rehearsal/project_mgmt/holdout_rehearsal_001_2d44f4eb.json
```

Remaining known v0 gaps:

- The rehearsal pack is generated from public task structure and is not a real
  secret holdout.
- Real v0 still needs non-public human-designed holdout tasks, protected
  holdout execution, repeated real model baselines, live Docker runtime smoke,
  stronger route alias/randomization, and final release-readiness review.
