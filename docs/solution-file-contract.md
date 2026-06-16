# Solution File Contract

Status: public-safe contract and toy example. The real private solution file is
host-controlled and must not be committed to public Git.

## Purpose

Kaggle-style platforms often use a solution file with an `Id` column and a
public/private usage split. AuthZBench-SaaS can expose a similar contract for
host review, but the actual private oracle and private task details must remain
under maintainer or host custody.

## Public Contract

A platform-side solution file can use this conceptual schema:

| Column | Meaning |
| --- | --- |
| `Id` | Stable task identifier or host-issued row identifier |
| `Usage` | `Public` or `Private` scoring partition |
| `expected_vulnerable` | Whether the task is vulnerable |
| `control_type` | Empty for vulnerable tasks, otherwise `denial` or `authorized_allow` |
| `oracle_ref` | Host-controlled pointer to the scorer oracle |
| `task_pack_version` | Public or private pack version |

The public repo may include toy rows that use public task IDs. It must not
include raw private solution rows.

## Toy Example

```csv
Id,Usage,expected_vulnerable,control_type,oracle_ref,task_pack_version
tok_cross_tenant_secret_read,Public,true,,public-oracle:tok_cross_tenant_secret_read,public-2026-06
tok_secure_cross_tenant_secret_control,Public,false,denial,public-oracle:tok_secure_cross_tenant_secret_control,public-2026-06
private-row-placeholder,Private,false,denial,host-controlled,private-pack-version-only
```

The placeholder row demonstrates custody shape only. It is not a real private
task, solution, route, seed, or oracle.

## Custody Rules

- Public Git may hold public task IDs and toy examples.
- Public Git may hold private pack fingerprints, counts, and public summaries.
- Public Git must not hold raw private task bodies, routes, seeds, per-task
  private outcomes, or private oracle details.
- Host-controlled private solution files should be generated from protected
  private packs and stored outside public Git.
- Published leaderboard rows should contain only redacted public-safe metadata.

## Validation Expectations

Before a host pilot, maintainers should verify:

- every public sample row maps to a tracked public task;
- private rows are generated and stored outside public Git;
- `Usage` values match the intended scoring split;
- solution-file hashes are recorded in host-controlled evidence;
- no raw private content appears in public artifacts.

