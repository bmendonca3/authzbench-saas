from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import dump_json, load_json
from authzbench.validate_manifests import validate_patterns
from scripts.containerized_submission_smoke import validate_smoke_evidence
from scripts.validate_baseline_registry import validate_registry
from scripts.validate_holdout_pack import validate_holdout_pack
from scripts.validate_leaderboard_submission import _submission_paths, validate_submission


REQUIRED_REVIEW_LANES = (
    "Application security",
    "Benchmark/evals methodology",
    "AI-agent/tooling",
)

REQUIRED_REVIEW_PACKET_ARTIFACTS = (
    "README.md",
    "ROADMAP.md",
    "docs/benchmark-card.md",
    "docs/evidence-and-claims.md",
    "docs/methodology.md",
    "docs/score-policy.md",
    "docs/result-schema.md",
    "docs/leaderboard-schema.md",
    "docs/task-quality-rubric.md",
    "docs/task-quality-matrix.md",
    "docs/baseline-credibility.md",
    "docs/baseline-variance-analysis.md",
    "docs/boundary-reasoning-calibration-study.md",
    "docs/v1-community-submission-governance.md",
    "docs/authzbench-saas-v1-prep-technical-report.md",
    "baselines/baseline-registry.json",
    "baselines",
    "docs/assets/benchmark-charts",
)

EXTERNAL_REVIEW_EVIDENCE_PATH = "docs/reviews/external-review-summary.json"
HOSTED_EXECUTION_EVIDENCE_PATH = "artifact/submission-runner-smoke.json"
PAPER_READINESS_EVIDENCE_PATH = "docs/v1-paper-readiness.json"
RELEASE_VALIDATION_EVIDENCE_PATH = "artifact/v1-release-candidate-validation.json"
ROTATION_METADATA_PATH = "tasks_private/holdout/rotation-metadata.json"

VALID_REVIEW_DECISIONS = {"accepted", "rejected", "unresolved"}
VALID_REVIEW_DISPOSITIONS = {"findings", "no_findings"}

POST_SOURCE_EVIDENCE_ONLY_PATHS = {
    EXTERNAL_REVIEW_EVIDENCE_PATH,
    HOSTED_EXECUTION_EVIDENCE_PATH,
    PAPER_READINESS_EVIDENCE_PATH,
}
PAPER_POST_SOURCE_EVIDENCE_ONLY_PATHS = {
    PAPER_READINESS_EVIDENCE_PATH,
    "artifact/expected-output/v1-readiness-public-view.json",
    "docs/goal.md",
}


def _text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _json_object(path: Path, unmet: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        unmet.append(f"missing structured evidence: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
        return None
    try:
        data = load_json(path)
    except Exception as exc:
        unmet.append(f"{path.name} is not valid JSON: {exc}")
        return None
    if not isinstance(data, dict):
        unmet.append(f"{path.name} must contain a JSON object")
        return None
    return data


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _placeholder(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() in {"tbd", "todo", "pending", "unknown", "n/a"}


def _safe_existing_relative_path(root: Path, value: str) -> bool:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return False
    return candidate.is_file()


def _git_commit_exists(root: Path, ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).returncode
        == 0
    )


def _valid_follow_up_ref(root: Path, value: Any) -> bool:
    if not _nonempty_string(value) or _placeholder(value):
        return False
    text = str(value).strip()
    if _safe_existing_relative_path(root, text):
        return True
    if re.fullmatch(r"[0-9a-f]{7,40}", text):
        return _git_commit_exists(root, text)
    match = re.fullmatch(r"https://github\.com/bmendonca3/authzbench-saas/commit/([0-9a-f]{7,40})", text)
    if match:
        return _git_commit_exists(root, match.group(1))
    return False


def _current_commit_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
    except Exception:
        return ""


def _working_tree_clean(root: Path = ROOT, allowed_untracked: set[Path] | None = None) -> bool:
    for cmd in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        result = subprocess.run(cmd, cwd=root, check=False)
        if result.returncode != 0:
            return False
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.splitlines()
    allowed = {path.resolve() for path in (allowed_untracked or set())}
    for line in status:
        if not line.startswith("?? "):
            return False
        candidate = (root / line[3:]).resolve()
        if candidate not in allowed:
            return False
    return True


def _git_ok(root: Path, cmd: list[str]) -> bool:
    return subprocess.run(["git", *cmd], cwd=root, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0


def _benchmark_source_compatibility_errors(
    root: Path,
    source_sha: str,
    release_sha: str,
    *,
    allowed_post_source_paths: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    if not _git_ok(root, ["cat-file", "-e", f"{source_sha}^{{commit}}"]):
        errors.append("benchmark_source_sha must exist as a commit")
        return errors
    if not _git_ok(root, ["cat-file", "-e", f"{release_sha}^{{commit}}"]):
        errors.append("release commit_sha must exist as a commit")
        return errors
    if not _git_ok(root, ["merge-base", "--is-ancestor", source_sha, release_sha]):
        errors.append("benchmark_source_sha must be an ancestor of release commit_sha")
        return errors
    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{source_sha}..{release_sha}"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.splitlines()
    allowed_paths = allowed_post_source_paths or POST_SOURCE_EVIDENCE_ONLY_PATHS
    release_affecting = [path for path in diff if path not in allowed_paths]
    if release_affecting:
        errors.append(
            "release-affecting files changed after benchmark_source_sha: "
            + ", ".join(release_affecting[:10])
        )
    return errors


def _add_gate(
    gates: list[dict[str, Any]],
    gate_id: str,
    passed: bool,
    evidence: list[str],
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


def _manifest_count(pattern: str) -> int:
    result = validate_patterns([pattern])
    if result["errors"]:
        return 0
    return int(result["manifest_count"])


def _private_pack_fingerprint(pack_path: Path) -> str:
    digest = hashlib.sha256()
    for manifest_path in sorted(pack_path.glob("*/*.json")):
        relative = manifest_path.relative_to(pack_path).as_posix()
        manifest = load_json(manifest_path)
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(canonical.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_private_rotation_metadata(root: Path = ROOT) -> dict[str, Any]:
    metadata_path = root / ROTATION_METADATA_PATH
    unmet: list[str] = []
    data = _json_object(metadata_path, unmet)
    if data is None:
        return {
            "passed": False,
            "pack_ids": [],
            "roles": [],
            "validated_private_task_count": 0,
            "active_pack_id": None,
            "active_pack_fingerprint_sha256": None,
            "unmet": unmet,
        }

    packs = data.get("packs")
    if not isinstance(packs, list) or not packs:
        unmet.append("rotation metadata must include a non-empty packs list")
        packs = []

    pack_ids: list[str] = []
    roles: list[str] = []
    task_count = 0
    active_pack_id: str | None = None
    active_pack_fingerprint_sha256: str | None = None
    seen_ids: set[str] = set()
    seen_pack_paths: set[Path] = set()
    seen_task_ids: set[str] = set()
    comparison_private_patterns: list[str] = []
    for index, pack in enumerate(packs, start=1):
        if not isinstance(pack, dict):
            unmet.append(f"packs[{index}] must be an object")
            continue
        pack_id = pack.get("id")
        role = pack.get("role")
        raw_path = pack.get("path")
        if not _nonempty_string(pack_id):
            unmet.append(f"packs[{index}].id must be a non-empty string")
            pack_id = f"<missing-{index}>"
        if pack_id in seen_ids:
            unmet.append(f"duplicate private pack id: {pack_id}")
        seen_ids.add(str(pack_id))
        if role not in {"active", "shadow", "candidate"}:
            unmet.append(f"{pack_id}: role must be active, shadow, or candidate")
        if not _nonempty_string(raw_path):
            unmet.append(f"{pack_id}: path must be a non-empty string")
            continue
        path = Path(str(raw_path))
        if path.is_absolute() or ".." in path.parts:
            unmet.append(f"{pack_id}: path must be a safe relative path")
            continue
        pack_path = root / path
        holdout_root = root / "tasks_private" / "holdout"
        try:
            pack_path.resolve().relative_to(holdout_root.resolve())
        except ValueError:
            unmet.append(f"{pack_id}: path must be under tasks_private/holdout")
            continue
        if not pack_path.is_dir():
            unmet.append(f"{pack_id}: pack directory does not exist")
            continue
        resolved_pack_path = pack_path.resolve()
        if resolved_pack_path in seen_pack_paths:
            unmet.append(f"{pack_id}: pack path duplicates another declared private pack")
            continue
        seen_pack_paths.add(resolved_pack_path)
        pattern = str(pack_path / "*" / "*.json")
        result = validate_holdout_pack(
            [pattern],
            public_patterns=[str(root / "tasks" / "*" / "*.json")],
            comparison_private_patterns=list(comparison_private_patterns),
            min_count=20,
            preferred_count=24,
            max_count=40,
            min_vulnerable=10,
            min_controls=10,
            min_apps=6,
            max_per_app=10,
            min_denial_controls=4,
            min_authorized_allow_controls=4,
            min_route_variants=6,
            min_decoy_variants=6,
        )
        comparison_private_patterns.append(pattern)
        if not result["passed"]:
            unmet.append(f"{pack_id}: private pack manifests do not validate")
            continue
        if result.get("leaderboard_suitable") is not True:
            unmet.append(f"{pack_id}: private pack is not leaderboard_suitable")
            continue
        manifest_count = int(result["manifest_count"])
        if manifest_count <= 0:
            unmet.append(f"{pack_id}: private pack contains no task manifests")
            continue
        pack_task_ids: set[str] = set()
        for manifest_path in sorted(pack_path.glob("*/*.json")):
            manifest = load_json(manifest_path)
            task_id = manifest.get("id") if isinstance(manifest, dict) else None
            if not _nonempty_string(task_id):
                unmet.append(f"{pack_id}: manifest {manifest_path.name} is missing id")
                continue
            if str(task_id) in seen_task_ids:
                unmet.append(f"{pack_id}: duplicate private task id across packs: {task_id}")
                continue
            seen_task_ids.add(str(task_id))
            pack_task_ids.add(str(task_id))
        pack_fingerprint = _private_pack_fingerprint(pack_path)
        if role == "active":
            active_pack_id = str(pack_id)
            active_pack_fingerprint_sha256 = pack_fingerprint
        task_count += len(pack_task_ids)
        pack_ids.append(str(pack_id))
        roles.append(str(role))

    if "active" not in roles:
        unmet.append("rotation metadata must declare one active private pack")
    if not {"shadow", "candidate"} & set(roles):
        unmet.append("rotation metadata must declare one shadow or candidate private pack")
    if len([role for role in roles if role == "active"]) != 1:
        unmet.append("rotation metadata must declare exactly one active private pack")

    return {
        "passed": not unmet,
        "pack_ids": pack_ids,
        "roles": roles,
        "validated_private_task_count": task_count,
        "active_pack_id": active_pack_id,
        "active_pack_fingerprint_sha256": active_pack_fingerprint_sha256,
        "unmet": unmet,
    }


def _source_summaries_have_private_denial(
    submission_path: Path,
    submission: dict[str, Any],
    *,
    private_pack_fingerprint_sha256: str | None = None,
) -> bool:
    raw_paths = submission.get("source_run_summaries")
    if not isinstance(raw_paths, list) or not raw_paths:
        return False
    if private_pack_fingerprint_sha256 is None:
        return False
    if submission.get("private_pack_fingerprint_sha256") != private_pack_fingerprint_sha256:
        return False
    for raw_path in raw_paths:
        if not isinstance(raw_path, str):
            return False
        candidates = [submission_path.parent / raw_path, ROOT / raw_path]
        summary_path = next((candidate for candidate in candidates if candidate.exists()), None)
        if summary_path is None:
            return False
        summary = load_json(summary_path)
        protected = summary.get("protected_execution") if isinstance(summary, dict) else None
        if not isinstance(protected, dict) or protected.get("host_private_paths_denied") is not True:
            return False
        if summary.get("private_pack_fingerprint_sha256") != private_pack_fingerprint_sha256:
            return False
    return True


def _eligible_private_rows(
    harness_type: str,
    benchmark_source_sha: str,
    private_pack_fingerprint_sha256: str | None,
) -> list[dict[str, Any]]:
    if private_pack_fingerprint_sha256 is None:
        return []
    rows: list[dict[str, Any]] = []
    for path in _submission_paths([str(ROOT / "leaderboard_submissions" / "**" / "*.json")]):
        result = validate_submission(path, require_source_summary=True)
        if not result["leaderboard_eligible"]:
            continue
        try:
            submission = load_json(path)
        except Exception:
            continue
        if (
            submission.get("split") == "private-holdout"
            and submission.get("harness_type") == harness_type
            and submission.get("benchmark_commit_sha") == benchmark_source_sha
            and submission.get("private_pack_fingerprint_sha256") == private_pack_fingerprint_sha256
            and isinstance(submission.get("run_count"), int)
            and submission["run_count"] >= 2
        ):
            rows.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "harness_type": submission.get("harness_type"),
                    "run_count": submission["run_count"],
                    "model": submission.get("model"),
                    "benchmark_commit_sha": submission.get("benchmark_commit_sha"),
                    "private_pack_fingerprint_sha256": submission.get("private_pack_fingerprint_sha256"),
                    "target_request_coverage_rate": submission.get("target_request_coverage_rate"),
                    "source_private_path_denial": _source_summaries_have_private_denial(
                        path,
                        submission,
                        private_pack_fingerprint_sha256=private_pack_fingerprint_sha256,
                    ),
                }
            )
    return rows


def _external_review_summary_state() -> dict[str, Any]:
    summary = _text(ROOT / "docs" / "reviews" / "external-review-summary.md")
    packet = _text(ROOT / "docs" / "reviews" / "external-review-packet.md")
    summary_lower = summary.lower()
    incomplete_markers = (
        "no independent external review is claimed yet",
        "reviewer not yet completed",
        "current blocker",
        "tbd",
        "todo",
        "pending",
    )
    lanes_present = [lane for lane in REQUIRED_REVIEW_LANES if lane in summary and lane in packet]
    return {
        "packet_exists": bool(packet),
        "summary_exists": bool(summary),
        "lanes_present": lanes_present,
        "has_incomplete_marker": any(marker in summary_lower for marker in incomplete_markers),
    }


def _validate_external_review_evidence(root: Path = ROOT) -> dict[str, Any]:
    unmet: list[str] = []
    data = _json_object(root / EXTERNAL_REVIEW_EVIDENCE_PATH, unmet)
    if data is None:
        return {"passed": False, "lanes": [], "unmet": unmet}

    lanes = data.get("review_lanes")
    if not isinstance(lanes, list):
        unmet.append("review_lanes must be a list")
        lanes = []
    lanes_by_name: dict[str, dict[str, Any]] = {}
    for index, lane in enumerate(lanes, start=1):
        if not isinstance(lane, dict):
            unmet.append(f"review_lanes[{index}] must be an object")
            continue
        name = lane.get("lane")
        if name not in REQUIRED_REVIEW_LANES:
            unmet.append(f"review_lanes[{index}].lane must be one of the required review lanes")
            continue
        lanes_by_name[str(name)] = lane
        try:
            review_date = date.fromisoformat(str(lane.get("review_date", "")))
        except ValueError:
            unmet.append(f"{name}: review_date must use YYYY-MM-DD")
        else:
            if review_date > date.today():
                unmet.append(f"{name}: review_date cannot be in the future")
        if not _nonempty_string(lane.get("reviewer_role_scope")) or _placeholder(lane.get("reviewer_role_scope")):
            unmet.append(f"{name}: reviewer_role_scope is required")
        if not _nonempty_string(lane.get("claim_boundary_impact")) or _placeholder(lane.get("claim_boundary_impact")):
            unmet.append(f"{name}: claim_boundary_impact is required")
        artifacts = lane.get("artifacts_reviewed")
        if not isinstance(artifacts, list) or not artifacts or any(not _nonempty_string(item) for item in artifacts):
            unmet.append(f"{name}: artifacts_reviewed must be a non-empty string list")
            artifacts = []
        for artifact in artifacts:
            if _placeholder(artifact):
                unmet.append(f"{name}: artifacts_reviewed cannot contain placeholders")
                continue
            artifact_path = Path(str(artifact))
            if artifact_path.is_absolute() or ".." in artifact_path.parts:
                unmet.append(f"{name}: artifacts_reviewed entries must be safe relative paths")
                continue
            if not (root / artifact_path).exists():
                unmet.append(f"{name}: reviewed artifact does not exist: {artifact}")
        disposition = lane.get("disposition")
        if disposition not in VALID_REVIEW_DISPOSITIONS:
            unmet.append(f"{name}: disposition must be findings or no_findings")
        decisions = lane.get("decisions")
        if decisions is None:
            decisions = []
        if not isinstance(decisions, list):
            unmet.append(f"{name}: decisions must be a list")
            decisions = []
        if disposition == "findings" and not decisions:
            unmet.append(f"{name}: findings disposition requires at least one decision")
        for decision_index, decision in enumerate(decisions, start=1):
            if not isinstance(decision, dict):
                unmet.append(f"{name}: decisions[{decision_index}] must be an object")
                continue
            if not _nonempty_string(decision.get("finding")) or _placeholder(decision.get("finding")):
                unmet.append(f"{name}: decisions[{decision_index}].finding is required")
            if decision.get("decision") not in VALID_REVIEW_DECISIONS:
                unmet.append(f"{name}: decisions[{decision_index}].decision must be accepted, rejected, or unresolved")
            if decision.get("decision") in {"accepted", "unresolved"} and not _valid_follow_up_ref(
                root,
                decision.get("follow_up_artifact"),
            ):
                unmet.append(
                    f"{name}: accepted or unresolved decisions require a real follow_up_artifact path or existing commit"
                )
            if not _nonempty_string(decision.get("claim_boundary_impact")) or _placeholder(
                decision.get("claim_boundary_impact")
            ):
                unmet.append(f"{name}: decisions[{decision_index}].claim_boundary_impact is required")

    missing_lanes = sorted(set(REQUIRED_REVIEW_LANES) - set(lanes_by_name))
    if missing_lanes:
        unmet.append(f"missing structured review lanes: {', '.join(missing_lanes)}")
    return {"passed": not unmet, "lanes": sorted(lanes_by_name), "unmet": unmet}


def _validate_hosted_execution_evidence(
    root: Path = ROOT,
    benchmark_source_sha: str | None = None,
    private_pack_fingerprint_sha256: str | None = None,
) -> dict[str, Any]:
    unmet: list[str] = []
    data = _json_object(root / HOSTED_EXECUTION_EVIDENCE_PATH, unmet)
    if data is None:
        return {"passed": False, "path": HOSTED_EXECUTION_EVIDENCE_PATH, "unmet": unmet}

    expected_sha = benchmark_source_sha or _current_commit_sha()
    unmet.extend(
        validate_smoke_evidence(
            data,
            expected_benchmark_source_sha=expected_sha,
            expected_private_pack_fingerprint_sha256=private_pack_fingerprint_sha256,
        )
    )
    required_strings = (
        "runner_image_or_hosted_version",
        "private_pack_version",
        "isolation_model",
        "command",
    )
    if data.get("result") != "passed":
        unmet.append("submission-runner smoke result must be passed")
    if data.get("execution_scope") != "release_candidate":
        unmet.append("submission-runner smoke execution_scope must be release_candidate")
    if data.get("benchmark_source_sha") != expected_sha:
        unmet.append("benchmark_source_sha must match release benchmark_source_sha")
    if private_pack_fingerprint_sha256 is None:
        unmet.append("active private pack fingerprint is required for hosted smoke evidence")
    elif data.get("private_pack_fingerprint_sha256") != private_pack_fingerprint_sha256:
        unmet.append("private_pack_fingerprint_sha256 must match the active private pack fingerprint")
    for field in required_strings:
        if not _nonempty_string(data.get(field)):
            unmet.append(f"{field} is required")
    for field in (
        "submitter_private_manifest_read_denied",
        "scorer_controlled_private_eval",
        "cleanup_completed",
        "privacy_scan_passed",
    ):
        if data.get(field) is not True:
            unmet.append(f"{field} must be true")
    if data.get("public_output_private_artifacts_included") is not False:
        unmet.append("public_output_private_artifacts_included must be false")
    return {
        "passed": not unmet,
        "path": HOSTED_EXECUTION_EVIDENCE_PATH,
        "unmet": list(dict.fromkeys(unmet)),
    }


def _validate_paper_readiness_evidence(
    root: Path = ROOT,
    *,
    benchmark_source_sha: str | None = None,
    release_sha: str | None = None,
    allowed_post_source_paths: set[str] | None = None,
    upstream_gates_complete: bool = False,
) -> dict[str, Any]:
    unmet: list[str] = []
    data = _json_object(root / PAPER_READINESS_EVIDENCE_PATH, unmet)
    if data is None:
        return {"passed": False, "path": PAPER_READINESS_EVIDENCE_PATH, "unmet": unmet}
    for field in (
        "claim_boundary_reviewed",
        "generated_paper_tables_clean",
        "charts_current_stale_legacy_labeled",
        "latexmk_main_tex_passed",
    ):
        if data.get(field) is not True:
            unmet.append(f"{field} must be true")
    if data.get("evidence_scope") != "release_candidate":
        unmet.append("evidence_scope must be release_candidate")
    if data.get("upstream_review_and_infrastructure_complete") is not True:
        unmet.append("upstream_review_and_infrastructure_complete must be true")
    if not upstream_gates_complete:
        unmet.append("live upstream review and infrastructure gates must pass")
    evidence_sha = data.get("benchmark_source_sha")
    if not _sha(evidence_sha):
        unmet.append("benchmark_source_sha must be a 40-character lowercase Git SHA")
    else:
        if benchmark_source_sha is not None and evidence_sha != benchmark_source_sha:
            unmet.append("benchmark_source_sha must match release benchmark_source_sha")
        if release_sha is not None:
            if evidence_sha == release_sha:
                unmet.append("benchmark_source_sha must reference an ancestor commit, not the release commit")
            elif _sha(release_sha):
                unmet.extend(
                    _benchmark_source_compatibility_errors(
                        root,
                        str(evidence_sha),
                        release_sha,
                        allowed_post_source_paths=allowed_post_source_paths,
                    )
                )
            else:
                unmet.append("release_sha must be a 40-character lowercase Git SHA")
    return {"passed": not unmet, "path": PAPER_READINESS_EVIDENCE_PATH, "unmet": unmet}


def _validate_release_candidate_evidence(
    root: Path = ROOT,
    *,
    evidence_path: Path | None = None,
    target_sha: str | None = None,
    private_pack_fingerprint_sha256: str | None = None,
) -> dict[str, Any]:
    unmet: list[str] = []
    if evidence_path is None:
        unmet.append("release-candidate evidence must be supplied with --release-evidence")
        return {"passed": False, "path": "<external release evidence>", "unmet": unmet}
    data = _json_object(evidence_path if evidence_path.is_absolute() else root / evidence_path, unmet)
    if data is None:
        return {"passed": False, "path": str(evidence_path), "unmet": unmet}
    expected_sha = target_sha or _current_commit_sha()
    if data.get("commit_sha") != expected_sha:
        unmet.append("release validation commit_sha must match target release SHA")
    benchmark_source_sha = data.get("benchmark_source_sha")
    if not _sha(benchmark_source_sha):
        unmet.append("benchmark_source_sha must be a 40-character lowercase Git SHA")
    elif _sha(data.get("commit_sha")):
        unmet.extend(_benchmark_source_compatibility_errors(root, str(benchmark_source_sha), str(data["commit_sha"])))
    if data.get("exact_head_ci_conclusion") not in {"success", "passed"}:
        unmet.append("exact_head_ci_conclusion must be success or passed")
    if private_pack_fingerprint_sha256 is None:
        unmet.append("active private pack fingerprint is required for release-candidate evidence")
    elif data.get("private_pack_fingerprint_sha256") != private_pack_fingerprint_sha256:
        unmet.append("private_pack_fingerprint_sha256 must match the active private pack fingerprint")
    required_commands = (
        "python3 -m unittest discover -s tests",
        "python3 scripts/validate_public.py --include-scripted-baseline",
        "python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke",
        "python3 scripts/validate_v0_release.py",
        "python3 scripts/validate_baseline_registry.py",
        "python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary",
        "python3 scripts/generate_paper_tables.py",
        "git diff --exit-code -- paper/shared",
        "git diff --check",
        "git ls-files tasks_private/holdout results captures docs/reviews/panel-logs",
    )
    commands = data.get("commands")
    if not isinstance(commands, dict):
        unmet.append("commands must be an object keyed by required command")
        commands = {}
    for command in required_commands:
        command_result = commands.get(command)
        if not isinstance(command_result, dict) or command_result.get("passed") is not True:
            unmet.append(f"missing passed release validation command: {command}")
    if data.get("pushed_commit") is not True:
        unmet.append("pushed_commit must be true")
    evidence_resolved = {(evidence_path if evidence_path.is_absolute() else root / evidence_path).resolve()}
    if not _working_tree_clean(root, evidence_resolved):
        unmet.append("working tree must be clean when validating release-candidate evidence")
    return {"passed": not unmet, "path": str(evidence_path), "unmet": unmet}


def _benchmark_source_sha_from_release_evidence(release_evidence_path: Path | None) -> str | None:
    if release_evidence_path is None:
        return None
    path = release_evidence_path if release_evidence_path.is_absolute() else ROOT / release_evidence_path
    if not path.exists():
        return None
    try:
        data = load_json(path)
    except Exception:
        return None
    value = data.get("benchmark_source_sha") if isinstance(data, dict) else None
    return value if _sha(value) else None


def validate_v1_readiness(
    release_evidence_path: Path | None = None,
    *,
    public_view: bool = False,
) -> dict[str, Any]:
    gates: list[dict[str, Any]] = []
    target_sha = _current_commit_sha()
    benchmark_source_sha = _benchmark_source_sha_from_release_evidence(release_evidence_path) or target_sha

    manifest_result = validate_patterns([str(ROOT / "tasks" / "*" / "*.json")])
    registry_result = validate_registry()
    public_task_count = int(manifest_result["manifest_count"])
    vulnerable_task_count = int(manifest_result["vulnerable_count"])
    if public_view:
        rotation_result = {
            "passed": False,
            "pack_ids": [],
            "roles": [],
            "validated_private_task_count": 0,
            "active_pack_id": None,
            "active_pack_fingerprint_sha256": None,
            "unmet": ["private holdout rotation is intentionally not inspected in public view"],
        }
    else:
        rotation_result = _validate_private_rotation_metadata()
    validated_private_holdout_task_count = int(rotation_result["validated_private_task_count"])
    active_private_pack_fingerprint = rotation_result.get("active_pack_fingerprint_sha256")
    if not isinstance(active_private_pack_fingerprint, str):
        active_private_pack_fingerprint = None

    stable_unmet: list[str] = []
    if manifest_result["errors"]:
        stable_unmet.append("public task manifests do not validate")
    if public_task_count < 49:
        stable_unmet.append(f"current public split has {public_task_count} tasks, expected at least 49")
    if vulnerable_task_count < 20:
        stable_unmet.append(f"current public split has {vulnerable_task_count} vulnerable tasks, expected at least 20")
    if not registry_result["passed"]:
        stable_unmet.append("baseline registry validation has errors")
    if int(registry_result["current_public_model_family_count"]) < 6:
        stable_unmet.append("fewer than six current public model families are registered")
    if registry_result["has_current_public_tool_agent_baseline"] is not True:
        stable_unmet.append("missing current public tool-agent baseline")
    _add_gate(
        gates,
        "stable_v1_prep_public_evidence",
        not stable_unmet,
        [
            f"public_task_count={public_task_count}",
            f"vulnerable_task_count={vulnerable_task_count}",
            f"current_public_model_family_count={registry_result['current_public_model_family_count']}",
            f"has_current_public_tool_agent_baseline={registry_result['has_current_public_tool_agent_baseline']}",
        ],
        stable_unmet,
    )

    missing_packet_artifacts = [
        path for path in REQUIRED_REVIEW_PACKET_ARTIFACTS if not (ROOT / path).exists()
    ]
    review_state = _external_review_summary_state()
    packet_unmet: list[str] = []
    if not review_state["packet_exists"]:
        packet_unmet.append("external review packet is missing")
    if not review_state["summary_exists"]:
        packet_unmet.append("external review summary is missing")
    missing_lanes = sorted(set(REQUIRED_REVIEW_LANES) - set(review_state["lanes_present"]))
    if missing_lanes:
        packet_unmet.append(f"review packet is missing lanes: {', '.join(missing_lanes)}")
    if missing_packet_artifacts:
        packet_unmet.append(f"review packet artifact paths missing: {', '.join(missing_packet_artifacts)}")
    _add_gate(
        gates,
        "external_review_packet_ready",
        not packet_unmet,
        [
            "docs/reviews/external-review-packet.md",
            "docs/reviews/external-review-summary.md",
            f"review_lanes_present={len(review_state['lanes_present'])}",
        ],
        packet_unmet,
    )

    review_unmet: list[str] = []
    if review_state["has_incomplete_marker"]:
        review_unmet.append("independent external review lanes are not complete")
    if len(review_state["lanes_present"]) != len(REQUIRED_REVIEW_LANES):
        review_unmet.append("not all required external review lanes are present")
    structured_review = _validate_external_review_evidence()
    review_unmet.extend(structured_review["unmet"])
    _add_gate(
        gates,
        "external_review_completed",
        not review_unmet,
        [
            "docs/reviews/external-review-summary.md must record real review dates, reviewed artifacts, findings or no-finding dispositions, and decisions",
            EXTERNAL_REVIEW_EVIDENCE_PATH,
        ],
        review_unmet,
    )

    governance_text = _text(ROOT / "docs" / "v1-community-submission-governance.md")
    required_governance_sections = (
        "## Hosted Runner Path",
        "## Fully Containerized Path",
        "## Rotating Private Packs",
        "## Reruns, Ties, And Stale Scores",
        "## Minimum v1 Launch Bar",
    )
    governance_unmet = [section for section in required_governance_sections if section not in governance_text]
    if "does not claim that hosted" not in governance_text:
        governance_unmet.append("governance document must preserve hosted-infrastructure non-claim wording")
    _add_gate(
        gates,
        "submission_governance_spec_defined",
        not governance_unmet,
        ["docs/v1-community-submission-governance.md"],
        governance_unmet,
    )

    hosted_result = _validate_hosted_execution_evidence(
        benchmark_source_sha=benchmark_source_sha,
        private_pack_fingerprint_sha256=active_private_pack_fingerprint,
    )
    _add_gate(
        gates,
        "hosted_or_containerized_submission_execution",
        bool(hosted_result["passed"]),
        [hosted_result["path"]],
        hosted_result["unmet"],
    )

    _add_gate(
        gates,
        "rotating_private_holdouts_implemented",
        bool(rotation_result["passed"]),
        [
            ROTATION_METADATA_PATH,
            f"private_holdout_pack_ids={rotation_result['pack_ids']}",
            f"private_holdout_pack_roles={rotation_result['roles']}",
            f"active_private_pack_id={rotation_result['active_pack_id']}",
            f"active_private_pack_fingerprint_sha256={rotation_result['active_pack_fingerprint_sha256']}",
            f"validated_private_holdout_task_count={validated_private_holdout_task_count}",
        ],
        rotation_result["unmet"],
    )

    eligible_private_tool_rows = _eligible_private_rows(
        "tool-agent",
        benchmark_source_sha,
        active_private_pack_fingerprint,
    )
    private_tool_unmet: list[str] = []
    if not eligible_private_tool_rows:
        private_tool_unmet.append(
            "no repeated eligible private-holdout tool-agent leaderboard row exists"
        )
    elif not all(row["source_private_path_denial"] for row in eligible_private_tool_rows):
        private_tool_unmet.append("private tool-agent rows must prove source private-path denial")
    _add_gate(
        gates,
        "repeated_private_tool_agent_evidence",
        not private_tool_unmet,
        [f"eligible_private_tool_agent_rows={eligible_private_tool_rows}"],
        private_tool_unmet,
    )

    eligible_private_no_tools_rows = _eligible_private_rows(
        "no-tools-model",
        benchmark_source_sha,
        active_private_pack_fingerprint,
    )
    private_no_tools_unmet: list[str] = []
    if not eligible_private_no_tools_rows:
        private_no_tools_unmet.append(
            "no repeated eligible private-holdout no-tools model leaderboard row exists"
        )
    _add_gate(
        gates,
        "repeated_private_no_tools_evidence",
        not private_no_tools_unmet,
        [f"eligible_private_no_tools_rows={eligible_private_no_tools_rows}"],
        private_no_tools_unmet,
    )

    total_task_count = public_task_count + validated_private_holdout_task_count
    scale_unmet: list[str] = []
    if total_task_count < 100:
        scale_unmet.append(f"total public plus private holdout tasks is {total_task_count}, expected at least 100")
    _add_gate(
        gates,
        "v1_task_scale",
        not scale_unmet,
        [
            f"public_task_count={public_task_count}",
            f"validated_private_holdout_task_count={validated_private_holdout_task_count}",
            f"total_task_count={total_task_count}",
        ],
        scale_unmet,
    )

    paper_allowed_paths = (
        PAPER_POST_SOURCE_EVIDENCE_ONLY_PATHS
        if release_evidence_path is None
        else POST_SOURCE_EVIDENCE_ONLY_PATHS
    )
    paper_result = _validate_paper_readiness_evidence(
        benchmark_source_sha=_benchmark_source_sha_from_release_evidence(release_evidence_path),
        release_sha=target_sha,
        allowed_post_source_paths=paper_allowed_paths,
        upstream_gates_complete=(
            not review_unmet
            and bool(hosted_result["passed"])
            and bool(rotation_result["passed"])
        ),
    )
    _add_gate(
        gates,
        "paper_and_artifact_readiness",
        bool(paper_result["passed"]),
        [paper_result["path"]],
        paper_result["unmet"],
    )

    release_result = _validate_release_candidate_evidence(
        evidence_path=release_evidence_path,
        target_sha=target_sha,
        private_pack_fingerprint_sha256=active_private_pack_fingerprint,
    )
    _add_gate(
        gates,
        "final_release_candidate_validation",
        bool(release_result["passed"]),
        [release_result["path"]],
        release_result["unmet"],
    )

    passed_gate_count = sum(1 for gate in gates if gate["passed"])
    return {
        "passed": all(gate["passed"] for gate in gates),
        "v1_ready": all(gate["passed"] for gate in gates),
        "gate_count": len(gates),
        "passed_gate_count": passed_gate_count,
        "unmet_gate_count": len(gates) - passed_gate_count,
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AuthZBench-SaaS v1/community readiness gates.")
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Report v1 readiness state but exit successfully while planned gates remain incomplete.",
    )
    parser.add_argument(
        "--release-evidence",
        type=Path,
        help="External JSON release-candidate evidence file for strict v1 readiness validation.",
    )
    parser.add_argument(
        "--public-view",
        action="store_true",
        help="Ignore ignored/private checkout state so public expected output is deterministic.",
    )
    parser.add_argument(
        "--expected-output",
        type=Path,
        help="Require the rendered readiness JSON to match this expected-output fixture exactly.",
    )
    args = parser.parse_args()
    if args.public_view and args.release_evidence is not None:
        parser.error("--public-view cannot be combined with --release-evidence")
    result = validate_v1_readiness(args.release_evidence, public_view=args.public_view)
    print(dump_json(result))
    if args.expected_output is not None:
        expected_path = args.expected_output if args.expected_output.is_absolute() else ROOT / args.expected_output
        try:
            expected = load_json(expected_path)
        except Exception as exc:
            print(f"failed to load expected output {expected_path}: {exc}", file=sys.stderr)
            return 1
        if expected != result:
            print(
                f"v1 readiness output does not match expected fixture: {expected_path}",
                file=sys.stderr,
            )
            return 1
    if args.allow_incomplete:
        return 0
    return 0 if result["v1_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
