"""set_focus — set or clear task focus (ISO week) for authenticated callers."""
from __future__ import annotations

import os
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
from drive_io import DriveConflictError, DriveNotFoundError  # noqa: E402
from focus import (  # noqa: E402
    FOCUS_EPIC_LIMIT,
    FOCUS_TASK_LIMIT,
    current_focus_week,
    is_focus_current,
    parse_focus,
)
from task_io import FRONTMATTER_RE, iter_active_tasks, parse_task_text  # noqa: E402
from today_priority import (  # noqa: E402
    count_focus_epic_slots,
    count_focus_slots,
    paused_project_slugs,
    would_consume_epic_focus_slot,
    would_consume_focus_slot,
)

from app.auth_service import ServicePrincipal
from app.errors import BrainClientError
from app.policy import allow_focus_write
from app.request_principal import get_brain_principal
from app.vault_deps import brain_vault

_TASK_PATH_RE = re.compile(r"^02-PROJEKTY/[^/]+/tasks/[^/]+\.md$")
_NULLISH = frozenset({"", "null", "none", "~"})


def _prague_today(env: dict[str, str] | None = None) -> Any:
    env_map = env if env is not None else os.environ
    tz = ZoneInfo((env_map.get("TZ") or "Europe/Prague").strip() or "Europe/Prague")
    return datetime.now(tz).date()


def _paused_slugs_from_vault(vault: Any) -> set[str]:
    """Hub frontmatter status paused → slug set (same idea as agent_context_build)."""
    projects: list[dict[str, Any]] = []
    try:
        metas = vault.list_dir("02-PROJEKTY", pattern="*.md", recursive=False)
    except DriveNotFoundError:
        return set()
    for meta in metas:
        name = getattr(meta, "name", "") or ""
        if name.startswith("_") or "/" in name:
            continue
        try:
            text, _ = vault.read_text(meta.rel_path)
        except DriveNotFoundError:
            continue
        m = FRONTMATTER_RE.match(text)
        if not m:
            continue
        try:
            import yaml

            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            fm = {}
        if not isinstance(fm, dict):
            continue
        if str(fm.get("type") or "") != "project":
            continue
        slug = str(fm.get("slug") or Path(name).stem)
        projects.append({"slug": slug, "status": fm.get("status")})
    return paused_project_slugs(projects)


def _patch_focus_fm(text: str, *, focus_val: str, updated: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise BrainClientError(message="no frontmatter", status_code=400)
    fm_raw, body = m.group(1), m.group(2)
    lines = fm_raw.splitlines(keepends=True)
    keys_done: set[str] = set()
    new_lines: list[str] = []
    patch = {"focus": focus_val, "updated": updated}
    for line in lines:
        if ":" in line and not line.strip().startswith("#"):
            key = line.split(":", 1)[0].strip()
            if key in patch:
                val = patch[key]
                new_lines.append(f"{key}: {val}\n")
                keys_done.add(key)
                continue
        new_lines.append(line if line.endswith("\n") else line + "\n")
    for key, val in patch.items():
        if key not in keys_done:
            new_lines.append(f"{key}: {val}\n")
    return "---\n" + "".join(new_lines) + "---\n" + body


def set_focus(
    *,
    task_path: str = "",
    focus_week: str = "",
    expect_oid: str | None = None,
    principal: ServicePrincipal | str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    today = _prague_today(env)
    principal = principal if principal is not None else get_brain_principal()
    decision = allow_focus_write(principal)
    if not decision.allowed:
        raise BrainClientError(
            message=decision.reason or "focus_write_auth_required",
            status_code=403,
            error_reason="policy_denied",
        )

    path = (task_path or "").strip()
    if not path or not _TASK_PATH_RE.match(path):
        raise BrainClientError(
            message="task_path must be under 02-PROJEKTY/<slug>/tasks/*.md",
            status_code=400,
            error_reason="invalid_task_path",
        )

    raw_week = (focus_week or "").strip()
    clear = raw_week.lower() in _NULLISH
    if clear:
        target_week = ""
    else:
        parsed = parse_focus(raw_week)
        if parsed is None:
            raise BrainClientError(
                message="invalid_focus_week",
                status_code=400,
                error_reason="invalid_focus_week",
            )
        cur = current_focus_week(today)
        if parsed != cur:
            raise BrainClientError(
                message=f"focus_week_not_current want={cur!r} got={parsed!r}",
                status_code=400,
                error_reason="focus_week_not_current",
            )
        target_week = parsed

    with brain_vault(mode="mutate", env=env) as vault:
        delete_context_tombstone(vault)
        try:
            text, meta = vault.read_text(path)
        except DriveNotFoundError as exc:
            raise BrainClientError(
                message=f"task_not_found: {path}",
                status_code=404,
                error_reason="not_found",
            ) from exc

        oid = getattr(meta, "oid", None)
        if expect_oid is not None and oid is not None and str(oid) != str(expect_oid):
            raise BrainClientError(
                message=f"CAS conflict expect_oid={expect_oid!r} got={oid!r}",
                status_code=409,
                error_reason="cas_conflict",
            )

        parsed_task = parse_task_text(text, rel_path=path, meta=meta)
        already = is_focus_current(parsed_task.frontmatter.get("focus"), today)

        if not clear and not already:
            paused = _paused_slugs_from_vault(vault)
            active = list(iter_active_tasks(vault))
            if would_consume_focus_slot(parsed_task, paused):
                others = count_focus_slots(
                    active,
                    today,
                    paused_slugs=paused,
                    exclude_path=path,
                )
                if others >= FOCUS_TASK_LIMIT:
                    raise BrainClientError(
                        message=(
                            f"focus_task_limit_exceeded count={others} "
                            f"limit={FOCUS_TASK_LIMIT}"
                        ),
                        status_code=403,
                        error_reason="focus_limit_exceeded",
                    )
            elif would_consume_epic_focus_slot(parsed_task, paused):
                others_e = count_focus_epic_slots(
                    active,
                    today,
                    paused_slugs=paused,
                    exclude_path=path,
                )
                if others_e >= FOCUS_EPIC_LIMIT:
                    raise BrainClientError(
                        message=(
                            f"focus_epic_limit_exceeded count={others_e} "
                            f"limit={FOCUS_EPIC_LIMIT}"
                        ),
                        status_code=403,
                        error_reason="focus_epic_limit_exceeded",
                    )

        updated = today.isoformat()
        new_text = _patch_focus_fm(text, focus_val=target_week, updated=updated)
        try:
            kwargs: dict[str, Any] = {}
            if expect_oid is not None:
                kwargs["expect_oid"] = expect_oid
            meta2 = vault.write_text(path, new_text, **kwargs)
        except DriveConflictError as exc:
            raise BrainClientError(
                message=str(exc),
                status_code=409,
                error_reason="cas_conflict",
            ) from exc

        # Re-count after write (include target)
        paused = _paused_slugs_from_vault(vault)
        active_after = list(iter_active_tasks(vault))
        focus_count = count_focus_slots(active_after, today, paused_slugs=paused)
        focus_epic_count = count_focus_epic_slots(
            active_after, today, paused_slugs=paused
        )

    focus_out = parse_focus(target_week) if target_week else None
    return {
        "path": path,
        "focus": focus_out,
        "focus_week": target_week,
        "cleared": clear,
        "oid": getattr(meta2, "oid", None),
        "focus_count": focus_count,
        "focus_limit": FOCUS_TASK_LIMIT,
        "focus_epic_count": focus_epic_count,
        "focus_epic_limit": FOCUS_EPIC_LIMIT,
        "already_in_focus": already,
    }
