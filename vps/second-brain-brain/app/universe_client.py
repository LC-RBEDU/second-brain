"""Read-only Universe HTTP client for prepare_meeting (R18) — new module."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
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
    base = (env.get("UNIVERSE_API_BASE") or env.get("RB_UNIVERSE_API_BASE") or "").rstrip("/")
    token = (env.get("UNIVERSE_API_TOKEN") or env.get("RB_UNIVERSE_API_TOKEN") or "").strip()
    # Minimal read probe — full search wiring can expand; avoid inventing private APIs.
    _ = query
    url = f"{base}/healthz"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {"raw": body[:500]}
        return {"ok": True, "degraded": False, "data": data}
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"ok": False, "degraded": True, "reason": str(exc), "data": {}}
