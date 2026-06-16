# Realism notes: billing

The billing app is one of six AuthZBench-SaaS target apps. This file documents
the real-world authorization patterns it represents, what is intentionally
simplified, and what an AppSec or SaaS-billing reviewer should look at before
treating a finding here as evidence of a real production gap.

## Real-world authorization pattern represented

Plan changes, paid feature entitlements, invoice reads, and admin exports are
all gated by combinations of:

- organization membership (the actor must belong to the org that owns the
  invoice or entitlement)
- role (admin or member, with admin required for plan and entitlement writes)
- entitlement (some features are only available on certain plans)

This is the same shape that appears in real SaaS billing: a member of an org
should be able to read their own org's invoices, but only an admin should be
able to change the org's plan or toggle paid feature entitlements.

The two recurring bugs the app is designed to surface are:

- BFLA on the plan route: a member of the org can change the plan because
  the org-membership check is in place but the admin-role check is missing.
  This bug often hides behind an alias route (for example an
  `/api/accounts/{org}/entitlements/plan` route that mirrors the canonical
  `/api/orgs/{org}/settings/plan` route) and ships because the alias was
  added later and only inherited the membership check.
- BFLA on entitlement toggling: a member of the org can flip a paid
  feature entitlement (for example `audit_exports`) because the entitlement
  write path checks org membership but not admin role. In a real billing
  system this is the bug that lets a member self-upgrade paid features.

## Why the route and entity structure is plausible

The route shape mirrors what real SaaS billing systems expose:

- canonical `/api/orgs/{org}/settings/plan` and
  `/api/orgs/{org}/entitlements/{key}` paths
- an alias `/api/accounts/{org}/entitlements/plan` path that some teams
  build when they merge account-management and billing code paths
- a "secure" variant under `/api/secure/...` that is supposed to enforce
  admin role
- a GET on `/api/orgs/{org}/settings/admin-export` for admin-only exports

The org naming uses two distinct orgs (Atlas on `pro`, Beacon on
`enterprise`) so that cross-org authorization tests have a real second
org to point at instead of relying on synthetic UUIDs.

## What is intentionally simplified

- There is no payment processor integration. Plan changes are accepted
  directly, with no Stripe or billing-platform or usage-event validation.
- There is no subscription state machine. Plans flip directly; the
  reviewer should not treat a successful plan change as the org was
  downgraded in any business sense.
- There is no proration, refund, or invoice reconciliation logic.
- Entitlement keys are flat strings (`audit_exports`) and there is no
  nested entitlement hierarchy or feature flag service.
- There is no asynchronous billing event log and no webhooks.
- The export endpoints only return a queued status and do not produce a
  real export artifact.

## What would be needed for SaaS-provider validation

A real billing review with the SaaS provider would need to:

- validate the entitlement model against the provider's actual feature
  matrix
- confirm that the secure route is the one production code calls
- verify that entitlement writes go through a billing-event bus so that
  quota and rate-limit enforcement stay in sync
- check that the alias route is either removed or consistently guarded

## Example CWE and OWASP mapping

- CWE-285: Improper Authorization
- CWE-862: Missing Authorization
- CWE-863: Incorrect Authorization
- OWASP API Security Top 10: API5:2023 (Broken Function Level Authorization)
- OWASP API Security Top 10: API3:2023 (Broken Object Property Level
  Authorization) when entitlement toggles leak

## AppSec reviewer questions

- Does the org-membership check pass while the admin-role check is missing
  on the plan and entitlement write paths?
- Does the alias route for entitlements mirror the same authorization
  decisions as the canonical route?
- Is the secure admin-export route actually only reachable by admin
  actors?
- Are entitlement toggles logged as billing events, or is the audit trail
  left to application logs only?
- Could a member downgrade a paid plan in production in a way that would
  cause proration, refund, or compliance regressions?

## How this file is generated

This file is hand-curated from the billing app seed state, route list, and
public task manifest. The synthetic examples listed above are the ones an
external reviewer should treat as the canonical illustrations of the bug
class, not as exhaustive task coverage.
