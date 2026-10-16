"""toggle_step — micro checkbox on a task file. A story points at the child task."""
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
from hierarchy import is_story, parse_parent_id  # noqa: E402
from promoted_alias import load_applied_at  # noqa: E402
from task_io import parse_task_text  # noqa: E402

from app.errors import BrainClientError
from app.tools.task_catalog import load_tasks
from app.vault_deps import brain_vault

_BOX = re.compile(r"^(?P<prefix>\s*-\s+\[)(?P<mark>[ xX])(?P<rest>\]\s+\*\*[^*]+\*\*.*)$")
_TERMINAL = frozenset({"Done", "Cancelled"})


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


def toggle_step(
    *,
    path: str,
    step_id: str,
    checked: bool,
    source: str | None = None,
    reason: str | None = None,
    dry_run: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    src, why = _require_provenance(source, reason)
    mode = "read" if dry_run else "mutate"
    with brain_vault(mode=mode, env=env) as vault:
        if mode == "mutate":
            delete_context_tombstone(vault)
        try:
            text, meta = vault.read_text(path)
        except DriveNotFoundError as exc:
            raise BrainClientError(message="not_found", status_code=404, error_reason="not_found") from exc
        parsed = parse_task_text(text, rel_path=path, meta=meta)
        if load_applied_at(vault) is not None and is_story(parsed):
            tasks = load_tasks(vault)
            story_id = str(parsed.frontmatter.get("id") or "")
            child_ids = [
                str(item.frontmatter.get("id") or "")
                for item in tasks
                if parse_parent_id(item.frontmatter.get("parent")) == story_id
            ]
            raise BrainClientError(
                message="work is a child task; use update_task. children=" + ",".join(child_ids),
                status_code=409,
                error_reason="story_step_is_child_task",
                detail={"children": child_ids},
            )
        status = str(parsed.frontmatter.get("status") or "")
        if status in _TERMINAL:
            raise BrainClientError(message="task_terminal", status_code=409, error_reason="task_terminal")
        lines = text.splitlines(keepends=True)
        hits = [i for i, line in enumerate(lines) if f"**{step_id}**" in line and _BOX.match(line.rstrip("\n"))]
        if len(hits) != 1:
            raise BrainClientError(message="step_not_found", status_code=404, error_reason="step_not_found")
        index = hits[0]
        matched = _BOX.match(lines[index].rstrip("\n"))
        assert matched is not None
        mark = "x" if checked else " "
        if matched.group("mark").lower() == ("x" if checked else " "):
            return {"path": path, "step_id": step_id, "checked": checked, "changed": False}
        new_line = f"{matched.group('prefix')}{mark}{matched.group('rest')}\n"
        lines[index] = new_line
        now = datetime.now(ZoneInfo("Europe/Prague")).strftime("%Y-%m-%d %H:%M")
        lines.append(f"- {now} · {src} · {why}\n")
        new_text = "".join(lines)
        if dry_run:
            return {"path": path, "step_id": step_id, "checked": checked, "dry_run": True, "written": False}
        meta2 = vault.write_text(path, new_text)
        return {
            "path": path,
            "step_id": step_id,
            "checked": checked,
            "changed": True,
            "oid": getattr(meta2, "oid", None),
        }
