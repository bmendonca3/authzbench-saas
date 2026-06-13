# Realism notes: audit_settings

The audit_settings app is one of six AuthZBench-SaaS target apps. This file
documents the real-world authorization patterns it represents, what is
intentionally simplified, and what an AppSec or compliance reviewer should
look at before treating a finding here as evidence of a real production gap.

## Real-world authorization pattern represented

Audit log access and audit-driven exports in a SaaS organization are
typically gated by:

- organization membership (the actor must belong to the org that owns
  the audit log or export)
- role (admin or member, with auditor as a read-only role separate from
  admin in mature systems)
- a route-specific check on admin exports

The recurring bug class the app is designed to surface is **role-bypass
on the audit-export path**: a non-admin member of the org can download
or preview an admin-only audit export because the export route checks
org membership but not role.

A second class is **cross-org read via alias routes**: an event-stream
or audit-log alias can leak log entries from another organization when
the alias re-implements the tenant check incorrectly.

## Why the route and entity structure is plausible

The route shape mirrors what real SaaS compliance dashboards expose:

- canonical `/api/orgs/{org}/audit-logs/{id}` for reading
- alias `/api/orgs/{org}/events/{id}` that some platforms expose for
  stream-style access
- a secure variant `/api/secure/orgs/{org}/audit-logs/{id}` that is
  supposed to enforce stricter checks
- a `PATCH /api/orgs/{org}/security/settings` for SSO and session
  timeout updates that should require admin
- a `/api/orgs/{org}/settings/admin-export` for compliance exports

The org naming uses two distinct orgs (Nimbus on `enterprise`, Quasar on
`enterprise`) so that cross-org tests have a real second org to point at.

## What is intentionally simplified

- The audit log is a list of event strings; there is no real event
  ingestion, no log signing, no tamper-evident chain.
- There is no retention setting mutation; the plan callout for
  "viewer can read logs but not change retention" is a category in the
  fix-plan wish list, not a present route.
- The auditor role is a read-only role; in real systems auditor is
  often also a separate identity boundary, which the app does not
  model.
- There is no external SIEM, no log shipping, no compliance officer
  approval workflow.

## What would be needed for SaaS-provider validation

A real audit-log review with the SaaS provider would need to:

- validate the read role model against the provider's compliance matrix
- confirm that admin exports are gated to a separate compliance identity
- verify that the audit-log alias is either removed or consistently
  guarded
- check that the SSO-required and session-timeout settings cannot be
  modified by non-admin actors
- confirm that the audit log is append-only and tamper-evident

## Example CWE and OWASP mapping

- CWE-285: Improper Authorization
- CWE-862: Missing Authorization
- OWASP API Security Top 10: API5:2023 (Broken Function Level
  Authorization)
- OWASP API Security Top 10: API3:2023 (Broken Object Property Level
  Authorization) for audit-log alias leaks

## AppSec reviewer questions

- Can a non-admin member of the org download or preview an admin-only
  audit export?
- Can a non-admin modify SSO or session-timeout settings?
- Does the audit-log alias re-validate org membership and role?
- Are admin exports signed, rate-limited, and tied to a compliance
  identity?
- Is the audit log append-only and tamper-evident?

## How this file is generated

This file is hand-curated from the audit_settings app seed state, route
list, and public task manifest.
