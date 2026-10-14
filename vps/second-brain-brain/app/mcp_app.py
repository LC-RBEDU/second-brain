"""MCP tool surface — same vault tools as REST; errors → isError text (A57)."""
from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from app.errors import BrainClientError, BrainVaultError
from app.tools import allocate_task_id as allocate_tool
from app.tools import capture_daily as capture_daily_tool
from app.tools import create_task as create_task_tool
from app.tools import external_propose_apply as external_tool
from app.tools import get_context as get_context_tool
from app.tools import get_triage_candidates as triage_tool
from app.tools import ingest_sembly as ingest_tool
from app.tools import list_dir as list_dir_tool
from app.tools import mailbox_propose_apply as mailbox_tool
from app.tools import prepare_meeting as prepare_tool
from app.tools import read_file as read_file_tool
from app.tools import reminders_tools as reminders_tool
from app.tools import set_focus as set_focus_tool
from app.tools import slack_live as slack_live_tool
from app.tools import update_task as update_task_tool
from app.tools import append_task_note as append_task_note_tool


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
            "Vault errors return JSON {error_reason, message}. "
            "External/mailbox mutate: propose here, then client apply (1×/2× UX)."
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

    @mcp.tool(
        description="Patch task frontmatter (CAS expect_oid); focus key denied — use set_focus."
    )
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

    @mcp.tool(
        description=(
            "Append one bullet to an existing task file. target=log writes into "
            "## Poznámky / log (target note is an alias; matching is case-insensitive; "
            "the result target is log or step). target=step adds the next unchecked "
            "**ID-N** checkbox in ## Operativní kroky. A new step on Done or Cancelled "
            "returns 409 task_terminal. An epic with no operational-steps section returns "
            "400 epic_has_no_steps. Optional expect_oid is the same CAS as update_task. "
            "Does not change status or focus, does not check off existing steps, and does "
            "not write ## Stav (auto) or Definition of done."
        )
    )
    def append_task_note(
        path: str,
        text: str,
        target: str,
        expect_oid: str | None = None,
    ) -> str:
        return _call(
            append_task_note_tool.append_task_note,
            path=path,
            text=text,
            target=target,
            expect_oid=expect_oid,
        )

    @mcp.tool(
        description=(
            "Set or clear task focus (current ISO week or empty). "
            "Max 5 eligible TOP slots. Confirm with the user in chat before calling."
        )
    )
    def set_focus(
        task_path: str = "",
        focus_week: str = "",
        expect_oid: str | None = None,
    ) -> str:
        return _call(
            set_focus_tool.set_focus,
            task_path=task_path,
            focus_week=focus_week,
            expect_oid=expect_oid,
        )

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

    @mcp.tool(description="Ingest Sembly payload → 01-INBOX/sembly MD (no LLM).")
    def ingest_sembly(payload_json: str) -> str:
        payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
        return _call(ingest_tool.ingest_sembly, payload=payload)

    @mcp.tool(description="Capture a daily INBOX note.")
    def capture_daily(text: str, title: str | None = None) -> str:
        return _call(capture_daily_tool.capture_daily, text=text, title=title)

    @mcp.tool(description="Triage L1 candidates (default live Slack + Gmail L1).")
    def get_triage_candidates(
        include_live_slack: bool = True, include_gmail: bool = True
    ) -> str:
        return _call(
            triage_tool.get_triage_candidates,
            include_live_slack=include_live_slack,
            include_gmail=include_gmail,
        )

    @mcp.tool(description="Live Slack search (default L1; does not dump).")
    def slack_live() -> str:
        return _call(slack_live_tool.slack_live_search)

    @mcp.tool(description="Propose mailbox actions (audit batch; 0 mutate).")
    def mailbox_propose(items_json: str) -> str:
        items = json.loads(items_json) if isinstance(items_json, str) else items_json
        return _call(mailbox_tool.mailbox_propose, items=items)

    @mcp.tool(description="Brain mailbox apply — F3 always 403/501; use client apply.")
    def mailbox_apply(batch_id: str, ids_json: str = "[]") -> str:
        ids = json.loads(ids_json) if isinstance(ids_json, str) else ids_json
        # MCP has no principal — treat as service path via error
        from app.auth_service import ServicePrincipal

        return _call(
            mailbox_tool.mailbox_apply,
            batch_id=batch_id,
            ids=ids,
            principal=ServicePrincipal(label="mcp"),
        )

    @mcp.tool(description="Propose external Slack actions (audit batch; 0 mutate).")
    def external_propose(items_json: str) -> str:
        items = json.loads(items_json) if isinstance(items_json, str) else items_json
        return _call(external_tool.external_propose, items=items)

    @mcp.tool(description="Brain external apply — F3 always 403/501; use client apply.")
    def external_apply(batch_id: str, ids_json: str = "[]") -> str:
        ids = json.loads(ids_json) if isinstance(ids_json, str) else ids_json
        from app.auth_service import ServicePrincipal

        return _call(
            external_tool.external_apply,
            batch_id=batch_id,
            ids=ids,
            principal=ServicePrincipal(label="mcp"),
        )

    @mcp.tool(description="Prepare meeting brief SSOT (+ optional Grok deliver).")
    def prepare_meeting(
        event_id: str,
        title: str = "",
        starts_at: str = "",
        force: bool = False,
        deliver: bool = True,
        dry_run: bool = False,
    ) -> str:
        return _call(
            prepare_tool.prepare_meeting,
            event_id=event_id,
            title=title,
            starts_at=starts_at,
            force=force,
            deliver=deliver,
            dry_run=dry_run,
        )

    @mcp.tool(description="Read meeting prep SSOT from vault.")
    def get_meeting_prep(event_id: str, day: str | None = None) -> str:
        return _call(prepare_tool.get_meeting_prep, event_id=event_id, day=day)

    return mcp
