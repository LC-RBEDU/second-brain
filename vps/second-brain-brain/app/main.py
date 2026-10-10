"""Second Brain Brain API — healthz + FastAPI shell (tools/auth in F2-c…e)."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import BrainVaultError


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


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
