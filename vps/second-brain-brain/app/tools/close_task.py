"""close_task — close one file. The parent story is only suggested, never written."""
from __future__ import annotations

import re
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

from context_tombstone import delete_context_tombstone  # noqa: E402
from drive_io import DriveNotFoundError  # noqa: E402
from hierarchy import is_epic, is_story, parse_parent_id, work_type_of  # noqa: E402
from task_io import open_checkbox_count, parse_task_text  # noqa: E402
from task_query import OPEN_STATUSES, card  # noqa: E402

from app.errors import BrainClientError
from app.tools.task_catalog import load_tasks
from app.vault_deps import brain_vault

_BOX = re.compile(r"^(\s*-\s+\[)[ ](\]\s+)")


def _require_provenance(source: str | None, reason: str | None) -> tuple[str, str]:
    src = (source or "").strip()
    why = (reason or "").strip()
    if not src or not why:
        raise BrainClientError(
            message="source and reason are required",
            status_code=400,
            error_reason="missing_provenance",
        )
    return src, why


def _set_status(text: str, status: str) -> str:
    lines = text.splitlines(keepends=True)
    in_fm = False
    seen = False
    out: list[str] = []
    for i, line in enumerate(lines):
        if i == 0 and line.startswith("---"):
            in_fm = True
            out.append(line)
            continue
        if in_fm and line.strip() == "---":
            if not seen:
                out.append(f"status: {status}\n")
            in_fm = False
            out.append(line)
            continue
        if in_fm and line.split(":", 1)[0].strip() == "status":
            out.append(f"status: {status}\n")
            seen = True
            continue
        if in_fm and line.split(":", 1)[0].strip() == "focus":
            out.append("focus:\n")
            continue
        out.append(line)
    return "".join(out)


def close_task(
    *,
    path: str,
    resolution: str = "done",
    note: str = "",
    source: str | None = None,
    reason: str | None = None,
    dry_run: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    src, why = _require_provenance(source, reason)
    wanted = {"done": "Done", "cancelled": "Cancelled"}.get((resolution or "").strip().lower())
    if wanted is None:
        raise BrainClientError(message="resolution must be done or cancelled", status_code=400, error_reason="bad_resolution")
    mode = "read" if dry_run else "mutate"
    with brain_vault(mode=mode, env=env) as vault:
        if mode == "mutate":
            delete_context_tombstone(vault)
        try:
            text, meta = vault.read_text(path)
        except DriveNotFoundError as exc:
            raise BrainClientError(message="not_found", status_code=404, error_reason="not_found") from exc
        parsed = parse_task_text(text, rel_path=path, meta=meta)
        current = str(parsed.frontmatter.get("status") or "")
        if current == wanted:
            row = card(parsed)
            return {"path": path, "status": wanted, "noop": True, "parent_story": row["parent"], "open_siblings": 0, "suggest_close_parent": False}
        if current in {"Done", "Cancelled"}:
            raise BrainClientError(message="already_terminal", status_code=409, error_reason="already_terminal")
        tasks = load_tasks(vault)
        me = card(parsed)
        open_children = [
            card(item)
            for item in tasks
            if card(item)["parent"] == me["id"] and card(item)["status"] in OPEN_STATUSES
        ]
        if (is_story(parsed) or is_epic(parsed)) and (open_children or open_checkbox_count(parsed.body) > 0):
            raise BrainClientError(
                message="parent_has_open_children",
                status_code=409,
                error_reason="parent_has_open_children",
            )
        siblings = [
            card(item)
            for item in tasks
            if me["parent"] and card(item)["parent"] == me["parent"] and card(item)["id"] != me["id"] and card(item)["status"] in OPEN_STATUSES
        ]
        parent_task = next((item for item in tasks if card(item)["id"] == me["parent"]), None)
        parent_is_story = parent_task is not None and work_type_of(parent_task) == "story"
        parent_open_boxes = open_checkbox_count(parent_task.body) if parent_task is not None else 1
        suggest = bool(
            work_type_of(parsed) == "task"
            and parent_is_story
            and not siblings
            and parent_open_boxes == 0
        )
        lines = text.splitlines(keepends=True)
        seen_close = 0
        rewritten: list[str] = []
        for line in lines:
            if line.strip() == "---":
                seen_close += 1
            if seen_close >= 2:
                rewritten.append(_BOX.sub(r"\1x\2", line))
            else:
                rewritten.append(line)
        now = datetime.now(ZoneInfo("Europe/Prague")).strftime("%Y-%m-%d %H:%M")
        extra = f" {note.strip()}" if note and note.strip() else ""
        rewritten.append(f"- {now} · {src} · {why}{extra}\n")
        new_text = _set_status("".join(rewritten), wanted)
        payload = {
            "path": path,
            "status": wanted,
            "parent_story": me["parent"] if parent_is_story else None,
            "open_siblings": len(siblings),
            "suggest_close_parent": suggest,
            "written": not dry_run,
        }
        if dry_run:
            payload["dry_run"] = True
            return payload
        meta2 = vault.write_text(path, new_text)
        payload["oid"] = getattr(meta2, "oid", None)
        return payload
