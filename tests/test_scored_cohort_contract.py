"""
Tests for scored-cohort-contract.v1.json validation.

Tests cover:
- Valid contract passes validation
- Duplicate/missing public task mapping fails
- Manifest-set digest mismatch fails
- Leaked private task identifiers fail
- Nonzero admitted scored tasks with pending cluster verification fails
- Invented/complete independent review fails
- Numeric minimum supplied with pending-review status fails
- launch_ready=true fails
- Exact aggregate totals 63/27/21/15
- Wrong cluster apps fails
- Wrong cluster behavior_counts fails
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from validate_scored_cohort_contract import validate_contract

REPO_ROOT = Path(__file__).parent.parent
CONTRACT_PATH = REPO_ROOT / 'artifact' / 'scored-cohort-contract.v1.json'
TASKS_DIR = REPO_ROOT / 'tasks'

SUMMARY_ARTIFACT_NAMES = (
    'private-holdout-active-public-summary.json',
    'private-holdout-shadow-public-summary.json',
    'v1-task-scale-roadmap.json',
    'private-holdout-operation-blocker.json',
)

REQUIRED_AGG_KEYS = [
    'active_private_holdout_count',
    'shadow_private_holdout_count',
    'total_private_holdout_count',
    'public_structure_overlap_count',
    'total_vulnerable_count',
    'total_control_count',
    'total_denial_control_count',
    'total_authorized_allow_control_count',
]

REQUIRED_AGG_VALUES = {
    'active_private_holdout_count': 24,
    'shadow_private_holdout_count': 24,
    'total_private_holdout_count': 48,
    'public_structure_overlap_count': 0,
    'total_vulnerable_count': 24,
    'total_control_count': 24,
    'total_denial_control_count': 12,
    'total_authorized_allow_control_count': 12,
}

NORMALIZED_FORBIDDEN_KEYS = ['Oracle-Bodies', 'diagnostic details']


class ScoredCohortContractTestCase(unittest.TestCase):
    """Provide a mutable contract copy and summary artifacts per test."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp_dir.cleanup)
        temp_root = Path(self._temp_dir.name)

        self.temp_contract = temp_root / 'scored-cohort-contract.v1.json'
        shutil.copy2(CONTRACT_PATH, self.temp_contract)

        self.summary_root = temp_root / 'summary-root'
        summary_artifact_dir = self.summary_root / 'artifact'
        summary_artifact_dir.mkdir(parents=True)
        for artifact_name in SUMMARY_ARTIFACT_NAMES:
            shutil.copy2(
                REPO_ROOT / 'artifact' / artifact_name,
                summary_artifact_dir / artifact_name,
            )

    def _load_temp_contract(self) -> dict:
        with open(self.temp_contract) as f:
            return json.load(f)

    def _write_temp_contract(self, contract: dict) -> None:
        with open(self.temp_contract, 'w') as f:
            json.dump(contract, f)

    def _cluster(self, contract: dict) -> dict:
        clusters = contract['public_calibration_inventory']['clusters']
        return clusters[list(clusters.keys())[0]]

    def _active_summary_path(self) -> Path:
        return self.summary_root / 'artifact' / 'private-holdout-active-public-summary.json'

    def _shadow_summary_path(self) -> Path:
        return self.summary_root / 'artifact' / 'private-holdout-shadow-public-summary.json'


class ContractValidationTests(ScoredCohortContractTestCase):
    """Core contract validation: the real contract and mutations of a copy."""

    def test_valid_contract_passes(self) -> None:
        """Test that the actual contract passes validation."""
        result = validate_contract(CONTRACT_PATH, TASKS_DIR)
        self.assertTrue(result['valid'], f"Valid contract failed: {result['errors']}")
        self.assertEqual(result['cluster_count'], 17)
        self.assertEqual(result['public_task_count'], 63)
        self.assertEqual(len(result['errors']), 0)

    def test_exact_aggregate_totals(self) -> None:
        """Test that aggregate behavior totals are exactly 63/27/21/15."""
        result = validate_contract(CONTRACT_PATH, TASKS_DIR)
        self.assertTrue(result['valid'], f"Valid contract failed: {result['errors']}")

        behavior_totals = result.get('behavior_totals', {})
        self.assertEqual(
            behavior_totals.get('vulnerable'), 27,
            f"Expected 27 vulnerable, got {behavior_totals.get('vulnerable')}",
        )
        self.assertEqual(
            behavior_totals.get('denial'), 21,
            f"Expected 21 denial, got {behavior_totals.get('denial')}",
        )
        self.assertEqual(
            behavior_totals.get('authorized_allow'), 15,
            f"Expected 15 authorized_allow, got {behavior_totals.get('authorized_allow')}",
        )

    def test_duplicate_task_mapping_fails(self) -> None:
        """Test that duplicate task IDs in cluster mapping fail validation."""
        contract = self._load_temp_contract()

        # Duplicate a task ID in the first cluster
        first_cluster = self._cluster(contract)

        # Add duplicate task ID
        if first_cluster['task_ids']:
            first_cluster['task_ids'].append(first_cluster['task_ids'][0])
            first_cluster['task_count'] = len(first_cluster['task_ids'])

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('duplicate' in err.lower() for err in result['errors']),
            result['errors'],
        )

    def test_missing_task_mapping_fails(self) -> None:
        """Test that missing task IDs in cluster mapping fail validation."""
        contract = self._load_temp_contract()

        # Remove a task ID from the first cluster
        first_cluster = self._cluster(contract)

        if first_cluster['task_ids']:
            first_cluster['task_ids'].pop()
            first_cluster['task_count'] = len(first_cluster['task_ids'])

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('missing' in err.lower() or 'total task_ids' in err.lower()
                for err in result['errors']),
            result['errors'],
        )

    def test_manifest_digest_mismatch_fails(self) -> None:
        """Test that incorrect manifest-set SHA-256 fails validation."""
        contract = self._load_temp_contract()

        # Corrupt the manifest digest
        contract['source_bindings']['public_manifest_set_sha256'] = '0' * 64

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('manifest_set_sha256' in err for err in result['errors']),
            result['errors'],
        )

    def test_leaked_private_task_ids_fail(self) -> None:
        """Test that leaked private task identifiers fail validation."""
        contract = self._load_temp_contract()

        # Add a forbidden private detail pattern
        contract['public_claim_boundary'] = "Contains tasks_private/ path"

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('forbidden private detail' in err for err in result['errors']),
            result['errors'],
        )

    def test_nonzero_admitted_scored_tasks_fails(self) -> None:
        """Test that nonzero admitted_scored_task_count with pending cluster verification fails."""
        contract = self._load_temp_contract()

        # Set admitted_scored_task_count to nonzero while cluster_disjointness_verified is False
        contract['private_scored_cohort_candidate']['admitted_scored_task_count'] = 5

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('admitted_scored_task_count' in err for err in result['errors']),
            result['errors'],
        )

    def test_invented_independent_review_fails(self) -> None:
        """Test that invented/complete independent review fails validation."""
        contract = self._load_temp_contract()

        # Set review status to complete with invented reviewer
        contract['independent_methodology_review_gate']['status'] = 'complete'
        contract['independent_methodology_review_gate']['decision'] = 'approved'
        contract['independent_methodology_review_gate']['reviewer_evidence'] = 'reviewer@example.com'

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('status' in err or 'decision' in err or 'reviewer_evidence' in err
                for err in result['errors']),
            result['errors'],
        )

    def test_numeric_minimum_with_pending_review_fails(self) -> None:
        """Test that numeric minimum supplied with pending-review status fails."""
        contract = self._load_temp_contract()

        # Set numeric minimums while status is pending-review
        contract['minimum_discriminating_cohort']['minimum_task_count'] = 20
        contract['minimum_discriminating_cohort']['minimum_cluster_count'] = 6

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('minimum_task_count' in err or 'minimum_cluster_count' in err
                for err in result['errors']),
            result['errors'],
        )

    def test_launch_ready_true_fails(self) -> None:
        """Test that launch_ready=true fails validation."""
        contract = self._load_temp_contract()

        # Set launch_ready to true in private_scored_cohort_candidate
        contract['private_scored_cohort_candidate']['launch_ready'] = True

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('launch_ready' in err for err in result['errors']),
            result['errors'],
        )

    def test_launch_ready_true_in_review_gate_fails(self) -> None:
        """Test that launch_ready=true in independent_methodology_review_gate fails."""
        contract = self._load_temp_contract()

        # Set launch_ready to true in independent_methodology_review_gate
        contract['independent_methodology_review_gate']['launch_ready'] = True

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('launch_ready' in err for err in result['errors']),
            result['errors'],
        )

    def test_cluster_disjointness_verified_true_fails(self) -> None:
        """Test that cluster_disjointness_verified=true fails validation."""
        contract = self._load_temp_contract()

        # Set cluster_disjointness_verified to true
        contract['private_scored_cohort_candidate']['cluster_disjointness_verified'] = True

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('cluster_disjointness_verified' in err for err in result['errors']),
            result['errors'],
        )

    def test_invalid_status_fails(self) -> None:
        """Test that invalid status fails validation."""
        contract = self._load_temp_contract()

        # Change status to invalid value
        contract['status'] = 'launch_ready'

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('status' in err for err in result['errors']),
            result['errors'],
        )

    def test_invalid_schema_version_fails(self) -> None:
        """Test that invalid schema_version fails validation."""
        contract = self._load_temp_contract()

        # Change schema_version to invalid value
        contract['schema_version'] = 'scored-cohort-contract-v0'

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('schema_version' in err for err in result['errors']),
            result['errors'],
        )

    def test_missing_required_fields_fail(self) -> None:
        """Test that missing required fields fail validation."""
        contract = self._load_temp_contract()

        # Remove a required field
        del contract['public_claim_boundary']

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('public_claim_boundary' in err for err in result['errors']),
            result['errors'],
        )

    def test_cluster_id_as_task_id_fails(self) -> None:
        """Test that cluster IDs that look like task IDs fail validation."""
        contract = self._load_temp_contract()

        # Rename a cluster to look like a task ID
        clusters = contract['public_calibration_inventory']['clusters']
        old_key = list(clusters.keys())[0]
        cluster_data = clusters.pop(old_key)
        clusters['tok_cross_tenant_secret_read'] = cluster_data

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('appears to be a task ID' in err for err in result['errors']),
            result['errors'],
        )

    def test_wrong_cluster_apps_fails(self) -> None:
        """Test that wrong cluster apps value fails validation."""
        contract = self._load_temp_contract()

        # Modify apps in first cluster to wrong value
        first_cluster = self._cluster(contract)

        # Set wrong apps
        first_cluster['apps'] = ['wrong_app']

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('apps mismatch' in err for err in result['errors']),
            result['errors'],
        )

    def test_wrong_cluster_behavior_counts_fails(self) -> None:
        """Test that wrong cluster behavior_counts value fails validation."""
        contract = self._load_temp_contract()

        # Modify behavior_counts in first cluster to wrong value
        first_cluster = self._cluster(contract)

        # Set wrong behavior_counts
        first_cluster['behavior_counts'] = {'vulnerable': 999}

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('behavior_counts mismatch' in err for err in result['errors']),
            result['errors'],
        )


class PublicSafeSummaryTests(ScoredCohortContractTestCase):
    """Public-safe summary validation tests (T005B1)."""

    def test_public_safe_summary_paths_validation(self) -> None:
        """Test that public-safe summary artifacts are validated correctly."""
        result = validate_contract(CONTRACT_PATH, TASKS_DIR, self.summary_root)
        self.assertTrue(result['valid'], f"Validation failed: {result['errors']}")

        # Check private totals are present
        private_totals = result.get('private_totals', {})
        self.assertEqual(private_totals.get('private'), 48)
        self.assertEqual(private_totals.get('vulnerable'), 24)
        self.assertEqual(private_totals.get('controls'), 24)
        self.assertEqual(private_totals.get('denial'), 12)
        self.assertEqual(private_totals.get('authorized_allow'), 12)
        self.assertEqual(private_totals.get('overlap'), 0)

    def test_wrong_source_summary_paths_fails(self) -> None:
        """Test that wrong source-summary path list fails validation."""
        contract = self._load_temp_contract()

        # Modify the public_safe_summary_paths to wrong values
        contract['source_bindings']['public_safe_summary_paths'] = [
            'artifact/wrong-path.json',
            'artifact/another-wrong.json',
        ]

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('public_safe_summary_paths' in err for err in result['errors']),
            result['errors'],
        )

    def test_public_safe_summary_false_fails(self) -> None:
        """Test that public_safe_summary=false fails validation."""
        # Modify the active summary artifact to set public_safe_summary=false
        active_summary_path = self._active_summary_path()
        with open(active_summary_path) as f:
            summary = json.load(f)

        summary['public_safe_summary'] = False

        with open(active_summary_path, 'w') as f:
            json.dump(summary, f)

        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('public_safe_summary must be true' in err for err in result['errors']),
            result['errors'],
        )

    def test_publication_safety_flag_true_fails(self) -> None:
        """Test that any publication-safety flag set true fails validation."""
        # Modify the active summary artifact to set a publication_safety flag to true
        active_summary_path = self._active_summary_path()
        with open(active_summary_path) as f:
            summary = json.load(f)

        summary['publication_safety']['contains_private_file_paths'] = True

        with open(active_summary_path, 'w') as f:
            json.dump(summary, f)

        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('publication_safety' in err for err in result['errors']),
            result['errors'],
        )

    def test_wrong_active_summary_count_fails(self) -> None:
        """Test that wrong active summary count fails validation."""
        # Modify the active summary artifact to have wrong private_holdout_count
        active_summary_path = self._active_summary_path()
        with open(active_summary_path) as f:
            summary = json.load(f)

        summary['counts']['private_holdout_count'] = 30  # Wrong count

        with open(active_summary_path, 'w') as f:
            json.dump(summary, f)

        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('private_holdout_count must be 24' in err for err in result['errors']),
            result['errors'],
        )


class SourceBindingTests(ScoredCohortContractTestCase):
    """Source bindings validation tests (T005B2A)."""

    def test_invalid_kebab_case_cluster_id_fails(self) -> None:
        """Test that a cluster ID with invalid kebab-case (e.g. 'Bad Cluster') fails."""
        contract = self._load_temp_contract()

        clusters = contract['public_calibration_inventory']['clusters']
        old_key = list(clusters.keys())[0]
        cluster_data = clusters.pop(old_key)
        clusters['Bad Cluster'] = cluster_data

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('kebab-case' in err for err in result['errors']),
            result['errors'],
        )

    def test_manifest_app_mismatch_fails(self) -> None:
        """Test that a manifest app value not matching its parent directory fails.

        Uses a temporary copy of the public tasks only.
        """
        # Create temp tasks dir with a modified manifest
        tmp_tasks = Path(self._temp_dir.name) / 'tmp_tasks'
        tmp_tasks.mkdir()

        # Copy all task manifests
        for app_dir in TASKS_DIR.iterdir():
            if app_dir.is_dir():
                dst_dir = tmp_tasks / app_dir.name
                dst_dir.mkdir()
                for manifest in app_dir.glob('*.json'):
                    shutil.copy(manifest, dst_dir / manifest.name)

        # Modify one manifest's app field to mismatch parent directory
        first_app_dir = sorted(p for p in tmp_tasks.iterdir() if p.is_dir())[0]
        first_manifest = sorted(first_app_dir.glob('*.json'))[0]
        with open(first_manifest) as f:
            task = json.load(f)
        task['app'] = 'wrong_app_name'
        with open(first_manifest, 'w') as f:
            json.dump(task, f)

        result = validate_contract(self.temp_contract, tmp_tasks)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('does not match parent directory' in err for err in result['errors']),
            result['errors'],
        )

    def test_wrong_public_manifest_paths_fails(self) -> None:
        """Test that a wrong public_manifest_paths list fails validation."""
        contract = self._load_temp_contract()

        # Set wrong manifest paths
        contract['source_bindings']['public_manifest_paths'] = [
            'tasks/wrong/path.json',
            'tasks/another/wrong.json',
        ]

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('public_manifest_paths mismatch' in err for err in result['errors']),
            result['errors'],
        )

    def test_nonexistent_audited_baseline_sha_fails(self) -> None:
        """Test that a nonexistent audited baseline SHA fails validation."""
        contract = self._load_temp_contract()

        # Set a valid-format but nonexistent SHA
        fake_sha = '0' * 40
        contract['source_bindings']['audited_baseline_commit'] = fake_sha

        self._write_temp_contract(contract)

        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('audited_baseline_commit' in err for err in result['errors']),
            result['errors'],
        )


class AggregateFieldMutationTests(ScoredCohortContractTestCase):
    """T005B2B — focused temporary-copy mutation tests."""

    def test_missing_required_aggregate_field_fails(self) -> None:
        """Removing any required aggregate field must fail validation."""
        for field in REQUIRED_AGG_KEYS:
            with self.subTest(field=field):
                shutil.copy2(CONTRACT_PATH, self.temp_contract)
                c = self._load_temp_contract()
                del c['private_scored_cohort_candidate']['aggregate_private_summary_counts'][field]
                self._write_temp_contract(c)
                result = validate_contract(self.temp_contract, TASKS_DIR)
                self.assertFalse(result['valid'])
                self.assertTrue(
                    any(field in e and 'missing' in e for e in result['errors']),
                    result['errors'],
                )

    def test_wrong_aggregate_value_fails(self) -> None:
        """Setting an aggregate field to a wrong integer must fail."""
        c = self._load_temp_contract()
        c['private_scored_cohort_candidate']['aggregate_private_summary_counts']['total_private_holdout_count'] = 99
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('total_private_holdout_count' in e and 'must be 48' in e
                for e in result['errors']),
            result['errors'],
        )

    def test_boolean_public_structure_overlap_count_fails(self) -> None:
        """A boolean value for an integer aggregate field must fail (type(value) is int)."""
        c = self._load_temp_contract()
        c['private_scored_cohort_candidate']['aggregate_private_summary_counts']['public_structure_overlap_count'] = False
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('public_structure_overlap_count' in e and 'integer' in e
                for e in result['errors']),
            result['errors'],
        )

    def test_nested_private_task_ids_forbidden(self) -> None:
        """Nested private_task_ids key anywhere in pscc must be rejected."""
        c = self._load_temp_contract()
        c['private_scored_cohort_candidate']['notes'] = {'private_task_ids': ['tok_abc']}
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('forbidden' in e.lower() and 'private' in e.lower()
                for e in result['errors']),
            result['errors'],
        )

    def test_normalized_plural_forbidden_key_fails(self) -> None:
        """Normalized/plural forbidden keys must be rejected recursively."""
        for bad_key in NORMALIZED_FORBIDDEN_KEYS:
            with self.subTest(bad_key=bad_key):
                shutil.copy2(CONTRACT_PATH, self.temp_contract)
                c = self._load_temp_contract()
                c['private_scored_cohort_candidate']['notes'] = {bad_key: 'x'}
                self._write_temp_contract(c)
                result = validate_contract(self.temp_contract, TASKS_DIR)
                self.assertFalse(result['valid'])
                self.assertTrue(
                    any('forbidden' in e.lower() for e in result['errors']),
                    result['errors'],
                )

    def test_empty_publication_safety_fails(self) -> None:
        """Empty publication_safety object must fail."""
        active_path = self._active_summary_path()
        with open(active_path) as f:
            s = json.load(f)
        s['publication_safety'] = {}
        with open(active_path, 'w') as f:
            json.dump(s, f)
        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('publication_safety' in e and 'non-empty' in e for e in result['errors']),
            result['errors'],
        )

    def test_non_object_publication_safety_fails(self) -> None:
        """Non-object publication_safety must fail."""
        active_path = self._active_summary_path()
        with open(active_path) as f:
            s = json.load(f)
        s['publication_safety'] = "not-an-object"
        with open(active_path, 'w') as f:
            json.dump(s, f)
        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('publication_safety' in e for e in result['errors']),
            result['errors'],
        )

    def test_whitespace_cluster_rule_fails(self) -> None:
        """Whitespace-only cluster_disjoint_rules value must fail."""
        c = self._load_temp_contract()
        c['cluster_disjoint_rules']['no_cross_cluster_split'] = '   '
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('no_cross_cluster_split' in e and 'non-empty' in e for e in result['errors']),
            result['errors'],
        )

    def test_empty_cluster_rule_fails(self) -> None:
        """Empty cluster_disjoint_rules value must fail."""
        c = self._load_temp_contract()
        c['cluster_disjoint_rules']['no_cross_cluster_split'] = ''
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('no_cross_cluster_split' in e for e in result['errors']),
            result['errors'],
        )

    def test_whitespace_seed_variant_policy_fails(self) -> None:
        """Whitespace-only seed_and_variant_handling field must fail."""
        c = self._load_temp_contract()
        c['seed_and_variant_handling']['rotation_policy'] = '   '
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('rotation_policy' in e and 'non-empty' in e for e in result['errors']),
            result['errors'],
        )

    def test_empty_seed_variant_policy_fails(self) -> None:
        """Empty seed_and_variant_handling field must fail."""
        c = self._load_temp_contract()
        c['seed_and_variant_handling']['rotation_policy'] = ''
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('rotation_policy' in e for e in result['errors']),
            result['errors'],
        )

    def test_non_list_required_analysis_fails(self) -> None:
        """Non-list required_analysis must fail."""
        c = self._load_temp_contract()
        c['minimum_discriminating_cohort']['required_analysis'] = "not-a-list"
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('required_analysis' in e and 'list' in e for e in result['errors']),
            result['errors'],
        )

    def test_duplicate_required_analysis_fails(self) -> None:
        """Duplicate entries in required_analysis must fail."""
        c = self._load_temp_contract()
        ra = c['minimum_discriminating_cohort']['required_analysis']
        ra.append(ra[0])
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('duplicate' in e.lower() or 'required_analysis' in e
                for e in result['errors']),
            result['errors'],
        )

    def test_non_string_required_analysis_item_fails(self) -> None:
        """Non-string item in required_analysis must fail."""
        c = self._load_temp_contract()
        c['minimum_discriminating_cohort']['required_analysis'][0] = 42
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('required_analysis' in e for e in result['errors']),
            result['errors'],
        )

    def test_empty_review_questions_fails(self) -> None:
        """Empty review_questions list must fail."""
        c = self._load_temp_contract()
        c['independent_methodology_review_gate']['review_questions'] = []
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('review_questions' in e and 'non-empty' in e for e in result['errors']),
            result['errors'],
        )

    def test_non_string_acceptance_criterion_fails(self) -> None:
        """Non-string acceptance criterion must fail."""
        c = self._load_temp_contract()
        c['independent_methodology_review_gate']['acceptance_criteria'][0] = 123
        self._write_temp_contract(c)
        result = validate_contract(self.temp_contract, TASKS_DIR)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('acceptance_criteria' in e for e in result['errors']),
            result['errors'],
        )

    def test_malformed_active_summary_root_produces_errors(self) -> None:
        """Non-object active summary root must produce errors, not exceptions."""
        active_path = self._active_summary_path()
        with open(active_path, 'w') as f:
            json.dump([1, 2, 3], f)
        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('active summary' in e.lower() for e in result['errors']),
            result['errors'],
        )

    def test_malformed_shadow_summary_root_produces_errors(self) -> None:
        """Non-object shadow summary root must produce errors, not exceptions."""
        shadow_path = self._shadow_summary_path()
        with open(shadow_path, 'w') as f:
            json.dump("not-an-object", f)
        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('shadow summary' in e.lower() for e in result['errors']),
            result['errors'],
        )

    def test_malformed_active_counts_produces_errors(self) -> None:
        """Non-object counts in active summary must produce errors, not exceptions."""
        active_path = self._active_summary_path()
        with open(active_path) as f:
            s = json.load(f)
        s['counts'] = 42
        with open(active_path, 'w') as f:
            json.dump(s, f)
        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('counts' in e.lower() and 'object' in e.lower() for e in result['errors']),
            result['errors'],
        )

    def test_malformed_shadow_counts_produces_errors(self) -> None:
        """Non-object counts in shadow summary must produce errors, not exceptions."""
        shadow_path = self._shadow_summary_path()
        with open(shadow_path) as f:
            s = json.load(f)
        s['counts'] = None
        with open(shadow_path, 'w') as f:
            json.dump(s, f)
        result = validate_contract(self.temp_contract, TASKS_DIR, self.summary_root)
        self.assertFalse(result['valid'])
        self.assertTrue(
            any('counts' in e.lower() and 'object' in e.lower() for e in result['errors']),
            result['errors'],
        )


class WiringAndDocsTests(unittest.TestCase):
    """Cross-checks against the public validator wiring and design docs."""

    def test_public_validator_invokes_scored_cohort_validator_exactly_once(self) -> None:
        """The public validation script invokes the scored-cohort validator exactly once."""
        validate_public = (REPO_ROOT / 'scripts' / 'validate_public.py').read_text()
        needle = 'scripts/validate_scored_cohort_contract.py'
        count = validate_public.count(needle)
        self.assertEqual(
            count, 1,
            f"Expected exactly 1 invocation of {needle} in validate_public.py, found {count}",
        )

    def test_docs_section3_links_contract_and_preserves_pending_gates(self) -> None:
        """Section 3 links the versioned contract, exposes the command and exact public
        totals, and retains explicit pending/false/zero/null launch boundaries."""
        docs = (REPO_ROOT / 'docs' / 'kaggle-benchmark-design-contract.md').read_text()
        section3 = docs.split(
            '## 3. Cohorts, Contamination, And Clusters',
            maxsplit=1,
        )[1].split('\n## 4.', maxsplit=1)[0]

        # Versioned contract link
        self.assertIn('../artifact/scored-cohort-contract.v1.json', section3)

        # Validation command
        self.assertIn('python3 scripts/validate_scored_cohort_contract.py', section3)

        # Exact public totals
        self.assertIn('63 public calibration tasks', section3)
        self.assertIn('17 semantic clusters', section3)
        self.assertIn('27 vulnerable', section3)
        self.assertIn('21 denial', section3)
        self.assertIn('15 authorized-allow', section3)

        # Public-safe aggregate private evidence
        self.assertIn('48 total private holdouts', section3)
        self.assertIn('24 active', section3)
        self.assertIn('24 shadow', section3)
        self.assertIn('aggregate public structure overlap 0', section3)

        # Overlap 0 is not proof of disjointness
        self.assertIn('not proof of semantic cluster disjointness', section3)

        # Pending gates preserved
        self.assertIn('private cluster assignment pending', section3)
        self.assertIn('cluster disjointness unverified', section3)
        self.assertIn('pending-review', section3)
        self.assertIn('independent methodology review pending', section3)
        self.assertIn('admitted scored tasks 0', section3)
        self.assertIn('launch readiness false', section3)

        # Candidate, not accepted methodology
        self.assertIn('candidate pending independent', section3)
        self.assertIn('not accepted methodology or launch evidence', section3)


if __name__ == '__main__':
    unittest.main()
