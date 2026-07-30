from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from unittest.mock import patch

from authzbench.core import (
    BENCHMARK_SOURCE_MANIFEST_PATH,
    benchmark_git_source_state,
    benchmark_source_hashes_at_git_commit,
    benchmark_source_paths,
    runner_integrity_envelope,
)


class BenchmarkSourceStateTests(unittest.TestCase):
    def _run_result(
        self,
        args: list[str],
        *,
        committed: bytes,
        commit_sha: str,
    ) -> subprocess.CompletedProcess:
        if args[1:4] == ["rev-parse", "--verify", "HEAD^{commit}"]:
            return subprocess.CompletedProcess(args, 0, stdout=commit_sha + "\n", stderr="")
        if args[1:3] == ["show", f"{commit_sha}:source.py"]:
            return subprocess.CompletedProcess(args, 0, stdout=committed, stderr=b"")
        raise AssertionError(args)

    def test_exact_materialized_sources_resolve_to_head(self) -> None:
        commit_sha = "a" * 40
        content = b"current executable source\n"
        with (
            patch(
                "authzbench.core.benchmark_source_hashes",
                return_value={"source.py": hashlib.sha256(content).hexdigest()},
            ),
            patch(
                "authzbench.core.subprocess.run",
                side_effect=lambda args, **_kwargs: self._run_result(
                    args, committed=content, commit_sha=commit_sha
                ),
            ),
        ):
            result = benchmark_git_source_state(commit_sha)

        self.assertEqual(result["benchmark_commit_sha"], commit_sha)
        self.assertEqual(result["benchmark_source_state"], "exact-commit-clean")

    def test_dirty_materialized_sources_are_unfrozen_and_reject_explicit_commit(self) -> None:
        commit_sha = "b" * 40
        current = b"changed executable source\n"
        committed = b"committed executable source\n"
        with (
            patch(
                "authzbench.core.benchmark_source_hashes",
                return_value={"source.py": hashlib.sha256(current).hexdigest()},
            ),
            patch(
                "authzbench.core.subprocess.run",
                side_effect=lambda args, **_kwargs: self._run_result(
                    args, committed=committed, commit_sha=commit_sha
                ),
            ),
        ):
            development = benchmark_git_source_state()
            with self.assertRaisesRegex(ValueError, "every executable benchmark source"):
                benchmark_git_source_state(commit_sha)

        self.assertIsNone(development["benchmark_commit_sha"])
        self.assertEqual(
            development["benchmark_source_state"],
            "development-dirty-unfrozen",
        )

    def test_malformed_explicit_commit_is_rejected(self) -> None:
        commit_sha = "c" * 40
        content = b"source\n"
        with (
            patch(
                "authzbench.core.benchmark_source_hashes",
                return_value={"source.py": hashlib.sha256(content).hexdigest()},
            ),
            patch(
                "authzbench.core.subprocess.run",
                side_effect=lambda args, **_kwargs: self._run_result(
                    args, committed=content, commit_sha=commit_sha
                ),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "40-character lowercase Git SHA"):
                benchmark_git_source_state("not-a-commit")

    def test_local_source_manifest_is_sorted_self_bound_and_complete(self) -> None:
        paths = benchmark_source_paths()
        self.assertEqual(paths, tuple(sorted(paths)))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertIn(BENCHMARK_SOURCE_MANIFEST_PATH, paths)
        self.assertIn("authzbench/score.py", paths)
        self.assertIn("scripts/protected_private_eval.py", paths)
        self.assertIn("authzbench_harbor/adapter.py", paths)

    def test_historical_source_paths_are_resolved_from_declared_commit(self) -> None:
        commit_sha = "d" * 40
        manifest = {
            "schema_version": "benchmark-source-manifest-v1",
            "paths": [
                BENCHMARK_SOURCE_MANIFEST_PATH,
                "old-only-source.py",
            ],
        }
        payloads = {
            BENCHMARK_SOURCE_MANIFEST_PATH: json.dumps(
                manifest,
                sort_keys=True,
            ).encode("utf-8"),
            "old-only-source.py": b"historical source\n",
        }

        def run(args: list[str], **_kwargs) -> subprocess.CompletedProcess:
            prefix = f"{commit_sha}:"
            if args[1] != "show" or not args[2].startswith(prefix):
                raise AssertionError(args)
            path = args[2][len(prefix):]
            if path not in payloads:
                raise AssertionError(f"current-checkout path leaked into validation: {path}")
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=payloads[path],
                stderr=b"",
            )

        with patch("authzbench.core.subprocess.run", side_effect=run):
            hashes = benchmark_source_hashes_at_git_commit(commit_sha)

        self.assertEqual(set(hashes), set(payloads))
        self.assertEqual(
            hashes["old-only-source.py"],
            hashlib.sha256(payloads["old-only-source.py"]).hexdigest(),
        )

    def test_runner_integrity_v2_binds_every_public_summary_field(self) -> None:
        summary = {"run_id": "run-1", "mean_score": 0.5, "custom_metric": 7}
        first = runner_integrity_envelope(
            summary,
            generator="unit-generator",
            raw_summary_sha256="a" * 64,
        )
        changed = runner_integrity_envelope(
            {**summary, "custom_metric": 8},
            generator="unit-generator",
            raw_summary_sha256="a" * 64,
        )

        self.assertEqual(first["schema_version"], "runner-integrity-v2")
        self.assertEqual(
            first["claim_scope"],
            "unkeyed-tamper-evidence-not-origin-attestation",
        )
        self.assertNotEqual(first["public_payload_sha256"], changed["public_payload_sha256"])
        self.assertNotEqual(first["envelope_sha256"], changed["envelope_sha256"])

    def test_historical_runner_integrity_v1_remains_reproducible(self) -> None:
        summary = {
            "agent": "legacy",
            "run_id": "legacy-run",
            "runner_integrity": {"schema_version": "runner-integrity-v1"},
        }
        envelope = runner_integrity_envelope(
            summary,
            generator="scripts/protected_private_eval.py",
        )

        self.assertEqual(envelope["schema_version"], "runner-integrity-v1")
        self.assertIn("payload_sha256", envelope)


if __name__ == "__main__":
    unittest.main()
