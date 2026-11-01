"""Dashboard BFF. The browser never calls Brain and never opens the vault."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from base64 import urlsafe_b64decode, urlsafe_b64encode
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from dashboard_bff.batches import BatchRejected, pack_batches

COOKIE = "sb_dashboard_session"
ALLOWED_EMAIL = "lukas@redbuttonedu.cz"
_STRIP = frozenset({"focus", "updated"})


class ApiError(Exception):
    def __init__(self, status: int, reason: str, **extra: Any) -> None:
        self.status = status
        self.reason = reason
        self.extra = extra


def sign_session(email: str, secret: str) -> str:
    payload = urlsafe_b64encode(json.dumps({"email": email}).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def read_session(token: str, secret: str) -> str | None:
    if "." not in token:
        return None
    payload, signature = token.rsplit(".", 1)
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    padded = payload + "=" * (-len(payload) % 4)
    try:
        data = json.loads(urlsafe_b64decode(padded.encode()))
    except (json.JSONDecodeError, ValueError):
        return None
    email = data.get("email")
    return str(email) if email else None


def _archive(path: str) -> bool:
    return str(path or "").startswith("07-ARCHIV/")


def _clean_patch(patch: dict[str, Any] | None) -> dict[str, Any]:
    return {key: value for key, value in (patch or {}).items() if key not in _STRIP}


# Brain vault CAS / export can exceed httpx's 5s default (dashboard log: ReadTimeout on PATCH).
BRAIN_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class HttpxBrain:
    def __init__(self, base_url: str, token: str, transport: httpx.BaseTransport | None = None) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._transport = transport

    def call(self, method: str, path: str, *, json_body: dict | None = None, params: dict | None = None) -> httpx.Response:
        try:
            with httpx.Client(
                transport=self._transport,
                base_url=self._base,
                timeout=BRAIN_TIMEOUT,
            ) as client:
                return client.request(
                    method,
                    path,
                    json=json_body,
                    params=params,
                    headers={"Authorization": f"Bearer {self._token}"},
                )
        except httpx.TimeoutException as exc:
            raise ApiError(504, "brain_timeout") from exc
        except httpx.HTTPError as exc:
            raise ApiError(502, "brain_unreachable") from exc


def create_app(brain: Any, *, secret: str, batch_limit: int = 40) -> FastAPI:
    app = FastAPI()
    app.state.brain = brain
    app.state.secret = secret
    app.state.batch_limit = batch_limit

    @app.exception_handler(ApiError)
    def _api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content={"error_reason": exc.reason, "dialog": None, "force_save": False, **exc.extra},
        )

    def email_of(request: Request) -> str:
        token = request.cookies.get(COOKIE)
        if not token:
            raise ApiError(401, "unauthorized")
        email = read_session(token, app.state.secret)
        if not email:
            raise ApiError(401, "unauthorized")
        if email != ALLOWED_EMAIL:
            raise ApiError(403, "forbidden")
        return email

    def brain_json(response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = {"error_reason": "brain_error"}
        if response.status_code >= 400:
            extra = {}
            if body.get("detail") is not None:
                extra["detail"] = body.get("detail")
            if body.get("oid"):
                extra["oid"] = body.get("oid")
            raise ApiError(response.status_code, str(body.get("error_reason") or "brain_error"), **extra)
        return body

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/export")
    def export(request: Request) -> dict[str, Any]:
        email_of(request)
        response = app.state.brain.call(
            "GET",
            "/v1/tasks/export",
            params={"include_closed_days": 0},
        )
        return brain_json(response)

    @app.get("/api/tasks/item")
    def item(request: Request, task_id: str) -> dict[str, Any]:
        email_of(request)
        return brain_json(app.state.brain.call("GET", "/v1/tasks/item", params={"task_id": task_id}))

    @app.patch("/api/tasks")
    def patch_task(request: Request, body: dict[str, Any]) -> dict[str, Any]:
        email_of(request)
        _reject_archive([body])
        sent = {
            "path": body.get("path") or "",
            "patch": _clean_patch(body.get("patch")),
        }
        expect_oid = body.get("expect_oid")
        if expect_oid:
            sent["expect_oid"] = expect_oid
        return brain_json(app.state.brain.call("PATCH", "/v1/tasks", json_body=sent))

    @app.post("/api/tasks")
    def create_task(request: Request, body: dict[str, Any]) -> dict[str, Any]:
        email_of(request)
        deadline = body.get("deadline") or ""
        materials = body.get("materials")
        if not isinstance(materials, list):
            materials = []
        sent = {
            "slug": body.get("slug") or "",
            "title": body.get("title") or "",
            "level": body.get("level") or "task",
            "status": body.get("status") or "Next",
            "parent": "" if body.get("level") == "epic" else (body.get("parent") or ""),
            "deadline": deadline,
            "review_deadline": "" if deadline else (body.get("review_deadline") or ""),
            "waitUntil": body.get("waitUntil") or "",
            "detail": body.get("detail") or "",
            "materials": [str(item).strip() for item in materials if str(item or "").strip()],
        }
        return brain_json(app.state.brain.call("POST", "/v1/tasks", json_body=sent))

    @app.post("/api/tasks/edit-body")
    def edit_body(request: Request, body: dict[str, Any]) -> dict[str, Any]:
        email_of(request)
        path = str(body.get("path") or "")
        if _archive(path):
            raise ApiError(400, "archive_readonly")
        preview = brain_json(
            app.state.brain.call(
                "POST",
                "/v1/tasks/edit-body",
                json_body={
                    "path": path,
                    "operation": body.get("operation") or "replace",
                    "match": body.get("match") or "",
                    "new_text": body.get("new_text") or "",
                    "confirm": False,
                    "dry_run": False,
                    "source": body.get("source") or "dashboard",
                    "reason": body.get("reason") or "úprava detailu",
                },
            )
        )
        digest = preview.get("hash")
        if not digest:
            return preview
        return brain_json(
            app.state.brain.call(
                "POST",
                "/v1/tasks/edit-body",
                json_body={
                    "path": path,
                    "operation": body.get("operation") or "replace",
                    "match": body.get("match") or "",
                    "new_text": body.get("new_text") or "",
                    "expected_hash": digest,
                    "expect_oid": body.get("expect_oid"),
                    "confirm": True,
                    "dry_run": False,
                    "source": body.get("source") or "dashboard",
                    "reason": body.get("reason") or "úprava detailu",
                },
            )
        )

    @app.post("/api/cleanup")
    def cleanup(request: Request, body: dict[str, Any]) -> dict[str, Any]:
        email_of(request)
        items = list(body.get("items") or [])
        _reject_archive(items)
        try:
            chunks = pack_batches(items, limit=app.state.batch_limit)
        except BatchRejected as exc:
            raise ApiError(400, exc.reason) from exc
        return _run_chunks(app.state.brain, chunks, items)

    @app.post("/api/focus/propose")
    def propose(request: Request, body: dict[str, Any]) -> dict[str, Any]:
        email_of(request)
        if _archive(str(body.get("task_path") or "")):
            raise ApiError(400, "archive_readonly")
        result = brain_json(
            app.state.brain.call(
                "POST",
                "/v1/focus/propose",
                json_body={
                    "task_path": body.get("task_path") or "",
                    "focus_week": body.get("focus_week") or "",
                    "expect_oid": body.get("expect_oid"),
                },
            )
        )
        result["dialog"] = None
        result["force_save"] = False
        return result

    @app.post("/api/focus/apply")
    def apply_focus(request: Request, body: dict[str, Any]) -> dict[str, Any]:
        email_of(request)
        if _archive(str(body.get("task_path") or "")):
            raise ApiError(400, "archive_readonly")
        result = brain_json(
            app.state.brain.call(
                "POST",
                "/v1/focus/apply",
                json_body={"proposal_id": body.get("proposal_id") or ""},
            )
        )
        result["dialog"] = None
        result["force_save"] = False
        return result

    from dashboard_bff.oauth import attach_oauth

    attach_oauth(app)
    dist = Path(os.environ.get("DASHBOARD_DIST") or "/app/web/dist")
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="web")
    return app


def _reject_archive(items: list[dict[str, Any]]) -> None:
    for item in items:
        if _archive(str(item.get("path") or item.get("task_path") or "")):
            raise ApiError(400, "archive_readonly")


def _brain_body(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except json.JSONDecodeError:
        return {}
    return body if isinstance(body, dict) else {}


_TERMINAL_STATUS = frozenset({"Done", "Cancelled"})


def _is_terminal_item(item: dict[str, Any]) -> bool:
    """A11‴ / A46′: keep (no status) is not terminal; Done/Cancelled are."""
    patch = item.get("patch") or {}
    if not isinstance(patch, dict):
        return False
    return str(patch.get("status") or "") in _TERMINAL_STATUS


def _saved_from_request(written: list[str], items: list[dict[str, Any]]) -> list[str]:
    """saved = written minus ids whose request patch closes the task (0× export)."""
    by_id = {str(i.get("id")): i for i in items if i.get("id") is not None}
    return [tid for tid in written if not _is_terminal_item(by_id.get(tid) or {})]


def _lines(detail: dict[str, Any], titles: dict[str, str]) -> list[str]:
    ids: list[str] = []
    failures = detail.get("failures")
    if isinstance(failures, list) and failures and "parent_id" in failures[0]:
        for failure in failures:
            ids.append(str(failure.get("parent_id") or ""))
            ids.extend(str(child) for child in failure.get("child_ids") or [])
    else:
        if detail.get("parent_id"):
            ids.append(str(detail["parent_id"]))
        ids.extend(str(child) for child in detail.get("child_ids") or [])
    return [f"{task_id} — {titles.get(task_id) or task_id}" for task_id in ids if task_id]


def _run_chunks(brain: Any, chunks: list[list[dict[str, Any]]], items: list[dict[str, Any]]) -> dict[str, Any]:
    titles = {str(item["id"]): str(item.get("title") or item["id"]) for item in items}
    written: list[str] = []
    for index, chunk in enumerate(chunks):
        updates = [
            {
                "id": item["id"],
                "patch": _clean_patch(item.get("patch")),
                "expect_oid": item.get("expect_oid"),
            }
            for item in chunk
        ]
        if len(chunk) == 1:
            only = chunk[0]
            response = brain.call(
                "PATCH",
                "/v1/tasks",
                json_body={
                    "path": only.get("path") or "",
                    "patch": _clean_patch(only.get("patch")),
                    "expect_oid": only.get("expect_oid"),
                },
            )
        else:
            response = brain.call("POST", "/v1/tasks/bulk", json_body={"updates": updates})
        if response.status_code >= 400:
            body = _brain_body(response)
            detail = body.get("detail") if isinstance(body.get("detail"), dict) else {}
            # A11‴ fail path: 0× export — failed = whole failed chunk; pending = rest.
            failed = [str(item["id"]) for item in chunk]
            pending = [
                str(item["id"])
                for later in chunks[index + 1 :]
                for item in later
            ]
            saved = _saved_from_request(written, items)
            expect_oid = {
                str(failure["id"]): failure["oid"]
                for failure in (detail.get("failures") or [])
                if isinstance(failure, dict) and failure.get("id") and failure.get("oid")
            }
            if not expect_oid and len(chunk) == 1 and body.get("oid"):
                expect_oid = {str(chunk[0]["id"]): body.get("oid")}
            reason = str(body.get("error_reason") or "brain_error")
            return {
                "written": {"count": len(written), "ids": written},
                "saved": saved,
                "failed": failed,
                "pending": pending,
                "expect_oid": expect_oid,
                "selection": [str(item["id"]) for item in items],
                "lines": _lines(detail, titles) if reason == "open_child_under_closed_parent" else [],
                "error_reason": reason,
                "detail": detail or None,
                "dialog": None,
                "preview_open": bool(failed or pending),
                "stopped": response.status_code,
            }
        written.extend(str(item["id"]) for item in chunk)
    return {
        "written": {"count": len(written), "ids": written},
        "saved": _saved_from_request(written, items),
        "failed": [],
        "pending": [],
        "expect_oid": {},
        "selection": [str(item["id"]) for item in items],
        "lines": [],
        "dialog": None,
        "preview_open": False,
        "stopped": None,
    }
