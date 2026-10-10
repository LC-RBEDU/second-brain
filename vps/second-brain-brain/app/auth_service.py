"""Machine service-token auth (R5 / B15) — not for human clients (B2b)."""
from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ServicePrincipal:
    """Authenticated machine caller — audit as service:."""

    label: str = "service"

    @property
    def audit_id(self) -> str:
        return f"service:{self.label}"


def load_service_token(env: Mapping[str, str] | None = None) -> str:
    env_map = env if env is not None else os.environ
    return (env_map.get("BRAIN_SERVICE_TOKEN") or "").strip()


def authenticate_service_token(
    presented: str | None,
    *,
    env: Mapping[str, str] | None = None,
) -> ServicePrincipal | None:
    expected = load_service_token(env)
    if not expected or not presented:
        return None
    if not hmac.compare_digest(presented.strip(), expected):
        return None
    return ServicePrincipal()


def reject_human_api_key(header_name: str | None, header_value: str | None) -> bool:
    """B2b — any X-API-Key / Bearer api_key style for humans must be refused.

    Returns True when the request looks like a human API-key attempt that
    must get 401/403 (service token uses Authorization: Bearer <service> only
    when it matches BRAIN_SERVICE_TOKEN — checked separately).
    """
    name = (header_name or "").lower()
    if name in ("x-api-key", "api-key"):
        return bool((header_value or "").strip())
    return False
