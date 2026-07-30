#!/usr/bin/env python3
"""
Validate scored-cohort-contract.v1.json structure and semantics.

This validator checks that the contract:
- Has correct schema version and status
- Maps all 63 public tasks exactly once to semantic clusters
- Computes deterministic manifest-set SHA-256
- Reports aggregate private counts without leaking private details
- Maintains pending-review state for minimums and independent review
- Preserves launch_ready=false
- Derives behaviors from manifests and validates cluster behavior_counts
- Validates public-safe summary artifacts without reading tasks_private/
- Validates source bindings: app field, manifest paths, cluster IDs, baseline commit
- Fails closed on missing/wrong aggregate fields (never mutates input)
- Rejects private-detail keys recursively in private_scored_cohort_candidate
- Hardens publication_safety: must be non-empty object with all-false values
- Hardens required-methodology fields with type and content checks
"""
import json
import hashlib
import os
import sys
import re
import subprocess
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from authzbench.core import (
    EVIDENCE_CONTRACT_VERSION,
    SCORE_POLICY_VERSION,
    benchmark_source_hashes,
    stable_json_sha256,
)


def compute_manifest_set_sha256(tasks_dir):
    """Compute deterministic SHA-256 over sorted relative manifest paths and contents."""
    files = sorted(tasks_dir.glob('*/*.json'))
    # Use relative paths from repo root for determinism
    repo_root = tasks_dir.parent
    relpaths = sorted(os.path.relpath(f, repo_root) for f in files)
    h = hashlib.sha256()
    for rp in relpaths:
        h.update(rp.encode('utf-8'))
        h.update(b'\x00')
        full_path = repo_root / rp
        with open(full_path, 'rb') as fh:
            h.update(fh.read())
        h.update(b'\x00')
    return h.hexdigest()


def derive_task_behavior(manifest):
    """Derive behavior from manifest fields."""
    expected_vulnerable = manifest.get('expected_vulnerable', False)
    control_type = manifest.get('control_type')
    
    if expected_vulnerable is True:
        return 'vulnerable'
    elif expected_vulnerable is False:
        if control_type == 'denial':
            return 'denial'
        elif control_type == 'authorized_allow':
            return 'authorized_allow'
    
    return None


def validate_cluster_id_syntax(cid):
    """Validate cluster ID matches kebab-case pattern."""
    pattern = r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$'
    return re.match(pattern, cid) is not None


def _normalize_key(k):
    """Normalize a key: lowercase, replace hyphens/spaces with underscores, strip."""
    if not isinstance(k, str):
        k = str(k)
    return k.lower().replace('-', '_').replace(' ', '_').strip('_')


# Forbidden private-detail concepts (singular and plural forms)
_FORBIDDEN_PRIVATE_CONCEPTS = {
    'task_id', 'task_ids',
    'seed', 'seeds',
    'route', 'routes',
    'oracle', 'oracles',
    'body', 'bodies',
    'manifest_path', 'manifest_paths',
    'raw_result', 'raw_results',
    'diagnostic_detail', 'diagnostic_details',
}

# Approved aggregate/status/notes keys that are allowed in pscc
_APPROVED_PSCC_KEYS = {
    'private_cluster_assignment_status',
    'cluster_disjointness_verified',
    'admitted_scored_task_count',
    'launch_ready',
    'aggregate_private_summary_counts',
    'notes',
}


def _check_forbidden_keys_recursive(obj, path, errors):
    """Walk nested dicts/lists and reject forbidden private-detail keys."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            norm = _normalize_key(k)
            # Check if this normalized key matches any forbidden concept
            # Also check compound keys like 'private_task_ids' -> contains 'task_ids'
            is_forbidden = False
            if norm in _FORBIDDEN_PRIVATE_CONCEPTS:
                is_forbidden = True
            else:
                # Check if the normalized key contains a forbidden concept as a suffix/word
                for concept in _FORBIDDEN_PRIVATE_CONCEPTS:
                    if norm == concept:
                        is_forbidden = True
                        break
                    # Check if key ends with _<concept> or is <prefix>_<concept>
                    if norm.endswith('_' + concept) or norm.startswith(concept + '_'):
                        is_forbidden = True
                        break
                    # Check if key contains the concept as a substring word boundary
                    if '_' + concept + '_' in ('_' + norm + '_'):
                        is_forbidden = True
                        break
            
            if is_forbidden:
                errors.append(
                    f"forbidden private-detail key '{k}' found at path '{path}'")
            
            # Recurse into value
            _check_forbidden_keys_recursive(v, f"{path}.{k}", errors)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _check_forbidden_keys_recursive(item, f"{path}[{i}]", errors)


def _validate_publication_safety(ps, label, errors):
    """Validate publication_safety: must be non-empty object, all values exactly false."""
    if not isinstance(ps, dict):
        errors.append(f"{label} publication_safety must be a JSON object, got {type(ps).__name__}")
        return
    if len(ps) == 0:
        errors.append(f"{label} publication_safety must be a non-empty object")
        return
    for key, value in ps.items():
        if value is not False:
            errors.append(
                f"{label} publication_safety.{key} must be exactly false, got {value!r}")


def _validate_nonempty_string_list(obj, path, errors):
    """Validate that obj is a non-empty list of non-empty strings."""
    if not isinstance(obj, list):
        errors.append(f"{path} must be a list, got {type(obj).__name__}")
        return
    if len(obj) == 0:
        errors.append(f"{path} must be a non-empty list")
        return
    for i, item in enumerate(obj):
        if not isinstance(item, str) or not item:
            errors.append(f"{path}[{i}] must be a non-empty string, got {item!r}")


def validate_contract(contract_path, tasks_dir, summary_root=None):
    """Validate contract and return result dict."""
    errors = []
    warnings = []

    try:
        with open(contract_path) as f:
            contract = json.load(f)
        
        if summary_root is None:
            summary_root = tasks_dir.parent
    except Exception as e:
        return {
            'valid': False,
            'errors': ['Failed to load contract: {}'.format(e)],
            'warnings': [],
            'cluster_count': 0,
            'public_task_count': 0,
            'manifest_set_sha256': '',
            'behavior_totals': {},
            'private_totals': {},
        }

    # Check schema version
    if contract.get('schema_version') != 'scored-cohort-contract-v1':
        errors.append(
            "schema_version must be 'scored-cohort-contract-v1', got {}".format(
                contract.get('schema_version')))

    # Check status
    if contract.get('status') != 'candidate_pending_independent_review':
        errors.append(
            "status must be 'candidate_pending_independent_review', got {}".format(
                contract.get('status')))

    # Check evidence date without hard-coding one historical build day.
    evidence_date = contract.get('evidence_date')
    if not isinstance(evidence_date, str) or re.fullmatch(r'\d{4}-\d{2}-\d{2}', evidence_date) is None:
        errors.append("evidence_date must be an ISO YYYY-MM-DD date")

    # Check public claim boundary
    if 'public_claim_boundary' not in contract:
        errors.append("missing public_claim_boundary")

    # Check source bindings
    sb = contract.get('source_bindings', {})
    if not isinstance(sb, dict):
        errors.append("source_bindings must be a JSON object")
        sb = {}

    if sb.get('audited_baseline_scope') != 'historical-private-summary-source-only':
        errors.append(
            "audited_baseline_scope must prevent treating the historical commit as the current source")
    if sb.get('source_state') not in {
        'development-uncommitted-not-release-frozen',
        'release-frozen-clean-commit',
    }:
        errors.append("source_state must declare development or clean release-frozen state")

    # Validate audited_baseline_commit with local Git
    acb = sb.get('audited_baseline_commit', '')
    if not re.match(r'^[0-9a-f]{40}$', acb):
        errors.append("audited_baseline_commit must be exactly 40 lowercase hex characters")
    else:
        try:
            # Check if commit exists
            result = subprocess.run(
                ['git', 'cat-file', '-t', acb],
                cwd=tasks_dir.parent,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0 or result.stdout.strip() != 'commit':
                errors.append(f"audited_baseline_commit {acb} does not exist in local Git")
            else:
                # Check if it's an ancestor of HEAD
                result = subprocess.run(
                    ['git', 'merge-base', '--is-ancestor', acb, 'HEAD'],
                    cwd=tasks_dir.parent,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    errors.append(f"audited_baseline_commit {acb} is not an ancestor of HEAD")
        except subprocess.TimeoutExpired:
            errors.append("Git command timed out while validating audited_baseline_commit")
        except Exception as e:
            errors.append(f"Git command error while validating audited_baseline_commit: {e}")

    if sb.get('public_manifest_count') != 63:
        errors.append(
            "public_manifest_count must be 63, got {}".format(
                sb.get('public_manifest_count')))

    # Validate public_manifest_paths
    expected_manifest_paths = sorted(
        os.path.relpath(f, tasks_dir.parent)
        for f in tasks_dir.glob('*/*.json')
    )
    declared_manifest_paths = sb.get('public_manifest_paths', [])
    if declared_manifest_paths != expected_manifest_paths:
        errors.append(
            "public_manifest_paths mismatch: expected {} paths, got {}".format(
                len(expected_manifest_paths), len(declared_manifest_paths)))

    # Verify manifest set SHA-256
    expected_sha = compute_manifest_set_sha256(tasks_dir)
    if sb.get('public_manifest_set_sha256') != expected_sha:
        errors.append(
            "public_manifest_set_sha256 mismatch: expected {}, got {}".format(
                expected_sha, sb.get('public_manifest_set_sha256')))

    expected_source_sha = stable_json_sha256(benchmark_source_hashes())
    if sb.get('public_benchmark_source_set_sha256') != expected_source_sha:
        errors.append(
            "public_benchmark_source_set_sha256 mismatch: expected {}, got {}".format(
                expected_source_sha,
                sb.get('public_benchmark_source_set_sha256'),
            )
        )

    if sb.get('public_safe_private_summary_count') != 48:
        errors.append(
            "public_safe_private_summary_count must be 48, got {}".format(
                sb.get('public_safe_private_summary_count')))

    if sb.get('active_scoring_policy_id') != SCORE_POLICY_VERSION:
        errors.append(
            "active_scoring_policy_id mismatch: {}".format(
                sb.get('active_scoring_policy_id')))
    if sb.get('evidence_contract_version') != EVIDENCE_CONTRACT_VERSION:
        errors.append(
            "evidence_contract_version mismatch: {}".format(
                sb.get('evidence_contract_version')))

    # Validate public-safe summary paths
    expected_summary_paths = [
        'artifact/private-holdout-active-public-summary.json',
        'artifact/private-holdout-shadow-public-summary.json',
        'artifact/v1-task-scale-roadmap.json',
        'artifact/private-holdout-operation-blocker.json',
    ]
    if sb.get('public_safe_summary_paths') != expected_summary_paths:
        errors.append(
            "public_safe_summary_paths mismatch: expected {}, got {}".format(
                expected_summary_paths, sb.get('public_safe_summary_paths')))

    # Load and validate the four public-safe summary artifacts
    private_totals = {
        'private': 0,
        'vulnerable': 0,
        'controls': 0,
        'denial': 0,
        'authorized_allow': 0,
        'overlap': 0,
    }

    try:
        # Load active summary
        active_summary_path = Path(summary_root) / 'artifact' / 'private-holdout-active-public-summary.json'
        with open(active_summary_path) as f:
            active_summary = json.load(f)

        if not isinstance(active_summary, dict):
            errors.append("active summary must be a JSON object")
            active_summary = {}

        if active_summary.get('schema_version') != 'holdout-public-safe-summary-v1':
            errors.append("active summary schema_version mismatch")
        if active_summary.get('public_safe_summary') is not True:
            errors.append("active summary public_safe_summary must be true")
        if active_summary.get('passed') is not True:
            errors.append("active summary passed must be true")
        if active_summary.get('private_holdouts_untracked') is not True:
            errors.append("active summary private_holdouts_untracked must be true")

        # Check publication_safety: must be non-empty object, all values exactly false
        pub_safety = active_summary.get('publication_safety')
        _validate_publication_safety(pub_safety, "active summary", errors)

        active_counts = active_summary.get('counts', {})
        if not isinstance(active_counts, dict):
            errors.append("active summary counts must be a JSON object")
            active_counts = {}
        if active_counts.get('private_holdout_count') != 24:
            errors.append("active summary private_holdout_count must be 24")
        if active_counts.get('vulnerable_count') != 12:
            errors.append("active summary vulnerable_count must be 12")
        if active_counts.get('control_count') != 12:
            errors.append("active summary control_count must be 12")
        if active_counts.get('denial_control_count') != 6:
            errors.append("active summary denial_control_count must be 6")
        if active_counts.get('authorized_allow_control_count') != 6:
            errors.append("active summary authorized_allow_control_count must be 6")
        if active_counts.get('public_structure_overlap_count') != 0:
            errors.append("active summary public_structure_overlap_count must be 0")

        # Load shadow summary
        shadow_summary_path = Path(summary_root) / 'artifact' / 'private-holdout-shadow-public-summary.json'
        with open(shadow_summary_path) as f:
            shadow_summary = json.load(f)

        if not isinstance(shadow_summary, dict):
            errors.append("shadow summary must be a JSON object")
            shadow_summary = {}

        if shadow_summary.get('schema_version') != 'holdout-public-safe-summary-v1':
            errors.append("shadow summary schema_version mismatch")
        if shadow_summary.get('public_safe_summary') is not True:
            errors.append("shadow summary public_safe_summary must be true")
        if shadow_summary.get('passed') is not True:
            errors.append("shadow summary passed must be true")
        if shadow_summary.get('private_holdouts_untracked') is not True:
            errors.append("shadow summary private_holdouts_untracked must be true")

        pub_safety = shadow_summary.get('publication_safety')
        _validate_publication_safety(pub_safety, "shadow summary", errors)

        shadow_counts = shadow_summary.get('counts', {})
        if not isinstance(shadow_counts, dict):
            errors.append("shadow summary counts must be a JSON object")
            shadow_counts = {}
        if shadow_counts.get('private_holdout_count') != 24:
            errors.append("shadow summary private_holdout_count must be 24")
        if shadow_counts.get('vulnerable_count') != 12:
            errors.append("shadow summary vulnerable_count must be 12")
        if shadow_counts.get('control_count') != 12:
            errors.append("shadow summary control_count must be 12")
        if shadow_counts.get('denial_control_count') != 6:
            errors.append("shadow summary denial_control_count must be 6")
        if shadow_counts.get('authorized_allow_control_count') != 6:
            errors.append("shadow summary authorized_allow_control_count must be 6")
        if shadow_counts.get('public_structure_overlap_count') != 0:
            errors.append("shadow summary public_structure_overlap_count must be 0")

        # Compute combined totals
        private_totals['private'] = active_counts.get('private_holdout_count', 0) + shadow_counts.get('private_holdout_count', 0)
        private_totals['vulnerable'] = active_counts.get('vulnerable_count', 0) + shadow_counts.get('vulnerable_count', 0)
        private_totals['controls'] = active_counts.get('control_count', 0) + shadow_counts.get('control_count', 0)
        private_totals['denial'] = active_counts.get('denial_control_count', 0) + shadow_counts.get('denial_control_count', 0)
        private_totals['authorized_allow'] = active_counts.get('authorized_allow_control_count', 0) + shadow_counts.get('authorized_allow_control_count', 0)
        private_totals['overlap'] = active_counts.get('public_structure_overlap_count', 0) + shadow_counts.get('public_structure_overlap_count', 0)

        # Validate combined totals
        if private_totals['private'] != 48:
            errors.append(f"combined private total must be 48, got {private_totals['private']}")
        if private_totals['vulnerable'] != 24:
            errors.append(f"combined vulnerable total must be 24, got {private_totals['vulnerable']}")
        if private_totals['controls'] != 24:
            errors.append(f"combined controls total must be 24, got {private_totals['controls']}")
        if private_totals['denial'] != 12:
            errors.append(f"combined denial total must be 12, got {private_totals['denial']}")
        if private_totals['authorized_allow'] != 12:
            errors.append(f"combined authorized_allow total must be 12, got {private_totals['authorized_allow']}")
        if private_totals['overlap'] != 0:
            errors.append(f"combined overlap total must be 0, got {private_totals['overlap']}")

    except FileNotFoundError as e:
        errors.append(f"public-safe summary artifact not found: {e}")
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        errors.append(f"public-safe summary artifact malformed: {e}")

    # Validate roadmap and operation blocker
    try:
        roadmap_path = Path(summary_root) / 'artifact' / 'v1-task-scale-roadmap.json'
        with open(roadmap_path) as f:
            roadmap = json.load(f)
        if roadmap.get('current_validated_private_holdout_task_count') != 48:
            errors.append("roadmap current_validated_private_holdout_task_count must be 48")
    except FileNotFoundError as e:
        errors.append(f"roadmap artifact not found: {e}")
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        errors.append(f"roadmap artifact malformed: {e}")

    try:
        blocker_path = Path(summary_root) / 'artifact' / 'private-holdout-operation-blocker.json'
        with open(blocker_path) as f:
            blocker = json.load(f)
        count_level = blocker.get('count_level_public_evidence', {})
        if count_level.get('validated_private_holdout_task_count') != 48:
            errors.append("blocker validated_private_holdout_task_count must be 48")
    except FileNotFoundError as e:
        errors.append(f"blocker artifact not found: {e}")
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        errors.append(f"blocker artifact malformed: {e}")

    # Load all manifests and derive behaviors, validate app field
    task_id_to_behavior = {}
    task_id_to_apps = {}
    manifest_task_ids = set()
    duplicate_task_ids = []

    for tf in tasks_dir.glob('*/*.json'):
        try:
            with open(tf) as f:
                task = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            errors.append(f"malformed task manifest {tf}: {e}")
            continue

        if not isinstance(task, dict):
            errors.append(f"task manifest {tf} is not a JSON object")
            continue

        if 'id' not in task:
            errors.append(f"task manifest {tf} missing 'id' field")
            continue

        task_id = task['id']
        if task_id in manifest_task_ids:
            duplicate_task_ids.append(task_id)
        manifest_task_ids.add(task_id)

        # Validate app field
        app_field = task.get('app')
        if not isinstance(app_field, str) or not app_field:
            errors.append(f"task {task_id} has missing or empty 'app' field")
        else:
            parent_dir = tf.parent.name
            if app_field != parent_dir:
                errors.append(
                    f"task {task_id} app field '{app_field}' does not match parent directory '{parent_dir}'")

        behavior = derive_task_behavior(task)
        if behavior is None:
            errors.append("task {} has unknown/malformed behavior".format(task_id))
        else:
            task_id_to_behavior[task_id] = behavior

        # Use manifest app field for cluster app derivation
        app_name = task.get('app', tf.parent.name)
        task_id_to_apps[task_id] = app_name

    if duplicate_task_ids:
        errors.append(f"duplicate task IDs in manifests: {sorted(set(duplicate_task_ids))}")

    # Check public calibration inventory
    pci = contract.get('public_calibration_inventory', {})
    clusters = pci.get('clusters', {})
    if pci.get('cluster_count') != len(clusters):
        errors.append(
            "cluster_count mismatch: {} vs {}".format(
                pci.get('cluster_count'), len(clusters)))

    # Verify all 63 public tasks appear exactly once
    all_task_ids = []
    aggregate_behavior_counts = Counter()
    
    for cid, cluster in clusters.items():
        # Check cluster ID syntax
        if not validate_cluster_id_syntax(cid):
            errors.append(
                f"cluster_id '{cid}' does not match required kebab-case pattern ^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")

        # Also check it's not a task ID
        task_id_prefixes = ('tok_', 'aud_', 'bill_', 'fs_', 'pm_', 'sup_')
        if not cid or any(cid.startswith(p) for p in task_id_prefixes):
            errors.append(
                "cluster_id '{}' appears to be a task ID, not a semantic name".format(cid))

        task_ids = cluster.get('task_ids', [])
        all_task_ids.extend(task_ids)

        # Check cluster has required fields
        for field in ('task_count', 'apps', 'app_count', 'behavior_counts'):
            if field not in cluster:
                errors.append("cluster '{}' missing {}".format(cid, field))

        # Verify task_count matches
        if cluster.get('task_count') != len(task_ids):
            errors.append(
                "cluster '{}' task_count mismatch: {} vs {}".format(
                    cid, cluster.get('task_count'), len(task_ids)))

        # Derive expected apps from task_ids
        expected_apps = sorted(set(task_id_to_apps.get(tid, '') for tid in task_ids if tid in task_id_to_apps))
        declared_apps = cluster.get('apps', [])
        
        # Verify apps are sorted and unique
        if declared_apps != sorted(declared_apps):
            errors.append("cluster '{}' apps must be sorted".format(cid))
        if len(declared_apps) != len(set(declared_apps)):
            errors.append("cluster '{}' apps must be unique".format(cid))
        
        # Verify apps match derived apps
        if declared_apps != expected_apps:
            errors.append(
                "cluster '{}' apps mismatch: declared {} vs derived {}".format(
                    cid, declared_apps, expected_apps))

        # Verify app_count matches
        if cluster.get('app_count') != len(declared_apps):
            errors.append(
                "cluster '{}' app_count mismatch: {} vs {}".format(
                    cid, cluster.get('app_count'), len(declared_apps)))

        # Derive expected behavior_counts from task_ids
        expected_behavior_counts = Counter()
        for tid in task_ids:
            if tid in task_id_to_behavior:
                expected_behavior_counts[task_id_to_behavior[tid]] += 1
        
        declared_behavior_counts = cluster.get('behavior_counts', {})
        
        # Verify behavior_counts match
        if dict(declared_behavior_counts) != dict(expected_behavior_counts):
            errors.append(
                "cluster '{}' behavior_counts mismatch: declared {} vs derived {}".format(
                    cid, declared_behavior_counts, dict(expected_behavior_counts)))
        
        # Aggregate behavior counts
        aggregate_behavior_counts.update(expected_behavior_counts)

    # Check all 63 tasks appear exactly once
    task_id_counts = Counter(all_task_ids)
    if len(all_task_ids) != 63:
        errors.append(
            "total task_ids must be 63, got {}".format(len(all_task_ids)))

    duplicates = [tid for tid, count in task_id_counts.items() if count > 1]
    if duplicates:
        errors.append("duplicate task_ids: {}".format(sorted(duplicates)))

    # Load actual public task IDs
    actual_task_ids = set()
    for tf in tasks_dir.glob('*/*.json'):
        try:
            with open(tf) as f:
                task = json.load(f)
            if isinstance(task, dict) and 'id' in task:
                actual_task_ids.add(task['id'])
        except (json.JSONDecodeError, IOError):
            pass

    missing_tasks = actual_task_ids - set(all_task_ids)
    if missing_tasks:
        errors.append(
            "missing public tasks in cluster inventory: {}".format(sorted(missing_tasks)))

    extra_tasks = set(all_task_ids) - actual_task_ids
    if extra_tasks:
        errors.append(
            "extra task_ids in cluster inventory (not in public manifests): {}".format(
                sorted(extra_tasks)))

    # Verify aggregate behavior totals: 63 / 27 / 21 / 15
    total_vulnerable = aggregate_behavior_counts.get('vulnerable', 0)
    total_denial = aggregate_behavior_counts.get('denial', 0)
    total_authorized_allow = aggregate_behavior_counts.get('authorized_allow', 0)
    
    if total_vulnerable != 27:
        errors.append("aggregate vulnerable count must be 27, got {}".format(total_vulnerable))
    if total_denial != 21:
        errors.append("aggregate denied count must be 21, got {}".format(total_denial))
    if total_authorized_allow != 15:
        errors.append("aggregate authorized_allow count must be 15, got {}".format(total_authorized_allow))

    behavior_totals = {
        'vulnerable': total_vulnerable,
        'denial': total_denial,
        'authorized_allow': total_authorized_allow,
    }

    # =========================================================================
    # Check private scored cohort candidate — fail-closed aggregate validation
    # =========================================================================
    pscc = contract.get('private_scored_cohort_candidate', {})
    if not isinstance(pscc, dict):
        errors.append("private_scored_cohort_candidate must be a JSON object")
        pscc = {}

    if pscc.get('private_cluster_assignment_status') != 'pending_maintainer_private_work':
        errors.append(
            "private_cluster_assignment_status must be 'pending_maintainer_private_work', got {}".format(
                pscc.get('private_cluster_assignment_status')))

    if pscc.get('cluster_disjointness_verified') is not False:
        errors.append(
            "cluster_disjointness_verified must be False, got {}".format(
                pscc.get('cluster_disjointness_verified')))

    if pscc.get('admitted_scored_task_count') != 0:
        errors.append(
            "admitted_scored_task_count must be 0, got {}".format(
                pscc.get('admitted_scored_task_count')))

    if pscc.get('launch_ready') is not False:
        errors.append(
            "launch_ready must be False, got {}".format(
                pscc.get('launch_ready')))

    # --- Fail-closed aggregate validation (never mutates input) ---
    apsc = pscc.get('aggregate_private_summary_counts')
    if not isinstance(apsc, dict):
        errors.append("aggregate_private_summary_counts must be a JSON object")
        apsc = {}

    # Required aggregate fields with exact expected values
    required_aggregates = {
        'active_private_holdout_count': 24,
        'shadow_private_holdout_count': 24,
        'total_private_holdout_count': 48,
        'public_structure_overlap_count': 0,
        'total_vulnerable_count': 24,
        'total_control_count': 24,
        'total_denial_control_count': 12,
        'total_authorized_allow_control_count': 12,
    }

    for field, expected in required_aggregates.items():
        if field not in apsc:
            errors.append(f"aggregate_private_summary_counts missing required field '{field}'")
        elif type(apsc[field]) is not int:
            errors.append(
                f"aggregate_private_summary_counts.{field} must be an integer, got {type(apsc[field]).__name__}")
        elif apsc[field] != expected:
            errors.append(
                f"aggregate_private_summary_counts.{field} must be {expected}, got {apsc[field]!r}")

    # Verify aggregates equal totals derived from the two public-safe summaries
    derived_aggregate_map = {
        'total_private_holdout_count': private_totals.get('private'),
        'total_vulnerable_count': private_totals.get('vulnerable'),
        'total_control_count': private_totals.get('controls'),
        'total_denial_control_count': private_totals.get('denial'),
        'total_authorized_allow_control_count': private_totals.get('authorized_allow'),
        'public_structure_overlap_count': private_totals.get('overlap'),
    }
    for field, derived_val in derived_aggregate_map.items():
        if field in apsc and isinstance(apsc[field], int) and apsc[field] == required_aggregates.get(field):
            if apsc[field] != derived_val:
                errors.append(
                    f"aggregate_private_summary_counts.{field} ({apsc[field]}) does not equal "
                    f"derived total from public-safe summaries ({derived_val})")

    # --- Reject private-detail keys recursively in pscc ---
    _check_forbidden_keys_recursive(pscc, "private_scored_cohort_candidate", errors)

    # Check for forbidden private details in the serialized contract
    contract_str = json.dumps(contract)
    forbidden_patterns = [
        'tasks_private/',
        'private-holdout-active/',
        'private-holdout-shadow/',
    ]
    for pattern in forbidden_patterns:
        if pattern in contract_str:
            errors.append(
                "contract contains forbidden private detail pattern: {}".format(pattern))

    # =========================================================================
    # Cluster disjoint rules — hardened: non-empty strings
    # =========================================================================
    cdr = contract.get('cluster_disjoint_rules', {})
    if not isinstance(cdr, dict):
        errors.append("cluster_disjoint_rules must be a JSON object")
        cdr = {}
    required_rules = [
        'no_cross_cluster_split',
        'alias_and_variant_grouping',
        'overlap_quarantine',
        'version_isolation',
    ]
    for rule in required_rules:
        if rule not in cdr:
            errors.append("missing cluster_disjoint_rules.{}".format(rule))
        elif not isinstance(cdr[rule], str) or not cdr[rule] or not cdr[rule].strip():
            errors.append(f"cluster_disjoint_rules.{rule} must be a non-empty string")

    # Check negative control requirements
    ncr = contract.get('negative_control_requirements', {})
    if not isinstance(ncr, dict):
        errors.append("negative_control_requirements must be a JSON object")
        ncr = {}
    if 'required_behaviors' not in ncr:
        errors.append("missing negative_control_requirements.required_behaviors")

    required_behaviors = {'vulnerable', 'denial', 'authorized_allow'}
    rb = ncr.get('required_behaviors', [])
    if not isinstance(rb, list):
        errors.append("negative_control_requirements.required_behaviors must be a list")
    elif set(rb) != required_behaviors:
        errors.append(
            "required_behaviors must be {}, got {}".format(
                required_behaviors, set(rb)))

    if 'aggregate_observed_private_summary_counts' not in ncr:
        errors.append(
            "missing negative_control_requirements.aggregate_observed_private_summary_counts")

    # Validate aggregate_observed_private_summary_counts matches derived totals
    aopsc = ncr.get('aggregate_observed_private_summary_counts', {})
    if not isinstance(aopsc, dict):
        errors.append("aggregate_observed_private_summary_counts must be a JSON object")
        aopsc = {}
    if aopsc.get('active_vulnerable_count') != 12:
        errors.append("aggregate_observed_private_summary_counts.active_vulnerable_count must be 12")
    if aopsc.get('shadow_vulnerable_count') != 12:
        errors.append("aggregate_observed_private_summary_counts.shadow_vulnerable_count must be 12")
    if aopsc.get('active_denial_control_count') != 6:
        errors.append("aggregate_observed_private_summary_counts.active_denial_control_count must be 6")
    if aopsc.get('shadow_denial_control_count') != 6:
        errors.append("aggregate_observed_private_summary_counts.shadow_denial_control_count must be 6")
    if aopsc.get('active_authorized_allow_control_count') != 6:
        errors.append("aggregate_observed_private_summary_counts.active_authorized_allow_control_count must be 6")
    if aopsc.get('shadow_authorized_allow_control_count') != 6:
        errors.append("aggregate_observed_private_summary_counts.shadow_authorized_allow_control_count must be 6")

    if ncr.get('per_cluster_private_coverage_status') != 'pending_maintainer_private_work':
        errors.append(
            "per_cluster_private_coverage_status must be 'pending_maintainer_private_work', got {}".format(
                ncr.get('per_cluster_private_coverage_status')))

    # =========================================================================
    # Seed and variant handling — hardened: non-empty strings
    # =========================================================================
    svh = contract.get('seed_and_variant_handling', {})
    if not isinstance(svh, dict):
        errors.append("seed_and_variant_handling must be a JSON object")
        svh = {}
    required_svh = [
        'rotation_policy',
        'retirement_and_invalidation',
        'rerun_requirements',
        'incident_reporting',
    ]
    for field in required_svh:
        if field not in svh:
            errors.append("missing seed_and_variant_handling.{}".format(field))
        elif not isinstance(svh[field], str) or not svh[field] or not svh[field].strip():
            errors.append(f"seed_and_variant_handling.{field} must be a non-empty string")

    # =========================================================================
    # Minimum discriminating cohort — hardened with type checks
    # =========================================================================
    mdc = contract.get('minimum_discriminating_cohort', {})
    if not isinstance(mdc, dict):
        errors.append("minimum_discriminating_cohort must be a JSON object")
        mdc = {}
    if mdc.get('minimum_task_count') is not None:
        errors.append(
            "minimum_task_count must be null, got {}".format(
                mdc.get('minimum_task_count')))

    if mdc.get('minimum_cluster_count') is not None:
        errors.append(
            "minimum_cluster_count must be null, got {}".format(
                mdc.get('minimum_cluster_count')))

    if mdc.get('status') != 'pending-review':
        errors.append(
            "minimum_discriminating_cohort.status must be 'pending-review', got {}".format(
                mdc.get('status')))

    if 'required_analysis' not in mdc:
        errors.append("missing minimum_discriminating_cohort.required_analysis")
    else:
        ra = mdc['required_analysis']
        if not isinstance(ra, list):
            errors.append("minimum_discriminating_cohort.required_analysis must be a list")
        else:
            expected_ra = [
                "discriminability_and_statistical_power",
                "uncertainty_or_bootstrap_intervals",
                "false_positive_sensitivity",
                "per_cluster_balance",
                "ranking_stability",
            ]
            if len(ra) != 5:
                errors.append(
                    f"required_analysis must have exactly 5 items, got {len(ra)}")
            elif ra != expected_ra:
                errors.append(
                    f"required_analysis must be exactly {expected_ra}, got {ra}")
            else:
                # Check all are non-empty strings with no duplicates
                if len(set(ra)) != len(ra):
                    errors.append("required_analysis contains duplicates")
                for i, item in enumerate(ra):
                    if not isinstance(item, str) or not item:
                        errors.append(f"required_analysis[{i}] must be a non-empty string")

    # =========================================================================
    # Independent methodology review gate — hardened with type checks
    # =========================================================================
    imrg = contract.get('independent_methodology_review_gate', {})
    if not isinstance(imrg, dict):
        errors.append("independent_methodology_review_gate must be a JSON object")
        imrg = {}
    if imrg.get('status') != 'pending':
        errors.append(
            "independent_methodology_review_gate.status must be 'pending', got {}".format(
                imrg.get('status')))

    if imrg.get('decision') is not None:
        errors.append(
            "decision must be null, got {}".format(imrg.get('decision')))

    if imrg.get('reviewer_evidence') is not None:
        errors.append(
            "reviewer_evidence must be null, got {}".format(
                imrg.get('reviewer_evidence')))

    if 'review_questions' not in imrg:
        errors.append("missing independent_methodology_review_gate.review_questions")
    else:
        _validate_nonempty_string_list(
            imrg['review_questions'],
            "independent_methodology_review_gate.review_questions",
            errors)

    if 'acceptance_criteria' not in imrg:
        errors.append("missing independent_methodology_review_gate.acceptance_criteria")
    else:
        _validate_nonempty_string_list(
            imrg['acceptance_criteria'],
            "independent_methodology_review_gate.acceptance_criteria",
            errors)

    if imrg.get('launch_ready') is not False:
        errors.append(
            "independent_methodology_review_gate.launch_ready must be False, got {}".format(
                imrg.get('launch_ready')))

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'cluster_count': pci.get('cluster_count', 0),
        'public_task_count': len(all_task_ids),
        'manifest_set_sha256': expected_sha,
        'behavior_totals': behavior_totals,
        'private_totals': private_totals,
    }


def main():
    """Main entry point."""
    repo_root = Path(__file__).resolve().parent.parent
    contract_path = repo_root / 'artifact' / 'scored-cohort-contract.v1.json'
    tasks_dir = repo_root / 'tasks'

    if not contract_path.exists():
        print(json.dumps({
            'valid': False,
            'errors': ['Contract not found: {}'.format(contract_path)],
            'warnings': [],
        }, indent=2))
        sys.exit(1)

    if not tasks_dir.exists():
        print(json.dumps({
            'valid': False,
            'errors': ['Tasks directory not found: {}'.format(tasks_dir)],
            'warnings': [],
        }, indent=2))
        sys.exit(1)

    result = validate_contract(contract_path, tasks_dir)

    # Print compact structured result
    output = {
        'valid': result['valid'],
        'cluster_count': result.get('cluster_count', 0),
        'public_task_count': result.get('public_task_count', 0),
        'manifest_set_sha256': result.get('manifest_set_sha256', ''),
        'behavior_totals': result.get('behavior_totals', {}),
        'private_totals': result.get('private_totals', {}),
        'error_count': len(result['errors']),
        'warning_count': len(result['warnings']),
    }

    if result['errors']:
        output['errors'] = result['errors']

    if result['warnings']:
        output['warnings'] = result['warnings']

    print(json.dumps(output, indent=2))

    sys.exit(0 if result['valid'] else 1)


if __name__ == '__main__':
    main()
