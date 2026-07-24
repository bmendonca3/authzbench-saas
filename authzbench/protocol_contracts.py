from __future__ import annotations

import glob
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .core import build_context, load_app, replay_request, resolve_templates, stable_json_sha256
from .score import _contains_subset, _evidence_requirement_matches
from .validate_manifests import validate_manifest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = REPOSITORY_ROOT / "schemas/blinded-control-evidence-v2.schema.json"
SCHEMA_BUNDLE_VERSION = "blinded-control-evidence-v2-draft"
EVIDENCE_CONTRACT_VERSION = "evidence-requirements-v2-draft"
SCHEMA_STATUS = "draft-non-promotable"
EXPECTED_SCHEMA_CANONICAL_SHA256 = "4442c9fddc8f10ceb35912dff789037746d857ea4c1ceabca3b13b104ab4a4f1"
REQUIRED_SCHEMA_DEFINITIONS = {
    "controlVerification",
    "evidenceItem",
    "meaningfulJsonMatch",
    "participantSubmission",
    "replayRequest",
    "runSummaryContractIdentity",
    "taskEvidenceRequirement",
    "vulnerableFinding",
}


class DuplicateJsonKeyError(ValueError):
    pass


class NonFiniteJsonNumberError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_without_duplicate_keys(path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise NonFiniteJsonNumberError(f"non-finite JSON number: {value}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(
            handle,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=reject_constant,
        )


def validate_schema_bundle(schema: Any) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(schema, dict):
        return [{"code": "schema_root_invalid", "detail": "schema root must be an object"}]
    expected_values = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:authzbench:schemas:blinded-control-evidence-v2",
        "x-authzbench-status": SCHEMA_STATUS,
        "x-authzbench-version": SCHEMA_BUNDLE_VERSION,
    }
    for field, expected in expected_values.items():
        if schema.get(field) != expected:
            findings.append(
                {
                    "code": "schema_identity_invalid",
                    "detail": f"{field} must equal {expected!r}",
                }
            )
    definitions = schema.get("$defs")
    if not isinstance(definitions, dict):
        findings.append(
            {"code": "schema_definitions_invalid", "detail": "$defs must be an object"}
        )
    else:
        missing = sorted(REQUIRED_SCHEMA_DEFINITIONS - set(definitions))
        if missing:
            findings.append(
                {
                    "code": "schema_definitions_missing",
                    "detail": f"missing definitions: {', '.join(missing)}",
                }
            )
        for name in sorted(REQUIRED_SCHEMA_DEFINITIONS & set(definitions)):
            if not isinstance(definitions[name], dict):
                findings.append(
                    {
                        "code": "schema_definition_invalid",
                        "detail": f"$defs.{name} must be an object",
                    }
                )
    if schema.get("$ref") != "#/$defs/participantSubmission":
        findings.append(
            {
                "code": "schema_root_reference_invalid",
                "detail": "$ref must select the participantSubmission definition",
            }
        )
    return findings


def schema_bundle_identity(schema_path: Path = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    schema = load_json_without_duplicate_keys(schema_path)
    findings = validate_schema_bundle(schema)
    canonical_sha256 = stable_json_sha256(schema)
    if canonical_sha256 != EXPECTED_SCHEMA_CANONICAL_SHA256:
        findings.append(
            {
                "code": "schema_digest_mismatch",
                "detail": (
                    "canonical schema digest changed without an explicit versioned identity update"
                ),
            }
        )
    return {
        "schema_version": SCHEMA_BUNDLE_VERSION,
        "status": SCHEMA_STATUS,
        "canonical_sha256": canonical_sha256,
        "valid": not findings,
        "findings": findings,
    }


def _finding(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _unexpected_fields(value: dict[Any, Any], allowed: set[str]) -> list[str]:
    return sorted(
        (key if isinstance(key, str) else repr(key))
        for key in value
        if key not in allowed
    )


def _request_findings(request: Any, path: str) -> list[dict[str, str]]:
    if not isinstance(request, dict):
        return [_finding("replay_request_invalid", path, "request must be an object")]
    findings: list[dict[str, str]] = []
    allowed = {"actor", "method", "path", "headers", "body"}
    extra = _unexpected_fields(request, allowed)
    if extra:
        findings.append(
            _finding("replay_request_extra_fields", path, f"unexpected fields: {', '.join(extra)}")
        )
    for field in ("actor", "method", "path"):
        if not isinstance(request.get(field), str) or not request[field].strip():
            findings.append(
                _finding("replay_request_missing_field", path, f"{field} must be a non-empty string")
            )
    method = request.get("method")
    if isinstance(method, str) and method and re.fullmatch(r"[A-Z]+", method) is None:
        findings.append(
            _finding("replay_request_method_invalid", path, "method must contain uppercase letters only")
        )
    request_path = request.get("path")
    if isinstance(request_path, str) and request_path and (
        not request_path.startswith("/")
        or any(ord(character) < 0x20 or ord(character) > 0x7E for character in request_path)
    ):
        findings.append(
            _finding("replay_request_path_invalid", path, "path must start with /")
        )
    if "headers" in request:
        headers = request["headers"]
        if not isinstance(headers, dict) or not all(
            isinstance(key, str)
            and re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", key) is not None
            and isinstance(value, str)
            and all(character == "\t" or 0x20 <= ord(character) <= 0x7E for character in value)
            for key, value in headers.items()
        ):
            findings.append(
                _finding("replay_request_headers_invalid", path, "headers must map strings to strings")
            )
    if "body" in request and not isinstance(request["body"], dict):
        findings.append(
            _finding("replay_request_body_invalid", path, "body must be an object")
        )
    return findings


def validate_participant_submission_v2(submission: Any) -> list[dict[str, str]]:
    root_path = "submission"
    if not isinstance(submission, dict):
        return [_finding("submission_root_invalid", root_path, "submission must be an object")]
    findings: list[dict[str, str]] = []
    extra = _unexpected_fields(submission, {"findings", "verification"})
    if extra:
        findings.append(
            _finding("submission_extra_fields", root_path, f"unexpected fields: {', '.join(extra)}")
        )
    submitted_findings = submission.get("findings")
    if not isinstance(submitted_findings, list):
        return findings + [
            _finding("submission_findings_invalid", root_path, "findings must be a list")
        ]
    if len(submitted_findings) > 1:
        findings.append(
            _finding("submission_findings_ambiguous", root_path, "at most one primary finding is allowed")
        )

    verification = submission.get("verification")
    if submitted_findings:
        if "verification" in submission:
            findings.append(
                _finding(
                    "submission_mode_ambiguous",
                    root_path,
                    "a vulnerable finding submission must not include verification",
                )
            )
        finding = submitted_findings[0]
        finding_path = "submission.findings[0]"
        if not isinstance(finding, dict):
            return findings + [
                _finding("vulnerable_finding_invalid", finding_path, "finding must be an object")
            ]
        allowed_finding = {"claim", "evidence", "boundary", "impact", "out_of_scope_actions"}
        extra_finding = _unexpected_fields(finding, allowed_finding)
        if extra_finding:
            findings.append(
                _finding(
                    "vulnerable_finding_extra_fields",
                    finding_path,
                    f"unexpected fields: {', '.join(extra_finding)}",
                )
            )
        for field in ("claim", "impact"):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                findings.append(
                    _finding(
                        "vulnerable_finding_missing_field",
                        finding_path,
                        f"{field} must be a non-empty string",
                    )
                )
        boundary = finding.get("boundary")
        if not isinstance(boundary, dict) or not boundary or not all(
            isinstance(key, str)
            and bool(key.strip())
            and isinstance(value, str)
            and bool(value.strip())
            for key, value in (boundary.items() if isinstance(boundary, dict) else [])
        ):
            findings.append(
                _finding(
                    "vulnerable_finding_boundary_invalid",
                    finding_path,
                    "boundary must be a non-empty string-to-string object",
                )
            )
        evidence = finding.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            findings.append(
                _finding(
                    "vulnerable_finding_evidence_invalid",
                    finding_path,
                    "evidence must contain at least one request item",
                )
            )
        else:
            for index, item in enumerate(evidence):
                item_path = f"{finding_path}.evidence[{index}]"
                if not isinstance(item, dict) or set(item) != {"request"}:
                    findings.append(
                        _finding(
                            "evidence_item_invalid",
                            item_path,
                            "evidence item must contain exactly one request field",
                        )
                    )
                    continue
                findings.extend(_request_findings(item["request"], f"{item_path}.request"))
        actions = finding.get("out_of_scope_actions")
        if not isinstance(actions, list) or not all(
            isinstance(action, str) and bool(action.strip()) for action in actions
        ):
            findings.append(
                _finding(
                    "vulnerable_finding_actions_invalid",
                    finding_path,
                    "out_of_scope_actions must be a list of non-empty strings",
                )
            )
    else:
        if not isinstance(verification, list) or not verification:
            findings.append(
                _finding(
                    "control_verification_missing",
                    root_path,
                    "findings: [] requires at least one verification item",
                )
            )
        elif len(verification) != 1:
            findings.append(
                _finding(
                    "control_verification_count_invalid",
                    root_path,
                    "findings: [] requires exactly one verification item",
                )
            )
        else:
            for index, item in enumerate(verification):
                item_path = f"submission.verification[{index}]"
                if not isinstance(item, dict) or set(item) != {"request", "expected"}:
                    findings.append(
                        _finding(
                            "control_verification_invalid",
                            item_path,
                            "verification item must contain exactly request and expected",
                        )
                    )
                    continue
                findings.extend(_request_findings(item["request"], f"{item_path}.request"))
                expected = item["expected"]
                status = expected.get("status") if isinstance(expected, dict) else None
                if (
                    not isinstance(expected, dict)
                    or set(expected) != {"status"}
                    or isinstance(status, bool)
                    or not isinstance(status, int)
                    or not 100 <= status <= 599
                ):
                    findings.append(
                        _finding(
                            "control_verification_expected_invalid",
                            f"{item_path}.expected",
                            "expected must contain exactly one integer HTTP status from 100 to 599",
                        )
                    )
    return findings


def _evidence_requirement_findings(task: dict[str, Any], path: str) -> list[dict[str, str]]:
    requirements = task.get("evidence_requirements")
    if not isinstance(requirements, list) or not requirements:
        return [
            _finding(
                "evidence_contract_missing",
                path,
                "vulnerable task requires a non-empty evidence_requirements list",
            )
        ]
    findings: list[dict[str, str]] = []
    indexes: list[int] = []
    names: list[str] = []
    for position, requirement in enumerate(requirements):
        requirement_path = f"{path}:evidence_requirements[{position}]"
        if not isinstance(requirement, dict):
            findings.append(
                _finding("evidence_requirement_invalid", requirement_path, "requirement must be an object")
            )
            continue
        allowed = {"name", "index", "request", "status", "body_contains"}
        extra = _unexpected_fields(requirement, allowed)
        if extra:
            findings.append(
                _finding(
                    "evidence_requirement_extra_fields",
                    requirement_path,
                    f"unexpected fields: {', '.join(extra)}",
                )
            )
        name = requirement.get("name")
        if not isinstance(name, str) or not name.strip():
            findings.append(
                _finding("evidence_requirement_name_invalid", requirement_path, "name must be non-empty")
            )
        else:
            names.append(name)
        index = requirement.get("index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            findings.append(
                _finding("evidence_requirement_index_invalid", requirement_path, "index must be non-negative")
            )
        else:
            indexes.append(index)
        findings.extend(
            _request_findings(requirement.get("request"), f"{requirement_path}.request")
        )
        status = requirement.get("status")
        if "status" in requirement and (
            isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599
        ):
            findings.append(
                _finding(
                    "evidence_requirement_status_invalid",
                    requirement_path,
                    "status must be an integer HTTP status from 100 to 599",
                )
            )
        if "status" not in requirement and "body_contains" not in requirement:
            findings.append(
                _finding(
                    "evidence_requirement_oracle_missing",
                    requirement_path,
                    "status or body_contains is required",
                )
            )
        if "body_contains" in requirement and requirement["body_contains"] in (
            None,
            "",
            [],
            {},
        ):
            findings.append(
                _finding(
                    "evidence_requirement_body_invalid",
                    requirement_path,
                    "body_contains must be meaningful when supplied",
                )
            )
    if indexes != list(range(len(requirements))):
        findings.append(
            _finding(
                "evidence_requirement_indexes_invalid",
                path,
                "indexes must be unique and contiguous in list order starting at 0",
            )
        )
    if len(names) != len(set(names)):
        findings.append(
            _finding(
                "evidence_requirement_names_invalid",
                path,
                "requirement names must be unique",
            )
        )
    return findings


def _evidence_replay_findings(task: dict[str, Any], path: str) -> list[dict[str, str]]:
    try:
        refs = build_context(task)["refs"]
        requirements = resolve_templates(task["evidence_requirements"], refs)
        oracle = resolve_templates(task["oracle"], refs)
        state = load_app(task["app"]).seed_state(task["seed"])
    except Exception as exc:  # noqa: BLE001 - audit must fail closed on task-controlled input.
        return [
            _finding(
                "evidence_replay_setup_failed",
                path,
                f"{type(exc).__name__}: {exc}",
            )
        ]

    responses: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    for position, requirement in enumerate(requirements):
        requirement_path = f"{path}:evidence_requirements[{position}]"
        try:
            response = replay_request(task, requirement["request"], state=state)
        except Exception as exc:  # noqa: BLE001 - audit must report instead of escaping.
            findings.append(
                _finding(
                    "evidence_replay_failed",
                    requirement_path,
                    f"{type(exc).__name__}: {exc}",
                )
            )
            continue
        responses.append(response)
        if not _evidence_requirement_matches(response, requirement):
            findings.append(
                _finding(
                    "evidence_requirement_response_mismatch",
                    requirement_path,
                    "replayed response did not satisfy the declared status/body constraint",
                )
            )
    if len(responses) != len(requirements):
        return findings
    final_response = responses[-1]
    if (
        final_response.get("status") != oracle.get("status")
        or not _contains_subset(final_response.get("body"), oracle.get("body_contains"))
    ):
        findings.append(
            _finding(
                "evidence_final_oracle_mismatch",
                path,
                "the final evidence step did not satisfy the task oracle",
            )
        )
    return findings


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _replay_source_set_sha256() -> str:
    paths = {
        "protocol_contracts": Path(__file__).resolve(),
        "core": REPOSITORY_ROOT / "authzbench/core.py",
        "score": REPOSITORY_ROOT / "authzbench/score.py",
        "manifest_validator": REPOSITORY_ROOT / "authzbench/validate_manifests.py",
    }
    for path in sorted((REPOSITORY_ROOT / "apps").rglob("*.py")):
        paths[f"app:{path.relative_to(REPOSITORY_ROOT).as_posix()}"] = path
    hashes = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in sorted(paths.items())
    }
    return stable_json_sha256(hashes)


def _task_paths(
    patterns: list[str], *, required_root: Path | None = None
) -> tuple[list[Path], list[dict[str, str]]]:
    paths: dict[Path, Path] = {}
    findings: list[dict[str, str]] = []
    for pattern in patterns:
        for value in glob.glob(pattern, recursive=True):
            candidate = Path(value)
            if candidate.is_symlink():
                findings.append(
                    _finding(
                        "task_path_symlink",
                        candidate.as_posix(),
                        "task manifest symlinks are not accepted",
                    )
                )
                continue
            if required_root is not None:
                lexical_root = required_root.absolute()
                lexical_candidate = candidate.absolute()
                try:
                    relative_candidate = lexical_candidate.relative_to(lexical_root)
                except ValueError:
                    relative_candidate = None
                if relative_candidate is not None:
                    current = lexical_root
                    symlink_component: Path | None = None
                    for component in relative_candidate.parts:
                        current = current / component
                        if current.is_symlink():
                            symlink_component = current
                            break
                    if symlink_component is not None:
                        findings.append(
                            _finding(
                                "task_path_symlink",
                                candidate.as_posix(),
                                f"task path traverses symlink component {symlink_component.as_posix()}",
                            )
                        )
                        continue
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if required_root is not None:
                try:
                    resolved.relative_to(required_root.resolve())
                except ValueError:
                    findings.append(
                        _finding(
                            "task_path_outside_root",
                            candidate.as_posix(),
                            f"task manifest resolves outside {required_root.resolve().as_posix()}",
                        )
                    )
                    continue
            paths.setdefault(resolved, candidate)
    return sorted(paths), findings


def audit_evidence_contracts(
    patterns: list[str],
    *,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
    expected_task_count: int | None = None,
    expected_vulnerable_task_count: int | None = None,
    required_task_root: Path | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    try:
        schema_identity = schema_bundle_identity(schema_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        schema_identity = {
            "schema_version": SCHEMA_BUNDLE_VERSION,
            "status": SCHEMA_STATUS,
            "canonical_sha256": None,
            "valid": False,
            "findings": [
                {"code": "schema_load_failed", "detail": f"{type(exc).__name__}: {exc}"}
            ],
        }
    findings.extend(
        _finding(item["code"], schema_path.as_posix(), item["detail"])
        for item in schema_identity["findings"]
    )

    paths, path_findings = _task_paths(patterns, required_root=required_task_root)
    findings.extend(path_findings)
    if not paths:
        findings.append(_finding("task_set_empty", "tasks", "no task manifests matched"))
    seen_ids: set[str] = set()
    vulnerable_task_ids: list[str] = []
    covered_task_ids: list[str] = []
    invalid_task_paths: set[str] = set()
    audited_task_items: list[dict[str, Any]] = []
    for path in paths:
        path_text = _display_path(path)
        try:
            task = load_json_without_duplicate_keys(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            invalid_task_paths.add(path_text)
            findings.append(
                _finding("task_json_invalid", path_text, f"{type(exc).__name__}: {exc}")
            )
            continue
        if not isinstance(task, dict):
            invalid_task_paths.add(path_text)
            findings.append(_finding("task_root_invalid", path_text, "task root must be an object"))
            continue
        audited_task_items.append({"path": path_text, "manifest": task})
        manifest_errors = validate_manifest(path, seen_ids)
        if manifest_errors:
            invalid_task_paths.add(path_text)
            findings.extend(
                _finding("task_manifest_invalid", path_text, error) for error in manifest_errors
            )
        if task.get("expected_vulnerable") is True:
            task_id = task.get("id")
            display_id = task_id if isinstance(task_id, str) else path_text
            vulnerable_task_ids.append(display_id)
            contract_findings = _evidence_requirement_findings(task, path_text)
            if not manifest_errors and not contract_findings:
                contract_findings = _evidence_replay_findings(task, path_text)
            if manifest_errors or contract_findings:
                findings.extend(contract_findings)
            else:
                covered_task_ids.append(display_id)

    vulnerable_task_ids.sort()
    covered_task_ids.sort()
    missing_task_ids = sorted(set(vulnerable_task_ids) - set(covered_task_ids))
    if expected_task_count is not None and len(paths) != expected_task_count:
        findings.append(
            _finding(
                "task_count_mismatch",
                "tasks",
                f"matched {len(paths)} tasks; expected {expected_task_count}",
            )
        )
    if (
        expected_vulnerable_task_count is not None
        and len(vulnerable_task_ids) != expected_vulnerable_task_count
    ):
        findings.append(
            _finding(
                "vulnerable_task_count_mismatch",
                "tasks",
                (
                    f"matched {len(vulnerable_task_ids)} vulnerable tasks; "
                    f"expected {expected_vulnerable_task_count}"
                ),
            )
        )
    invalid_codes = {
        "schema_load_failed",
        "schema_root_invalid",
        "schema_identity_invalid",
        "schema_definitions_invalid",
        "schema_definitions_missing",
        "schema_definition_invalid",
        "schema_root_reference_invalid",
        "schema_digest_mismatch",
        "task_set_empty",
        "task_json_invalid",
        "task_root_invalid",
        "task_manifest_invalid",
        "task_path_symlink",
        "task_path_outside_root",
        "task_count_mismatch",
        "vulnerable_task_count_mismatch",
    }
    migration_debt_codes = {"evidence_contract_missing"}
    valid = not any(
        item["code"] in invalid_codes or item["code"] not in migration_debt_codes
        for item in findings
    )
    complete = valid and bool(vulnerable_task_ids) and not missing_task_ids
    finding_counts = Counter(item["code"] for item in findings)
    return {
        "schema_version": "evidence-contract-coverage-audit-v1",
        "contract_version": EVIDENCE_CONTRACT_VERSION,
        "contract_status": SCHEMA_STATUS,
        "schema_bundle": schema_identity,
        "audited_task_set_sha256": stable_json_sha256(audited_task_items),
        "replay_source_set_sha256": _replay_source_set_sha256(),
        "task_count": len(paths),
        "vulnerable_task_count": len(vulnerable_task_ids),
        "covered_vulnerable_task_count": len(covered_task_ids),
        "coverage_rate": (
            round(len(covered_task_ids) / len(vulnerable_task_ids), 4)
            if vulnerable_task_ids
            else 0
        ),
        "covered_task_ids": covered_task_ids,
        "missing_task_ids": missing_task_ids,
        "invalid_task_paths": sorted(invalid_task_paths),
        "finding_counts": dict(sorted(finding_counts.items())),
        "valid": valid,
        "complete": complete,
        "findings": findings,
    }
