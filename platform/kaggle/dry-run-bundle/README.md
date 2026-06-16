# AuthZBench-SaaS Public Dry-Run Bundle

Status: Toy public dry-run shape. Not leaderboard eligible, not scored evidence.

This directory contains a complete public-safe mock submission bundle to demonstrate the format and layout required for evaluating submissions.

## Contents
- `sample_submission.csv`: The row index containing exactly three public tasks demonstrating each task type:
  1. One vulnerable task (`tok_cross_tenant_secret_read`)
  2. One denial control (`tok_secure_cross_tenant_secret_control`)
  3. One authorized-allow control (`sup_admin_reassignment_control`)
- `manifest.json`: The metadata manifest for the dry-run bundle.
- `submissions/`: The per-task findings files.
- `expected-shape/`: Example templates representing system outputs.
