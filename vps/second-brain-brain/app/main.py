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
from app.tools import create_task as create_task_tool
from app.tools import get_context as get_context_tool
from app.tools import list_dir as list_dir_tool
from app.tools import read_file as read_file_tool
from app.tools import reminders_tools as reminders_tool
from app.tools import set_focus as set_focus_tool
from app.tools import update_task as update_task_tool


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


@app.patch("/v1/tasks")
def rest_update_task(body: UpdateTaskBody, _auth: AuthPrincipal) -> dict:
    return update_task_tool.update_task(
        path=body.path, patch=body.patch, expect_oid=body.expect_oid
    )


@app.post("/v1/set_focus")
def rest_set_focus(_auth: AuthPrincipal) -> dict:
    return set_focus_tool.set_focus()


@app.get("/v1/allocate_task_id")
def rest_allocate(slug: str, _auth: AuthPrincipal, level: str | None = None) -> dict:
    return allocate_tool.allocate_task_id(slug, level=level)


class CreateTaskBody(BaseModel):
    slug: str
    title: str
    detail: str = ""
    level: str = "story"
    status: str = "Next"


@app.post("/v1/tasks")
def rest_create_task(body: CreateTaskBody, _auth: AuthPrincipal) -> dict:
    return create_task_tool.create_task(
        slug=body.slug,
        title=body.title,
        detail=body.detail,
        level=body.level,
        status=body.status,
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


@app.api_route("/v1/f3/{name}", methods=["GET", "POST", "PUT", "DELETE"])
def f3_stub(name: str, _auth: AuthPrincipal) -> JSONResponse:
    _ = name
    return JSONResponse(
        status_code=501,
        content={"error_reason": "f3_stub", "message": "F3 tool — not in F2"},
    )
