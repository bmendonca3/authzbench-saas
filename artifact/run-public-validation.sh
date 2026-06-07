#!/usr/bin/env bash
set -euo pipefail

python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_leaderboard_submission.py \
  --submission 'leaderboard_submissions/**/*.json' \
  --require-source-summary
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
