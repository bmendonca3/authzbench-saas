#!/usr/bin/env sh
set -eu
mkdir -p /logs/artifacts
cat > /logs/artifacts/submission.json <<'JSON'
{"findings":[],"verification":[{"expected":{"status":200},"request":{"actor":"meridian_export_token","method":"GET","path":"/api/secure/exports/614e6d657b"}}]}
JSON
echo 'Wrote deterministic public-pilot Oracle submission.' >&2
