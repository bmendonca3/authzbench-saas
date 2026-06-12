"""Tests for Harbor parity experiment validators and evidence checks."""

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
from authzbench_harbor.schemas import PARITY_EXPERIMENT_SCHEMA_VERSION


class TestValidateParityExperiment(unittest.TestCase):
    def _write_parity(self, tmp: str, data: dict) -> Path:
        path = Path(tmp) / "parity.json"
        path.write_text(json.dumps(data))
        return path

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

    def test_parity_verified_true_without_harbor_results_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = {
                "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
                "evidence_status": "complete",
                "public_claim_boundary": "test",
                "parity_verified": True,
                "native_authzbench_results": {"task1": {"score": 1.0}},
            }
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("harbor_results" in e for e in result["errors"]))

    def test_parity_verified_true_without_harbor_run_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = {
                "schema_version": PARITY_EXPERIMENT_SCHEMA_VERSION,
                "evidence_status": "complete",
                "public_claim_boundary": "test",
                "parity_verified": True,
                "harbor_results": {"reward_mean": 0.5},
                "native_authzbench_results": {"task1": {"score": 1.0}},
            }
            path = self._write_parity(tmp, data)
            result = validate_parity_experiment(path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("harbor_run_id" in e for e in result["errors"]))

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
