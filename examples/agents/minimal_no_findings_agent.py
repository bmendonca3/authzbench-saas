from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> int:
    context_path = Path(os.environ["AUTHZBENCH_CONTEXT"])
    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])

    # Read the context to prove the runner contract is wired. This template is
    # intentionally conservative and reports no findings.
    json.loads(context_path.read_text(encoding="utf-8"))
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    submission_path.write_text(json.dumps({"findings": []}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
