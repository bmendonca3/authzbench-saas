# Run-Bundle Integrity Specification

Status: active implementation specification
Classification: full Spec Kit workflow

## Purpose

Make the complete retained evidence directory for a benchmark run
content-addressed and independently recheckable before any result is promoted.

## User Scenarios

### US-001 — Maintainer freezes a completed run

After the evaluator and outer wrapper finish, the maintainer builds one
deterministic manifest that inventories every retained regular file without
copying file contents into the manifest.

### US-002 — Reviewer detects custody drift

A reviewer validates the manifest later and receives a fail-closed result if a
file changed, disappeared, appeared, became a symlink, or no longer satisfies
the declared evidence requirements.

### US-003 — Promotion remains honestly bounded

The runbook makes clear that the manifest proves local content consistency only;
it does not prove model identity, external custody, benchmark eligibility,
platform acceptance, or independent attestation.

## Functional Requirements

- **FR-001**: Build a manifest for one explicit existing run directory without following symlinks.
- **FR-002**: Record every regular file except the manifest itself using a sorted POSIX relative path, byte size, and SHA-256 digest.
- **FR-003**: Bind schema version, declared required paths/globs, and file entries into a deterministic bundle SHA-256.
- **FR-004**: Refuse to overwrite an existing manifest.
- **FR-005**: Validate schema/types, duplicate keys, safe paths, sorted unique entries, sizes, hashes, aggregate counts, requirements, and bundle digest.
- **FR-006**: Fail validation on altered, missing, unexpected, symlinked, or non-regular paths.
- **FR-007**: Support repeatable exact-path and glob evidence requirements recorded inside the manifest.
- **FR-008**: Keep manifest contents public-safe by storing metadata only, while warning that private filenames and manifests remain private unless separately reviewed.
- **FR-009**: Provide build and validate CLIs with stable exit behavior and no network or dependency requirement.
- **FR-010**: Integrate the gate into the baseline rerun and run-bundle guidance without changing existing scores, baselines, or promotion eligibility.

## Edge Cases

- Empty run directory.
- Existing manifest from an earlier freeze attempt.
- Symlink to a file inside or outside the run directory.
- Manifest path containing absolute, parent, backslash, empty, or duplicate components.
- Duplicate JSON keys that a normal parser would silently collapse.
- Required glob that matched during build but no longer matches during validation.
- A wrapper log added after the manifest was created.
- Manifest copied away from its run directory.

## Success Criteria

- **SC-001**: Two manifest payloads over unchanged files are byte-for-byte identical.
- **SC-002**: Every adversarial mutation produces a non-passing validation result with a stable finding code.
- **SC-003**: Focused unit/CLI tests and the complete public validation pass.
- **SC-004**: Documentation names the post-wrapper timing, required evidence examples, privacy boundary, and non-attestation claim.
- **SC-005**: No pre-existing user work, baseline result, score, registry entry, or external state changes.

## Non-Goals

- Signing, timestamping, notarizing, uploading, or publishing the manifest.
- Reading or packaging private holdout bodies.
- Deciding leaderboard eligibility.
- Automatically rewriting an existing manifest.
- Running any model or benchmark matrix.
