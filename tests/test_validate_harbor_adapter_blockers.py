from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_harbor_adapter_blockers import (
    BLOCKERS_PATH,
    REQUIRED_BLOCKERS,
    REQUIRED_HELPERS,
    validate_harbor_adapter_blockers,
)


class HarborAdapterBlockerValidatorTests(unittest.TestCase):
    def test_current_blocker_artifact_passes(self) -> None:
        result = validate_harbor_adapter_blockers()

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["blocked_item_count"], len(REQUIRED_BLOCKERS))
        self.assertGreaterEqual(result["repo_side_helper_count"], len(REQUIRED_HELPERS))

    def test_rejects_unblocked_parity_and_private_leak_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harbor-adapter-readiness-blockers.json"
            data = json.loads(BLOCKERS_PATH.read_text(encoding="utf-8"))
            data["public_claim_boundary"] = "This is parity evidence for adapter readiness."
            data["required_before_adapter_ready"][0]["status"] = "unblocked_and_verified"
            data["required_before_adapter_ready"][1]["required_evidence"] = []
            data["repo_side_progress"][0]["claim_boundary"] = "Proves Harbor execution."
            data["debug_note"] = "raw private output at /tmp/authzbench/private.json"
            path.write_text(json.dumps(data), encoding="utf-8")

            result = validate_harbor_adapter_blockers(path)

        self.assertFalse(result["passed"], result)
        self.assertIn(
            "public_claim_boundary must reject platform acceptance, hosted operation, and external review claims",
            result["errors"],
        )
        self.assertTrue(any("status must be" in error for error in result["errors"]), result)
        self.assertTrue(any("required_evidence must be a non-empty list" in error for error in result["errors"]), result)
        self.assertTrue(any("claim_boundary must state what the helper does not prove" in error for error in result["errors"]), result)
        self.assertTrue(any("sensitive private detail marker" in error for error in result["errors"]), result)
        self.assertTrue(any("local absolute path is not allowed" in error for error in result["errors"]), result)

    def test_rejects_authored_complete_status_when_evidence_is_historical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harbor-adapter-readiness-blockers.json"
            data = json.loads(BLOCKERS_PATH.read_text(encoding="utf-8"))
            parity = next(
                row
                for row in data["required_before_adapter_ready"]
                if row["item"] == "parity_experiment_json"
            )
            parity["status"] = "complete"
            parity.pop("missing_input", None)
            path.write_text(json.dumps(data), encoding="utf-8")

            result = validate_harbor_adapter_blockers(path)

        self.assertFalse(result["passed"], result)
        self.assertIn(
            "parity_experiment_json: declared status 'complete' does not match derived status 'historical_stale'",
            result["errors"],
        )
        self.assertEqual(
            result["derived_statuses"]["parity_experiment_json"],
            "historical_stale",
        )

    def test_rejects_positive_external_or_hosted_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harbor-adapter-readiness-blockers.json"
            data = json.loads(BLOCKERS_PATH.read_text(encoding="utf-8"))
            data["harbor_acceptance_claimed"] = True
            data["hosted_execution_verified"] = True
            path.write_text(json.dumps(data), encoding="utf-8")

            result = validate_harbor_adapter_blockers(path)

        self.assertFalse(result["passed"], result)
        self.assertIn(
            "harbor_acceptance_claimed must be explicitly false",
            result["errors"],
        )
        self.assertIn(
            "hosted_execution_verified must be explicitly false",
            result["errors"],
        )

    def test_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harbor-adapter-readiness-blockers.json"
            path.write_text(
                '{"schema_version":"harbor-adapter-readiness-blockers-v1",'
                '"schema_version":"harbor-adapter-readiness-blockers-v1"}',
                encoding="utf-8",
            )

            result = validate_harbor_adapter_blockers(path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any("duplicate JSON key: schema_version" in error for error in result["errors"]),
            result,
        )


if __name__ == "__main__":
    unittest.main()
