"""propose_focus stores a batch. apply_focus is the only focus write."""
from __future__ import annotations

from typing import Any

from app.batch_store import consume_batch, create_batch, get_batch
from app.errors import BrainClientError
from app.request_principal import get_brain_principal
from app.tools.set_focus import set_focus


def propose_focus(
    *,
    task_path: str,
    focus_week: str = "",
    expect_oid: str | None = None,
    principal: str | None = None,
) -> dict[str, Any]:
    who = principal if principal is not None else str(get_brain_principal() or "")
    batch = create_batch(
        "focus",
        [
            {
                "id": "focus",
                "action": "set_focus",
                "payload": {
                    "task_path": task_path,
                    "focus_week": focus_week,
                    "expect_oid": expect_oid,
                },
            }
        ],
        principal=who,
    )
    return {"proposal_id": batch.batch_id, "written": False}


def apply_focus(
    *,
    proposal_id: str,
    principal: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    batch = get_batch(proposal_id)
    if batch is None or batch.kind != "focus" or not batch.items:
        raise BrainClientError(
            message="focus proposal not found",
            status_code=404,
            error_reason="not_found",
        )
    payload = batch.items[0].payload
    result = set_focus(
        task_path=str(payload.get("task_path") or ""),
        focus_week=str(payload.get("focus_week") or ""),
        expect_oid=payload.get("expect_oid"),
        principal=principal,
        env=env,
        via_apply=True,
    )
    consume_batch(proposal_id)
    result["proposal_id"] = proposal_id
    return result
