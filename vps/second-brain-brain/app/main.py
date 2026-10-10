"""Second Brain Brain API — healthz + FastAPI shell (tools/auth in F2-c…e)."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import BrainClientError, BrainVaultError
from app.tools import get_context as get_context_tool
from app.tools import read_file as read_file_tool


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
    # Coolify Brain must push (R23 / A47). Fail fast at boot if misconfigured.
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
def rest_get_context() -> dict:
    """REST get_context (service auth wired in F2-c middleware next)."""
    return get_context_tool.get_context()


@app.get("/v1/file")
def rest_read_file(path: str) -> dict:
    return read_file_tool.read_file(path)
