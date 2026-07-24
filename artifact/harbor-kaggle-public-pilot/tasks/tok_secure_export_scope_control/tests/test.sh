#!/usr/bin/env sh
set -eu
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
for path in (Path('/logs/artifacts/score.json'), Path('/logs/verifier/score.json')):
    path.write_text(json.dumps(score, sort_keys=True) + '\n')
reward = {'reward': 0.0}
for path in (Path('/logs/artifacts/reward.json'), Path('/logs/verifier/reward.json')):
    path.write_text(json.dumps(reward, sort_keys=True) + '\n')
for path in (Path('/logs/artifacts/reward.txt'), Path('/logs/verifier/reward.txt')):
    path.write_text('0.0\n')
ctrf = {
    'results': {
        'tool': {'name': 'authzbench-saas', 'version': 'score-policy-v2'},
        'summary': {'tests': 1, 'passed': 0, 'failed': 1, 'skipped': 0, 'pending': 0, 'other': 0, 'start': 0, 'stop': 0},
        'tests': [{'name': 'authorization-verifier::' + str(task.get('id')), 'status': 'failed', 'duration': 0, 'start': 0, 'stop': 0, 'retries': 0, 'file_path': 'tests/test.sh'}],
    }
}
Path('/logs/verifier/ctrf.json').write_text(json.dumps(ctrf, sort_keys=True) + '\n')
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
    score = score_submission(task, submission, require_control_verification=True)
except Exception as exc:
    score = {
        'task_id': task.get('id'),
        'score': 0,
        'passed': False,
        'invalid_submission': True,
        'reason': 'invalid agent submission: ' + type(exc).__name__,
    }
for path in (Path('/logs/artifacts/score.json'), Path('/logs/verifier/score.json')):
    path.write_text(dump_json(score) + '\n')
reward = float(score.get('score') or 0)
Path('/logs/artifacts/reward.json').write_text(json.dumps({'reward': reward}) + '\n')
Path('/logs/artifacts/reward.txt').write_text(f'{reward}\n')
Path('/logs/verifier/reward.json').write_text(json.dumps({'reward': reward}) + '\n')
Path('/logs/verifier/reward.txt').write_text(f'{reward}\n')
passed = bool(score.get('passed')) and reward == 1.0
status = 'passed' if passed else 'failed'
ctrf = {
    'results': {
        'tool': {'name': 'authzbench-saas', 'version': 'score-policy-v2'},
        'summary': {'tests': 1, 'passed': int(passed), 'failed': int(not passed), 'skipped': 0, 'pending': 0, 'other': 0, 'start': 0, 'stop': 0},
        'tests': [{'name': 'authorization-verifier::' + str(task.get('id')), 'status': status, 'duration': 0, 'start': 0, 'stop': 0, 'retries': 0, 'file_path': 'tests/test.sh'}],
    }
}
Path('/logs/verifier/ctrf.json').write_text(json.dumps(ctrf, sort_keys=True) + '\n')
raise SystemExit(0)
PY
