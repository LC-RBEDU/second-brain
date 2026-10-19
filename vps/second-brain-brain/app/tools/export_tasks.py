"""export_tasks — read-only vault snapshot. Does not rebuild agent-context."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, NotRequired, TypedDict

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from task_export import export_tasks as build_export  # noqa: E402

from app.errors import BrainClientError
from app.vault_deps import brain_vault

_INVALID = {
    "invalid_include_closed_days": "include_closed_days must be >= 0",
    "invalid_fields": "fields must be standard or full",
    "invalid_since": "since must be an ISO date or datetime",
}


class ExportProject(TypedDict):
    slug: str
    title: str
    status: str
    hierarchy: bool


class ExportTask(TypedDict):
    id: str
    title: str
    type: str
    status: str
    parent: str | None
    project: str
    path: str
    oid: str | None
    deadline: str | None
    review_deadline: str | None
    waitUntil: str | None
    focus: str | None
    agent: str
    ice_i: int | None
    ice_c: int | None
    ice_e: int | None
    priority_score: float | None
    is_recurring: bool
    promoted_from: str | None
    created: str | None
    updated: str | None
    steps_total: int
    steps_done: int
    filename_title_mismatch: bool
    parse_errors: list[str]
    materials: NotRequired[list[str]]
    blocked_by: NotRequired[list[str]]
    company_priorities: NotRequired[list[str]]
    source: NotRequired[Any]


class ExportTasksResult(TypedDict):
    generated_at: str
    vault_head: str | None
    focus_week: str
    count: int
    projects: list[ExportProject]
    tasks: list[ExportTask]


def export_tasks(
    *,
    include_closed_days: int = 0,
    projects_csv: str = "",
    fields: str = "standard",
    since: str | None = None,
    env: dict[str, str] | None = None,
) -> ExportTasksResult:
    with brain_vault(mode="read", env=env) as vault:
        try:
            return build_export(
                vault,
                include_closed_days=include_closed_days,
                projects_csv=projects_csv,
                fields=fields,
                since=since,
            )
        except ValueError as exc:
            code = str(exc)
            if code not in _INVALID:
                raise
            raise BrainClientError(
                message=_INVALID[code],
                status_code=400,
                error_reason=code,
            ) from exc
