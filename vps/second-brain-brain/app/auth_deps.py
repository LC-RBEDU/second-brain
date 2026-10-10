"""FastAPI auth dependencies — service token now; OAuth session later."""
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.auth_service import (
    ServicePrincipal,
    authenticate_service_token,
    reject_human_api_key,
)


def require_service_or_dev(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> ServicePrincipal | str:
    """B1/B2b/B15 — machine Bearer service token; reject human API keys.

    When ``BRAIN_ALLOW_NO_PUSH=1`` (local tests) and no token configured,
    allow anonymous ``dev`` principal so unit tests can hit routes.
    """
    if reject_human_api_key("X-API-Key", x_api_key):
        raise HTTPException(status_code=401, detail="human API keys are not accepted")

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


AuthPrincipal = Annotated[ServicePrincipal | str, Depends(require_service_or_dev)]
