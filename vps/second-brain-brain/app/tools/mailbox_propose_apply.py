"""mailbox propose + apply gate (R4 / R10 / R17) — apply never mutates in F3."""
from __future__ import annotations

from typing import Any

from app.auth_apply import gate_brain_apply
from app.auth_service import ServicePrincipal
from app.batch_store import create_batch, get_batch
from app.errors import BrainClientError


def mailbox_propose(
    items: list[dict[str, Any]],
    *,
    principal: ServicePrincipal | str = "",
) -> dict[str, Any]:
    if not items:
        raise BrainClientError(message="items required", status_code=400)
    for raw in items:
        label = str(
            (raw.get("payload") or {}).get("label")
            or raw.get("label")
            or "INBOX"
        ).upper()
        if label != "INBOX":
            raise BrainClientError(
                message="L2 mailbox propose only on Inbox",
                status_code=400,
                error_reason="l2_sent_forbidden",
            )
    batch = create_batch("mailbox", items, principal=str(principal))
    return {
        "batch_id": batch.batch_id,
        "kind": "mailbox",
        "items": [
            {
                "id": i.id,
                "action": i.action,
                "reversible": i.reversible,
            }
            for i in batch.items
        ],
        "mutated": False,
    }


def mailbox_apply(
    batch_id: str,
    ids: list[str] | None = None,
    *,
    principal: ServicePrincipal | str,
) -> dict[str, Any]:
    gate_brain_apply(principal)
    # unreachable if gate raises — keep for type checkers
    batch = get_batch(batch_id)
    if batch is None:
        raise BrainClientError(
            message="batch not found or expired",
            status_code=404,
            error_reason="batch_not_found",
        )
    _ = ids
    return {"ok": False, "mutated": False}
