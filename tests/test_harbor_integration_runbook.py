from __future__ import annotations

import unittest
from pathlib import Path


RUNBOOK = Path("docs/harbor-integration-runbook.md")


class HarborIntegrationRunbookTests(unittest.TestCase):
    def test_records_required_public_safe_mapping(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")

        required_terms = [
            "Harbor-compatible execution target",
            "Dataset builder",
            "Task context renderer",
            "Runner bridge",
            "Output collector",
            "Verifier/scorer bridge",
            "Metadata normalizer",
            "Redaction policy",
            "No-Tools Lane",
            "Live HTTP Tool-Agent Lane",
            "findings: []",
            "comparability key",
            "private-pack fingerprint",
            "not yet contain a verified Harbor adapter",
        ]
        missing = [term for term in required_terms if term not in text]
        self.assertEqual(missing, [])

    def test_excludes_private_source_and_positive_overclaims(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        lower = text.lower()

        disallowed = [
            "accepted by",
            "endorsed by",
            "private meeting",
            "calendar." + "google.com",
            "appointments/" + "schedules",
        ]
        self.assertEqual([term for term in disallowed if term in lower], [])
        self.assertIn("not claim Harbor hosted execution", text)
        self.assertIn("does not yet contain a verified Harbor adapter", text)


if __name__ == "__main__":
    unittest.main()
