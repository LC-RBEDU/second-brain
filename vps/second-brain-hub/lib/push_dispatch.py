"""OS push → Slack/chat fallback (R5 / B18). F3: OS often unavailable."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PushResult:
    ok: bool
    channel: str
    detail: str = ""
    b18: str = "FAIL"


def dispatch_proactivity(
    message: str,
    *,
    dry_run: bool = False,
    prefer_os: bool = True,
) -> PushResult:
    """Try native OS (not available from VPS) → fallback Slack/chat/log."""
    _ = prefer_os
    if dry_run:
        return PushResult(ok=True, channel="dry-run", detail="no send", b18="SKIP")
    # Brain/hub on Coolify cannot push to Mac/iPhone OS notifications.
    return PushResult(
        ok=False,
        channel="fallback_log",
        detail=f"os_push_unavailable; would notify: {message[:200]}",
        b18="FAIL",
    )


def as_dict(result: PushResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "channel": result.channel,
        "detail": result.detail,
        "b18": result.b18,
        "fallback": ["slack_dm", "chat"],
    }
