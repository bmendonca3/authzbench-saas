#!/usr/bin/env bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/submission.json <<'JSON'
{"findings":[]}
JSON
echo 'Wrote public secure-control empty-findings submission.' >&2
