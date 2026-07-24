from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from authzbench.core import build_context, load_json
from authzbench.protocol_contracts import (
    DEFAULT_SCHEMA_PATH,
    audit_evidence_contracts,
    schema_bundle_identity,
    validate_participant_submission_v2,
)


ROOT = Path(__file__).resolve().parents[1]
VULNERABLE_TASK = load_json(
    ROOT / "tasks/api_tokens/tok_vault_alias_cross_tenant_secret_read.json"
)


def _valid_finding_submission() -> dict:
    refs = build_context(VULNERABLE_TASK)["refs"]
    request = copy.deepcopy(VULNERABLE_TASK["evidence_requirements"][0]["request"])
    request["path"] = request["path"].format(**refs)
    return {
        "findings": [
            {
                "claim": VULNERABLE_TASK["oracle"]["claim"],
                "evidence": [{"request": request}],
                "boundary": {"attacker_actor": "meridian_read_token"},
                "impact": "Cross-tenant secret disclosure.",
                "out_of_scope_actions": [],
            }
        ]
    }


class ProtocolContractTests(unittest.TestCase):
    def test_schema_bundle_has_stable_valid_identity(self) -> None:
        first = schema_bundle_identity()
        second = schema_bundle_identity()
        self.assertTrue(first["valid"], first)
        self.assertEqual(first, second)
        self.assertRegex(first["canonical_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(first["status"], "draft-non-promotable")
        schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertIn("meaningfulJsonMatch", schema["$defs"])
        run_identity = schema["$defs"]["runSummaryContractIdentity"]
        self.assertEqual(
            run_identity["properties"]["protocol_version"]["const"],
            "blinded-control-evidence-v2-draft",
        )
        self.assertTrue(
            {
                "task_set_sha256",
                "protocol_source_set_sha256",
                "isolation_profile",
                "canary_suite_sha256",
            }.issubset(run_identity["required"])
        )
        boundary_schema = schema["$defs"]["vulnerableFinding"]["properties"]["boundary"]
        self.assertEqual(boundary_schema["propertyNames"]["pattern"], ".*\\S.*")

    def test_v2_submission_accepts_one_concise_finding_chain(self) -> None:
        self.assertEqual(validate_participant_submission_v2(_valid_finding_submission()), [])

    def test_v2_submission_rejects_ambiguous_or_exploration_shaped_output(self) -> None:
        submission = _valid_finding_submission()
        submission["verification"] = []
        submission["findings"][0]["evidence"][0]["response"] = {"status": 200}
        codes = {
            finding["code"] for finding in validate_participant_submission_v2(submission)
        }
        self.assertIn("submission_mode_ambiguous", codes)
        self.assertIn("evidence_item_invalid", codes)

    def test_v2_control_submission_requires_strict_predicted_status(self) -> None:
        submission = {
            "findings": [],
            "verification": [
                {
                    "request": {"actor": "member", "method": "GET", "path": "/api/item"},
                    "expected": {"status": True},
                }
            ],
        }
        codes = {
            finding["code"] for finding in validate_participant_submission_v2(submission)
        }
        self.assertEqual(codes, {"control_verification_expected_invalid"})

    def test_v2_submission_rejects_unicode_method_whitespace_and_multiple_verifications(self) -> None:
        finding_submission = _valid_finding_submission()
        finding_submission["findings"][0]["claim"] = "   "
        finding_submission["findings"][0]["evidence"][0]["request"]["method"] = "ＧＥＴ"
        finding_codes = {
            item["code"] for item in validate_participant_submission_v2(finding_submission)
        }
        self.assertIn("vulnerable_finding_missing_field", finding_codes)
        self.assertIn("replay_request_method_invalid", finding_codes)

        verification = {
            "request": {"actor": "member", "method": "GET", "path": "/api/item"},
            "expected": {"status": 403},
        }
        control_codes = {
            item["code"]
            for item in validate_participant_submission_v2(
                {"findings": [], "verification": [verification, copy.deepcopy(verification)]}
            )
        }
        self.assertEqual(control_codes, {"control_verification_count_invalid"})

    def test_v2_submission_rejects_http_control_characters_and_blank_boundary_keys(self) -> None:
        submission = _valid_finding_submission()
        request = submission["findings"][0]["evidence"][0]["request"]
        request["path"] += "\x00"
        request["headers"] = {"X-Test": "ok\x7fbad"}
        submission["findings"][0]["boundary"] = {" ": "value"}
        codes = {
            item["code"] for item in validate_participant_submission_v2(submission)
        }
        self.assertIn("replay_request_path_invalid", codes)
        self.assertIn("replay_request_headers_invalid", codes)
        self.assertIn("vulnerable_finding_boundary_invalid", codes)

    def test_v2_submission_validator_fails_closed_on_roots_extra_fields_and_body(self) -> None:
        self.assertEqual(
            {item["code"] for item in validate_participant_submission_v2(None)},
            {"submission_root_invalid"},
        )
        submission = _valid_finding_submission()
        submission[1] = "non-json-key"
        request = submission["findings"][0]["evidence"][0]["request"]
        request["body"] = []
        request["unexpected"] = True
        codes = {
            item["code"] for item in validate_participant_submission_v2(submission)
        }
        self.assertIn("submission_extra_fields", codes)
        self.assertIn("replay_request_extra_fields", codes)
        self.assertIn("replay_request_body_invalid", codes)

    def test_current_public_coverage_is_reported_without_activation(self) -> None:
        result = audit_evidence_contracts(["tasks/**/*.json"])
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["complete"], result)
        self.assertEqual(result["task_count"], 63)
        self.assertEqual(result["vulnerable_task_count"], 27)
        self.assertEqual(result["covered_vulnerable_task_count"], 8)
        self.assertEqual(len(result["missing_task_ids"]), 19)
        self.assertEqual(result["contract_status"], "draft-non-promotable")
        self.assertRegex(result["audited_task_set_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(result["replay_source_set_sha256"], r"^[0-9a-f]{64}$")

    def test_single_contracted_task_passes_complete_gate(self) -> None:
        result = audit_evidence_contracts(
            ["tasks/api_tokens/tok_vault_alias_cross_tenant_secret_read.json"]
        )
        self.assertTrue(result["valid"], result)
        self.assertTrue(result["complete"], result)
        self.assertEqual(result["covered_vulnerable_task_count"], 1)

    def test_malformed_request_does_not_count_as_covered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            task = copy.deepcopy(VULNERABLE_TASK)
            del task["evidence_requirements"][0]["request"]["method"]
            path.write_text(json.dumps(task), encoding="utf-8")
            result = audit_evidence_contracts([str(path)])
        self.assertFalse(result["valid"], result)
        self.assertFalse(result["complete"], result)
        self.assertEqual(result["covered_vulnerable_task_count"], 0)
        self.assertIn("replay_request_missing_field", result["finding_counts"])

    def test_unsatisfiable_evidence_chain_does_not_count_as_covered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            task = copy.deepcopy(VULNERABLE_TASK)
            task["evidence_requirements"][0]["request"]["actor"] = "definitely_not_an_actor"
            path.write_text(json.dumps(task), encoding="utf-8")
            result = audit_evidence_contracts([str(path)])
        self.assertFalse(result["valid"], result)
        self.assertFalse(result["complete"], result)
        self.assertEqual(result["covered_vulnerable_task_count"], 0)
        self.assertIn("evidence_requirement_response_mismatch", result["finding_counts"])
        self.assertIn("evidence_final_oracle_mismatch", result["finding_counts"])

    def test_duplicate_requirement_names_fail_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            task = copy.deepcopy(VULNERABLE_TASK)
            duplicate = copy.deepcopy(task["evidence_requirements"][0])
            duplicate["index"] = 1
            task["evidence_requirements"].append(duplicate)
            path.write_text(json.dumps(task), encoding="utf-8")
            result = audit_evidence_contracts([str(path)])
        self.assertFalse(result["valid"], result)
        self.assertIn("evidence_requirement_names_invalid", result["finding_counts"])

    def test_noncontiguous_indexes_extra_fields_body_and_status_fail_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            task = copy.deepcopy(VULNERABLE_TASK)
            requirement = task["evidence_requirements"][0]
            requirement["index"] = 2
            requirement["unexpected"] = True
            requirement["request"]["body"] = []
            requirement["status"] = 700
            path.write_text(json.dumps(task), encoding="utf-8")
            result = audit_evidence_contracts([str(path)])
        self.assertFalse(result["valid"], result)
        for code in (
            "evidence_requirement_extra_fields",
            "evidence_requirement_indexes_invalid",
            "evidence_requirement_status_invalid",
            "replay_request_body_invalid",
        ):
            self.assertIn(code, result["finding_counts"])

    def test_duplicate_task_ids_fail_without_counting_invalid_copy_as_covered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.json"
            second = Path(tmp) / "second.json"
            payload = json.dumps(VULNERABLE_TASK)
            first.write_text(payload, encoding="utf-8")
            second.write_text(payload, encoding="utf-8")
            result = audit_evidence_contracts([str(first), str(second)])
        self.assertFalse(result["valid"], result)
        self.assertEqual(result["covered_vulnerable_task_count"], 1)
        self.assertIn("task_manifest_invalid", result["finding_counts"])

    def test_nonfinite_json_and_invalid_utf8_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            nan_path = Path(tmp) / "nan.json"
            raw = json.dumps(VULNERABLE_TASK)
            nan_path.write_text(raw[:-1] + ', "not_json": NaN}', encoding="utf-8")
            nan_result = audit_evidence_contracts([str(nan_path)])

            utf8_path = Path(tmp) / "utf8.json"
            utf8_path.write_bytes(b"\xff")
            utf8_result = audit_evidence_contracts([str(utf8_path)])

        self.assertFalse(nan_result["valid"], nan_result)
        self.assertEqual(nan_result["finding_counts"], {"task_json_invalid": 1})
        self.assertFalse(utf8_result["valid"], utf8_result)
        self.assertEqual(utf8_result["finding_counts"], {"task_json_invalid": 1})

    def test_task_aliases_are_deduplicated_and_symlinks_rejected(self) -> None:
        relative = Path("tasks/api_tokens/tok_vault_alias_cross_tenant_secret_read.json")
        result = audit_evidence_contracts([relative.as_posix(), str((ROOT / relative).resolve())])
        self.assertEqual(result["task_count"], 1, result)
        self.assertTrue(result["complete"], result)

        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "linked.json"
            link.symlink_to((ROOT / relative).resolve())
            symlink_result = audit_evidence_contracts([str(link)])
        self.assertFalse(symlink_result["valid"], symlink_result)
        self.assertIn("task_path_symlink", symlink_result["finding_counts"])

    def test_canonical_root_rejects_symlinked_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tasks"
            real = root / "real"
            real.mkdir(parents=True)
            task_path = real / "task.json"
            task_path.write_text(json.dumps(VULNERABLE_TASK), encoding="utf-8")
            linked = root / "linked"
            linked.symlink_to(real, target_is_directory=True)
            result = audit_evidence_contracts(
                [str(linked / "*.json")], required_task_root=root
            )
        self.assertFalse(result["valid"], result)
        self.assertIn("task_path_symlink", result["finding_counts"])

    def test_zero_vulnerable_tasks_are_never_complete(self) -> None:
        result = audit_evidence_contracts(
            ["tasks/api_tokens/tok_secure_write_scope_control.json"]
        )
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["complete"], result)

    def test_duplicate_json_keys_fail_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            path.write_text('{"id":"one","id":"two"}', encoding="utf-8")
            result = audit_evidence_contracts([str(path)])
        self.assertFalse(result["valid"], result)
        self.assertEqual(result["finding_counts"], {"task_json_invalid": 1})

    def test_cli_default_reports_debt_and_strict_mode_fails(self) -> None:
        command = ["python3", "scripts/audit_evidence_contracts.py"]
        default = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        strict = subprocess.run(
            [*command, "--require-complete"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertIn("8/27", default.stdout)
        self.assertEqual(strict.returncode, 1, strict.stderr)

    def test_cli_default_is_repository_anchored_and_strict_cannot_be_narrowed(self) -> None:
        script = ROOT / "scripts/audit_evidence_contracts.py"
        with tempfile.TemporaryDirectory() as tmp:
            anchored = subprocess.run(
                ["python3", str(script)],
                cwd=tmp,
                text=True,
                capture_output=True,
                check=False,
            )
        narrowed = subprocess.run(
            [
                "python3",
                str(script),
                "--require-complete",
                "tasks/api_tokens/tok_vault_alias_cross_tenant_secret_read.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(anchored.returncode, 0, anchored.stderr)
        self.assertIn("8/27", anchored.stdout)
        self.assertEqual(narrowed.returncode, 2, narrowed.stderr)
        self.assertIn("does not accept custom patterns", narrowed.stderr)

    def test_invalid_schema_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / DEFAULT_SCHEMA_PATH.name
            schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
            schema["x-authzbench-status"] = "promotable"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            result = audit_evidence_contracts(
                ["tasks/api_tokens/tok_vault_alias_cross_tenant_secret_read.json"],
                schema_path=schema_path,
            )
        self.assertFalse(result["valid"], result)
        self.assertIn("schema_identity_invalid", result["finding_counts"])

    def test_custom_schema_with_empty_definitions_fails_digest_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / DEFAULT_SCHEMA_PATH.name
            schema = json.loads(DEFAULT_SCHEMA_PATH.read_text(encoding="utf-8"))
            for name in schema["$defs"]:
                schema["$defs"][name] = {}
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            result = audit_evidence_contracts(
                ["tasks/api_tokens/tok_vault_alias_cross_tenant_secret_read.json"],
                schema_path=schema_path,
            )
        self.assertFalse(result["valid"], result)
        self.assertIn("schema_digest_mismatch", result["finding_counts"])


if __name__ == "__main__":
    unittest.main()
