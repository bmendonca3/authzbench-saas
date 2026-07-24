from __future__ import annotations

import unittest

from scripts.agy_baseline_agent import _effective_model_label, _extract_json


class AgyBaselineAdapterTests(unittest.TestCase):
    def test_extracts_fenced_findings_json(self) -> None:
        self.assertEqual(_extract_json('```json\n{"findings":[]}\n```'), {"findings": []})

    def test_effective_model_label_uses_last_propagated_label(self) -> None:
        log = (
            'Propagating selected model override to backend: label="Gemini 3.5 Flash (High)"\n'
            'Propagating selected model override to backend: label="Gemini 3.1 Pro (High)"\n'
        )
        self.assertEqual(_effective_model_label(log), "Gemini 3.1 Pro (High)")


if __name__ == "__main__":
    unittest.main()
