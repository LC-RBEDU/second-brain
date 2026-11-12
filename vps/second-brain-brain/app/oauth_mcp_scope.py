"""Tool scopes for a Claude OAuth principal. Service and cookie callers are not filtered."""
from __future__ import annotations

from dataclasses import dataclass

READ = "brain:read"
WRITE = "brain:write"

TOOL_SCOPES: dict[str, str] = {
    "get_context": READ,
    "read_file": READ,
    "list_dir": READ,
    "export_tasks": READ,
    "find_tasks": READ,
    "get_task": READ,
    "list_children": READ,
    "get_tree": READ,
    "list_reminders": READ,
    "get_triage_candidates": READ,
    "slack_live": READ,
    "get_meeting_prep": READ,
    "allocate_task_id": READ,
    "update_task": WRITE,
    "append_task_note": WRITE,
    "set_focus": WRITE,
    "propose_focus": WRITE,
    "apply_focus": WRITE,
    "edit_task_body": WRITE,
    "toggle_step": WRITE,
    "close_task": WRITE,
    "create_task": WRITE,
    "bulk_update": WRITE,
    "schedule_reminder": WRITE,
    "cancel_reminder": WRITE,
    "finalize_meeting": WRITE,
    "ingest_sembly": WRITE,
    "capture_daily": WRITE,
    "mailbox_propose": WRITE,
    "mailbox_apply": WRITE,
    "external_propose": WRITE,
    "external_apply": WRITE,
    "prepare_meeting": WRITE,
}


@dataclass(frozen=True)
class OAuthPrincipal:
    email: str
    scopes: frozenset[str]
    client_name: str


def oauth_denied(name: str, principal: OAuthPrincipal) -> bool:
    """True when this OAuth caller must not run the tool. dry_run does not lower a write."""
    required = TOOL_SCOPES.get(name)
    if required is None:
        return True
    return required not in principal.scopes


def context_may_rebuild(principal: object) -> bool:
    if isinstance(principal, OAuthPrincipal) and WRITE not in principal.scopes:
        return False
    return True
