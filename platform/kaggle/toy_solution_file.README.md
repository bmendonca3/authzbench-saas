# Toy Private Solution File README

This directory contains `toy_solution_file.csv` to demonstrate the platform-side solution file contract for host review.

## Solution File Schema
The CSV uses the following columns:
- `Id`: Stable public or private task identifier.
- `Usage`: `Public` or `Private` partition.
- `expected_vulnerable`: Boolean indicating if the task is vulnerable.
- `control_type`: Empty for vulnerable tasks, otherwise `denial` or `authorized_allow`.
- `oracle_ref`: Pointer to the scorer oracle.
- `task_pack_version`: Pack version identifier.

## Custody Rules
The real private solution file is generated from gitignored private holdout packs and stored in host-controlled private storage. It must never be committed to public Git.
