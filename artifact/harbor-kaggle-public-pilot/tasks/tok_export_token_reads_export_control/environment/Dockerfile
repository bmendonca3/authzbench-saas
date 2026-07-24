# Public-safe placeholder environment for the Harbor dataset skeleton.
# This file is not Harbor execution evidence.
FROM python:3.11-alpine
# Harbor 0.13.2 wraps Docker exec commands with `bash -c`; the
# generated scripts remain POSIX sh, so forward that wrapper to sh.
RUN printf '#!/bin/sh\nexec /bin/sh "$@"\n' > /bin/bash && chmod +x /bin/bash
WORKDIR /workspace
ENV PYTHONUNBUFFERED=1
COPY context.json environment/context.json

# A verified Harbor adapter must replace this placeholder with a
# pinned image/package path that provides authzbench scoring code.
