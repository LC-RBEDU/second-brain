"""Drive read for meeting prep attachments (R18 / A29) — SA or OAuth."""
from __future__ import annotations

import os
from typing import Any


def configured(env: dict | None = None) -> bool:
    env = env if env is not None else dict(os.environ)
    sa = (env.get("GOOGLE_DRIVE_SA_JSON") or env.get("DRIVE_SA_JSON") or "").strip()
    oauth = (env.get("GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN") or "").strip()
    return bool(sa or oauth)


def list_event_attachments(event_id: str, *, env: dict | None = None) -> dict[str, Any]:
    env = env if env is not None else dict(os.environ)
    if not configured(env):
        return {
            "ok": False,
            "degraded": True,
            "reason": "drive_env_missing",
            "attachments": [],
        }
    _ = event_id
    # Credentials present but Drive API not wired yet — explicit degrade (no silent OK).
    return {
        "ok": False,
        "degraded": True,
        "reason": "drive_api_not_wired",
        "attachments": [],
    }
