"""MCP tool surface — same vault tools as REST; errors → isError text (A57)."""
from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from app.errors import BrainClientError, BrainVaultError
from app.tools import allocate_task_id as allocate_tool
from app.tools import create_task as create_task_tool
from app.tools import get_context as get_context_tool
from app.tools import list_dir as list_dir_tool
from app.tools import read_file as read_file_tool
from app.tools import reminders_tools as reminders_tool
from app.tools import set_focus as set_focus_tool
from app.tools import update_task as update_task_tool


def _err_text(exc: BaseException) -> str:
    if isinstance(exc, (BrainVaultError, BrainClientError)):
        return json.dumps(exc.as_dict(), ensure_ascii=False)
    return str(exc)


def _call(fn, **kwargs: Any) -> str:
    try:
        result = fn(**kwargs)
        return json.dumps(result, ensure_ascii=False, default=str)
    except (BrainVaultError, BrainClientError) as exc:
        # MCPServer wraps Exception → CallToolResult(is_error=True, text=str(exc))
        raise RuntimeError(_err_text(exc)) from exc


def build_mcp() -> MCPServer:
    mcp = MCPServer(
        name="second-brain-brain",
        instructions=(
            "Second Brain vault tools. Mutate requires OAuth (human) or service token. "
            "Vault errors return JSON {error_reason, message}."
        ),
    )

    @mcp.tool(description="Warm or rebuild agent-context snapshot (TTL 15 min).")
    def get_context() -> str:
        return _call(get_context_tool.get_context)

    @mcp.tool(description="Read allowlisted vault file.")
    def read_file(path: str) -> str:
        return _call(read_file_tool.read_file, rel_path=path)

    @mcp.tool(description="List allowlisted vault directory.")
    def list_dir(path: str, pattern: str | None = None, recursive: bool = False) -> str:
        return _call(
            list_dir_tool.list_dir,
            rel_path=path,
            pattern=pattern,
            recursive=recursive,
        )

    @mcp.tool(description="Patch task frontmatter (CAS expect_oid); focus denied.")
    def update_task(
        path: str, patch_json: str, expect_oid: str | None = None
    ) -> str:
        patch = json.loads(patch_json) if isinstance(patch_json, str) else patch_json
        return _call(
            update_task_tool.update_task,
            path=path,
            patch=patch,
            expect_oid=expect_oid,
        )

    @mcp.tool(description="Denied — focus is human-owned (B6).")
    def set_focus(task_path: str = "", focus_week: str = "") -> str:
        return _call(set_focus_tool.set_focus, task_path=task_path, focus_week=focus_week)

    @mcp.tool(description="Preview next task ID (non-reserving).")
    def allocate_task_id(slug: str, level: str | None = None) -> str:
        return _call(allocate_tool.allocate_task_id, slug=slug, level=level)

    @mcp.tool(description="Create task file under 02-PROJEKTY/<slug>/tasks/.")
    def create_task(
        slug: str,
        title: str,
        detail: str = "",
        level: str = "story",
        status: str = "Next",
    ) -> str:
        return _call(
            create_task_tool.create_task,
            slug=slug,
            title=title,
            detail=detail,
            level=level,
            status=status,
        )

    @mcp.tool(description="Schedule reminder (attempt_count=0) into Reminders-Pending.")
    def schedule_reminder(
        message: str, deliver_at: str, task_ref: str | None = None
    ) -> str:
        return _call(
            reminders_tool.schedule_reminder,
            message=message,
            deliver_at=deliver_at,
            task_ref=task_ref,
        )

    @mcp.tool(description="List pending/failed reminders.")
    def list_reminders() -> str:
        return _call(reminders_tool.list_reminders)

    @mcp.tool(description="Cancel a pending reminder by id substring.")
    def cancel_reminder(reminder_id: str) -> str:
        return _call(reminders_tool.cancel_reminder, reminder_id=reminder_id)

    @mcp.tool(description="F3 stub — not available in F2.")
    def f3_stub(name: str = "unknown") -> str:
        raise RuntimeError(
            json.dumps(
                {"error_reason": "f3_stub", "message": f"F3 tool {name!r} — not in F2"}
            )
        )

    return mcp
