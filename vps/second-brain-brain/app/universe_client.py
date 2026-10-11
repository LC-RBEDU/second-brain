"""Read-only Universe HTTP client for prepare_meeting (R18) — new module."""
from __future__ import annotations

import os
from typing import Any


def configured(env: dict | None = None) -> bool:
    env = env if env is not None else dict(os.environ)
    return bool(
        (env.get("UNIVERSE_API_BASE") or env.get("RB_UNIVERSE_API_BASE") or "").strip()
        and (env.get("UNIVERSE_API_TOKEN") or env.get("RB_UNIVERSE_API_TOKEN") or "").strip()
    )


def fetch_context(query: str, *, env: dict | None = None) -> dict[str, Any]:
    env = env if env is not None else dict(os.environ)
    if not configured(env):
        return {"ok": False, "degraded": True, "reason": "universe_env_missing", "data": {}}
    _ = query
    # Env present but meeting-context API not wired — explicit degrade (no fake healthz OK).
    return {
        "ok": False,
        "degraded": True,
        "reason": "universe_api_not_wired",
        "data": {},
    }
