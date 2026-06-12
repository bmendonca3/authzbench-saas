#!/usr/bin/env bash
set -euo pipefail
mkdir -p /logs/artifacts /logs/verifier
if [ ! -s /logs/artifacts/submission.json ]; then
  python3 - <<'PY'
import json
from pathlib import Path
task = json.loads(Path('/tests/task_manifest.json').read_text())
score = {
    'task_id': task.get('id'),
    'score': 0,
    'passed': False,
    'invalid_submission': True,
    'reason': 'missing agent submission',
}
for path in (Path('/logs/artifacts/score.json'),):
    path.write_text(json.dumps(score, sort_keys=True) + '\n')
reward = {'reward': 0.0}
for path in (Path('/logs/artifacts/reward.json'), Path('/logs/verifier/reward.json')):
    path.write_text(json.dumps(reward, sort_keys=True) + '\n')
for path in (Path('/logs/artifacts/reward.txt'), Path('/logs/verifier/reward.txt')):
    path.write_text('0.0\n')
PY
  exit 0
fi
python3 - <<'PY'
import json
from pathlib import Path
from authzbench.core import dump_json, load_json
from authzbench.score import score_submission
task = load_json('/tests/task_manifest.json')
try:
    submission = load_json('/logs/artifacts/submission.json')
    score = score_submission(task, submission)
except Exception as exc:
    score = {
        'task_id': task.get('id'),
        'score': 0,
        'passed': False,
        'invalid_submission': True,
        'reason': 'invalid agent submission: ' + type(exc).__name__,
    }
Path('/logs/artifacts/score.json').write_text(dump_json(score) + '\n')
reward = float(score.get('score') or 0)
Path('/logs/artifacts/reward.json').write_text(json.dumps({'reward': reward}) + '\n')
Path('/logs/artifacts/reward.txt').write_text(f'{reward}\n')
Path('/logs/verifier/reward.json').write_text(json.dumps({'reward': reward}) + '\n')
Path('/logs/verifier/reward.txt').write_text(f'{reward}\n')
raise SystemExit(0)
PY
