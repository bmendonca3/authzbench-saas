#!/usr/bin/env python3
"""Generate deny/setup/bypass evidence contracts for all public vulnerable tasks."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from authzbench.core import build_context, load_json
from scripts.scripted_baseline_agent import solve


EVIDENCE_CONTRACT_VERSION = "evidence-requirements-v2-deny-then-bypass"
TASK_GLOB = "tasks/*/*.json"


def _request_from_control(control: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(control[key])
        for key in ("actor", "method", "path", "headers", "body")
        if key in control
    }


def _template_value(value: Any, refs: dict[str, str]) -> Any:
    if isinstance(value, str):
        result = value
        for name, resolved in sorted(
            refs.items(),
            key=lambda item: len(str(item[1])),
            reverse=True,
        ):
            if str(resolved):
                result = result.replace(str(resolved), "{" + name + "}")
        return result
    if isinstance(value, list):
        return [_template_value(item, refs) for item in value]
    if isinstance(value, dict):
        return {key: _template_value(item, refs) for key, item in value.items()}
    return value


def _negative_control(task: dict[str, Any]) -> dict[str, Any]:
    controls = task.get("controls")
    if not isinstance(controls, list):
        raise ValueError(f"{task.get('id')}: controls must be a list")
    candidates = [
        control
        for control in controls
        if isinstance(control, dict)
        and isinstance(control.get("status"), int)
        and not isinstance(control.get("status"), bool)
        and not 200 <= control["status"] < 300
    ]
    if not candidates:
        raise ValueError(f"{task.get('id')}: no declared negative control")
    control = candidates[0]
    requirement: dict[str, Any] = {
        "name": f"negative_{control.get('name') or 'authorization_control'}",
        "index": 0,
        "request": _request_from_control(control),
        "status": control["status"],
    }
    if control.get("body_contains") not in (None, "", [], {}):
        requirement["body_contains"] = copy.deepcopy(control["body_contains"])
    return requirement


def _authored_positive_requirements(task: dict[str, Any]) -> list[dict[str, Any]]:
    existing = task.get("evidence_requirements")
    if isinstance(existing, list) and existing:
        authored = existing
        if task.get("evidence_contract_version") == EVIDENCE_CONTRACT_VERSION:
            # The current generated form always owns position zero. Strip that
            # generated negative control before rebuilding the canonical chain
            # so both check mode and repeated write mode are idempotent.
            authored = existing[1:]
        if authored:
            return [copy.deepcopy(requirement) for requirement in authored]

    context = build_context(task)
    submission = solve(context)
    findings = submission.get("findings") if isinstance(submission, dict) else None
    if not isinstance(findings, list) or len(findings) != 1:
        raise ValueError(f"{task.get('id')}: scripted oracle must return one finding")
    evidence = findings[0].get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError(f"{task.get('id')}: scripted oracle has no evidence")
    final_item = evidence[-1]
    if not isinstance(final_item, dict) or not isinstance(final_item.get("request"), dict):
        raise ValueError(f"{task.get('id')}: scripted oracle final request is malformed")
    oracle = task.get("oracle")
    if not isinstance(oracle, dict) or not isinstance(oracle.get("status"), int):
        raise ValueError(f"{task.get('id')}: oracle status is missing")
    requirement: dict[str, Any] = {
        "name": "authorization_bypass_proof",
        "index": 0,
        "request": _template_value(final_item["request"], context["refs"]),
        "status": oracle["status"],
    }
    if oracle.get("body_contains") not in (None, "", [], {}):
        requirement["body_contains"] = copy.deepcopy(oracle["body_contains"])
    return [requirement]


def expected_task(task: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(task)
    if result.get("expected_vulnerable") is not True:
        return result
    negative = _negative_control(result)
    positives = _authored_positive_requirements(result)
    requirements = [negative, *positives]
    for index, requirement in enumerate(requirements):
        requirement["index"] = index
    if not 200 <= int(requirements[-1].get("status", 0)) < 300:
        raise ValueError(f"{result.get('id')}: final bypass proof must be successful")
    result["evidence_contract_version"] = EVIDENCE_CONTRACT_VERSION
    result["evidence_requirements"] = requirements
    final_index = len(requirements) - 1
    result["output_schema"] = (
        "Submit JSON with findings[0].claim, "
        f"evidence[0..{final_index}].request in the required "
        "negative-control/setup/bypass order, boundary, impact, and "
        "out_of_scope_actions."
    )
    return result


def generate(root: Path = ROOT, *, write: bool = False) -> dict[str, Any]:
    changed: list[str] = []
    vulnerable_count = 0
    for path in sorted(root.glob(TASK_GLOB)):
        task = load_json(path)
        if not isinstance(task, dict):
            raise ValueError(f"{path}: task root must be an object")
        if task.get("expected_vulnerable") is not True:
            continue
        vulnerable_count += 1
        expected = expected_task(task)
        rendered = json.dumps(expected, indent=2, ensure_ascii=True) + "\n"
        if path.read_text(encoding="utf-8") != rendered:
            changed.append(path.relative_to(root).as_posix())
            if write:
                path.write_text(rendered, encoding="utf-8")
    return {
        "schema_version": "vulnerable-evidence-contract-generation-v1",
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "public_task_count": len(list(root.glob(TASK_GLOB))),
        "vulnerable_task_count": vulnerable_count,
        "changed_paths": changed,
        "passed": not changed or write,
        "write": write,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = generate(args.root.resolve(), write=args.write)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["changed_paths"] and not args.write:
        print(
            "vulnerable evidence contracts are stale: "
            + ", ".join(result["changed_paths"]),
            file=sys.stderr,
        )
    else:
        print(
            "vulnerable evidence contracts: "
            f"{result['vulnerable_task_count']} vulnerable / "
            f"{result['public_task_count']} public tasks; "
            f"changed={len(result['changed_paths'])}"
        )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
