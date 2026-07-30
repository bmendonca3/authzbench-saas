# AuthZBench-SaaS public validation image
#
# This is a single-image reproduction target for the public
# validation surface. It builds the apps/ fixtures into a
# per-port base image and exposes a single entrypoint that runs
# the public validation gates.
#
# It is intentionally separate from the per-app Dockerfiles under
# apps/*/Dockerfile, which are the target-app images that
# docker-compose.yml orchestrates. The image built from THIS file
# is the reviewer-side runner, not a target-app image.
FROM python:3.11-slim AS runner

WORKDIR /bench

# Install the project in editable mode. There are no third-party
# runtime dependencies for the public validation surface; see
# requirements.lock.
COPY pyproject.toml README.md LICENSE requirements.lock ./
COPY authzbench ./authzbench
COPY authzbench_harbor ./authzbench_harbor
COPY apps ./apps
COPY tasks ./tasks
COPY scripts ./scripts
COPY tests ./tests
COPY artifact ./artifact
COPY baselines ./baselines
COPY docs ./docs
COPY examples ./examples
COPY leaderboard_sources ./leaderboard_sources
COPY leaderboard_submissions ./leaderboard_submissions
COPY .python-version ./

RUN pip install --no-cache-dir -e .

# Default entrypoint runs the public validation gates with the
# scripted baseline and the CI claim-boundary checks.
ENTRYPOINT ["python", "scripts/validate_public.py"]
CMD ["--include-scripted-baseline"]
