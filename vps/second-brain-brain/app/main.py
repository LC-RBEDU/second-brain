"""Second Brain Brain API — healthz + REST vault tools (MCP plugin in F2-j)."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.auth_deps import AuthPrincipal
from app.errors import BrainClientError, BrainVaultError
from app.tools import allocate_task_id as allocate_tool
from app.tools import create_task as create_task_tool
from app.tools import get_context as get_context_tool
from app.tools import read_file as read_file_tool
from app.tools import reminders_tools as reminders_tool


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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not _push_ok() and not _allow_no_push():
        raise RuntimeError(
            "Brain requires GIT_VAULT_PUSH=1 (set BRAIN_ALLOW_NO_PUSH=1 only for tests)"
        )
    yield


app = FastAPI(title="Second Brain Brain", version="0.1.0", lifespan=lifespan)


@app.exception_handler(BrainVaultError)
async def _brain_vault_error(_request: Request, exc: BrainVaultError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())


@app.exception_handler(BrainClientError)
async def _brain_client_error(_request: Request, exc: BrainClientError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.as_dict())


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/context")
def rest_get_context(_auth: AuthPrincipal) -> dict[str, Any]:
    return get_context_tool.get_context()


@app.get("/v1/file")
def rest_read_file(path: str, _auth: AuthPrincipal) -> dict[str, Any]:
    return read_file_tool.read_file(path)


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
    """A10 / B12 — F3 tools return 501."""
    _ = name
    return JSONResponse(
        status_code=501,
        content={"error_reason": "f3_stub", "message": "F3 tool — not in F2"},
    )
