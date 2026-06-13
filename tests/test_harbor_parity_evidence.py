"""Tests for Harbor parity experiment validators and evidence checks.

Covers:
- Baseline file/schema checks (T1 baseline);
- Methodology enforcement: missing/unknown methodology, aggregate_means +
  verified requires historical_backcompat (T11, T12, T13, T28);
- per_task_pairing completeness: missing fields, mismatches, missing tasks
  (T14, T15, T16);
- Strict reward tolerance behavior (T17, T19);
- per_task_disagreements consistency (T18, T19);
- aggregate historical evidence can omit per-task maps (T20);
- blocked evidence can omit per-task fields (item 29);
- CLI --parity-methodology default (item 30);
- Validator does not silently default methodology for verified evidence (item 28).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_harbor_parity_experiment import validate_parity_experiment
from scripts.validate_harbor_adapter_metadata import validate_adapter_metadata
from authzbench_harbor.schemas import (
    DEFAULT_REWARD_TOLERANCE,
    PARITY_EVIDENCE_STATUS_VALUES,
    PARITY_EXPERIMENT_SCHEMA_VERSION,
    REQUIRED_MATCH_RATE,
)


def _make_task_pairing_payload(
    *,
    evidence_status: str = "current",
    methodology: str = "per_task_pairing",
    match_rate: float = 1.0,
    per_task_match: dict | None = None,
    per_task_disagreements: list | None = None,
    per_task_match_count: int | None = None,
    task_ids: list[str] | None = None,
    reward_tolerance: float = DEFAULT_REWARD_TOLERANCE,
    required_match_rate: float = REQUIRED_MATCH_RATE,
    parity_verified: bool = True,
    reward_overrides: dict | None = None,
    score_overrides: dict | None = None,
    harbor_rewards: dict | None = None,
    native_scores: dict | None = None,
) -> dict:
    task_ids = task_ids or ["task1", "task2"]
    if harbor_rewards is None:
        harbor_rewards = {tid: 1.0 for tid in task_ids}
    if native_scores is None:
        native_scores = {tid: 1.0 for tid in task_ids}
    if reward_overrides:
        harbor_rewards = {**harbor_rewards, **reward_overrides}
    if score_overrides:
        native_scores = {**native_scores, **score_overrides}

    per_task_match = per_task_match if per_task_match is not None else {
        tid: abs(native_scores[tid] - harbor_rewards[tid]) <= reward_tolerance
        for tid in task_ids
    }
    per_task_disagreements = per_task_disagreements if per_task_disagreements is not None else [
        tid for tid in task_ids if not per_task_match.get(tid, False)
    ]
    match_count = per_task_match_count if per_task_match_count is not None else sum(
        1 for v in per_task_match.values() if v
    )

    return {
        "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
        "evidence_status": evidence_status,
        "public_claim_boundary": "test",
        "parity_verified": parity_verified,
        "parity_methodology": methodology,
        "reward_tolerance": reward_tolerance,
        "required_match_rate": required_match_rate,
        "parity_match_threshold": 1.0,
        "harbor_results": {"harbor_run_id": "run-1", "reward_mean": 1.0},
        "native_authzbench_results": {tid: {"score": native_scores[tid]} for tid in task_ids},
        "harbor_per_task_rewards": harbor_rewards,
        "native_per_task_scores": native_scores,
        "per_task_match": per_task_match,
        "per_task_match_count": match_count,
        "per_task_match_rate": match_rate,
        "per_task_disagreements": per_task_disagreements,
        "task_ids": task_ids,
        "task_count": len(task_ids),
        "raw_harbor_jobs_tracked": False,
        "private_artifacts_tracked": False,
    }


class TestValidateParityExperiment(unittest.TestCase):
    def _write_parity(self, tmp: str, data: dict) -> Path:
        path = Path(tmp) / "parity.json"
        path.write_text(json.dumps(data))
        return path

    # --- Baseline file checks -------------------------------------------

    def test_template_file_passes_as_template(self) -> None:
        template_path = ROOT / "artifact" / "harbor-parity-experiment.template.json"
        if not template_path.is_file():
            self.skipTest("template file not present")
        result = validate_parity_experiment(template_path)
        self.assertTrue(result["passed"])
        self.assertTrue(result.get("is_template"))

    def test_missing_file_fails(self) -> None:
        result = validate_parity_experiment(Path("/nonexistent/parity.json"))
        self.assertFalse(result["passed"])
        self.assertTrue(any("not found" in e for e in result["errors"]))

    def test_invalid_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "parity.json"
            path.write_text("not valid json")
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])

    # --- T1: verified evidence without harbor_results fails -------------

    def test_parity_verified_true_without_harbor_results_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            del data["harbor_results"]
            data["parity_methodology"] = "aggregate_means"
            data["evidence_status"] = "historical_backcompat"
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("harbor_results" in e for e in result["errors"]))

    def test_parity_verified_true_without_harbor_run_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            data["parity_methodology"] = "aggregate_means"
            data["evidence_status"] = "historical_backcompat"
            data["harbor_results"] = {"reward_mean": 0.5}
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("harbor_run_id" in e for e in result["errors"]))

    # --- Blocked evidence (item 29) can omit per-task fields -----------

    def test_parity_verified_false_with_blocked_status_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = {
                "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
                "evidence_status": "blocked",
                "public_claim_boundary": "test",
                "parity_verified": False,
                "blocked_until": ["Harbor CLI not available"],
                "raw_harbor_jobs_tracked": False,
                "private_artifacts_tracked": False,
            }
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")

    def test_complete_blocked_experiment_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = {
                "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
                "evidence_status": "blocked",
                "public_claim_boundary": "This does not claim Harbor acceptance.",
                "parity_verified": False,
                "blocked_until": ["Harbor CLI not installed"],
                "adapter_version": "0.1.0",
                "task_count": 6,
                "task_ids": ["task-1"],
                "raw_harbor_jobs_tracked": False,
                "private_artifacts_tracked": False,
            }
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")

    # --- raw/private tracking -------------------------------------------

    def test_raw_harbor_jobs_tracked_true_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = {
                "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
                "evidence_status": "blocked",
                "public_claim_boundary": "test",
                "parity_verified": False,
                "raw_harbor_jobs_tracked": True,
            }
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("raw_harbor_jobs_tracked" in e for e in result["errors"]))

    def test_private_artifacts_tracked_true_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = {
                "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
                "evidence_status": "blocked",
                "public_claim_boundary": "test",
                "parity_verified": False,
                "private_artifacts_tracked": True,
            }
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])

    # --- Complete per_task_pairing evidence passes ----------------------

    def test_complete_parity_evidence_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")

    # --- T11: missing methodology fails ---------------------------------

    def test_missing_methodology_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            del data["parity_methodology"]
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("parity_methodology" in e for e in result["errors"])
            )

    # --- T12: unknown methodology fails ---------------------------------

    def test_unknown_methodology_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(methodology="unknown_method")
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("parity_methodology must be one of" in e for e in result["errors"]))

    # --- T13: aggregate_means + verified + non-historical fails ---------

    def test_aggregate_means_verified_non_historical_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                methodology="aggregate_means",
                evidence_status="current",
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("requires evidence_status='historical_backcompat'" in e for e in result["errors"])
            )

    def test_aggregate_means_verified_historical_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                methodology="aggregate_means",
                evidence_status="historical_backcompat",
            )
            # Historical evidence is allowed to omit per-task fields.
            for f in (
                "harbor_per_task_rewards",
                "native_per_task_scores",
                "per_task_match",
                "per_task_match_count",
                "per_task_match_rate",
                "per_task_disagreements",
                "parity_match_threshold",
            ):
                data.pop(f, None)
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")

    def test_aggregate_means_verified_allow_flag_passes(self) -> None:
        # Plan 6.2: aggregate_means with current status is not permitted
        # even with the allow flag, because the allow flag only relaxes
        # the aggregate_means + historical_backcompat contract; it does
        # not permit a current evidence payload to use aggregate_means.
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                methodology="aggregate_means",
                evidence_status="current",
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(
                path, allow_aggregate_means=True
            )
            self.assertFalse(
                result["passed"],
                "aggregate_means + current must fail under plan 6.2 even with allow flag",
            )
            self.assertTrue(
                any("evidence_status='current'" in e for e in result["errors"]),
                f"expected plan-6.2 cross-direction error, got: {result['errors']}",
            )

    def test_current_evidence_requires_per_task_pairing_methodology(self) -> None:
        # Plan 6.2 cross-direction validator contract: any payload
        # declaring evidence_status='current' must also declare
        # parity_methodology='per_task_pairing'. This applies regardless
        # of parity_verified.
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                methodology="per_task_pairing",
                evidence_status="current",
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")

        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                methodology="aggregate_means",
                evidence_status="current",
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(
                result["passed"],
                "current + aggregate_means must fail under plan 6.2",
            )
            self.assertTrue(
                any("evidence_status='current'" in e for e in result["errors"]),
                f"expected cross-direction error, got: {result['errors']}",
            )

    # --- T14: per_task_pairing missing fields fails ---------------------

    def test_per_task_pairing_missing_fields_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            del data["per_task_disagreements"]
            del data["parity_match_threshold"]
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("per_task_disagreements" in e for e in result["errors"])
            )
            self.assertTrue(
                any("parity_match_threshold" in e for e in result["errors"])
            )

    # --- T15: per_task mismatch fails -----------------------------------

    def test_per_task_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                per_task_match={"task1": True, "task2": True},  # lies
                reward_overrides={"task2": 0.0},  # real mismatch
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("per_task_match" in e for e in result["errors"]))

    # --- T16: per_task missing task fails -------------------------------

    def test_per_task_missing_task_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(task_ids=["task1", "task2"])
            # Remove task2 from harbor_per_task_rewards
            del data["harbor_per_task_rewards"]["task2"]
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("harbor_per_task_rewards for every task_id" in e for e in result["errors"])
            )

    # --- T17: tolerance behavior ----------------------------------------

    def test_tolerance_strict_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Build a payload where task1 native score is outside the strict
            # tolerance but the per_task_match record lies and says True. The
            # validator must recompute and surface the disagreement.
            data = _make_task_pairing_payload(
                reward_overrides={"task1": 1.0 + 1.5 * DEFAULT_REWARD_TOLERANCE},
                per_task_match={"task1": True, "task2": True},  # lies on task1
                per_task_disagreements=[],  # lies
                per_task_match_count=2,  # lies
                match_rate=1.0,  # lies
                parity_verified=True,  # so per-task validation runs
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("per_task_match" in e and "recomputed" in e for e in result["errors"])
            )

    def test_reward_tolerance_above_default_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(reward_tolerance=1e-3)
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("reward_tolerance" in e for e in result["errors"]))

    # --- T18: per_task_disagreements consistency ------------------------

    def test_per_task_disagreements_consistency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Make task1 actually disagree (out of tolerance), but lie that
            # there are no disagreements. Validator must surface the mismatch.
            data = _make_task_pairing_payload(
                reward_overrides={"task1": 0.0},
                per_task_disagreements=[],  # lies
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("per_task_disagreements" in e for e in result["errors"])
            )

    # --- T19: match-rate consistency (recompute) ------------------------

    def test_match_rate_consistency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                per_task_match_count=1,  # lies; should be 2
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("per_task_match_count" in e for e in result["errors"])
            )

    def test_match_rate_below_required_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                match_rate=0.5,
                per_task_match={"task1": True, "task2": False},
                per_task_match_count=1,
                per_task_disagreements=["task2"],
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("per_task_match_rate" in e for e in result["errors"]))

    # --- T20: aggregate historical evidence does not require per-task ----

    def test_aggregate_historical_omits_per_task_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                methodology="aggregate_means",
                evidence_status="historical_backcompat",
            )
            # Drop all per-task fields entirely.
            for f in (
                "harbor_per_task_rewards",
                "native_per_task_scores",
                "per_task_match",
                "per_task_match_count",
                "per_task_match_rate",
                "per_task_disagreements",
                "parity_match_threshold",
            ):
                data.pop(f, None)
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")

    # --- Item 28: validator does not silently default methodology -----

    def test_no_silent_default_methodology_for_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Build a complete-looking payload but omit parity_methodology.
            data = _make_task_pairing_payload()
            del data["parity_methodology"]
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("parity_methodology" in e and "explicitly set" in e for e in result["errors"])
            )

    # --- Item 30: CLI --parity-methodology default ----------------------

    def test_cli_parity_methodology_default(self) -> None:
        # Smoke check: the generator exposes --parity-methodology with default
        # per_task_pairing. We invoke the CLI and inspect the help text.
        import subprocess
        result = subprocess.run(
            [
                "python3.11",
                "scripts/run_harbor_parity_experiment.py",
                "--help",
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--parity-methodology", result.stdout)
        self.assertIn("per_task_pairing", result.stdout)
        self.assertIn("aggregate_means", result.stdout)

    # --- Validator constants exposed via schemas -----------------------

    def test_schema_constants(self) -> None:
        self.assertEqual(DEFAULT_REWARD_TOLERANCE, 1e-5)
        self.assertEqual(REQUIRED_MATCH_RATE, 1.0)
        self.assertIn("current", PARITY_EVIDENCE_STATUS_VALUES)
        self.assertIn("historical_backcompat", PARITY_EVIDENCE_STATUS_VALUES)
        self.assertIn("blocked", PARITY_EVIDENCE_STATUS_VALUES)


class TestValidateAdapterMetadata(unittest.TestCase):
    def test_template_file_passes_as_template(self) -> None:
        template_path = ROOT / "artifact" / "harbor-adapter-metadata.template.json"
        if not template_path.is_file():
            self.skipTest("template file not present")
        result = validate_adapter_metadata(template_path)
        self.assertTrue(result["passed"])
        self.assertTrue(result.get("is_template"))

    def test_missing_file_fails(self) -> None:
        result = validate_adapter_metadata(Path("/nonexistent/metadata.json"))
        self.assertFalse(result["passed"])

    def test_real_metadata_without_required_fields_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metadata.json"
            path.write_text(json.dumps({"schema_version": "harbor-adapter-metadata-v1"}))
            result = validate_adapter_metadata(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("missing required field" in e for e in result["errors"]))

    def test_real_metadata_with_all_required_fields_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metadata.json"
            data = {
                "schema_version": "harbor-adapter-metadata-v1",
                "evidence_status": "implementation_target",
                "public_claim_boundary": "No Harbor acceptance claimed.",
                "adapter_version": "0.1.0",
            }
            path.write_text(json.dumps(data))
            result = validate_adapter_metadata(path)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")

    def test_private_path_in_metadata_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metadata.json"
            data = {
                "schema_version": "harbor-adapter-metadata-v1",
                "evidence_status": "complete",
                "public_claim_boundary": "ok",
                "adapter_version": "0.1.0",
                "tasks_private/holdout": "leaked",
            }
            path.write_text(json.dumps(data))
            result = validate_adapter_metadata(path)
            self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
