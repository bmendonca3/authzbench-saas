from __future__ import annotations

import argparse
import glob
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
from authzbench.validate_manifests import validate_patterns
from scripts.validate_baseline_registry import validate_registry
from scripts.validate_holdout_pack import validate_holdout_pack
from scripts.validate_leaderboard_submission import _submission_paths, validate_submission


REQUIRED_DOCS = [
    "README.md",
    "ROADMAP.md",
    "docs/goal.md",
    "docs/v0-release-plan.md",
    "docs/v0-task-build-matrix.md",
    "docs/methodology.md",
    "docs/benchmark-card.md",
    "docs/holdout-and-contamination.md",
    "docs/leaderboard-schema.md",
    "docs/publish-checklist.md",
    "docs/release-evidence.json",
    "CHANGELOG.md",
]

V0_TARGETS = {
    "min_public_tasks": 40,
    "min_apps": 6,
    "min_private_holdout_tasks": 20,
    "max_private_holdout_tasks": 30,
    "min_vulnerable_tasks": 25,
    "min_total_controls": 30,
    "min_control_ratio": 0.40,
    "min_authorized_allow_controls": 10,
}

RELEASE_EVIDENCE_FIELDS = [
    "local_public_validation_passed",
    "fresh_clone_validation_passed",
    "remote_ci_passed",
    "docker_container_smoke_passed",
    "privacy_scan_passed",
    "release_notes_separate_public_and_private_results",
    "protected_private_holdout_execution_available",
]


def _manifest_paths(pattern: str) -> list[Path]:
    return sorted(Path(path) for path in glob.glob(str(ROOT / pattern), recursive=True) if Path(path).is_file())


def _load_manifests(pattern: str) -> list[dict[str, Any]]:
    return [load_json(path) for path in _manifest_paths(pattern)]


def _private_holdout_pack_patterns() -> list[str]:
    rotation_metadata = ROOT / "tasks_private" / "holdout" / "rotation-metadata.json"
    if rotation_metadata.exists():
        try:
            data = load_json(rotation_metadata)
        except Exception:  # noqa: BLE001 - validation below should report malformed task evidence separately.
            return [str(ROOT / "tasks_private" / "holdout" / "*" / "*.json")]
        packs = data.get("packs")
        if isinstance(packs, list):
            active_patterns: list[str] = []
            for pack in packs:
                if not isinstance(pack, dict) or pack.get("role") != "active":
                    continue
                raw_path = pack.get("path")
                if not isinstance(raw_path, str):
                    continue
                path = Path(raw_path)
                if path.is_absolute() or ".." in path.parts:
                    continue
                active_patterns.append(str(ROOT / path / "*" / "*.json"))
            if active_patterns:
                return active_patterns
    return [str(ROOT / "tasks_private" / "holdout" / "*" / "*.json")]


def _git_ls_files(pathspec: str) -> tuple[list[str], str | None]:
    try:
        result = subprocess.run(
            ["git", "ls-files", pathspec],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        return [], str(exc)
    return [line for line in result.stdout.splitlines() if line.strip()], None


def _add_gate(
    gates: list[dict[str, Any]],
    gate_id: str,
    passed: bool,
    evidence: dict[str, Any],
    *,
    unmet: list[str] | None = None,
) -> None:
    gates.append(
        {
            "id": gate_id,
            "passed": passed,
            "evidence": evidence,
            "unmet": unmet or [],
        }
    )


def _review_registry() -> dict[str, Any]:
    path = ROOT / "docs" / "reviews" / "review-registry.json"
    if not path.exists():
        return {
            "passed": False,
            "errors": ["docs/reviews/review-registry.json is missing"],
            "section_count": 0,
            "v0_ready_section_count": 0,
        }
    registry = load_json(path)
    errors: list[str] = []
    sections = registry.get("sections")
    if registry.get("schema_version") != "review-registry-v1":
        errors.append("review registry schema_version must be review-registry-v1")
    if not isinstance(sections, list) or not sections:
        errors.append("review registry sections must be a non-empty list")
        sections = []
    required_sections = [item for item in sections if isinstance(item, dict) and item.get("required_for_v0") is True]
    v0_ready_sections = []
    missing_artifacts: list[str] = []
    for section in required_sections:
        section_id = str(section.get("id", "<missing-id>"))
        summary_paths = section.get("summary_paths")
        if not isinstance(summary_paths, list) or not summary_paths:
            errors.append(f"{section_id}: summary_paths must be a non-empty list")
            continue
        for raw_path in summary_paths:
            if not isinstance(raw_path, str) or not raw_path.strip():
                errors.append(f"{section_id}: summary_paths entries must be non-empty strings")
                continue
            if Path(raw_path).is_absolute():
                errors.append(f"{section_id}: summary path must be relative: {raw_path}")
                continue
            candidate = ROOT / "docs" / "reviews" / raw_path
            if not candidate.exists():
                missing_artifacts.append(f"{section_id}:{raw_path}")
        if section.get("v0_ready") is True:
            v0_ready_sections.append(section_id)
    if missing_artifacts:
        errors.append("review registry references missing artifact(s): " + ", ".join(missing_artifacts[:8]))
    return {
        "passed": not errors,
        "errors": errors,
        "section_count": len(required_sections),
        "v0_ready_section_count": len(v0_ready_sections),
        "required_section_ids": [str(item.get("id", "<missing-id>")) for item in required_sections],
        "v0_ready_section_ids": v0_ready_sections,
        "all_required_sections_v0_ready": len(v0_ready_sections) == len(required_sections) and not errors,
    }


def _release_evidence() -> dict[str, Any]:
    path = ROOT / "docs" / "release-evidence.json"
    if not path.exists():
        return {"passed": False, "errors": ["docs/release-evidence.json is missing"], "ready_field_count": 0}
    evidence = load_json(path)
    errors: list[str] = []
    if evidence.get("schema_version") != "release-evidence-v1":
        errors.append("release evidence schema_version must be release-evidence-v1")
    required = evidence.get("required_for_v0")
    if not isinstance(required, dict):
        errors.append("release evidence required_for_v0 must be an object")
        required = {}
    ready_fields = [field for field in RELEASE_EVIDENCE_FIELDS if required.get(field) is True]
    missing_fields = [field for field in RELEASE_EVIDENCE_FIELDS if field not in required]
    if missing_fields:
        errors.append("release evidence missing required field(s): " + ", ".join(missing_fields))
    false_fields = [field for field in RELEASE_EVIDENCE_FIELDS if required.get(field) is not True]
    for field in false_fields:
        errors.append(f"release evidence not satisfied: {field}")
    return {
        "passed": not errors,
        "errors": errors,
        "ready_field_count": len(ready_fields),
        "required_field_count": len(RELEASE_EVIDENCE_FIELDS),
        "ready_fields": ready_fields,
        "unsatisfied_fields": false_fields,
    }


def validate_v0_release() -> dict[str, Any]:
    gates: list[dict[str, Any]] = []

    public_counts = validate_patterns([str(ROOT / "tasks" / "*" / "*.json")])
    public_manifests = _load_manifests("tasks/*/*.json")
    app_count = len({str(item.get("app")) for item in public_manifests})
    public_unmet: list[str] = []
    public_task_count = int(public_counts["manifest_count"])
    if public_task_count < V0_TARGETS["min_public_tasks"]:
        public_unmet.append(
            f"public tasks must be at least {V0_TARGETS['min_public_tasks']}; got {public_task_count}"
        )
    if app_count < V0_TARGETS["min_apps"]:
        public_unmet.append(f"synthetic app count must be at least {V0_TARGETS['min_apps']}; got {app_count}")
    if public_counts["errors"]:
        public_unmet.extend(public_counts["errors"])
    _add_gate(
        gates,
        "public_split_scope",
        not public_unmet,
        {
            "task_count": public_task_count,
            "app_count": app_count,
            "vulnerable_task_count": public_counts["vulnerable_count"],
            "control_task_count": public_counts["control_count"],
        },
        unmet=public_unmet,
    )

    private_patterns = _private_holdout_pack_patterns()
    private_paths = sorted(
        Path(path)
        for pattern in private_patterns
        for path in glob.glob(pattern, recursive=True)
        if Path(path).is_file()
    )
    private_unmet: list[str] = []
    holdout_result: dict[str, Any] | None = None
    if private_paths:
        holdout_result = validate_holdout_pack(
            private_patterns,
            public_patterns=[str(ROOT / "tasks" / "*" / "*.json")],
            min_count=V0_TARGETS["min_private_holdout_tasks"],
            preferred_count=24,
            max_count=V0_TARGETS["max_private_holdout_tasks"],
            min_vulnerable=12,
            min_controls=8,
            min_apps=6,
            max_per_app=8,
            min_denial_controls=4,
            min_authorized_allow_controls=4,
            min_route_variants=6,
            min_decoy_variants=6,
        )
        if not holdout_result["passed"]:
            private_unmet.extend(holdout_result["errors"])
        if not holdout_result.get("leaderboard_suitable"):
            private_unmet.append("private holdout pack is not leaderboard_suitable")
        if int(holdout_result.get("rehearsal_manifest_count", 0)):
            private_unmet.append("holdout pack contains rehearsal manifests, not real private leaderboard tasks")
    else:
        private_unmet.append("real private holdout pack is missing")
    tracked_private, git_error = _git_ls_files("tasks_private/holdout")
    if git_error:
        private_unmet.append(f"cannot verify private holdout Git tracking: {git_error}")
    if tracked_private:
        private_unmet.append("private holdout manifests are tracked in Git")
    _add_gate(
        gates,
        "private_holdout_pack",
        not private_unmet,
        {
            "manifest_count": holdout_result.get("manifest_count") if holdout_result else 0,
            "leaderboard_suitable": holdout_result.get("leaderboard_suitable") if holdout_result else False,
            "tracked_private_manifest_count": len(tracked_private),
        },
        unmet=private_unmet,
    )

    holdout_counts_for_v0 = holdout_result if holdout_result and holdout_result.get("leaderboard_suitable") else None
    total_tasks = public_task_count + (int(holdout_counts_for_v0["manifest_count"]) if holdout_counts_for_v0 else 0)
    total_vulnerable = int(public_counts["vulnerable_count"]) + (
        int(holdout_counts_for_v0["vulnerable_count"]) if holdout_counts_for_v0 else 0
    )
    total_controls = int(public_counts["control_count"]) + (
        int(holdout_counts_for_v0["control_count"]) if holdout_counts_for_v0 else 0
    )
    total_authorized_allow = int(public_counts["authorized_allow_control_count"]) + (
        int(holdout_counts_for_v0["authorized_allow_control_count"]) if holdout_counts_for_v0 else 0
    )
    mix_unmet: list[str] = []
    control_ratio = round(total_controls / total_tasks, 4) if total_tasks else 0
    if total_vulnerable < V0_TARGETS["min_vulnerable_tasks"]:
        mix_unmet.append(
            f"total vulnerable tasks must be at least {V0_TARGETS['min_vulnerable_tasks']}; got {total_vulnerable}"
        )
    if total_controls < V0_TARGETS["min_total_controls"]:
        mix_unmet.append(f"total secure controls must be at least {V0_TARGETS['min_total_controls']}; got {total_controls}")
    if control_ratio < V0_TARGETS["min_control_ratio"]:
        mix_unmet.append(f"secure-control ratio must be at least {V0_TARGETS['min_control_ratio']}; got {control_ratio}")
    if total_authorized_allow < V0_TARGETS["min_authorized_allow_controls"]:
        mix_unmet.append(
            "authorized-allow controls must be at least "
            f"{V0_TARGETS['min_authorized_allow_controls']}; got {total_authorized_allow}"
        )
    _add_gate(
        gates,
        "task_mix",
        not mix_unmet,
        {
            "total_tasks": total_tasks,
            "total_vulnerable_tasks": total_vulnerable,
            "total_controls": total_controls,
            "control_ratio": control_ratio,
            "authorized_allow_control_count": total_authorized_allow,
        },
        unmet=mix_unmet,
    )

    baseline_result = validate_registry(ROOT / "baselines" / "baseline-registry.json")
    baseline_unmet = list(baseline_result["errors"])
    has_v0_baseline_evidence = bool(baseline_result["v0_baseline_ready"]) or bool(
        baseline_result.get("v0_release_snapshot_ready")
    )
    if not has_v0_baseline_evidence:
        baseline_unmet.extend(baseline_result["unmet_v0_requirements"])
        baseline_unmet.append("baseline registry has neither current v0 baselines nor a ready v0.0 release snapshot")
    _add_gate(
        gates,
        "baseline_credibility",
        baseline_result["passed"] and has_v0_baseline_evidence,
        {
            "baseline_count": baseline_result["baseline_count"],
            "current_public_model_family_count": baseline_result["current_public_model_family_count"],
            "repeated_model_baseline_count": baseline_result["repeated_model_baseline_count"],
            "has_current_public_tool_agent_baseline": baseline_result["has_current_public_tool_agent_baseline"],
            "v0_baseline_ready": baseline_result["v0_baseline_ready"],
            "v0_release_snapshot_ready": baseline_result.get("v0_release_snapshot_ready", False),
            "release_snapshots": baseline_result.get("release_snapshots", []),
        },
        unmet=baseline_unmet,
    )

    example_paths = _submission_paths([str(ROOT / "examples" / "leaderboard" / "*.json")])
    candidate_paths = _submission_paths([str(ROOT / "leaderboard_submissions" / "**" / "*.json")])
    example_results = [validate_submission(path, require_source_summary=True) for path in example_paths]
    candidate_results = [validate_submission(path, require_source_summary=True) for path in candidate_paths]
    leaderboard_results = example_results + candidate_results
    leaderboard_unmet: list[str] = []
    for item in leaderboard_results:
        if not item["passed"]:
            leaderboard_unmet.extend(f"{item['path']}: {error}" for error in item["errors"])
    eligible_count = sum(1 for item in candidate_results if item["leaderboard_eligible"])
    if not candidate_paths:
        leaderboard_unmet.append("no release-candidate leaderboard submissions found under leaderboard_submissions/**/*.json")
    if eligible_count == 0:
        leaderboard_unmet.append("no release-candidate leaderboard submission is currently eligible")
    _add_gate(
        gates,
        "leaderboard_submissions",
        not leaderboard_unmet,
        {
            "example_submission_count": len(example_paths),
            "release_candidate_submission_count": len(candidate_paths),
            "release_candidate_leaderboard_eligible_count": eligible_count,
        },
        unmet=leaderboard_unmet,
    )

    review_result = _review_registry()
    review_unmet = list(review_result["errors"])
    if not review_result.get("all_required_sections_v0_ready"):
        review_unmet.append("not all required review sections are marked v0_ready")
    _add_gate(
        gates,
        "sectional_reviews",
        review_result["passed"] and bool(review_result.get("all_required_sections_v0_ready")),
        {
            "section_count": review_result["section_count"],
            "v0_ready_section_count": review_result["v0_ready_section_count"],
            "required_section_ids": review_result["required_section_ids"],
            "v0_ready_section_ids": review_result["v0_ready_section_ids"],
        },
        unmet=review_unmet,
    )

    missing_docs = [path for path in REQUIRED_DOCS if not (ROOT / path).exists()]
    _add_gate(
        gates,
        "documentation_packaging",
        not missing_docs,
        {"required_doc_count": len(REQUIRED_DOCS), "missing_docs": missing_docs},
        unmet=[f"missing required doc: {path}" for path in missing_docs],
    )

    release_evidence = _release_evidence()
    _add_gate(
        gates,
        "release_verification_evidence",
        release_evidence["passed"],
        {
            "ready_field_count": release_evidence["ready_field_count"],
            "required_field_count": release_evidence["required_field_count"],
            "ready_fields": release_evidence.get("ready_fields", []),
        },
        unmet=release_evidence["errors"],
    )

    v0_ready = all(gate["passed"] for gate in gates)
    return {
        "passed": v0_ready,
        "v0_ready": v0_ready,
        "gate_count": len(gates),
        "passed_gate_count": sum(1 for gate in gates if gate["passed"]),
        "unmet_gate_count": sum(1 for gate in gates if not gate["passed"]),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit AuthZBench-SaaS readiness for the real v0 release.")
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Return success even when v0_ready=false. Intended for alpha/pre-v0 public validation.",
    )
    args = parser.parse_args()
    result = validate_v0_release()
    print(dump_json(result))
    return 0 if result["passed"] or args.allow_incomplete else 1


if __name__ == "__main__":
    raise SystemExit(main())
