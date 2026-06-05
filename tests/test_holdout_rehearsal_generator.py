from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.generate_holdout_rehearsal_pack import (
    generate_holdout_rehearsal_tasks,
    write_rehearsal_pack,
)
from scripts.validate_holdout_pack import validate_holdout_pack


ROOT = Path(__file__).resolve().parents[1]


class HoldoutRehearsalGeneratorTests(unittest.TestCase):
    def test_generated_rehearsal_pack_passes_v0_shape_gate(self) -> None:
        public_patterns = [str(ROOT / "tasks" / "*" / "*.json")]
        tasks = generate_holdout_rehearsal_tasks(public_patterns)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "tasks_private" / "holdout" / "rehearsal"
            written = write_rehearsal_pack(tasks, output_dir, force=False)
            result = validate_holdout_pack(
                [str(output_dir / "**" / "*.json")],
                public_patterns=public_patterns,
                min_count=20,
                preferred_count=24,
                max_count=30,
                min_vulnerable=12,
                min_controls=8,
                min_apps=6,
                max_per_app=8,
                min_denial_controls=4,
                min_authorized_allow_controls=4,
            )

        self.assertEqual(len(written), 24)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["manifest_count"], 24, result)
        self.assertEqual(result["vulnerable_count"], 12, result)
        self.assertEqual(result["control_count"], 12, result)
        self.assertEqual(len(result["app_counts"]), 6, result)

    def test_generator_refuses_public_tasks_output_path(self) -> None:
        tasks = generate_holdout_rehearsal_tasks([str(ROOT / "tasks" / "*" / "*.json")])
        with tempfile.TemporaryDirectory() as tmp:
            public_tasks_path = Path(tmp) / "tasks" / "holdout"
            with self.assertRaises(ValueError):
                write_rehearsal_pack(tasks, public_tasks_path, force=False)


if __name__ == "__main__":
    unittest.main()
