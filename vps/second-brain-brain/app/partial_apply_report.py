"""Shared partial client-apply report shape (A20 / C15 / A36) — not Brain apply."""
from __future__ import annotations

from typing import Any


def normalize_report(
    succeeded: list[Any] | None = None,
    failed: list[Any] | None = None,
) -> dict[str, list]:
    """Return {succeeded: [...], failed: [{id, error_reason}, ...]}."""
    ok: list[Any] = []
    for item in succeeded or []:
        if isinstance(item, dict) and "id" in item:
            ok.append(item["id"])
        else:
            ok.append(item)

    bad: list[dict[str, str]] = []
    for item in failed or []:
        if isinstance(item, dict):
            eid = str(item.get("id") or item.get("item_id") or "")
            reason = str(
                item.get("error_reason") or item.get("error") or item.get("message") or "error"
            )
            if eid:
                bad.append({"id": eid, "error_reason": reason})
        else:
            bad.append({"id": str(item), "error_reason": "error"})

    return {"succeeded": ok, "failed": bad}


def is_all_ok(report: dict[str, list]) -> bool:
    return not (report.get("failed") or [])
