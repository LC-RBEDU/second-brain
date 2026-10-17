"""MCP tool surface — same vault tools as REST; errors → isError text (A57)."""
from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from app.errors import BrainClientError, BrainVaultError
from app.tools import allocate_task_id as allocate_tool
from app.tools import bulk_update as bulk_update_tool
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
from app.tools import close_task as close_task_tool
from app.tools import edit_task_body as edit_task_body_tool
from app.tools import find_tasks as find_tasks_tool
from app.tools import focus_proposal as focus_proposal_tool
from app.tools import get_task as get_task_tool
from app.tools import task_tree as task_tree_tool
from app.tools import toggle_step as toggle_step_tool


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
            "External/mailbox mutate: propose here, then client apply (1×/2× UX). "
            "Focus: propose_focus, then apply_focus after a yes. set_focus does not write."
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
        description=(
            "Patch task frontmatter (CAS expect_oid). Focus is refused: use "
            "propose_focus then apply_focus. parent and type in the patch follow "
            "the same parent rules as create. A deadline that would put a parent "
            "before an open descendant returns deadline_order."
        )
    )
    def update_task(
        path: str,
        patch_json: str,
        expect_oid: str | None = None,
        allow_parent_shift: bool = False,
        dry_run: bool = False,
    ) -> str:
        patch = json.loads(patch_json) if isinstance(patch_json, str) else patch_json
        return _call(
            update_task_tool.update_task,
            path=path,
            patch=patch,
            expect_oid=expect_oid,
            allow_parent_shift=allow_parent_shift,
            dry_run=dry_run,
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
        dry_run: bool = False,
    ) -> str:
        return _call(
            append_task_note_tool.append_task_note,
            path=path,
            text=text,
            target=target,
            expect_oid=expect_oid,
            dry_run=dry_run,
        )

    @mcp.tool(
        description=(
            "Does not write focus. Returns focus_requires_proposal. "
            "Call propose_focus, then apply_focus after an explicit yes. "
            "Cap is 10 tasks/stories and 5 epics."
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

    @mcp.tool(
        description=(
            "Store a focus proposal. Nothing is written until apply_focus. "
            "focus_week empty clears focus. Cap 10 tasks/stories and 5 epics."
        )
    )
    def propose_focus(
        task_path: str,
        focus_week: str = "",
        expect_oid: str | None = None,
    ) -> str:
        return _call(
            focus_proposal_tool.propose_focus,
            task_path=task_path,
            focus_week=focus_week,
            expect_oid=expect_oid,
        )

    @mcp.tool(description="Write a previously proposed focus. Second call is not found.")
    def apply_focus(proposal_id: str) -> str:
        return _call(focus_proposal_tool.apply_focus, proposal_id=proposal_id)

    @mcp.tool(description="Find task files by title, body, id, project, type, parent, status, deadline, or focus.")
    def find_tasks(
        query: str | None = None,
        task_id: str | None = None,
        project: str | None = None,
        work_type: str | None = None,
        parent: str | None = None,
        status_csv: str | None = None,
        limit: int = 20,
    ) -> str:
        status = [item.strip() for item in status_csv.split(",")] if status_csv else None
        return _call(
            find_tasks_tool.find_tasks,
            query=query,
            task_id=task_id,
            project=project,
            work_type=work_type,
            parent=parent,
            status=status,
            limit=limit,
        )

    @mcp.tool(description="Read one task by file id or by an old checkbox id inside the 90-day alias window.")
    def get_task(task_id: str) -> str:
        return _call(get_task_tool.get_task, task_id=task_id)

    @mcp.tool(description="Children of an epic or story: id, title, status, deadline, project. project is the folder slug of the file.")
    def list_children(task_id: str) -> str:
        return _call(task_tree_tool.list_children, task_id=task_id)

    @mcp.tool(description="Tree under an epic or story, with open-descendant counts. project on each node is the folder slug of the file.")
    def get_tree(task_id: str) -> str:
        return _call(task_tree_tool.get_tree, task_id=task_id)

    @mcp.tool(
        description=(
            "Edit one body line (replace, delete_line, insert_after). "
            "Does not change frontmatter. Writes only when confirm is true and expected_hash matches. "
            "source and reason are required."
        )
    )
    def edit_task_body(
        path: str,
        operation: str,
        match: str,
        new_text: str = "",
        expected_hash: str | None = None,
        expect_oid: str | None = None,
        confirm: bool = False,
        dry_run: bool = False,
        allow_migration_trace: bool = False,
        source: str = "",
        reason: str = "",
    ) -> str:
        return _call(
            edit_task_body_tool.edit_task_body,
            path=path,
            operation=operation,
            match=match,
            new_text=new_text,
            expected_hash=expected_hash,
            expect_oid=expect_oid,
            confirm=confirm,
            dry_run=dry_run,
            allow_migration_trace=allow_migration_trace,
            source=source,
            reason=reason,
        )

    @mcp.tool(description="Check or uncheck a micro-step on a task file. A story returns the child task ids.")
    def toggle_step(
        path: str,
        step_id: str,
        checked: bool = True,
        source: str = "",
        reason: str = "",
        dry_run: bool = False,
    ) -> str:
        return _call(
            toggle_step_tool.toggle_step,
            path=path,
            step_id=step_id,
            checked=checked,
            source=source,
            reason=reason,
            dry_run=dry_run,
        )

    @mcp.tool(
        description=(
            "Close one task file as done or cancelled. Does not close the parent story. "
            "The result includes suggest_close_parent."
        )
    )
    def close_task(
        path: str,
        resolution: str = "done",
        note: str = "",
        source: str = "",
        reason: str = "",
        dry_run: bool = False,
    ) -> str:
        return _call(
            close_task_tool.close_task,
            path=path,
            resolution=resolution,
            note=note,
            source=source,
            reason=reason,
            dry_run=dry_run,
        )

    @mcp.tool(description="Preview next task ID (non-reserving).")
    def allocate_task_id(slug: str, level: str | None = None) -> str:
        return _call(allocate_tool.allocate_task_id, slug=slug, level=level)

    @mcp.tool(description="Create a task file. A story needs an epic parent. A task may have no parent, or a story parent in any project. An unknown project slug is refused. dry_run returns ids and writes nothing. items_json creates several in one call and does not see siblings.")
    def create_task(
        slug: str,
        title: str = "",
        detail: str = "",
        level: str = "story",
        status: str = "Next",
        parent: str = "",
        deadline: str = "",
        review_deadline: str = "",
        promoted_from: str = "",
        dry_run: bool = False,
        items_json: str = "",
    ) -> str:
        items = json.loads(items_json) if items_json else None
        return _call(
            create_task_tool.create_task,
            slug=slug,
            title=title,
            detail=detail,
            level=level,
            status=status,
            parent=parent,
            deadline=deadline,
            review_deadline=review_deadline,
            promoted_from=promoted_from,
            dry_run=dry_run,
            items=items,
        )

    @mcp.tool(
        description=(
            "Patch several tasks in one transaction. parent and type in a patch follow "
            "the same parent rules as create. A deadline_order error writes nothing. "
            "A focus key is refused; use propose_focus."
        )
    )
    def bulk_update(updates_json: str, allow_parent_shift: bool = False, dry_run: bool = False) -> str:
        updates = json.loads(updates_json) if isinstance(updates_json, str) else updates_json
        return _call(
            bulk_update_tool.bulk_update,
            updates=updates,
            allow_parent_shift=allow_parent_shift,
            dry_run=dry_run,
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
