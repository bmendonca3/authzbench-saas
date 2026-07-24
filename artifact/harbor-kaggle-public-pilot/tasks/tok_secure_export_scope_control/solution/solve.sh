#!/usr/bin/env sh
set -eu
mkdir -p /logs/artifacts
cat > /logs/artifacts/submission.json <<'JSON'
{"findings":[],"verification":[{"expected":{"status":403},"request":{"actor":"meridian_read_token","method":"GET","path":"/api/secure/exports/1014b9f5f3"}}]}
JSON
echo 'Wrote deterministic public-pilot Oracle submission.' >&2
