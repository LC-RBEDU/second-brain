"""external (Slack) propose + apply gate (R15 / R17)."""
from __future__ import annotations

from typing import Any

from app.auth_apply import gate_brain_apply
from app.auth_service import ServicePrincipal
from app.batch_store import create_batch, get_batch
from app.errors import BrainClientError


def external_propose(
    items: list[dict[str, Any]],
    *,
    principal: ServicePrincipal | str = "",
) -> dict[str, Any]:
    if not items:
        raise BrainClientError(message="items required", status_code=400)
    normalized: list[dict[str, Any]] = []
    for raw in items:
        item = dict(raw)
        target = (item.get("payload") or {}).get("target") or item.get("target")
        if target and target not in ("dm", "gdm", "channel"):
            raise BrainClientError(
                message="target must be dm|gdm|channel",
                status_code=400,
                error_reason="invalid_target",
            )
        if "reversible" not in item:
            action = str(item.get("action") or "")
            item["reversible"] = action not in ("send", "permanent_delete")
        normalized.append(item)
    batch = create_batch("external", normalized, principal=str(principal))
    return {
        "batch_id": batch.batch_id,
        "kind": "external",
        "items": [
            {
                "id": i.id,
                "action": i.action,
                "reversible": i.reversible,
                "target": (i.payload or {}).get("target"),
            }
            for i in batch.items
        ],
        "mutated": False,
    }


def external_apply(
    batch_id: str,
    ids: list[str] | None = None,
    *,
    principal: ServicePrincipal | str,
) -> dict[str, Any]:
    gate_brain_apply(principal)
    batch = get_batch(batch_id)
    if batch is None:
        raise BrainClientError(
            message="batch not found or expired",
            status_code=404,
            error_reason="batch_not_found",
        )
    _ = ids
    return {"ok": False, "mutated": False}
