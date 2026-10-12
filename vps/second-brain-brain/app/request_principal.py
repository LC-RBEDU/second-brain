"""Request-scoped Brain principal for MCP tools (ContextVar)."""
from __future__ import annotations

from contextvars import ContextVar, Token

from app.auth_service import ServicePrincipal

BrainPrincipal = ServicePrincipal | str | None

_brain_principal: ContextVar[BrainPrincipal] = ContextVar("brain_principal", default=None)


def set_brain_principal(principal: BrainPrincipal) -> Token:
    return _brain_principal.set(principal)


def get_brain_principal() -> BrainPrincipal:
    return _brain_principal.get()


def reset_brain_principal(token: Token) -> None:
    _brain_principal.reset(token)
