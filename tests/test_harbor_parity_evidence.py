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
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_harbor_parity_experiment as parity_runner
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
    harbor_mean = sum(harbor_rewards.values()) / len(harbor_rewards)
    native_mean = sum(native_scores.values()) / len(native_scores)

    return {
        "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
        "evidence_status": evidence_status,
        "public_claim_boundary": "test",
        "parity_verified": parity_verified,
        "current_claim_eligible": (
            parity_verified if evidence_status == "current" else False
        ),
        "requires_rerun_before_current_claim": (
            not parity_verified if evidence_status == "current" else True
        ),
        "parity_methodology": methodology,
        "reward_tolerance": reward_tolerance,
        "required_match_rate": required_match_rate,
        "parity_match_threshold": 1.0,
        "harbor_results": {
            "harbor_run_id": "run-1",
            "n_total_trials": len(task_ids),
            "n_completed_trials": len(task_ids),
            "n_errored_trials": 0,
            "reward_mean": harbor_mean,
        },
        "native_authzbench_results": {tid: {"score": native_scores[tid]} for tid in task_ids},
        "harbor_reward_mean": harbor_mean,
        "native_mean_score": native_mean,
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

    # --- P0 adversarial evidence-integrity checks -----------------------

    def test_duplicate_task_ids_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            data["task_ids"] = ["task1", "task1"]
            data["task_count"] = 2
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("duplicate task_ids" in e for e in result["errors"]), result)

    def test_per_task_maps_require_exact_task_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            data["harbor_per_task_rewards"]["unknown-task"] = 1.0
            data["native_authzbench_results"]["unknown-task"] = {"score": 1.0}
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("harbor_per_task_rewards keys must exactly match task_ids" in e for e in result["errors"]),
                result,
            )
            self.assertTrue(
                any("native_authzbench_results keys must exactly match task_ids" in e for e in result["errors"]),
                result,
            )

    def test_non_finite_rewards_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            data["harbor_per_task_rewards"]["task1"] = float("nan")
            data["harbor_reward_mean"] = float("nan")
            data["harbor_results"]["reward_mean"] = float("nan")
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any(
                    "finite number" in error or "non-finite JSON number" in error
                    for error in result["errors"]
                ),
                result,
            )

    def test_duplicate_json_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "parity.json"
            path.write_text(
                '{"schema_version":"harbor-parity-experiment-v1",'
                '"schema_version":"harbor-parity-experiment-v1"}',
                encoding="utf-8",
            )

            result = validate_parity_experiment(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any("duplicate JSON key: schema_version" in error for error in result["errors"]),
            result,
        )

    def test_task_and_trial_counts_must_be_exact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            data["task_count"] = 3
            data["harbor_results"]["n_total_trials"] = 3
            data["harbor_results"]["n_completed_trials"] = 3
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("task_count" in e and "task_ids" in e for e in result["errors"]), result)
            self.assertTrue(any("n_total_trials" in e and "task_count" in e for e in result["errors"]), result)

    def test_verified_parity_rejects_errored_trials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            data["harbor_results"]["n_completed_trials"] = 1
            data["harbor_results"]["n_errored_trials"] = 1
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("zero errored trials" in e for e in result["errors"]), result)

    def test_declared_means_are_recomputed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            data["native_mean_score"] = 0.25
            data["harbor_reward_mean"] = 0.75
            data["harbor_results"]["reward_mean"] = 0.5
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("native_mean_score" in e and "recomputed" in e for e in result["errors"]), result)
            self.assertTrue(any("harbor_reward_mean" in e and "recomputed" in e for e in result["errors"]), result)

    def test_current_false_parity_is_recomputed_and_cannot_hide_a_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(parity_verified=False)
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("parity_verified" in e and "recomputed value is True" in e for e in result["errors"]), result)

    def test_current_false_parity_with_honest_disagreement_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(
                parity_verified=False,
                reward_overrides={"task2": 0.0},
                per_task_match={"task1": True, "task2": False},
                per_task_disagreements=["task2"],
                per_task_match_count=1,
                match_rate=0.5,
            )
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertTrue(result["passed"], result)

    def test_current_claim_eligibility_is_recomputed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload()
            data["current_claim_eligible"] = False
            data["requires_rerun_before_current_claim"] = True
            path = self._write_parity(tmp, data)

            result = validate_parity_experiment(path)

            self.assertFalse(result["passed"], result)
            self.assertTrue(
                any("current_claim_eligible" in error for error in result["errors"]),
                result,
            )

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

    def test_historical_stale_per_task_evidence_preserves_result_but_is_ineligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(evidence_status="historical_stale")
            data["current_claim_eligible"] = False
            data["requires_rerun_before_current_claim"] = True
            data["stale_reason"] = "benchmark source changed after this local run"
            path = self._write_parity(tmp, data)

            result = validate_parity_experiment(path)

            self.assertTrue(result["passed"], result)
            self.assertTrue(result["parity_verified"])

    def test_historical_stale_requires_explicit_ineligibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _make_task_pairing_payload(evidence_status="historical_stale")
            data.pop("current_claim_eligible")
            data.pop("requires_rerun_before_current_claim")
            path = self._write_parity(tmp, data)

            result = validate_parity_experiment(path)

            self.assertFalse(result["passed"], result)
            self.assertTrue(
                any("current_claim_eligible=false" in error for error in result["errors"]),
                result,
            )

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

    def test_runner_rejects_new_aggregate_means_evidence_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "parity.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_harbor_parity_experiment.py",
                    "--parity-methodology",
                    "aggregate_means",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                cwd=ROOT,
                timeout=30,
            )
            output_exists = output.exists()

        self.assertEqual(result.returncode, 2, result)
        self.assertIn("historical validation compatibility only", result.stderr)
        self.assertFalse(output_exists)

    # --- Validator constants exposed via schemas -----------------------

    def test_schema_constants(self) -> None:
        self.assertEqual(DEFAULT_REWARD_TOLERANCE, 1e-5)
        self.assertEqual(REQUIRED_MATCH_RATE, 1.0)
        self.assertIn("current", PARITY_EVIDENCE_STATUS_VALUES)
        self.assertIn("historical_backcompat", PARITY_EVIDENCE_STATUS_VALUES)
        self.assertIn("historical_stale", PARITY_EVIDENCE_STATUS_VALUES)
        self.assertIn("blocked", PARITY_EVIDENCE_STATUS_VALUES)


class TestHarborParityRunnerIntegrity(unittest.TestCase):
    @staticmethod
    def _write_job_result(path: Path, run_id: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "id": run_id,
                    "n_total_trials": 1,
                    "stats": {
                        "n_completed_trials": 1,
                        "n_errored_trials": 0,
                        "evals": {"oracle": {"metrics": [{"mean": 1.0}]}},
                    },
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _write_trial(job_dir: Path, name: str, task_name: str, reward: object) -> None:
        trial_path = job_dir / name / "result.json"
        trial_path.parent.mkdir(parents=True, exist_ok=True)
        trial_path.write_text(
            json.dumps(
                {
                    "id": name,
                    "task_name": task_name,
                    "verifier_result": {"rewards": {"reward": reward}},
                }
            ),
            encoding="utf-8",
        )

    def test_run_harbor_selects_only_the_newly_created_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp)
            (dataset_dir / "run_authzbench_saas.yaml").write_text("tasks: []\n", encoding="utf-8")
            old_result = dataset_dir / "harbor-jobs" / "zzz-old" / "result.json"
            self._write_job_result(old_result, "old-run")

            def fake_run(*args: object, **kwargs: object) -> SimpleNamespace:
                new_result = dataset_dir / "harbor-jobs" / "aaa-new" / "result.json"
                self._write_job_result(new_result, "new-run")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch.object(parity_runner.subprocess, "run", side_effect=fake_run):
                result = parity_runner._run_harbor(dataset_dir, ["harbor"])

        self.assertIsInstance(result, dict)
        self.assertEqual(result["harbor_run_id"], "new-run")
        self.assertTrue(str(result["job_dir"]).endswith("aaa-new"))

    def test_runner_rejects_duplicate_manifest_task_ids(self) -> None:
        task_ids, error = parity_runner._manifest_task_ids(
            {
                "task_count": 2,
                "tasks": [{"id": "task1"}, {"id": "task1"}],
            }
        )
        self.assertEqual(task_ids, [])
        self.assertIsInstance(error, str)
        self.assertIn("duplicate task ids", error)

    def test_runner_rejects_inexact_harbor_summary_counts(self) -> None:
        error = parity_runner._harbor_summary_error(
            {
                "harbor_run_id": "run-1",
                "n_total_trials": 3,
                "n_completed_trials": 3,
                "n_errored_trials": 0,
                "reward_mean": 1.0,
            },
            2,
        )
        self.assertIsInstance(error, str)
        self.assertIn("exactly match dataset task_count", error)

    def test_runner_rejects_native_scoring_errors(self) -> None:
        error = parity_runner._native_results_error(
            ["task1"],
            {"task1": {"score": 0.0, "error": "scorer crashed"}},
        )
        self.assertIsInstance(error, str)
        self.assertIn("scoring error", error)

    def test_run_harbor_rejects_ambiguous_new_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp)
            (dataset_dir / "run_authzbench_saas.yaml").write_text("tasks: []\n", encoding="utf-8")

            def fake_run(*args: object, **kwargs: object) -> SimpleNamespace:
                self._write_job_result(
                    dataset_dir / "harbor-jobs" / "new-one" / "result.json",
                    "new-one",
                )
                self._write_job_result(
                    dataset_dir / "harbor-jobs" / "new-two" / "result.json",
                    "new-two",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch.object(parity_runner.subprocess, "run", side_effect=fake_run):
                result = parity_runner._run_harbor(dataset_dir, ["harbor"])

        self.assertIsInstance(result, str)
        self.assertIn("exactly one newly created", result)

    def test_trial_collection_rejects_unknown_and_duplicate_task_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_trial(job_dir, "trial-1", "authzbench-saas/task1", 1.0)
            self._write_trial(job_dir, "trial-2", "authzbench-saas/unknown", 1.0)
            result = parity_runner._collect_harbor_trial_rewards(
                job_dir,
                ["task1", "task2"],
            )
            self.assertIsInstance(result, str)
            self.assertIn("unknown trial task key", result)

        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_trial(job_dir, "trial-1", "authzbench-saas/task1", 1.0)
            self._write_trial(job_dir, "trial-2", "authzbench-saas/task1", 1.0)
            result = parity_runner._collect_harbor_trial_rewards(
                job_dir,
                ["task1", "task2"],
            )
            self.assertIsInstance(result, str)
            self.assertIn("duplicate trial task key", result)

    def test_trial_collection_rejects_non_finite_reward(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            self._write_trial(job_dir, "trial-1", "authzbench-saas/task1", float("inf"))
            result = parity_runner._collect_harbor_trial_rewards(job_dir, ["task1"])
            self.assertIsInstance(result, str)
            self.assertTrue(
                "finite numeric reward" in result or "non-finite JSON number" in result,
                result,
            )


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
            data = json.loads(
                (ROOT / "artifact" / "harbor-adapter-metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            path.write_text(json.dumps(data))
            result = validate_adapter_metadata(path)
            self.assertTrue(result["passed"], f"errors: {result['errors']}")

    def test_real_metadata_rejects_live_http_as_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metadata.json"
            data = json.loads(
                (ROOT / "artifact" / "harbor-adapter-metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            data["supported_lanes"].append("live_http_tool_agent")
            path.write_text(json.dumps(data))

            result = validate_adapter_metadata(path)

            self.assertFalse(result["passed"], result)
            self.assertIn(
                "supported_lanes must contain only the implemented no_tools lane",
                result["errors"],
            )

    def test_real_metadata_rejects_positive_external_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metadata.json"
            data = json.loads(
                (ROOT / "artifact" / "harbor-adapter-metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            data["hosted_execution_verified"] = True
            path.write_text(json.dumps(data))

            result = validate_adapter_metadata(path)

            self.assertFalse(result["passed"], result)
            self.assertIn(
                "hosted_execution_verified must be explicitly false in local adapter metadata",
                result["errors"],
            )

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
