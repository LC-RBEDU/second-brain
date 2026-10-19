"""Second Brain Brain API — REST + MCP + Google OAuth."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.auth_deps import AuthPrincipal
from app.errors import BrainClientError, BrainVaultError
from app.mcp_app import build_mcp
from app.mcp_auth import McpAuthMiddleware
from app.oauth_routes import router as oauth_router
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
from app.tools import close_task as close_task_tool
from app.tools import edit_task_body as edit_task_body_tool
from app.tools import export_tasks as export_tasks_tool
from app.tools import find_tasks as find_tasks_tool
from app.tools import focus_proposal as focus_proposal_tool
from app.tools import get_task as get_task_tool
from app.tools import task_tree as task_tree_tool
from app.tools import toggle_step as toggle_step_tool


def _push_ok() -> bool:
    return (os.environ.get("GIT_VAULT_PUSH") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _allow_no_push() -> bool:
    return (os.environ.get("BRAIN_ALLOW_NO_PUSH") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _mcp_transport_security() -> TransportSecuritySettings:
    """Allow Host/Origin for BRAIN_PUBLIC_URL (+ localhost for TestClient)."""
    hosts = ["localhost", "127.0.0.1", "testserver"]
    origins = [
        "http://localhost",
        "http://127.0.0.1",
        "http://testserver",
    ]
    public = (os.environ.get("BRAIN_PUBLIC_URL") or "").strip()
    if public:
        parsed = urlparse(public)
        if parsed.netloc:
            hosts.append(parsed.netloc)
            origins.append(f"{parsed.scheme}://{parsed.netloc}")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


# MCP streamable HTTP — session manager must run inside FastAPI lifespan
# (otherwise RuntimeError: Task group is not initialized).
_mcp = build_mcp()
_mcp_http = _mcp.streamable_http_app(
    streamable_http_path="/",
    transport_security=_mcp_transport_security(),
)
_mcp_asgi = McpAuthMiddleware(_mcp_http)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not _push_ok() and not _allow_no_push():
        raise RuntimeError(
            "Brain requires GIT_VAULT_PUSH=1 (set BRAIN_ALLOW_NO_PUSH=1 only for tests)"
        )
    async with _mcp.session_manager.run():
        yield


class _HttpsRedirectFixMiddleware(BaseHTTPMiddleware):
    """Behind Traefik, slash redirects must keep https (BRAIN_PUBLIC_URL)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        public = (os.environ.get("BRAIN_PUBLIC_URL") or "").strip()
        loc = response.headers.get("location")
        if public.startswith("https://") and loc and loc.startswith("http://"):
            response.headers["location"] = "https://" + loc[len("http://") :]
        return response


app = FastAPI(title="Second Brain Brain", version="0.2.0", lifespan=lifespan)
# Trust X-Forwarded-Proto/Host from Coolify Traefik (fixes /mcp → http://…/mcp/).
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(_HttpsRedirectFixMiddleware)
app.include_router(oauth_router)
app.mount("/mcp", _mcp_asgi)


@app.exception_handler(BrainVaultError)
async def _brain_vault_error(_request: Request, exc: BrainVaultError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())


@app.exception_handler(BrainClientError)
async def _brain_client_error(_request: Request, exc: BrainClientError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "mcp": "/mcp"}


@app.get("/v1/context")
def rest_get_context(_auth: AuthPrincipal) -> dict[str, Any]:
    return get_context_tool.get_context()


@app.get("/v1/context/light")
def rest_get_context_light(_auth: AuthPrincipal) -> dict[str, Any]:
    """F4 — warm light only; human OAuth required (service → 403)."""
    from app.auth_service import ServicePrincipal
    from app.errors import BrainClientError
    from app.tools import get_context_light as light_tool

    if isinstance(_auth, ServicePrincipal) or _auth == "dev":
        raise BrainClientError(
            message="GET /v1/context/light requires human OAuth.",
            status_code=403,
            error_reason="human_oauth_required",
        )
    if not (isinstance(_auth, str) and _auth.startswith("oauth:")):
        raise BrainClientError(
            message="GET /v1/context/light requires human OAuth.",
            status_code=403,
            error_reason="human_oauth_required",
        )
    return light_tool.get_context_light()


@app.get("/v1/file")
def rest_read_file(path: str, _auth: AuthPrincipal) -> dict[str, Any]:
    return read_file_tool.read_file(path)


@app.get("/v1/dir")
def rest_list_dir(
    path: str,
    _auth: AuthPrincipal,
    pattern: str | None = None,
    recursive: bool = False,
) -> dict[str, Any]:
    return list_dir_tool.list_dir(path, pattern=pattern, recursive=recursive)


class UpdateTaskBody(BaseModel):
    path: str
    patch: dict[str, Any]
    expect_oid: str | None = None
    allow_parent_shift: bool = False
    dry_run: bool = False


@app.patch("/v1/tasks")
def rest_update_task(body: UpdateTaskBody, _auth: AuthPrincipal) -> dict:
    return update_task_tool.update_task(
        path=body.path,
        patch=body.patch,
        expect_oid=body.expect_oid,
        allow_parent_shift=body.allow_parent_shift,
        dry_run=body.dry_run,
    )


class AppendTaskBody(BaseModel):
    path: str
    text: str
    target: str
    expect_oid: str | None = None
    dry_run: bool = False


@app.post("/v1/tasks/append")
def rest_append_task_note(body: AppendTaskBody, _auth: AuthPrincipal) -> dict:
    return append_task_note_tool.append_task_note(
        path=body.path,
        text=body.text,
        target=body.target,
        expect_oid=body.expect_oid,
        dry_run=body.dry_run,
    )


class SetFocusBody(BaseModel):
    task_path: str
    focus_week: str = ""
    expect_oid: str | None = None


@app.post("/v1/set_focus")
def rest_set_focus(body: SetFocusBody, _auth: AuthPrincipal) -> dict:
    return set_focus_tool.set_focus(
        task_path=body.task_path,
        focus_week=body.focus_week,
        expect_oid=body.expect_oid,
        principal=_auth,
    )


class FindTasksBody(BaseModel):
    query: str | None = None
    task_id: str | None = None
    project: str | None = None
    work_type: str | None = None
    parent: str | None = None
    status: list[str] | None = None
    limit: int = 20


@app.post("/v1/tasks/find")
def rest_find_tasks(body: FindTasksBody, _auth: AuthPrincipal) -> dict:
    return find_tasks_tool.find_tasks(
        query=body.query,
        task_id=body.task_id,
        project=body.project,
        work_type=body.work_type,
        parent=body.parent,
        status=body.status,
        limit=body.limit,
    )


@app.get("/v1/tasks/export")
def rest_export_tasks(
    _auth: AuthPrincipal,
    include_closed_days: int = 0,
    projects_csv: str = "",
    fields: str = "standard",
    since: str | None = None,
) -> dict[str, Any]:
    return export_tasks_tool.export_tasks(
        include_closed_days=include_closed_days,
        projects_csv=projects_csv,
        fields=fields,
        since=since,
    )


@app.get("/v1/tasks/item")
def rest_get_task(task_id: str, _auth: AuthPrincipal) -> dict:
    return get_task_tool.get_task(task_id=task_id)


@app.get("/v1/tasks/tree")
def rest_get_tree(task_id: str, _auth: AuthPrincipal) -> dict:
    return task_tree_tool.get_tree(task_id=task_id)


class EditBody(BaseModel):
    path: str
    operation: str
    match: str
    new_text: str = ""
    expected_hash: str | None = None
    expect_oid: str | None = None
    confirm: bool = False
    dry_run: bool = False
    allow_migration_trace: bool = False
    source: str = ""
    reason: str = ""


@app.post("/v1/tasks/edit-body")
def rest_edit_body(body: EditBody, _auth: AuthPrincipal) -> dict:
    return edit_task_body_tool.edit_task_body(**body.model_dump())


class ToggleBody(BaseModel):
    path: str
    step_id: str
    checked: bool = True
    source: str = ""
    reason: str = ""
    dry_run: bool = False


@app.post("/v1/tasks/toggle-step")
def rest_toggle_step(body: ToggleBody, _auth: AuthPrincipal) -> dict:
    return toggle_step_tool.toggle_step(**body.model_dump())


class CloseBody(BaseModel):
    path: str
    resolution: str = "done"
    note: str = ""
    source: str = ""
    reason: str = ""
    dry_run: bool = False


@app.post("/v1/tasks/close")
def rest_close_task(body: CloseBody, _auth: AuthPrincipal) -> dict:
    return close_task_tool.close_task(**body.model_dump())


class ProposeFocusBody(BaseModel):
    task_path: str
    focus_week: str = ""
    expect_oid: str | None = None


@app.post("/v1/focus/propose")
def rest_propose_focus(body: ProposeFocusBody, _auth: AuthPrincipal) -> dict:
    return focus_proposal_tool.propose_focus(
        task_path=body.task_path,
        focus_week=body.focus_week,
        expect_oid=body.expect_oid,
        principal=str(_auth),
    )


class ApplyFocusBody(BaseModel):
    proposal_id: str


@app.post("/v1/focus/apply")
def rest_apply_focus(body: ApplyFocusBody, _auth: AuthPrincipal) -> dict:
    return focus_proposal_tool.apply_focus(
        proposal_id=body.proposal_id,
        principal=_auth,
    )


@app.get("/v1/allocate_task_id")
def rest_allocate(slug: str, _auth: AuthPrincipal, level: str | None = None) -> dict:
    return allocate_tool.allocate_task_id(slug, level=level)


class CreateTaskBody(BaseModel):
    slug: str
    title: str
    detail: str = ""
    level: str = "story"
    status: str = "Next"
    parent: str = ""


@app.post("/v1/tasks")
def rest_create_task(body: CreateTaskBody, _auth: AuthPrincipal) -> dict:
    return create_task_tool.create_task(
        slug=body.slug,
        title=body.title,
        detail=body.detail,
        level=body.level,
        status=body.status,
        parent=body.parent,
    )


class ScheduleBody(BaseModel):
    message: str
    deliver_at: str
    task_ref: str | None = None


@app.post("/v1/reminders")
def rest_schedule(body: ScheduleBody, _auth: AuthPrincipal) -> dict:
    return reminders_tool.schedule_reminder(
        message=body.message,
        deliver_at=body.deliver_at,
        task_ref=body.task_ref,
    )


@app.get("/v1/reminders")
def rest_list_reminders(_auth: AuthPrincipal) -> dict:
    return reminders_tool.list_reminders()


@app.delete("/v1/reminders/{reminder_id}")
def rest_cancel(reminder_id: str, _auth: AuthPrincipal) -> dict:
    return reminders_tool.cancel_reminder(reminder_id)


# --- F3 tools ---


class IngestSemblyBody(BaseModel):
    payload: dict[str, Any]


@app.post("/v1/ingest_sembly")
def rest_ingest_sembly(body: IngestSemblyBody, _auth: AuthPrincipal) -> dict:
    return ingest_tool.ingest_sembly(body.payload)


class CaptureDailyBody(BaseModel):
    text: str
    title: str | None = None


@app.post("/v1/capture_daily")
def rest_capture_daily(body: CaptureDailyBody, _auth: AuthPrincipal) -> dict:
    return capture_daily_tool.capture_daily(body.text, title=body.title)


@app.get("/v1/triage/candidates")
def rest_triage(
    _auth: AuthPrincipal,
    include_live_slack: bool = True,
    include_gmail: bool = True,
) -> dict:
    return triage_tool.get_triage_candidates(
        include_live_slack=include_live_slack,
        include_gmail=include_gmail,
    )


@app.get("/v1/slack/live")
def rest_slack_live(_auth: AuthPrincipal) -> dict:
    return slack_live_tool.slack_live_search()


class ProposeBody(BaseModel):
    items: list[dict[str, Any]]


@app.post("/v1/mailbox/propose")
def rest_mailbox_propose(body: ProposeBody, auth: AuthPrincipal) -> dict:
    return mailbox_tool.mailbox_propose(body.items, principal=auth)


class ApplyBody(BaseModel):
    batch_id: str
    ids: list[str] | None = None


@app.post("/v1/mailbox/apply")
def rest_mailbox_apply(body: ApplyBody, auth: AuthPrincipal) -> dict:
    return mailbox_tool.mailbox_apply(body.batch_id, body.ids, principal=auth)


@app.post("/v1/external/propose")
def rest_external_propose(body: ProposeBody, auth: AuthPrincipal) -> dict:
    return external_tool.external_propose(body.items, principal=auth)


@app.post("/v1/external/apply")
def rest_external_apply(body: ApplyBody, auth: AuthPrincipal) -> dict:
    return external_tool.external_apply(body.batch_id, body.ids, principal=auth)


class PrepareMeetingBody(BaseModel):
    event_id: str
    title: str = ""
    starts_at: str = ""
    force: bool = False
    deliver: bool = True
    dry_run: bool = False


@app.post("/v1/prepare_meeting")
def rest_prepare_meeting(body: PrepareMeetingBody, _auth: AuthPrincipal) -> dict:
    return prepare_tool.prepare_meeting(
        body.event_id,
        title=body.title,
        starts_at=body.starts_at,
        force=body.force,
        deliver=body.deliver,
        dry_run=body.dry_run,
    )


@app.get("/v1/meeting_prep")
def rest_get_meeting_prep(
    event_id: str, _auth: AuthPrincipal, day: str | None = None
) -> dict:
    return prepare_tool.get_meeting_prep(event_id, day=day)


@app.post("/v1/push/test")
def rest_push_test(_auth: AuthPrincipal) -> dict:
    """B18 OS push probe — F3 ships Slack/chat fallback; native OS may FAIL."""
    return {
        "ok": False,
        "channel": "none",
        "error_reason": "os_push_not_configured",
        "fallback": ["slack_dm", "chat"],
        "b18": "FAIL",
    }
