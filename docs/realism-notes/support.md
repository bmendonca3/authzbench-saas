# Realism notes: support

The support app is one of six AuthZBench-SaaS target apps. This file
documents the real-world authorization patterns it represents, what is
intentionally simplified, and what an AppSec or customer-support
reviewer should look at before treating a finding here as evidence of a
real production gap.

## Real-world authorization pattern represented

Support ticket access in a SaaS support platform is typically gated by:

- organization membership (the actor must belong to the org that owns
  the ticket)
- role (admin can reassign across the org, agent can update status,
  viewer can only read)
- assignment (some systems restrict status updates to the assigned
  agent)
- a route-specific check on cross-org reassignment

The recurring bug class the app is designed to surface is **BFLA on
the reassignment path**: an agent (non-admin) of the org can reassign
tickets through the non-secure reassignment route because the route
checks org membership but not admin role. Real systems often expose
this bug through a `case/owner` alias route that was added later and
inherited only the membership check.

A second class is **BFLA on invite creation**: an agent can create an
admin invite through the non-secure invite route, allowing the agent
to elevate a future user to admin without going through the admin
approval flow.

## Why the route and entity structure is plausible

The route shape mirrors what real SaaS support platforms expose:

- canonical `/api/tickets/{id}` for reading
- alias `/api/cases/{id}` that some platforms expose for case-style
  access
- a secure variant `/api/secure/tickets/{id}` that is supposed to
  enforce stricter checks
- a `PATCH /api/orgs/{org}/tickets/{id}/status` for status updates
- a `PATCH /api/orgs/{org}/tickets/{id}/assignee` for reassignment
- a secure variant `/api/secure/orgs/{org}/tickets/{id}/assignee` that
  is supposed to require admin
- a `POST /api/orgs/{org}/invites` for invite creation
- a secure variant `/api/secure/orgs/{org}/invites` that is supposed
  to require admin

The org naming uses two distinct orgs (Acme on `business`, Orbit on
`enterprise`) so that cross-org tests have a real second org to point
at.

## What is intentionally simplified

- Tickets are simple dicts; there is no thread, no comment, no
  attachment, no SLA timer.
- There is no assignment enforcement on status updates: an agent can
  update any Acme ticket regardless of whether they are the assignee.
  Real systems often gate status updates to the assigned agent.
- There is no invite acceptance flow; invites are just records.
- The cross-org reassignment check is at the org-membership level
  only; there is no check that the new assignee is in the same org.
- There is no support-manager role separate from admin; in real
  systems the support manager can reassign within the org but cannot
  cross orgs.

## What would be needed for SaaS-provider validation

A real support review with the SaaS provider would need to:

- validate the role model against the provider's support RBAC matrix
- confirm that reassignment requires admin, not just agent
- verify that the case/owner alias route is either removed or
  consistently guarded
- check that invites created by an agent are tagged for admin review
- confirm that the support-manager role is a distinct identity
  boundary, not just a flag on the admin role

## Example CWE and OWASP mapping

- CWE-285: Improper Authorization
- CWE-862: Missing Authorization
- OWASP API Security Top 10: API5:2023 (Broken Function Level
  Authorization)
- OWASP API Security Top 10: API1:2023 (Broken Object Level
  Authorization) for cross-org ticket reads

## AppSec reviewer questions

- Can an agent of the org reassign tickets through the non-secure
  route, and is that a known product behavior?
- Can an agent of the org create an admin invite, and is that gated
  to admin in production?
- Does the case/owner alias route re-validate admin role?
- Are status updates restricted to the assigned agent, and is that
  restriction enforced regardless of the route used?
- Is the support-manager role a distinct identity boundary?

## How this file is generated

This file is hand-curated from the support app seed state, route list,
and public task manifest.
