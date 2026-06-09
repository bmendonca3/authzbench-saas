from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_harbor_integration import (
    CONTRACT_PATH,
    REQUIRED_COMPONENTS,
    REQUIRED_LANES,
    REQUIRED_METADATA,
    RUNBOOK_PATH,
    validate_harbor_integration,
)


class HarborIntegrationValidatorTests(unittest.TestCase):
    def test_current_contract_passes(self) -> None:
        result = validate_harbor_integration()

        self.assertTrue(result["passed"], result)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["adapter_component_count"], len(REQUIRED_COMPONENTS))
        self.assertEqual(result["lane_count"], len(REQUIRED_LANES))
        self.assertEqual(result["required_metadata_count"], len(REQUIRED_METADATA))

    def test_rejects_overclaims_missing_lanes_and_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "harbor-adapter-contract.json"
            runbook = root / "harbor-integration-runbook.md"
            data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
            data["public_claim_boundary"] = "Harbor accepted and endorsed this as v1-ready evidence."
            data["local_run_template"] = "python run.py"
            data["lanes"] = [lane for lane in data["lanes"] if lane["name"] != "live_http_tool_agent"]
            data["required_run_metadata"] = ["benchmark_source_sha"]
            data["debug_note"] = "raw private output at /tmp/authzbench/private.json"
            contract.write_text(json.dumps(data), encoding="utf-8")
            runbook.write_text("# Harbor\n\nNo SDK mapping here.\n", encoding="utf-8")

            result = validate_harbor_integration(contract, runbook)

        self.assertFalse(result["passed"], result)
        self.assertIn("local_run_template must include harbor run -p", result["errors"])
        self.assertIn("lanes missing: live_http_tool_agent", result["errors"])
        self.assertTrue(any("required_run_metadata missing:" in error for error in result["errors"]), result)
        self.assertTrue(any("disallowed overclaim/private marker" in error for error in result["errors"]), result)
        self.assertTrue(any("local absolute path is not allowed" in error for error in result["errors"]), result)
        self.assertTrue(any("runbook missing required term:" in error for error in result["errors"]), result)

    def test_allows_public_harbor_artifact_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = root / "harbor-adapter-contract.json"
            data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
            data["artifact_path_example"] = "/logs/artifacts/submission.json"
            contract.write_text(json.dumps(data), encoding="utf-8")

            result = validate_harbor_integration(contract, RUNBOOK_PATH)

        self.assertTrue(result["passed"], result)


if __name__ == "__main__":
    unittest.main()
