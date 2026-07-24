from __future__ import annotations

from typing import Any

from authzbench.core import build_context, resolve_templates


PUBLIC_PILOT_TASKS = {
    "tok_cross_tenant_secret_read": "vulnerable",
    "tok_secure_export_scope_control": "secure_denial",
    "tok_export_token_reads_export_control": "authorized_allow",
}


def public_pilot_behavior(task: dict[str, Any]) -> str:
    task_id = task.get("id")
    try:
        return PUBLIC_PILOT_TASKS[str(task_id)]
    except KeyError as exc:
        raise ValueError(f"task is not admitted to the public Harbor pilot: {task_id}") from exc


def build_public_pilot_reference_submission(task: dict[str, Any]) -> dict[str, Any]:
    """Return the public pilot's deterministic, verifier-replayable Oracle submission.

    This helper is deliberately allowlisted to the three public pilot tasks. It
    must never be used to export private tasks or to imply a generic Oracle for
    the full benchmark.
    """

    behavior = public_pilot_behavior(task)
    context = build_context(task)
    refs = context["refs"]

    if behavior == "vulnerable":
        return {
            "findings": [
                {
                    "claim": "token_cross_tenant_secret_read",
                    "boundary": {
                        "attacker_actor": "meridian_read_token",
                        "victim_tenant": "helio",
                        "required_scope": "secrets:read",
                    },
                    "impact": "A Meridian read token can read Helio tenant secret material.",
                    "evidence": [
                        {
                            "request": {
                                "actor": "meridian_read_token",
                                "method": "GET",
                                "path": f"/api/secrets/{refs['HELIO_SECRET_ID']}",
                            }
                        }
                    ],
                    "out_of_scope_actions": [],
                }
            ]
        }

    controls = resolve_templates(task.get("controls", []), refs)
    if not controls:
        raise ValueError("public Harbor pilot controls must declare a verification request")
    control = controls[0]
    request = {
        key: control[key]
        for key in ("actor", "method", "path", "body")
        if key in control
    }
    return {
        "findings": [],
        "verification": [
            {
                "request": request,
                "expected": {"status": control["status"]},
            }
        ],
    }
