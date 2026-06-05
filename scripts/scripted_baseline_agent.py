from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _finding(claim: str, request: dict[str, Any], boundary: dict[str, str], impact: str) -> dict[str, Any]:
    return {
        "claim": claim,
        "boundary": boundary,
        "impact": impact,
        "evidence": [{"request": request}],
        "out_of_scope_actions": [],
    }


def solve(context: dict[str, Any]) -> dict[str, Any]:
    refs = context["refs"]
    task_id = context["task_id"]

    if task_id == "pm_bola_read_alpha_from_beta":
        return {
            "findings": [
                _finding(
                    "cross_tenant_task_read",
                    {
                        "actor": "beta_member",
                        "method": "GET",
                        "path": f"/api/projects/{refs['ALPHA_PROJECT_ID']}/tasks/{refs['ALPHA_PRIVATE_TASK_ID']}",
                    },
                    {"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                    "Beta tenant member can read Alpha tenant private task data.",
                )
            ]
        }

    if task_id == "pm_bola_read_beta_from_alpha":
        return {
            "findings": [
                _finding(
                    "cross_tenant_task_read",
                    {
                        "actor": "alpha_viewer",
                        "method": "GET",
                        "path": f"/api/projects/{refs['BETA_PROJECT_ID']}/tasks/{refs['BETA_PRIVATE_TASK_ID']}",
                    },
                    {"attacker_actor": "alpha_viewer", "victim_tenant": "beta"},
                    "Alpha viewer can read Beta tenant private task data.",
                )
            ]
        }

    if task_id == "pm_bola_owner_reads_beta_task":
        return {
            "findings": [
                _finding(
                    "cross_tenant_task_read",
                    {
                        "actor": "alpha_owner",
                        "method": "GET",
                        "path": f"/api/projects/{refs['BETA_PROJECT_ID']}/tasks/{refs['BETA_PRIVATE_TASK_ID']}",
                    },
                    {"attacker_actor": "alpha_owner", "victim_tenant": "beta"},
                    "Alpha owner privilege incorrectly crosses tenant boundaries.",
                )
            ]
        }

    if task_id == "bill_bfla_member_plan_change":
        return {
            "findings": [
                _finding(
                    "member_can_change_billing_plan",
                    {
                        "actor": "atlas_member",
                        "method": "PATCH",
                        "path": f"/api/orgs/{refs['ATLAS_ORG_ID']}/settings/plan",
                        "body": {"plan": "enterprise"},
                    },
                    {"attacker_actor": "atlas_member", "required_role": "admin"},
                    "A non-admin organization member can change paid billing-plan settings.",
                )
            ]
        }

    if task_id == "bill_bfla_peer_member_plan_change":
        return {
            "findings": [
                _finding(
                    "member_can_change_billing_plan",
                    {
                        "actor": "beacon_member",
                        "method": "PATCH",
                        "path": f"/api/orgs/{refs['BEACON_ORG_ID']}/settings/plan",
                        "body": {"plan": "starter"},
                    },
                    {"attacker_actor": "beacon_member", "required_role": "admin"},
                    "A non-admin organization member can change paid billing-plan settings.",
                )
            ]
        }

    if task_id == "bill_bfla_member_reads_plan_settings":
        return {
            "findings": [
                _finding(
                    "member_can_read_billing_plan_settings",
                    {
                        "actor": "atlas_member",
                        "method": "GET",
                        "path": f"/api/orgs/{refs['ATLAS_ORG_ID']}/settings/plan",
                    },
                    {"attacker_actor": "atlas_member", "required_role": "admin"},
                    "A non-admin organization member can read billing-plan settings and billing contact data.",
                )
            ]
        }

    if task_id == "sup_bola_acme_reads_orbit_ticket":
        return {
            "findings": [
                _finding(
                    "cross_org_ticket_read",
                    {
                        "actor": "acme_agent",
                        "method": "GET",
                        "path": f"/api/tickets/{refs['ORBIT_TICKET_ID']}",
                    },
                    {"attacker_actor": "acme_agent", "victim_org": "orbit"},
                    "An Acme support agent can read Orbit's private support ticket.",
                )
            ]
        }

    if task_id == "sup_bfla_viewer_closes_ticket":
        return {
            "findings": [
                _finding(
                    "viewer_can_close_ticket",
                    {
                        "actor": "acme_viewer",
                        "method": "PATCH",
                        "path": f"/api/orgs/{refs['ACME_ORG_ID']}/tickets/{refs['ACME_TICKET_ID']}/status",
                        "body": {"status": "closed"},
                    },
                    {"attacker_actor": "acme_viewer", "required_role": "agent"},
                    "A read-only support viewer can close a support ticket through the non-secure route.",
                )
            ]
        }

    if task_id == "sup_invite_agent_creates_admin_invite":
        return {
            "findings": [
                _finding(
                    "agent_can_create_admin_invite",
                    {
                        "actor": "acme_agent",
                        "method": "POST",
                        "path": f"/api/orgs/{refs['ACME_ORG_ID']}/invites",
                        "body": {"email": "new-admin@example.test", "role": "admin"},
                    },
                    {"attacker_actor": "acme_agent", "required_role": "admin"},
                    "A non-admin support agent can create an admin invite.",
                )
            ]
        }

    if task_id == "fs_bola_northstar_reads_apex_file":
        return {
            "findings": [
                _finding(
                    "cross_workspace_file_read",
                    {
                        "actor": "northstar_viewer",
                        "method": "GET",
                        "path": f"/api/files/{refs['APEX_PRIVATE_FILE_ID']}",
                    },
                    {"attacker_actor": "northstar_viewer", "victim_workspace": "apex"},
                    "A Northstar viewer can read Apex private file contents.",
                )
            ]
        }

    if task_id == "fs_stale_expired_share_link_access":
        return {
            "findings": [
                _finding(
                    "expired_share_link_still_resolves",
                    {
                        "actor": "northstar_viewer",
                        "method": "GET",
                        "path": f"/api/share-links/{refs['EXPIRED_LINK_ID']}",
                    },
                    {"attacker_actor": "northstar_viewer", "required_link_state": "active"},
                    "An expired public share link still returns protected file contents.",
                )
            ]
        }

    if task_id == "fs_bfla_viewer_creates_public_link":
        return {
            "findings": [
                _finding(
                    "viewer_can_create_public_share_link",
                    {
                        "actor": "northstar_viewer",
                        "method": "POST",
                        "path": f"/api/workspaces/{refs['NORTHSTAR_WORKSPACE_ID']}/files/{refs['NORTHSTAR_SECRET_FILE_ID']}/share-links",
                        "body": {"visibility": "public"},
                    },
                    {"attacker_actor": "northstar_viewer", "required_role": "editor"},
                    "A read-only viewer can create a public share link for a confidential file.",
                )
            ]
        }

    return {"findings": []}


def main() -> int:
    context_path = Path(os.environ["AUTHZBENCH_CONTEXT"])
    submission_path = Path(os.environ["AUTHZBENCH_SUBMISSION"])
    context = json.loads(context_path.read_text(encoding="utf-8"))
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    submission_path.write_text(json.dumps(solve(context), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
