"""schedule_reminder / cancel_reminder / list_reminders (R13 / R28)."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from reminders import (  # noqa: E402
    CANCELLED_DIR,
    PENDING_DIR,
    build_reminder,
    parse_deliver_at,
    slugify_filename,
)

from app.errors import BrainClientError  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402

TZ = ZoneInfo("Europe/Prague")


def schedule_reminder(
    *,
    message: str,
    deliver_at: str,
    task_ref: str | None = None,
    source: str = "brain-api",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    deliver = parse_deliver_at(deliver_at, tz=TZ)
    reminder = build_reminder(
        message=message,
        deliver_at=deliver,
        task_ref=task_ref,
        source=source,
        tz=TZ,
    )
    rel = f"{PENDING_DIR}/{slugify_filename(reminder['id'])}"
    with brain_vault(mode="mutate", env=env) as vault:
        vault.mkdir_p(PENDING_DIR)
        if vault.exists(rel):
            raise BrainClientError(
                message=f"reminder file exists: {rel}",
                status_code=409,
                error_reason="reminder_exists",
            )
        vault.write_text(
            rel,
            json.dumps(reminder, ensure_ascii=False, indent=2) + "\n",
        )
    return {"id": reminder["id"], "deliver_at": reminder["deliver_at"], "path": rel}


def cancel_reminder(
    reminder_id: str,
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    rid = (reminder_id or "").strip()
    if not rid:
        raise BrainClientError(message="reminder id empty", status_code=400)
    cancelled: list[str] = []
    with brain_vault(mode="mutate", env=env) as vault:
        vault.mkdir_p(CANCELLED_DIR)
        try:
            metas = vault.list_dir(PENDING_DIR, pattern="*.json", recursive=False)
        except Exception as exc:
            raise BrainClientError(
                message=f"no pending dir / reminders: {exc}",
                status_code=404,
            ) from exc
        for meta in metas:
            name = getattr(meta, "name", "")
            rel = getattr(meta, "rel_path", f"{PENDING_DIR}/{name}")
            if rid not in name and rid not in rel:
                continue
            text, _ = vault.read_text(rel)
            data = json.loads(text)
            data["status"] = "cancelled"
            data["cancelled_at"] = datetime.now(TZ).isoformat(timespec="seconds")
            dest = f"{CANCELLED_DIR}/{name}"
            vault.write_text(
                dest, json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            )
            vault.delete(rel, permanent=True)
            cancelled.append(str(data.get("id") or rid))
    if not cancelled:
        raise BrainClientError(
            message=f"no pending reminder matching {rid!r}",
            status_code=404,
            error_reason="reminder_not_found",
        )
    return {"cancelled": cancelled}


def list_reminders(*, env: dict[str, str] | None = None) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    with brain_vault(mode="read", env=env) as vault:
        if hasattr(vault, "exists") and not vault.exists(PENDING_DIR):
            return {"reminders": []}
        try:
            metas = vault.list_dir(PENDING_DIR, pattern="*.json", recursive=False)
        except Exception:
            return {"reminders": []}
        for meta in metas:
            rel = getattr(meta, "rel_path", None)
            if not rel:
                continue
            try:
                text, _ = vault.read_text(rel)
                data = json.loads(text)
            except Exception:
                continue
            if str(data.get("status") or "").lower() not in {"pending", "failed"}:
                continue
            items.append(
                {
                    "id": data.get("id"),
                    "deliver_at": data.get("deliver_at"),
                    "message": data.get("message"),
                    "status": data.get("status"),
                    "attempt_count": data.get("attempt_count", 0),
                }
            )
    items.sort(key=lambda r: str(r.get("deliver_at") or ""))
    return {"reminders": items}
