from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.validate_harbor_compatibility_state import (
    CURRENT_STATUS,
    EVIDENCE_PATH,
    PILOT_DIR,
    validate_harbor_compatibility_state,
)


class HarborCompatibilityStateTests(unittest.TestCase):
    def _write_evidence(self, tmp: str, mutate) -> Path:
        data = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        mutate(data)
        path = Path(tmp) / "evidence.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_checked_in_pilot_is_honestly_classified_stale(self) -> None:
        result = validate_harbor_compatibility_state()

        self.assertTrue(result["passed"], result)
        self.assertFalse(result["active_compatibility_verified"])
        self.assertEqual(
            result["declared_status"],
            "historical_stale_requires_rebuild",
        )
        self.assertTrue(result["current_validation_errors"], result)

    def test_cannot_self_declare_current_when_dataset_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_evidence(
                tmp,
                lambda data: data.update(
                    {
                        "evidence_status": CURRENT_STATUS,
                        "current_claim_eligible": True,
                        "requires_rebuild_before_current_claim": False,
                    }
                ),
            )

            result = validate_harbor_compatibility_state(PILOT_DIR, path)

        self.assertFalse(result["passed"], result)
        self.assertFalse(result["active_compatibility_verified"])
        self.assertTrue(
            any("evidence_status must be" in error for error in result["errors"]),
            result,
        )

    def test_rejects_duplicate_task_evidence(self) -> None:
        def duplicate(data: dict) -> None:
            data["tasks"][1]["task_id"] = data["tasks"][0]["task_id"]

        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_evidence(tmp, duplicate)
            result = validate_harbor_compatibility_state(PILOT_DIR, path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any("duplicate task id" in error for error in result["errors"]),
            result,
        )

    def test_rejects_publish_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_evidence(
                tmp,
                lambda data: data["manifest_contract"].update(
                    {"publish_attempted": True}
                ),
            )
            result = validate_harbor_compatibility_state(PILOT_DIR, path)

        self.assertFalse(result["passed"], result)
        self.assertIn(
            "manifest_contract.publish_attempted must be false",
            result["errors"],
        )

    def test_current_status_requires_canonical_dataset_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_evidence(
                tmp,
                lambda data: data.update(
                    {
                        "evidence_status": CURRENT_STATUS,
                        "current_claim_eligible": True,
                        "requires_rebuild_before_current_claim": False,
                    }
                ),
            )
            with mock.patch(
                "scripts.validate_harbor_compatibility_state.validate_harbor_dataset_skeleton",
                return_value={"passed": True, "errors": []},
            ), mock.patch(
                "scripts.validate_harbor_compatibility_state._current_binding_errors",
                return_value=[],
            ):
                result = validate_harbor_compatibility_state(PILOT_DIR, path)

        self.assertTrue(result["passed"], result)
        self.assertTrue(result["active_compatibility_verified"])

    def test_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            path.write_text(
                '{"schema_version":"harbor-kaggle-public-pilot-evidence-v1",'
                '"schema_version":"harbor-kaggle-public-pilot-evidence-v1"}',
                encoding="utf-8",
            )

            result = validate_harbor_compatibility_state(PILOT_DIR, path)

        self.assertFalse(result["passed"], result)
        self.assertTrue(
            any("duplicate JSON key: schema_version" in error for error in result["errors"]),
            result,
        )


if __name__ == "__main__":
    unittest.main()
