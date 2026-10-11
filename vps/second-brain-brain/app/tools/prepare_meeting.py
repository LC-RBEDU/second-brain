"""prepare_meeting — SSOT Meeting-Preps + optional Grok deliver (R14)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import date
from typing import Any

from app import drive_client, universe_client
from app.errors import BrainClientError
from app.vault_deps import brain_vault

PREPS_DIR = "00-System/Meeting-Preps"


def _path_for(event_id: str, day: str | None = None) -> str:
    d = day or date.today().isoformat()
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in event_id)[:80]
    return f"{PREPS_DIR}/{safe}-{d}.md"


def _send_grok(brief: str, event_id: str, *, env: dict) -> dict[str, Any]:
    url = (env.get("GROK_BOT_MEETING_PREP_WEBHOOK_URL") or "").strip()
    key = (env.get("GROK_BOT_MEETING_PREP_WEBHOOK_KEY") or "").strip()
    if not url or not key:
        return {"ok": False, "detail": "meeting_prep_webhook_missing"}
    body = json.dumps(
        {"task": brief[:8000], "request_id": event_id, "source": "meeting_prep"}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
        return {"ok": 200 <= int(code) < 300, "detail": f"http_{code}"}
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"ok": False, "detail": str(exc)}


def prepare_meeting(
    event_id: str,
    *,
    title: str = "",
    starts_at: str = "",
    force: bool = False,
    deliver: bool = True,
    dry_run: bool = False,
    env: dict | None = None,
) -> dict[str, Any]:
    event_id = (event_id or "").strip()
    if not event_id:
        raise BrainClientError(message="event_id required", status_code=400)
    env = env if env is not None else dict(os.environ)
    day = (starts_at or "")[:10] or date.today().isoformat()
    rel = _path_for(event_id, day)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "path": rel,
            "would_prepare": True,
            "would_deliver": deliver,
            "written": False,
            "delivered": False,
        }

    uni = universe_client.fetch_context(title or event_id, env=env)
    drv = drive_client.list_event_attachments(event_id, env=env)
    degraded = []
    if uni.get("degraded"):
        degraded.append("universe")
    if drv.get("degraded"):
        degraded.append("drive")

    body = (
        f"# Meeting prep — {title or event_id}\n\n"
        f"**event_id**: {event_id}\n"
        f"**starts_at**: {starts_at or '—'}\n"
        f"**degraded**: {', '.join(degraded) or 'none'}\n\n"
        f"## Universe\n\n```json\n{json.dumps(uni.get('data') or {}, ensure_ascii=False)[:2000]}\n```\n\n"
        f"## Drive attachments\n\n"
        f"{len(drv.get('attachments') or [])} item(s)\n"
    )

    with brain_vault(mode="mutate", env=env) as vault:
        vault.mkdir_p(PREPS_DIR)
        if vault.exists(rel) and not force:
            return {
                "ok": True,
                "path": rel,
                "skipped": True,
                "written": False,
                "degraded": degraded,
            }
        vault.write_text(rel, body)

    deliver_result = None
    if deliver:
        deliver_result = _send_grok(body, event_id, env=env)

    return {
        "ok": True,
        "path": rel,
        "skipped": False,
        "written": True,
        "degraded": degraded,
        "degraded_flag": bool(degraded),
        "deliver": deliver_result,
    }


def get_meeting_prep(event_id: str, *, day: str | None = None, env: dict | None = None) -> dict[str, Any]:
    env = env if env is not None else dict(os.environ)
    rel = _path_for(event_id, day)
    with brain_vault(mode="read", env=env) as vault:
        if not vault.exists(rel):
            return {"ok": False, "path": rel, "exists": False}
        text, meta = vault.read_text(rel)
        return {
            "ok": True,
            "path": rel,
            "exists": True,
            "content": text,
            "oid": getattr(meta, "oid", None),
        }
