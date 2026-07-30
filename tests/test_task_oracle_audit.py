from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import load_json
from scripts import generate_task_oracle_audit


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class TaskOracleAuditTests(unittest.TestCase):
    def test_control_classification_uses_validated_semantics_not_names(self) -> None:
        vulnerable = load_json(
            ROOT / "tasks" / "api_tokens" / "tok_export_scope_bypass.json"
        )
        vulnerable["controls"][0]["name"] = "authorized_allow_alias_decoy"
        authorized_allow = load_json(
            ROOT
            / "tasks"
            / "api_tokens"
            / "tok_export_token_reads_export_control.json"
        )
        authorized_allow["controls"][0]["name"] = "forbidden_denial_secure"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_json(
                root / "tasks" / "api_tokens" / "tok_export_scope_bypass.json",
                vulnerable,
            )
            _write_json(
                root
                / "tasks"
                / "api_tokens"
                / "tok_export_token_reads_export_control.json",
                authorized_allow,
            )
            entries, _manifest_items = generate_task_oracle_audit.audit_public_tasks(
                root / "tasks",
                root=root,
            )

        by_id = {entry["id"]: entry for entry in entries}
        vulnerable_entry = by_id["tok_export_scope_bypass"]
        self.assertEqual(vulnerable_entry["task_behavior"], "vulnerable")
        self.assertTrue(vulnerable_entry["has_denial_control"])
        self.assertFalse(vulnerable_entry["has_successful_control"])
        self.assertEqual(
            vulnerable_entry["control_outcome_counts"],
            {"success_2xx": 0, "denial_4xx": 1, "other_status": 0},
        )
        self.assertNotIn("has_alias_control", vulnerable_entry)
        self.assertNotIn("has_decoy_control", vulnerable_entry)

        allow_entry = by_id["tok_export_token_reads_export_control"]
        self.assertEqual(allow_entry["task_behavior"], "authorized_allow")
        self.assertFalse(allow_entry["has_denial_control"])
        self.assertTrue(allow_entry["has_successful_control"])
        self.assertEqual(
            allow_entry["control_outcome_counts"],
            {"success_2xx": 1, "denial_4xx": 0, "other_status": 0},
        )

    def test_parse_failure_is_fatal_and_does_not_overwrite_outputs(self) -> None:
        valid = load_json(
            ROOT / "tasks" / "api_tokens" / "tok_export_scope_bypass.json"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_json(
                root / "tasks" / "api_tokens" / "tok_export_scope_bypass.json",
                valid,
            )
            malformed = root / "tasks" / "api_tokens" / "malformed.json"
            malformed.write_text('{"id": "incomplete"', encoding="utf-8")
            json_output = root / "audit.json"
            markdown_output = root / "audit.md"
            json_output.write_text("sentinel-json", encoding="utf-8")
            markdown_output.write_text("sentinel-markdown", encoding="utf-8")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = generate_task_oracle_audit.main(
                    [
                        "--root",
                        str(root),
                        "--json-output",
                        str(json_output),
                        "--markdown-output",
                        str(markdown_output),
                    ]
                )

            self.assertEqual(result, 1)
            self.assertIn("input validation FAILED", stderr.getvalue())
            self.assertIn("JSONDecodeError", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertEqual(json_output.read_text(encoding="utf-8"), "sentinel-json")
            self.assertEqual(
                markdown_output.read_text(encoding="utf-8"),
                "sentinel-markdown",
            )

    def test_canonical_manifest_digest_is_order_and_format_independent(self) -> None:
        first = {
            "manifest_path": "tasks/app/a.json",
            "manifest": {"z": 1, "a": [2, 3]},
        }
        second = {
            "manifest_path": "tasks/app/b.json",
            "manifest": {"nested": {"right": False, "left": True}},
        }
        reordered_first = {
            "manifest_path": "tasks/app/a.json",
            "manifest": json.loads(
                '{\n  "a": [2, 3],\n  "z": 1\n}'
            ),
        }
        expected = generate_task_oracle_audit.canonical_manifest_set_sha256(
            [first, second]
        )
        observed = generate_task_oracle_audit.canonical_manifest_set_sha256(
            [second, reordered_first]
        )
        self.assertEqual(observed, expected)
        self.assertRegex(observed, r"^[0-9a-f]{64}$")

    def test_check_binds_owned_outputs_without_rewriting_stale_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            json_output = root / "audit.json"
            markdown_output = root / "audit.md"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                generated = generate_task_oracle_audit.main(
                    [
                        "--root",
                        str(ROOT),
                        "--json-output",
                        str(json_output),
                        "--markdown-output",
                        str(markdown_output),
                    ]
                )
                checked = generate_task_oracle_audit.main(
                    [
                        "--check",
                        "--root",
                        str(ROOT),
                        "--json-output",
                        str(json_output),
                        "--markdown-output",
                        str(markdown_output),
                    ]
                )

            self.assertEqual(generated, 0)
            self.assertEqual(checked, 0)
            report = json.loads(json_output.read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "task-oracle-audit-v2")
            self.assertEqual(report["public_manifest_count"], 63)
            self.assertEqual(report["summary"]["total"], 63)
            self.assertRegex(report["public_manifest_set_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(
                report["source_binding"]["current_source_set_sha256"],
                r"^[0-9a-f]{64}$",
            )
            self.assertIn(
                "does not assert a clean Git worktree",
                report["source_binding"]["claim_boundary"],
            )

            report["public_manifest_count"] = 62
            stale = json.dumps(report, indent=2, sort_keys=True) + "\n"
            json_output.write_text(stale, encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                stale_result = generate_task_oracle_audit.main(
                    [
                        "--check",
                        "--root",
                        str(ROOT),
                        "--json-output",
                        str(json_output),
                        "--markdown-output",
                        str(markdown_output),
                    ]
                )

            self.assertEqual(stale_result, 1)
            self.assertIn("output binding FAILED", stderr.getvalue())
            self.assertEqual(json_output.read_text(encoding="utf-8"), stale)


if __name__ == "__main__":
    unittest.main()
