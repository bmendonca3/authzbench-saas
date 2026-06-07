from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CiWorkflowTests(unittest.TestCase):
    def test_public_validation_workflow_runs_release_gate(self) -> None:
        workflow = ROOT / ".github" / "workflows" / "validate.yml"
        self.assertTrue(workflow.exists(), "missing public validation workflow")
        text = workflow.read_text(encoding="utf-8")

        self.assertRegex(text, r"(?m)^on:\s*$")
        self.assertRegex(text, r"(?m)^\s+push:\s*$")
        self.assertRegex(text, r"(?m)^\s+pull_request:\s*$")
        self.assertRegex(text, r"(?m)^\s+workflow_dispatch:\s*$")
        self.assertRegex(text, r"(?m)^\s+- main\s*$")
        self.assertRegex(text, r"(?m)^jobs:\s*$")
        self.assertIn("actions/checkout@v6", text)
        self.assertIn("actions/setup-python@v6", text)
        self.assertIn('FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"', text)
        self.assertRegex(text, r"(?m)^\s+python-version:\s*[\"']?3\.11[\"']?\s*$")
        self.assertIn("docker compose version", text)
        self.assertIn("python scripts/validate_public.py --include-scripted-baseline --include-container-smoke", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("secrets.", text)
        self.assertRegex(text, r"(?m)^\s+timeout-minutes:\s*25\s*$")


if __name__ == "__main__":
    unittest.main()
