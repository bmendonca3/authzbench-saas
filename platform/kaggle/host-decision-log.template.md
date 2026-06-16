# Host Decision Log Template

Status: Template. Not a completed host decision record.

This decision log tracks key platform configuration choices and policy adoptions decided by the competition host prior to public benchmark launch.

## Packet Identity
- **Repository Commit**: 
- **Host Packet Manifest SHA-256**: 
- **Public Validation Run Status**: 
- **Container Smoke Run Status**: 
- **Host Reviewer**: 
- **Date**: 

## Host Model Decision
- **Chosen Model**: Model A (dataset/review package) + Model B (scoring pilot). Model C (native CSV scoring) deferred.
- **Reason**: AuthZBench-SaaS requires validating replayable backend evidence traces, which is not supported by native label-only CSV scoring. Native CSV will serve as an index mapping to the evidence bundle.

## Private Data Custody
- **Custody Owner**: [Host-controlled / Maintainer-operated]
- **Active Private Pack Version**: 
- **Active Private Pack Fingerprint**: 
- **Storage Location**: [Host secure private bucket / Maintainer secure workspace]

## Submission Format
- **Submissions Form**: CSV row-index mapping to finding paths + evidence bundle ZIP.
- **Verification Loop**: Platform Scorer executes local backend verification replay.

## Operational Policies
### Reruns
- **Allowed Reasons**: Platform infrastructure failure, verified runner bug, or scorer defect.
- **Max Reruns**: [e.g., 2 reruns per participant tier]

### Appeals
- **Appeal Process**: Participant submits appeal request with run metadata. Host reviews private execution traces and scorer logs.
- **Disclosure Policy**: Private manifests, routes, seeds, or target secrets are never disclosed to the participant under any circumstances.

### Rotation and Invalidation
- **Leakage Triggers**: Any suspected leak of private holdout tasks, routes, or oracles.
- **Pack Rotation Cadence**: [e.g., 3 months, or upon active pack retirement]
- **Legacy Row Policy**: Legacy rows marked as non-comparable snapshots after active pack rotation.
