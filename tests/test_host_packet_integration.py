import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_host_review_bundle import build_bundle, resolve_git_commit
from scripts.validate_host_review_bundle import validate_bundle

ROOT = Path(__file__).resolve().parents[1]


class HostPacketIntegrationTests(unittest.TestCase):
    def test_full_bundle_build_and_validation_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "authzbench-saas-host-review"
            
            # 1. Build host review bundle in temp directory
            # We pass allow_dirty=True to ensure the test passes even if there are uncommitted changes during development.
            build_result = build_bundle(
                tmp_path,
                ref_commit=resolve_git_commit(root=ROOT),
                allow_dirty=True,
                created_at_utc="2026-06-16T00:00:00Z"
            )
            self.assertTrue(build_result["passed"], f"Bundle building failed: {build_result.get('errors')}")

            # 2. Run bundle validation which checks manifests, checksums,required files,
            # private markers, claim boundaries, and runs Kaggle sample/dry-run/solution validators.
            validation_result = validate_bundle(tmp_path)
            self.assertTrue(validation_result["passed"], f"Bundle validation failed: {validation_result.get('errors')}")
