# Realism notes: file_sharing

The file_sharing app is one of six AuthZBench-SaaS target apps. This file
documents the real-world authorization patterns it represents, what is
intentionally simplified, and what an AppSec or document-management
reviewer should look at before treating a finding here as evidence of a
real production gap.

## Real-world authorization pattern represented

File and document access in a SaaS workspace is typically gated by:

- workspace membership (the actor must belong to the workspace that owns
  the file)
- role (owner, editor, viewer, with viewer unable to create public
  share links)
- share-link state (active vs expired vs revoked) and link visibility
  (workspace vs public)
- file classification (public, internal, confidential, restricted)

The recurring bug class the app is designed to surface is **stale or
revoked share-link access**: a link that was revoked or expired still
resolves to file content because the link route does not check link
state.

A second class is **BFLA on share-link creation**: a viewer-role actor
can create a public share link for a file because the share-link-create
route checks workspace membership but not role. This bug lets a viewer
exfiltrate confidential files by minting their own public link.

## Why the route and entity structure is plausible

The route shape mirrors what real SaaS file-sharing platforms expose:

- canonical `/api/files/{id}` for reading file content
- alias `/api/workspaces/{id}/documents/{id}` that some platforms
  expose for document-naming style access
- a secure variant `/api/secure/files/{id}` that is supposed to enforce
  classification checks
- a `/api/share-links/{id}` route that resolves share links to file
  content
- a secure variant `/api/secure/share-links/{id}` that is supposed to
  enforce link state
- a `POST /api/workspaces/{id}/files/{id}/share-links` to mint new
  share links

The workspace naming uses two distinct workspaces (Northstar on
`business`, Apex on `enterprise`) so that cross-workspace tests have a
real second workspace to point at.

## What is intentionally simplified

- Files are content strings, not real binary blobs. There is no
  pre-signed URL flow, no chunked download, no virus scan.
- Share links are not cryptographically signed; the link id is enough
  to identify the link.
- There is no link revocation separate from expiration. In real
  systems you can revoke an active link; the app exposes link state
  but the test is whether an expired link is still honored.
- There is no classification-based encryption-at-rest.
- There is no file versioning or audit trail of who downloaded what.

## What would be needed for SaaS-provider validation

A real file-sharing review with the SaaS provider would need to:

- validate the share-link state model against the provider's link
  management API
- confirm that revoked and expired links return 410 Gone
- verify that the share-link-create route enforces role on the workspace
  not just membership
- check that the secure share-link route is the one production code
  calls
- confirm that confidential files cannot be linked to a public
  visibility

## Example CWE and OWASP mapping

- CWE-285: Improper Authorization
- CWE-613: Insufficient Session Expiration (for stale share links)
- OWASP API Security Top 10: API1:2023 (Broken Object Level
  Authorization)
- OWASP API Security Top 10: API5:2023 (Broken Function Level
  Authorization) for share-link creation by viewers

## AppSec reviewer questions

- Does the share-link route check link state (active vs expired)?
- Can a viewer-role actor mint a public share link for a confidential
  file?
- Does the secure share-link route return 410 Gone for expired links
  and 404 Not Found for revoked links?
- Are confidential files encryptable at rest, and is the
  classification enforced regardless of the route used?
- Is there a way to revoke an active link without changing the link id?

## How this file is generated

This file is hand-curated from the file_sharing app seed state, route
list, and public task manifest.
