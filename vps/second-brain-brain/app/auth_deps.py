"""FastAPI auth dependencies — OAuth session (human) or service token (machine)."""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException

from app.auth_service import (
    ServicePrincipal,
    authenticate_service_token,
    reject_human_api_key,
)
from app.oauth_routes import _COOKIE, read_session_email


def require_auth(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    session: Annotated[str | None, Cookie(alias=_COOKIE)] = None,
) -> ServicePrincipal | str:
    """B1/B2/B2b/B15 — OAuth cookie or machine Bearer; reject human API keys."""
    if reject_human_api_key("X-API-Key", x_api_key):
        raise HTTPException(status_code=401, detail="human API keys are not accepted")

    email = read_session_email(session)
    if email:
        return f"oauth:{email}"

    presented: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        presented = authorization[7:].strip()

    env = os.environ
    principal = authenticate_service_token(presented, env=env)
    if principal is not None:
        return principal

    allow_dev = (env.get("BRAIN_ALLOW_NO_PUSH") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    has_token = bool((env.get("BRAIN_SERVICE_TOKEN") or "").strip())
    if allow_dev and not has_token:
        return "dev"

    raise HTTPException(status_code=401, detail="authentication required")


AuthPrincipal = Annotated[ServicePrincipal | str, Depends(require_auth)]
