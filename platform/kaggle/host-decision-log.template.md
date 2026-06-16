# Host Decision Log Template

Status: Template. Not a completed host decision record.

This decision log tracks key platform configuration choices and policy adoptions decided by the competition host prior to public benchmark launch.

## 1. Packet Identity
- **Repository Commit**: 
- **Host Packet Manifest SHA-256**: 
- **Public Validation Run Status**: 
- **Host Reviewer**: 
- **Date**: 

## 2. Configuration & Policy Decisions

| Decision Area | Available Options | Selected Value | Owner | Date | Rationale | Affected Docs/Scripts | Launch Blocker? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Host Model** | Model A (Review Only)<br>Model B (Private Pilot)<br>Model C (CSV Platform Scored) | Model A + Model B (Model C deferred) | Host / Maintainer | | Evidence replay scoring requires runner environment. | `docs/kaggle-hosting-model.md` | **Yes** |
| **Private Data Custody** | Host-controlled<br>Maintainer-operated | | Host | | Who holds the raw task manifests and keys. | `docs/privacy-and-holdout-custody.md` | **Yes** |
| **Submission Format** | CSV Index + ZIP Bundle<br>Runner Container Image<br>Direct API Sandbox | CSV Index + ZIP Bundle | Host / Maintainer | | Balance between validation fidelity and ease of platform integration. | `platform/kaggle/sample_submission.csv` | **Yes** |
| **Public Split Role** | Diagnostic Only<br>Public Leaderboard Scored | Diagnostic Only | Host | | Prevent leaderboard gaming and over-fitting to public tasks. | `platform/kaggle/rules-template.md` | No |
| **Scorer Location** | Host-operated Sandbox<br>Maintainer Staging Environment | | Host | | Execution safety and secret protection boundary. | `authzbench/score.py` | **Yes** |
| **Rerun Policy** | Infrastructure failure only<br>Participant requested (capped)<br>No reruns allowed | Infrastructure failure only | Host | | Minimize runner load and prevent oracle guessing. | `platform/kaggle/rules-template.md` | No |
| **Appeals Process** | Code/Evidence audit only<br>Self-service rerun<br>No appeals | Code/Evidence audit only | Host | | Maintainer-operated review of private logs without revealing secrets. | `platform/kaggle/rules-template.md` | No |
| **Pack Rotation** | On leak detection only<br>Fixed schedule (e.g. quarterly)<br>Every major release | On leak detection / major release | Host / Maintainer | | Maintain task confidentiality over time. | `docs/host-private-leakage-response.md` | No |
| **Legacy Score Policy** | Snapshots archived<br>Scores recalculated<br>Scores deleted | Snapshots archived | Host | | Ensure old scores remain visible but distinct from active pack. | `docs/host-packet-versioning.md` | No |
