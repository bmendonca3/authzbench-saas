# Realism notes: project_mgmt

The project_mgmt app is one of six AuthZBench-SaaS target apps. This file
documents the real-world authorization patterns it represents, what is
intentionally simplified, and what an AppSec or product-engineering
reviewer should look at before treating a finding here as evidence of a
real production gap.

## Real-world authorization pattern represented

Task, project, and portfolio access in a SaaS work-management platform
is typically gated by:

- tenant isolation (the actor's tenant must own the task or project)
- role within the tenant (owner can do anything, member can update
  task status, viewer can read)
- project membership (some projects are shared with select members of
  another tenant; not modeled in this app)
- a route-specific check (canonical vs alias vs portfolio routes)

The recurring bug class the app is designed to surface is **BOLA on
the cross-tenant read path**: a member of one tenant can read a task
in another tenant through an alias route that does not re-validate
tenant ownership.

A second class is **cross-tenant write through workflow**: a member of
one tenant performs a normal same-tenant task update, then uses the
same session to read or write another tenant's task through an alias.

## Why the route and entity structure is plausible

The route shape mirrors what real SaaS work-management platforms expose:

- canonical `/api/projects/{id}/tasks/{id}` for reading and updating
- alias `/api/workspaces/{id}/work-items/{id}` that some platforms
  expose for workspace-style access
- a `/api/portfolios/{tenant}/backlog-items/{id}` for portfolio views
- a secure variant `/api/secure/tenants/{tenant}/backlog-items/{id}`
  that is supposed to enforce tenant checks
- a `PATCH /api/projects/{id}/tasks/{id}` for status updates

The tenant naming uses two distinct tenants (Northstar Product, Helio
Research) so that cross-tenant tests have a real second tenant to point
at.

## What is intentionally simplified

- Projects and tasks are flat; there is no nested project hierarchy,
  no board, no sprint.
- There is no project membership other than tenant membership. Real
  systems often allow a project to be shared with select members of
  another tenant.
- There is no activity log, no comments, no attachments, no
  notifications.
- There is no soft delete or archive; tasks are simply open or
  updated.
- The "workflow" in multistep tasks is a simple setup write plus an
  exploit read; real workflows involve state machines.

## What would be needed for SaaS-provider validation

A real project-management review with the SaaS provider would need to:

- validate the tenant isolation model against the provider's
  authorization framework
- confirm that alias routes and portfolio routes use the same
  authorization middleware as the canonical route
- verify that workflow-style updates cannot leave a session in a state
  that unlocks cross-tenant reads
- check that the secure tenant-checked route is the one production code
  calls

## Example CWE and OWASP mapping

- CWE-285: Improper Authorization
- CWE-639: Authorization Bypass Through User-Controlled Key
- OWASP API Security Top 10: API1:2023 (Broken Object Level
  Authorization)
- OWASP API Security Top 10: API3:2023 (Broken Object Property Level
  Authorization) when private notes are exposed through an alias

## AppSec reviewer questions

- Can a member of tenant A read or write a task in tenant B through
  any alias or portfolio route?
- Does the cross-tenant workflow still require the setup write in
  tenant A before the exploit read in tenant B?
- Does the secure tenant-checked route enforce tenant membership, and
  is it the route production code calls?
- Are private task notes exposed through any alias route, even when
  the task body is gated?

## How this file is generated

This file is hand-curated from the project_mgmt app seed state, route
list, and public task manifest.
