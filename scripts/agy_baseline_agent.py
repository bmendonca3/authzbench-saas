from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


def _subprocess_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict) and "findings" in parsed:
            return parsed
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1))
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict) and "findings" in parsed:
            return parsed
    decoder = json.JSONDecoder()
    for match in reversed(list(re.finditer(r"\{", text))):
        try:
            parsed, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "findings" in parsed:
            return parsed
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


def _effective_model_label(log_text: str) -> str | None:
    labels = re.findall(r'Propagating selected model override to backend: label="([^"]+)"', log_text)
    return labels[-1] if labels else None


def run_agy(
    context: dict[str, Any],
    model: str,
    timeout_seconds: int,
    log_path: Path,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    command = [
        "agy",
        "--new-project",
        "--model",
        model,
        "--log-file",
        str(log_path),
        "--print-timeout",
        f"{timeout_seconds}s",
        "--print",
        _prompt(context),
    ]
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout_seconds + 30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return None, {
            "model": model,
            "command": "agy --new-project --model <model> --log-file <log> --print-timeout <seconds>s --print <prompt>",
            "returncode": None,
            "stdout": _subprocess_text(exc.stdout),
            "stderr": _subprocess_text(exc.stderr),
            "log_file": log_path.name,
            "effective_model_label": None,
            "model_label_verified": False,
            "parse_error": "agy command timed out",
        }
    log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    effective_label = _effective_model_label(log_text)
    metadata = {
        "model": model,
        "command": "agy --new-project --model <model> --log-file <log> --print-timeout <seconds>s --print <prompt>",
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "log_file": log_path.name,
        "effective_model_label": effective_label,
        "model_label_verified": effective_label == model,
    }
    if completed.returncode != 0:
        return None, metadata | {"parse_error": "agy command failed"}
    if effective_label != model:
        return None, metadata | {"parse_error": "agy model label was not verified"}
    try:
        submission = _extract_json(completed.stdout)
    except Exception as exc:  # noqa: BLE001 - preserve parse failure in metadata.
        return None, metadata | {"parse_error": str(exc)}
    if "findings" not in submission:
        return None, metadata | {"parse_error": "missing findings key"}
    return submission, metadata


def _write_adapter_result(
    submission_path: Path,
    submission: dict[str, Any] | None,
    metadata: dict[str, Any],
) -> int:
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path = submission_path.parent / "model-output.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if submission is None:
        submission_path.unlink(missing_ok=True)
        return 2
    submission_path.write_text(json.dumps(submission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Antigravity agy no-tools baseline adapter for AuthZBench-SaaS.")
    parser.add_argument("--model", default=os.environ.get("AUTHZBENCH_AGY_MODEL", "Gemini 3.5 Flash (High)"))
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()

    context_path = Path(os.environ["AUTHZBENCH_CONTEXT"])
    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
    context = json.loads(context_path.read_text(encoding="utf-8"))
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = submission_path.parent / "antigravity-cli.log"
    submission, metadata = run_agy(context, args.model, args.timeout_seconds, log_path)
    return _write_adapter_result(submission_path, submission, metadata)


if __name__ == "__main__":
    raise SystemExit(main())
