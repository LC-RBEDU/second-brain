"""ASGI auth gate for mounted MCP app (B1 / R5) — cookie or service Bearer."""
from __future__ import annotations

import os
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth_service import authenticate_service_token, reject_human_api_key
from app.oauth_routes import _COOKIE, read_session_email


class McpAuthMiddleware:
    """Reject unauthenticated MCP requests with 401 JSON."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        if reject_human_api_key("X-API-Key", request.headers.get("x-api-key")):
            resp = JSONResponse(
                {"error_reason": "client_error", "message": "human API keys are not accepted"},
                status_code=401,
            )
            await resp(scope, receive, send)
            return

        email = read_session_email(request.cookies.get(_COOKIE))
        if email:
            await self.app(scope, receive, send)
            return

        auth = request.headers.get("authorization") or ""
        presented = auth[7:].strip() if auth.lower().startswith("bearer ") else None
        if authenticate_service_token(presented, env=os.environ) is not None:
            await self.app(scope, receive, send)
            return

        allow_dev = (os.environ.get("BRAIN_ALLOW_NO_PUSH") or "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        has_token = bool((os.environ.get("BRAIN_SERVICE_TOKEN") or "").strip())
        if allow_dev and not has_token:
            await self.app(scope, receive, send)
            return

        resp = JSONResponse(
            {"error_reason": "client_error", "message": "authentication required"},
            status_code=401,
        )
        await resp(scope, receive, send)
