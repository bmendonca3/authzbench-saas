"""Validate all external-review surfaces without conflating pending and complete.

The default mode is a public/CI structural gate: well-formed pending review
records pass while ``external_validation_complete`` remains false. The strict
``--require-complete`` mode is the only gate that may support the repository's
externally-validated claim, and it requires the three independent lanes, their
public summary, the separate SaaS product-security lane, and cross-surface
source/status coherence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from authzbench.core import load_json
from scripts import validate_external_review_summary as registry_validator
from scripts import validate_cohort_methodology_decision as cohort_validator
from scripts import validate_saas_product_security_review as saas_validator
from scripts.validate_v1_readiness import (
    REVIEW_LANE_IDS,
    REQUIRED_REVIEW_LANES,
    _validate_external_review_evidence,
)

REGISTRY_PATH = ROOT / "docs/reviews/external-review-registry.json"
SUMMARY_JSON_PATH = ROOT / "docs/reviews/external-review-summary.json"
SUMMARY_MD_PATH = ROOT / "docs/reviews/external-review-summary.md"

# These paths are source/evidence inputs to at least one of the four review
# lanes. They are mandatory even when a reviewer accidentally omits them from
# ``artifacts_reviewed``. Review records and public summaries are deliberately
# not whole-tree-bound because they are created after the frozen source commit.
MANDATORY_REVIEW_SOURCE_TREES = (
    ".github/workflows",
    "apps",
    "artifact",
    "authzbench",
    "authzbench_harbor",
    "baselines",
    "examples",
    "leaderboard_sources",
    "leaderboard_submissions",
    "paper",
    "scripts",
    "tasks",
    "tests",
)
MANDATORY_REVIEW_SOURCE_FILES = {
    "Dockerfile",
    "LICENSE",
    "README.md",
    "ROADMAP.md",
    "docker-compose.yml",
    "pyproject.toml",
    "requirements.lock",
    "docs/agent-evaluator-kit.md",
    "docs/baseline-credibility.md",
    "docs/baseline-variance-analysis.md",
    "docs/benchmark-spec.md",
    "docs/claims-and-evidence.md",
    "docs/kaggle-benchmark-design-contract.md",
    "docs/score-stability-policy.md",
    "docs/scoring-and-submissions.md",
    "docs/task-quality-matrix.md",
    "docs/task-quality-rubric.md",
    "docs/v1-community-submission-governance.md",
}


def _load_object(path: Path, label: str, findings: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        findings.append(f"{label}: missing {path.relative_to(ROOT)}")
        return None
    try:
        payload = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(f"{label}: invalid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        findings.append(f"{label}: root must be an object")
        return None
    return payload


def _coherence_findings(
    registry: dict[str, Any],
    summary: dict[str, Any],
) -> list[str]:
    findings: list[str] = []
    registry_lanes = registry.get("lanes")
    summary_lanes = summary.get("review_lanes")
    if not isinstance(registry_lanes, list) or not isinstance(summary_lanes, list):
        return ["review registry and summary must both contain lane lists"]

    registry_by_id = {
        lane.get("lane"): lane
        for lane in registry_lanes
        if isinstance(lane, dict) and isinstance(lane.get("lane"), str)
    }
    summary_by_id = {
        lane.get("registry_lane_id", REVIEW_LANE_IDS.get(str(lane.get("lane")))): lane
        for lane in summary_lanes
        if isinstance(lane, dict) and lane.get("lane") in REQUIRED_REVIEW_LANES
    }
    for lane_name, lane_id in REVIEW_LANE_IDS.items():
        raw_lane = registry_by_id.get(lane_id)
        public_lane = summary_by_id.get(lane_id)
        if not isinstance(raw_lane, dict) or not isinstance(public_lane, dict):
            findings.append(f"{lane_id}: missing registry or summary lane for coherence")
            continue
        if public_lane.get("lane") != lane_name:
            findings.append(f"{lane_id}: summary lane name does not match canonical mapping")
        if raw_lane.get("review_status") != public_lane.get("review_status"):
            findings.append(f"{lane_id}: review_status differs between registry and summary")
            continue
        if raw_lane.get("review_status") == "complete":
            for field in ("review_date", "reviewed_commit_sha", "overall_disposition"):
                if raw_lane.get(field) != public_lane.get(field):
                    findings.append(f"{lane_id}: {field} differs between registry and summary")
    return findings


def _markdown_findings(
    summary: dict[str, Any],
    *,
    require_complete: bool,
) -> list[str]:
    if not SUMMARY_MD_PATH.is_file():
        return ["external review Markdown summary is missing"]
    text = SUMMARY_MD_PATH.read_text(encoding="utf-8")
    findings: list[str] = []
    for lane_name in REQUIRED_REVIEW_LANES:
        if lane_name not in text:
            findings.append(f"Markdown summary is missing lane heading/text: {lane_name}")
    if require_complete:
        lowered = text.lower()
        for marker in (
            "no independent external review is claimed yet",
            "reviewer not yet engaged",
            "current blocker",
            "review is pending",
        ):
            if marker in lowered:
                findings.append(f"Markdown summary retains incomplete marker: {marker}")
        lanes = summary.get("review_lanes")
        if isinstance(lanes, list):
            for lane in lanes:
                if not isinstance(lane, dict) or lane.get("review_status") != "complete":
                    continue
                commit_sha = lane.get("reviewed_commit_sha")
                if isinstance(commit_sha, str) and commit_sha not in text:
                    findings.append(
                        f"Markdown summary does not cite reviewed commit for {lane.get('lane')}"
                    )
    return findings


def _git_blob(root: Path, commit_sha: str, relative_path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{commit_sha}:{relative_path}"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout if result.returncode == 0 else None


def _git_path_set(
    root: Path,
    args: list[str],
    *,
    label: str,
    findings: list[str],
) -> set[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        findings.append(
            f"cannot enumerate {label}: {result.stderr.strip() or 'git command failed'}"
        )
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _strict_source_binding_findings(
    registry: dict[str, Any],
    summary: dict[str, Any],
    saas_registry: dict[str, Any],
) -> list[str]:
    findings: list[str] = []
    registry_lanes = registry.get("lanes")
    summary_lanes = summary.get("review_lanes")
    if not isinstance(registry_lanes, list) or not isinstance(summary_lanes, list):
        return ["strict source binding requires both canonical lane lists"]

    complete_registry_lanes = [
        lane
        for lane in registry_lanes
        if isinstance(lane, dict) and lane.get("review_status") == "complete"
    ]
    reviewed_shas = {
        lane.get("reviewed_commit_sha")
        for lane in complete_registry_lanes
        if isinstance(lane.get("reviewed_commit_sha"), str)
    }
    if saas_registry.get("review_status") == "complete" and isinstance(
        saas_registry.get("reviewed_commit_sha"),
        str,
    ):
        reviewed_shas.add(saas_registry["reviewed_commit_sha"])
    if len(reviewed_shas) != 1:
        findings.append(
            "strict external validation requires all three lanes and the SaaS lane to review one frozen commit"
        )
        return findings
    reviewed_sha = next(iter(reviewed_shas))
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", reviewed_sha, "HEAD"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestor.returncode != 0:
        findings.append(
            "the frozen reviewed commit must be an ancestor of the current review-record commit"
        )
        return findings

    bound_paths: set[str] = set(MANDATORY_REVIEW_SOURCE_FILES)
    for lane in complete_registry_lanes:
        for field in ("packet", "schema"):
            value = lane.get(field)
            if isinstance(value, str):
                bound_paths.add(value)
    for field in ("packet", "schema"):
        value = saas_registry.get(field)
        if isinstance(value, str):
            bound_paths.add(value)
    for lane in summary_lanes:
        if not isinstance(lane, dict) or lane.get("review_status") != "complete":
            continue
        artifacts = lane.get("artifacts_reviewed")
        if isinstance(artifacts, list):
            bound_paths.update(path for path in artifacts if isinstance(path, str))
    reviewed_tree_paths = _git_path_set(
        ROOT,
        [
            "ls-tree",
            "-r",
            "--name-only",
            reviewed_sha,
            "--",
            *MANDATORY_REVIEW_SOURCE_TREES,
        ],
        label="mandatory source paths at the reviewed commit",
        findings=findings,
    )
    current_tree_paths = _git_path_set(
        ROOT,
        [
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            *MANDATORY_REVIEW_SOURCE_TREES,
        ],
        label="current mandatory source paths",
        findings=findings,
    )
    bound_paths.update(reviewed_tree_paths)
    bound_paths.update(current_tree_paths)

    for relative_path in sorted(bound_paths):
        current_path = ROOT / relative_path
        reviewed_blob = _git_blob(ROOT, reviewed_sha, relative_path)
        if reviewed_blob is None:
            findings.append(
                f"reviewed commit does not contain declared review artifact: {relative_path}"
            )
            continue
        if not current_path.is_file():
            findings.append(f"current review artifact is missing: {relative_path}")
            continue
        if current_path.read_bytes() != reviewed_blob:
            findings.append(
                f"review artifact changed after reviewed commit: {relative_path}"
            )
    return findings


def validate(require_complete: bool = False) -> dict[str, Any]:
    findings: list[str] = []
    registry_result = registry_validator.validate(
        require_v2_complete=require_complete
    )
    summary_result = _validate_external_review_evidence(
        ROOT,
        require_complete=require_complete,
    )
    saas_result = saas_validator.validate(require_complete=require_complete)
    cohort_result = cohort_validator.validate(
        ROOT,
        require_complete=require_complete,
    )

    if not registry_result["passed"]:
        findings.extend(
            f"three-lane registry: {item}" for item in registry_result["findings"]
        )
    if not summary_result["passed"]:
        findings.extend(
            f"public review summary: {item}" for item in summary_result["unmet"]
        )
    if not saas_result["passed"]:
        findings.extend(
            f"SaaS product-security lane: {item}" for item in saas_result["findings"]
        )
    if not cohort_result["passed"]:
        findings.extend(
            f"cohort methodology: {item}" for item in cohort_result["errors"]
        )

    registry = _load_object(REGISTRY_PATH, "three-lane registry", findings)
    summary = _load_object(SUMMARY_JSON_PATH, "public review summary", findings)
    saas_registry = _load_object(
        saas_validator.REGISTRY_PATH,
        "SaaS product-security registry",
        findings,
    )
    if registry is not None and summary is not None:
        findings.extend(_coherence_findings(registry, summary))
        findings.extend(_markdown_findings(summary, require_complete=require_complete))
        if require_complete and saas_registry is not None:
            findings.extend(
                _strict_source_binding_findings(
                    registry,
                    summary,
                    saas_registry,
                )
            )

    complete = (
        not findings
        and registry_result.get("v2_external_validation_complete") is True
        and saas_result.get("saas_product_security_validation_complete") is True
        and cohort_result.get("methodology_complete") is True
        and require_complete
    )
    return {
        "schema_version": "v2-external-validation-gate-v1",
        "three_lane_registry_passed": registry_result["passed"],
        "three_lane_validation_complete": registry_result.get(
            "v2_external_validation_complete",
            False,
        ),
        "public_summary_passed": summary_result["passed"],
        "saas_product_security_registry_passed": saas_result["passed"],
        "saas_product_security_validation_complete": saas_result.get(
            "saas_product_security_validation_complete",
            False,
        ),
        "cohort_methodology_passed": cohort_result["passed"],
        "cohort_methodology_complete": cohort_result.get(
            "methodology_complete",
            False,
        ),
        "findings": findings,
        "passed": not findings,
        "external_validation_complete": complete,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Require all three independent lanes, the SaaS realism lane, and coherent public summaries.",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON output.")
    args = parser.parse_args()

    result = validate(require_complete=args.require_complete)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["passed"]:
        print(
            "v2 external validation gate: ok; "
            f"external_validation_complete={result['external_validation_complete']}"
        )
    else:
        print(
            f"v2 external validation gate: FAILED ({len(result['findings'])} findings)",
            file=sys.stderr,
        )
        for finding in result["findings"]:
            print(f"  - {finding}", file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
