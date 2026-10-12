"""ASGI auth gate for mounted MCP app (B1 / R5) — cookie or service Bearer."""
from __future__ import annotations

import os
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth_service import ServicePrincipal, authenticate_service_token, reject_human_api_key
from app.oauth_routes import _COOKIE, read_session_email
from app.request_principal import reset_brain_principal, set_brain_principal


class McpAuthMiddleware:
    """Reject unauthenticated MCP requests with 401 JSON; set principal ContextVar."""

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
        auth = request.headers.get("authorization") or ""
        presented = auth[7:].strip() if auth.lower().startswith("bearer ") else None
        service_ok = authenticate_service_token(presented, env=os.environ) is not None
        allow_dev = (os.environ.get("BRAIN_ALLOW_NO_PUSH") or "").strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        has_token = bool((os.environ.get("BRAIN_SERVICE_TOKEN") or "").strip())
        dev_ok = allow_dev and not has_token

        if email:
            principal: ServicePrincipal | str = f"oauth:{email}"
        elif service_ok:
            principal = ServicePrincipal()
        elif dev_ok:
            principal = "dev"
        else:
            resp = JSONResponse(
                {"error_reason": "client_error", "message": "authentication required"},
                status_code=401,
            )
            await resp(scope, receive, send)
            return

        token = set_brain_principal(principal)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_brain_principal(token)
