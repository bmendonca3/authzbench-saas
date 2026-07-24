from __future__ import annotations

import argparse
import json
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from scripts.agy_baseline_agent import _extract_json, _prompt
except ModuleNotFoundError:  # Direct execution adds scripts/, not the repository root, to sys.path.
    from agy_baseline_agent import _extract_json, _prompt


API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"


def _metadata(
    model: str,
    *,
    returncode: int | None,
    effective_model: str | None,
    error: str | None = None,
    usage: dict[str, Any] | None = None,
    attempt_count: int = 1,
) -> dict[str, Any]:
    verified = effective_model == model
    result: dict[str, Any] = {
        "model": model,
        "provider": "gemini-developer-api",
        "authentication": "api-key-environment",
        "command": "Gemini generateContent API (credential omitted)",
        "returncode": returncode,
        "effective_model_label": effective_model,
        "model_label_verified": verified,
        "adapter_failed": error is not None,
        "attempt_count": attempt_count,
    }
    if usage:
        result["usage_metadata"] = usage
    if error is not None:
        result["parse_error"] = error
    return result


def run_gemini(
    context: dict[str, Any],
    *,
    model: str,
    api_key: str | None,
    timeout_seconds: int,
    urlopen: Any = urllib.request.urlopen,
    sleep: Any = time.sleep,
    max_retries: int = 5,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not api_key:
        return None, _metadata(model, returncode=None, effective_model=None, error="GEMINI_API_KEY is not set")
    payload = {
        "contents": [{"role": "user", "parts": [{"text": _prompt(context)}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0, "maxOutputTokens": 8192},
    }
    request = urllib.request.Request(
        f"{API_ROOT}/{model}:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    response_data: dict[str, Any] | None = None
    attempt_count = 0
    for attempt_count in range(1, max_retries + 2):
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt_count > max_retries:
                return None, _metadata(
                    model,
                    returncode=exc.code,
                    effective_model=None,
                    error=f"Gemini API HTTP {exc.code}",
                    attempt_count=attempt_count,
                )
            sleep(min(2 ** (attempt_count - 1), 16))
        except (urllib.error.URLError, socket.timeout, TimeoutError):
            if attempt_count > max_retries:
                return None, _metadata(
                    model,
                    returncode=None,
                    effective_model=None,
                    error="Gemini API request failed or timed out",
                    attempt_count=attempt_count,
                )
            sleep(min(2 ** (attempt_count - 1), 16))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None, _metadata(
                model,
                returncode=None,
                effective_model=None,
                error="Gemini API response was unreadable",
                attempt_count=attempt_count,
            )
    if response_data is None:
        return None, _metadata(model, returncode=None, effective_model=None, error="Gemini API retry loop exhausted", attempt_count=attempt_count)

    effective_model = response_data.get("modelVersion")
    usage = response_data.get("usageMetadata") if isinstance(response_data.get("usageMetadata"), dict) else None
    if effective_model != model:
        return None, _metadata(
            model,
            returncode=0,
            effective_model=effective_model if isinstance(effective_model, str) else None,
            error="Gemini API model label was not verified",
            usage=usage,
            attempt_count=attempt_count,
        )
    try:
        text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        submission = _extract_json(text)
    except (KeyError, IndexError, TypeError, ValueError):
        return None, _metadata(
            model,
            returncode=0,
            effective_model=effective_model,
            error="Gemini API output did not contain a valid submission",
            usage=usage,
            attempt_count=attempt_count,
        )
    if not isinstance(submission.get("findings"), list):
        return None, _metadata(
            model,
            returncode=0,
            effective_model=effective_model,
            error="model output findings must be a list",
            usage=usage,
            attempt_count=attempt_count,
        )
    return submission, _metadata(model, returncode=0, effective_model=effective_model, usage=usage, attempt_count=attempt_count)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gemini Developer API no-tools baseline adapter.")
    parser.add_argument("--model", default=os.environ.get("AUTHZBENCH_GEMINI_MODEL", "gemini-2.5-flash"))
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--max-retries", type=int, default=5)
    args = parser.parse_args(argv)

    context_path = Path(os.environ["AUTHZBENCH_CONTEXT"])
    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
    context = json.loads(context_path.read_text(encoding="utf-8"))
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    submission, metadata = run_gemini(
        context,
        model=args.model,
        api_key=os.environ.get("GEMINI_API_KEY"),
        timeout_seconds=args.timeout_seconds,
        max_retries=args.max_retries,
    )
    (submission_path.parent / "model-output.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if submission is None:
        submission_path.unlink(missing_ok=True)
        return 1
    submission_path.write_text(json.dumps(submission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
