# Realism notes: api_tokens

The api_tokens app is one of six AuthZBench-SaaS target apps. This file
documents the real-world authorization patterns it represents, what is
intentionally simplified, and what an AppSec or SaaS-platform reviewer
should look at before treating a finding here as evidence of a real
production gap.

## Real-world authorization pattern represented

Vaulted secrets and exports in a SaaS platform are typically gated by:

- tenant isolation (the actor's tenant must own the secret or export)
- token scope (a token's OAuth-style scopes, e.g. `secrets:read`,
  `secrets:write`, `exports:read`, `tokens:admin`, must permit the action)
- a route-specific check (some routes are aliases and re-implement the
  scope check inconsistently)

The recurring bug class the app is designed to surface is **scope-bypass
BFLA**: the tenant isolation check is in place, but the scope check is
missing or wrong on at least one of the routes, so a token with a narrow
scope can do something a narrow scope should not be able to do.

Common real-world variants:

- a read-only token can update a secret because the update path checks
  tenant but not scope
- a tenant can read another tenant's secret through an alias route
  (e.g. `/api/vault/secrets/{id}` vs `/api/secrets/{id}`) that does not
  re-validate tenant membership
- a read-only export token can fetch an admin-only export because the
  export route checks tenant but not scope

## Why the route and entity structure is plausible

The route shape mirrors what real SaaS platform APIs expose:

- canonical `/api/secrets/{id}` for read and update
- alias `/api/vault/secrets/{id}` and `/api/secure/secrets/{id}` paths
- a separate `/api/exports/{id}` path for export artifacts
- a `/api/token-admin/exports/{id}` admin-only path that is supposed to
  require `tokens:admin`
- multiple token actors with distinct scopes, so a review can pinpoint
  the scope-bypass boundary

The tenant naming uses two distinct tenants (Meridian on `business`,
Helio on `enterprise`) so that cross-tenant tests have a real second
tenant to point at.

## What is intentionally simplified

- Tokens are statically seeded per run; there is no token issuance,
  rotation, or revocation flow.
- Scopes are flat strings; there is no scope hierarchy, no scope
  inheritance, and no scope-bound-to-resource semantics.
- There is no audit log of who read which secret when, beyond the
  per-request log the app already emits.
- There is no KMS, no envelope encryption, no HSM.
- "Updated by" is just a string on the secret; no actor history is kept.

## What would be needed for SaaS-provider validation

A real vault review with the SaaS provider would need to:

- validate the scope model against the provider's authorization
  framework
- confirm that every alias route uses the same authorization middleware
  as the canonical route
- verify that update paths reject requests from read-only scopes
  regardless of which route was used
- confirm that token-rotation invalidates the prior token immediately

## Example CWE and OWASP mapping

- CWE-285: Improper Authorization
- CWE-862: Missing Authorization
- CWE-863: Incorrect Authorization
- CWE-639: Authorization Bypass Through User-Controlled Key (when scope
  checks are inconsistent across routes)
- OWASP API Security Top 10: API5:2023 (Broken Function Level
  Authorization)
- OWASP API Security Top 10: API1:2023 (Broken Object Level
  Authorization) for cross-tenant secret reads

## AppSec reviewer questions

- Is the read-only scope check missing on the secret update path?
- Does the alias route re-validate tenant and scope?
- Does the secure variant route enforce both tenant and scope, and is
  it the route production code actually calls?
- Can a token with `exports:read` fetch an export that should require
  `tokens:admin`?
- Is there a token-rotation flow that revokes prior tokens?

## How this file is generated

This file is hand-curated from the api_tokens app seed state, route list,
and public task manifest.
