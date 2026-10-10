"""set_focus — always deny (B6); focus is human-owned."""
from __future__ import annotations

from typing import Any

from app.errors import BrainClientError
from app.policy import deny_focus_write


def set_focus(*_a: Any, **_k: Any) -> dict[str, Any]:
    d = deny_focus_write()
    raise BrainClientError(
        message=d.reason,
        status_code=403,
        error_reason="policy_denied",
    )
