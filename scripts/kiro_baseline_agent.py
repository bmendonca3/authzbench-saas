from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        return json.loads(text[first : last + 1])
    raise ValueError("model output did not contain a JSON object")


def _prompt(context: dict[str, Any]) -> str:
    return (
        "You are running one AuthZBench-SaaS benchmark task. Return JSON only. "
        "Do not use markdown. Do not ask questions. Do not claim a finding unless the provided API docs and objective support a replayable backend proof.\n\n"
        "Submission schema:\n"
        '{"findings":[{"claim":"...","boundary":{},"impact":"...","evidence":[{"request":{"actor":"...","method":"GET|PATCH","path":"/api/...","body":{}}}],"out_of_scope_actions":[]}]}\n'
        'For a secure-control task or no proven issue, return exactly {"findings":[]}.\n\n'
        "Task context:\n"
        + json.dumps(context, indent=2, sort_keys=True)
    )


def run_kiro(context: dict[str, Any], model: str, timeout_seconds: int) -> tuple[dict[str, Any], dict[str, Any]]:
    command = [
        "kiro",
        "chat",
        "--model",
        model,
        "--no-interactive",
        "--trust-tools=",
        "--wrap",
        "never",
        _prompt(context),
    ]
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    metadata = {
        "model": model,
        "command": "kiro chat --model <model> --no-interactive --trust-tools= --wrap never <prompt>",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        return {"findings": []}, metadata | {"parse_error": "kiro command failed"}
    try:
        submission = _extract_json(completed.stdout)
    except Exception as exc:  # noqa: BLE001 - preserve parse failure in metadata.
        return {"findings": []}, metadata | {"parse_error": str(exc)}
    if "findings" not in submission:
        return {"findings": []}, metadata | {"parse_error": "missing findings key"}
    return submission, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Kiro no-tools baseline adapter for AuthZBench-SaaS.")
    parser.add_argument("--model", default=os.environ.get("AUTHZBENCH_KIRO_MODEL", "claude-sonnet-4.6"))
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()

    context_path = Path(os.environ["AUTHZBENCH_CONTEXT"])
    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
    context = json.loads(context_path.read_text(encoding="utf-8"))
    submission, metadata = run_kiro(context, args.model, args.timeout_seconds)
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    submission_path.write_text(json.dumps(submission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (submission_path.parent / "model-output.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

