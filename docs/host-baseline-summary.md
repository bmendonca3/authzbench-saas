# Host Baseline Summary

This document summarizes the baseline families, partitions, and their leaderboard eligibility rules for host reviewers.

| Family | Split | Current? | Repeated? | Tool Access | Eligible? | Purpose / Description |
| --- | --- | --- | --- | --- | --- | --- |
| **scripted sanity public 60** | Public | Current | No | Scripted | No | Verifies public split and scorer-oracle replay paths |
| **model public 60 families** | Public | Current | Yes | no-tools | No | Diagnostic public baseline evidence (e.g. Qwen, Claude) |
| **live HTTP tool-agent public 60** | Public | Current/Stale | Yes | tool-agent | No | Verifies target-request correlation evidence under HTTP agent runs |
| **private no-tools empty response** | Private | Current | Yes | no-tools | Private only | Verifies false-positive scoring on secure controls against the private holdout |
| **private tool-agent empty response** | Private | Current | Yes | tool-agent | Private only | Verifies private target-request and custody boundaries |

## Eligibility Partitioning Rules
1. **Public Split Rows**: Diagnostic and testing purposes only. Public split rows are never eligible for the final leaderboard ranking.
2. **Private Split Rows**: Host-controlled or maintainer-operated runs utilizing gitignored private task holdouts. Only verified private split runs backing valid replay evidence are eligible for final leaderboard rankings.
