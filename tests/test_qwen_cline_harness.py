from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import run_qwen_cline_harness as harness


ROOT = Path(__file__).resolve().parents[1]


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout.strip()


class ContractAndWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "source"
        self.root.mkdir()
        (self.root / "AGENTS.md").write_text("# Test agent rules\n", encoding="utf-8")
        (self.root / "packet.md").write_text("# Packet\nEdit target.txt.\n", encoding="utf-8")
        (self.root / "target.txt").write_text("before\n", encoding="utf-8")
        (self.root / "tasks_private").mkdir()
        (self.root / "tasks_private" / "secret.txt").write_text(
            "must-not-copy\n", encoding="utf-8"
        )
        _run_git(self.root, "init", "-q")
        _run_git(self.root, "config", "user.name", "Harness Test")
        _run_git(self.root, "config", "user.email", "harness@example.invalid")
        _run_git(self.root, "add", "AGENTS.md", "packet.md", "target.txt")
        _run_git(self.root, "commit", "-qm", "fixture")
        self.pin = harness.load_runtime_pin()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def contract_data(self) -> dict[str, object]:
        return {
            "schema_version": harness.CONTRACT_SCHEMA,
            "task_id": "fixture-task",
            "source_commit": _run_git(self.root, "rev-parse", "HEAD"),
            "task": "Follow the packet.",
            "packet_path": "packet.md",
            "input_files": {
                "packet.md": harness.sha256_file(self.root / "packet.md"),
                "target.txt": harness.sha256_file(self.root / "target.txt"),
            },
            "create_files": [],
            "write_files": ["target.txt"],
            "required_change_files": ["target.txt"],
            "expected_output_sha256": {},
            "verification_commands": [["python3", "-m", "unittest", "-q"]],
            "model": "qwen3.8-max-preview",
            "thinking": "xhigh",
            "retries": 3,
            "timeout_seconds": 0,
        }

    def test_contract_accepts_exact_hash_bound_scope(self) -> None:
        contract = harness.validate_contract_data(self.contract_data(), self.pin)
        harness.verify_source_contract(self.root, contract)
        self.assertEqual(contract.write_files, ("target.txt",))
        self.assertEqual(contract.thinking, "xhigh")

    def test_contract_rejects_absolute_traversal_denied_and_collision_paths(self) -> None:
        for unsafe in (
            "/tmp/target.txt",
            "../target.txt",
            "tasks_private/secret.txt",
            ".agents/worker.md",
            ".env",
        ):
            with self.subTest(path=unsafe), self.assertRaises(harness.HarnessError):
                harness.validate_relative_path(unsafe)
        data = self.contract_data()
        data["create_files"] = ["Target.txt"]
        with self.assertRaisesRegex(harness.HarnessError, "colliding"):
            harness.validate_contract_data(data, self.pin)

    def test_contract_rejects_hash_drift_and_unknown_keys(self) -> None:
        data = self.contract_data()
        data["input_files"] = dict(data["input_files"])
        data["input_files"]["target.txt"] = "0" * 64
        contract = harness.validate_contract_data(data, self.pin)
        with self.assertRaisesRegex(harness.HarnessError, "hash drifted"):
            harness.verify_source_contract(self.root, contract)
        data = self.contract_data()
        data["ambient_access"] = True
        with self.assertRaisesRegex(harness.HarnessError, "unknown contract keys"):
            harness.validate_contract_data(data, self.pin)

    def test_symlink_and_hardlink_inputs_are_rejected(self) -> None:
        symlink = self.root / "link.txt"
        symlink.symlink_to(self.root / "target.txt")
        with self.assertRaisesRegex(harness.HarnessError, "symlink"):
            harness._assert_regular_source_file(
                self.root,
                "link.txt",
                harness.sha256_file(self.root / "target.txt"),
            )
        hardlink = self.root / "hardlink.txt"
        os.link(self.root / "target.txt", hardlink)
        with self.assertRaisesRegex(harness.HarnessError, "hardlinked"):
            harness._assert_regular_source_file(
                self.root,
                "hardlink.txt",
                harness.sha256_file(hardlink),
            )

    def test_materialization_contains_only_named_public_inputs_and_controls(self) -> None:
        contract = harness.validate_contract_data(self.contract_data(), self.pin)
        evidence = Path(self.temp_dir.name) / "evidence"
        evidence.mkdir()
        workspace, policy_path, _ = harness.materialize_workspace(
            self.root,
            contract,
            evidence,
        )
        files = {
            path.relative_to(workspace).as_posix()
            for path in workspace.rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            files,
            {
                "AGENTS.md",
                "packet.md",
                "target.txt",
                ".cline/hooks/PreToolUse.py",
                ".cline/rules/00-qwen-harness-contract.md",
            },
        )
        self.assertFalse((workspace / ".git").exists())
        self.assertFalse((workspace / "tasks_private").exists())
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertEqual(policy["allowed_tools"], list(harness.ALLOWED_TOOLS))
        self.assertEqual(policy["allowed_write_paths"], ["target.txt"])

    def test_snapshot_rejects_extra_delete_and_mode_changes(self) -> None:
        contract = harness.validate_contract_data(self.contract_data(), self.pin)
        evidence = Path(self.temp_dir.name) / "evidence"
        evidence.mkdir()
        workspace, _, _ = harness.materialize_workspace(self.root, contract, evidence)
        before = harness.snapshot_tree(workspace)
        (workspace / "target.txt").write_text("after\n", encoding="utf-8")
        (workspace / "extra.txt").write_text("extra\n", encoding="utf-8")
        after = harness.snapshot_tree(workspace)
        changed, violations = harness.compare_snapshots(before, after, contract)
        self.assertEqual(changed, ["extra.txt", "target.txt"])
        self.assertIn("out-of-scope workspace change: extra.txt", violations)
        (workspace / "extra.txt").unlink()
        os.chmod(workspace / "target.txt", 0o600)
        after = harness.snapshot_tree(workspace)
        _, violations = harness.compare_snapshots(before, after, contract)
        self.assertIn("allowed file mode changed: target.txt", violations)

    def test_generated_provider_profile_uses_cline_compatible_utc_timestamp(self) -> None:
        state = Path(self.temp_dir.name) / "state"
        harness.create_state_config(state, self.pin)
        data = json.loads(
            (state / "settings" / "providers.json").read_text(encoding="utf-8")
        )
        entry = data["providers"]["openai-compatible"]
        self.assertTrue(entry["updatedAt"].endswith("Z"))
        self.assertEqual(entry["settings"]["baseUrl"], "http://127.0.0.1:8790/v1")
        self.assertEqual(entry["settings"]["model"], "qwen3.8-max-preview")

    def test_create_file_uses_replaceable_sentinel_but_exports_as_new(self) -> None:
        data = self.contract_data()
        data["create_files"] = ["new.txt"]
        data["write_files"] = ["new.txt"]
        data["required_change_files"] = ["new.txt"]
        contract = harness.validate_contract_data(data, self.pin)
        evidence = Path(self.temp_dir.name) / "create-evidence"
        evidence.mkdir()
        workspace, _, baselines = harness.materialize_workspace(
            self.root,
            contract,
            evidence,
        )
        self.assertEqual(
            (workspace / "new.txt").read_text(encoding="utf-8"),
            harness.CREATE_FILE_SENTINEL,
        )
        self.assertEqual(baselines["new.txt"]["text"], "")
        self.assertEqual(baselines["new.txt"]["source"], "precreated-sentinel")

    def test_expected_output_hash_rejects_confident_but_inexact_bytes(self) -> None:
        data = self.contract_data()
        expected = harness.sha256_bytes(b"after\n")
        data["expected_output_sha256"] = {"target.txt": expected}
        contract = harness.validate_contract_data(data, self.pin)
        workspace = Path(self.temp_dir.name) / "expected-workspace"
        workspace.mkdir()
        (workspace / "target.txt").write_text("after\n\n", encoding="utf-8")
        violations = harness.expected_output_violations(workspace, contract)
        self.assertEqual(len(violations), 1)
        self.assertIn("expected output hash mismatch", violations[0])
        (workspace / "target.txt").write_text("after\n", encoding="utf-8")
        self.assertEqual(harness.expected_output_violations(workspace, contract), [])

    def test_patch_marks_a_new_file_without_trailing_newline(self) -> None:
        workspace = Path(self.temp_dir.name) / "patch-workspace"
        evidence = Path(self.temp_dir.name) / "patch-evidence"
        workspace.mkdir()
        evidence.mkdir()
        (workspace / "new.txt").write_text("exact", encoding="utf-8")
        patch_path, _ = harness.export_candidate_patch(
            workspace,
            evidence,
            {
                "new.txt": {
                    "source": "precreated-sentinel",
                    "text": "",
                }
            },
            ["new.txt"],
        )
        patch = patch_path.read_text(encoding="utf-8")
        self.assertIn("+exact\n\\ No newline at end of file\n", patch)


class HookPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        (self.workspace / "allowed.txt").write_text("public\n", encoding="utf-8")
        self.policy_path = self.root / "policy.json"
        self.audit_path = self.root / "audit.jsonl"
        self.policy_path.write_text(
            json.dumps(
                {
                    "schema_version": harness.POLICY_SCHEMA,
                    "workspace_root": str(self.workspace),
                    "allowed_tools": list(harness.ALLOWED_TOOLS),
                    "allowed_read_paths": ["AGENTS.md", "allowed.txt"],
                    "allowed_write_paths": ["allowed.txt"],
                    "allowed_commands": [],
                    "denied_paths": ["tasks_private/**", ".env*"],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def invoke(self, tool: str, tool_input: object, *, call_id: str = "call-1") -> dict:
        payload = {
            "hookName": "tool_call",
            "workspaceRoots": [str(self.workspace)],
            "tool_call": {"id": call_id, "name": tool, "input": tool_input},
        }
        environment = {
            **os.environ,
            "QWEN_HARNESS_REQUIRED": "1",
            "QWEN_HARNESS_POLICY": str(self.policy_path),
            "QWEN_HARNESS_AUDIT": str(self.audit_path),
        }
        result = subprocess.run(
            [sys.executable, str(harness.HOOK_SOURCE)],
            input=json.dumps(payload),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
            check=True,
        )
        return json.loads(result.stdout)

    def test_hook_allows_exact_read_and_records_call_id(self) -> None:
        output = self.invoke(
            "read_files",
            {"files": [{"path": str(self.workspace / "allowed.txt")}]},
        )
        self.assertEqual(output, {})
        record = json.loads(self.audit_path.read_text(encoding="utf-8"))
        self.assertTrue(record["allowed"])
        self.assertEqual(record["call_id"], "call-1")
        self.assertEqual(record["paths"], ["allowed.txt"])

    def test_hook_denies_private_outside_write_and_unknown_tool(self) -> None:
        cases = (
            ("read_files", {"files": [{"path": "tasks_private/secret.txt"}]}),
            ("read_files", {"paths": [str(self.root / "outside.txt")]}),
            ("editor", {"path": "other.txt", "old_text": "", "new_text": "x"}),
            ("search_codebase", {"query": "secret"}),
        )
        for index, (tool, tool_input) in enumerate(cases):
            with self.subTest(tool=tool, input=tool_input):
                output = self.invoke(tool, tool_input, call_id=f"denied-{index}")
                self.assertTrue(output["cancel"])
        records = [
            json.loads(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(records), len(cases))
        self.assertTrue(all(record["allowed"] is False for record in records))

    def test_required_harness_without_policy_cancels(self) -> None:
        environment = {
            **os.environ,
            "QWEN_HARNESS_REQUIRED": "1",
            "QWEN_HARNESS_AUDIT": str(self.audit_path),
        }
        result = subprocess.run(
            [sys.executable, str(harness.HOOK_SOURCE)],
            input="{}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
            check=True,
        )
        output = json.loads(result.stdout)
        self.assertTrue(output["cancel"])
        self.assertIn("policy is missing", output["errorMessage"])

    def test_hostile_hook_self_test_records_a_private_read_denial(self) -> None:
        hook = self.workspace / ".cline" / "hooks" / "PreToolUse.py"
        hook.parent.mkdir(parents=True)
        shutil.copyfile(harness.HOOK_SOURCE, hook)
        os.chmod(hook, 0o755)
        (self.workspace / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
        summary = harness.hostile_hook_self_test(
            workspace=self.workspace,
            policy_path=self.policy_path,
            evidence_dir=self.root,
        )
        self.assertTrue(summary["passed"])
        record = json.loads(
            (self.root / "hook-self-test-audit.jsonl").read_text(encoding="utf-8")
        )
        self.assertFalse(record["allowed"])
        self.assertEqual(record["call_id"], "hostile-private-read-probe")


class StreamAndAssessmentTests(unittest.TestCase):
    def contract(self) -> harness.TaskContract:
        return harness.TaskContract(
            task_id="stream-test",
            source_commit="a" * 40,
            task="edit",
            packet_path="packet.md",
            input_files={"packet.md": "b" * 64, "target.txt": "c" * 64},
            create_files=(),
            write_files=("target.txt",),
            required_change_files=("target.txt",),
            verification_commands=(),
            model="qwen3.8-max-preview",
            thinking="xhigh",
            retries=3,
            timeout_seconds=0,
        )

    def test_warning_is_tolerated_but_malformed_json_and_unknown_tool_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            ledger = harness.StreamLedger()
            rendered = harness.ingest_stream_line(
                "third-party warning\n", 1, ledger, workspace, self.contract()
            )
            self.assertIn("warning", rendered)
            harness.ingest_stream_line("{bad json\n", 2, ledger, workspace, self.contract())
            event = {
                "type": "agent_event",
                "event": {
                    "type": "content_start",
                    "contentType": "tool",
                    "toolCallId": "bad-tool",
                    "toolName": "run_commands",
                    "input": {"commands": ["pwd"]},
                },
            }
            harness.ingest_stream_line(
                json.dumps(event), 3, ledger, workspace, self.contract()
            )
            self.assertEqual(ledger.warnings, ["third-party warning"])
            self.assertEqual(ledger.malformed_json_lines, [2])
            self.assertTrue(any("not admitted" in item for item in ledger.tool_violations))

    def test_valid_terminal_tool_and_hook_ledgers_accept(self) -> None:
        ledger = harness.StreamLedger(
            terminal_results=[
                {
                    "type": "run_result",
                    "finishReason": "completed",
                    "model": {
                        "id": "qwen3.8-max-preview",
                        "provider": "openai-compatible",
                    },
                }
            ],
            tool_calls={
                "call-1": {
                    "tool": "editor",
                    "input": {"path": "target.txt"},
                }
            },
        )
        reasons = harness.assess_run(
            returncode=0,
            ledger=ledger,
            hook_records=[{"call_id": "call-1", "tool": "editor", "allowed": True}],
            hook_errors=[],
            contract=self.contract(),
            changed_files=["target.txt"],
            snapshot_violations=[],
            source_unchanged=True,
        )
        self.assertEqual(reasons, [])

    def test_wrong_model_duplicate_terminal_and_hook_mismatch_reject(self) -> None:
        ledger = harness.StreamLedger(
            terminal_results=[
                {
                    "finishReason": "completed",
                    "model": {"id": "wrong", "provider": "openai-compatible"},
                },
                {
                    "finishReason": "completed",
                    "model": {"id": "wrong", "provider": "openai-compatible"},
                },
            ],
            tool_calls={"call-1": {"tool": "editor", "input": {"path": "target.txt"}}},
        )
        reasons = harness.assess_run(
            returncode=0,
            ledger=ledger,
            hook_records=[],
            hook_errors=[],
            contract=self.contract(),
            changed_files=["target.txt"],
            snapshot_violations=[],
            source_unchanged=True,
        )
        self.assertTrue(any("exactly one run_result" in reason for reason in reasons))
        self.assertTrue(any("ledger mismatch" in reason for reason in reasons))

    def test_three_failed_tools_on_same_path_trigger_repetition_breaker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            ledger = harness.StreamLedger()
            for index in range(3):
                call_id = f"failed-{index}"
                start = {
                    "type": "agent_event",
                    "event": {
                        "type": "content_start",
                        "contentType": "tool",
                        "toolCallId": call_id,
                        "toolName": "editor",
                        "input": {"path": "target.txt", "new_text": "x"},
                    },
                }
                end = {
                    "type": "agent_event",
                    "event": {
                        "type": "content_end",
                        "contentType": "tool",
                        "toolCallId": call_id,
                        "toolName": "editor",
                        "output": {"success": False, "error": "failed"},
                    },
                }
                harness.ingest_stream_line(
                    json.dumps(start), index * 2 + 1, ledger, workspace, self.contract()
                )
                harness.ingest_stream_line(
                    json.dumps(end), index * 2 + 2, ledger, workspace, self.contract()
                )
            self.assertIn("failed 3 times", ledger.stop_reason)


@unittest.skipUnless(
    platform.system() == "Darwin" and Path("/usr/bin/sandbox-exec").is_file(),
    "requires macOS sandbox-exec",
)
class FakeClineSandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        base = Path.home() / ".local" / "state"
        base.mkdir(parents=True, exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(
            prefix="qwen-harness-test-",
            dir=base,
        )
        self.evidence = Path(self.temp_dir.name)
        self.workspace = self.evidence / "workspace"
        self.workspace.mkdir()
        (self.workspace / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
        (self.workspace / "packet.md").write_text("# packet\n", encoding="utf-8")
        (self.workspace / "target.txt").write_text("before\n", encoding="utf-8")
        hook = self.workspace / ".cline" / "hooks" / "PreToolUse.py"
        hook.parent.mkdir(parents=True)
        shutil.copyfile(harness.HOOK_SOURCE, hook)
        os.chmod(hook, 0o755)
        rule = self.workspace / ".cline" / "rules" / "00-qwen-harness-contract.md"
        rule.parent.mkdir(parents=True)
        rule.write_text("# generated rule\n", encoding="utf-8")
        self.state = self.evidence / "state"
        self.run_home = self.evidence / "home"
        self.temp = self.evidence / "tmp"
        for path in (self.state, self.run_home, self.temp):
            path.mkdir()
        self.policy = self.evidence / "policy.json"
        self.policy.write_text("{}\n", encoding="utf-8")
        self.audit = self.evidence / "audit.jsonl"
        self.audit.touch()
        self.runtime_audit = self.evidence / "runtime-hooks.jsonl"
        self.runtime_audit.touch()
        self.contract = harness.TaskContract(
            task_id="fake-cline",
            source_commit="a" * 40,
            task="edit target",
            packet_path="packet.md",
            input_files={"packet.md": "b" * 64, "target.txt": "c" * 64},
            create_files=(),
            write_files=("target.txt",),
            required_change_files=("target.txt",),
            verification_commands=(),
            model="qwen3.8-max-preview",
            thinking="xhigh",
            retries=3,
            timeout_seconds=0,
        )
        self.pin = harness.load_runtime_pin()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_fake(self, *, forbidden_stream_call: bool = False) -> Path:
        fake_dir = self.evidence / "fake-bin"
        fake_dir.mkdir()
        fake = fake_dir / "cline-fake"
        tool_name = "search_codebase" if forbidden_stream_call else "editor"
        tool_input = {"query": "secret"} if forbidden_stream_call else {"path": "target.txt"}
        fake.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/python3
                import json
                import os
                import sys
                from pathlib import Path

                args = sys.argv[1:]
                workspace = Path(args[args.index("--cwd") + 1])
                (workspace / "target.txt").write_text("after\\n", encoding="utf-8")
                call_id = "fake-call-1"
                audit = {{
                    "call_id": call_id,
                    "tool": {tool_name!r},
                    "allowed": True,
                    "reason": "allowed",
                    "paths": ["target.txt"],
                    "command_fingerprints": [],
                }}
                Path(os.environ["QWEN_HARNESS_AUDIT"]).write_text(
                    json.dumps(audit) + "\\n", encoding="utf-8"
                )
                event = {{
                    "type": "agent_event",
                    "event": {{
                        "type": "content_start",
                        "contentType": "tool",
                        "toolCallId": call_id,
                        "toolName": {tool_name!r},
                        "input": {tool_input!r},
                    }},
                }}
                print(json.dumps(event), flush=True)
                print(json.dumps({{
                    "type": "run_result",
                    "finishReason": "completed",
                    "iterations": 1,
                    "model": {{
                        "id": "qwen3.8-max-preview",
                        "provider": "openai-compatible",
                    }},
                    "usage": {{"inputTokens": 1, "outputTokens": 1}},
                }}), flush=True)
                """
            ),
            encoding="utf-8",
        )
        os.chmod(fake, 0o755)
        return fake

    def run_fake(self, *, forbidden_stream_call: bool = False) -> list[str]:
        fake = self.make_fake(forbidden_stream_call=forbidden_stream_call)
        profile = harness.build_sandbox_profile(
            user_home=Path.home(),
            cline_binary=fake,
            workspace=self.workspace,
            state_dir=self.state,
            run_home=self.run_home,
            temp_dir=self.temp,
            policy_path=self.policy,
            hook_audit_path=self.audit,
            runtime_hook_log_path=self.runtime_audit,
            write_files=[self.workspace / "target.txt"],
            bridge_port=self.pin.bridge_port,
        )
        before = harness.snapshot_tree(self.workspace)
        returncode, ledger, interrupted = harness.run_cline(
            cline_binary=fake,
            profile_text=profile,
            pin=self.pin,
            contract=self.contract,
            workspace=self.workspace,
            state_dir=self.state,
            run_home=self.run_home,
            temp_dir=self.temp,
            policy_path=self.policy,
            hook_audit_path=self.audit,
            runtime_hook_log_path=self.runtime_audit,
            evidence_dir=self.evidence,
        )
        self.assertFalse(interrupted)
        after = harness.snapshot_tree(self.workspace)
        changed, violations = harness.compare_snapshots(before, after, self.contract)
        hook_records, hook_errors = harness.read_hook_audit(self.audit)
        return harness.assess_run(
            returncode=returncode,
            ledger=ledger,
            hook_records=hook_records,
            hook_errors=hook_errors,
            contract=self.contract,
            changed_files=changed,
            snapshot_violations=violations,
            source_unchanged=True,
        )

    def test_fake_cline_exact_edit_is_accepted(self) -> None:
        self.assertEqual(self.run_fake(), [])

    def test_fake_cline_forbidden_stream_tool_is_rejected(self) -> None:
        reasons = self.run_fake(forbidden_stream_call=True)
        self.assertTrue(any("not admitted" in reason for reason in reasons), reasons)


if __name__ == "__main__":
    unittest.main()
