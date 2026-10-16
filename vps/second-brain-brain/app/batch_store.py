"""In-memory propose batch store (R16 / A23 / A27) — process-local, TTL 2h."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any


TTL_SECONDS = 2 * 60 * 60


@dataclass
class BatchItem:
    id: str
    action: str
    reversible: bool
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Batch:
    batch_id: str
    kind: str  # mailbox | external
    items: list[BatchItem]
    created_at: float
    principal: str


_STORE: dict[str, Batch] = {}


def _purge_expired(now: float | None = None) -> None:
    t = now if now is not None else time.time()
    dead = [k for k, b in _STORE.items() if t - b.created_at > TTL_SECONDS]
    for k in dead:
        del _STORE[k]


def create_batch(
    kind: str,
    items: list[dict[str, Any]],
    *,
    principal: str = "",
) -> Batch:
    """items: {id, action, reversible?, payload?}"""
    _purge_expired()
    batch_id = secrets.token_urlsafe(12)
    parsed: list[BatchItem] = []
    for raw in items:
        action = str(raw.get("action") or "")
        rev = raw.get("reversible")
        if rev is None:
            rev = action not in ("send", "permanent_delete", "delete_forever")
        parsed.append(
            BatchItem(
                id=str(raw["id"]),
                action=action,
                reversible=bool(rev),
                payload=dict(raw.get("payload") or {}),
            )
        )
    batch = Batch(
        batch_id=batch_id,
        kind=kind,
        items=parsed,
        created_at=time.time(),
        principal=principal,
    )
    _STORE[batch_id] = batch
    return batch


def get_batch(batch_id: str) -> Batch | None:
    _purge_expired()
    return _STORE.get(batch_id)


def consume_batch(batch_id: str) -> Batch | None:
    _purge_expired()
    return _STORE.pop(batch_id, None)


def clear_for_tests() -> None:
    _STORE.clear()
