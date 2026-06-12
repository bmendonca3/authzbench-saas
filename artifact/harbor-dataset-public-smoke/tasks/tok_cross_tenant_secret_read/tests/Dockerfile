# Public-safe placeholder verifier environment for Harbor.
# This file is not Harbor verifier/scorer parity evidence.
FROM python:3.11-slim
WORKDIR /workspace
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/tests
COPY test.sh /tests/test.sh
COPY task_manifest.json /tests/task_manifest.json
COPY authzbench /tests/authzbench
COPY apps /tests/apps
RUN chmod +x /tests/test.sh

# This image contains only public AuthZBench-SaaS scorer/app code
# copied into the generated verifier context.
