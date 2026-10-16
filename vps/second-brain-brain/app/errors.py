"""Brain HTTP/MCP error transport (A57 / A58)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Stable set asserted by T16 (A58 ⊇ A55 + flock + push_disabled + paused).
ERROR_REASONS: frozenset[str] = frozenset(
    {
        "vault_dirty_start",
        "vault_flock_busy",
        "vault_push_reset_ok",
        "vault_push_reset_failed",
        "vault_tip_ahead",
        "vault_push_disabled",
        "vault_paused",
        "context_light_stale",
    }
)

_MESSAGES: dict[str, str] = {
    "vault_dirty_start": (
        "Vault working tree je dirty na startu session. Mutate/rebuild blokováno — "
        "ukliď WT přes SSH dle runbooku."
    ),
    "vault_flock_busy": (
        "Vault flock je obsazený jiným writerem. Zkus znovu za chvíli."
    ),
    "vault_push_reset_ok": (
        "Push ff-only selhal; tip byl resetnut na @{upstream}. Zkus znovu."
    ),
    "vault_push_reset_failed": (
        "Push ff-only selhal a reset na @{upstream} taky. Tip může být ahead — "
        "ukliď přes SSH dle runbooku."
    ),
    "vault_tip_ahead": (
        "Vault tip není sync s remote (HEAD ≠ @{upstream}). "
        "Mutate/rebuild blokováno — ukliď tip přes SSH dle runbooku."
    ),
    "vault_push_disabled": (
        "GIT_VAULT_PUSH≠1 — Brain mutate/rebuild vyžaduje push."
    ),
    "vault_paused": (
        "VAULT_WRITERS_PAUSED=1 — mutate/rebuild dočasně vypnuté."
    ),
    "context_light_stale": (
        "Light context chybí nebo freshness trio nesedí. "
        "Nejdřív warm/rebuild přes get_context — /v1/context/light nerestartuje."
    ),
}


@dataclass
class BrainVaultError(Exception):
    """Maps to HTTP 503 + MCP isError with error_reason + message."""

    error_reason: str
    message: str
    status_code: int = 503

    def __post_init__(self) -> None:
        if self.error_reason not in ERROR_REASONS:
            # Still raise, but keep reason for debugging unexpected codes.
            pass
        Exception.__init__(self, self.message)

    def as_dict(self) -> dict[str, str]:
        return {"error_reason": self.error_reason, "message": self.message}


@dataclass
class BrainClientError(Exception):
    """Non-vault client errors (403 path deny, 401 auth, …)."""

    message: str
    status_code: int = 403
    error_reason: str = "client_error"
    detail: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"error_reason": self.error_reason, "message": self.message}
        if self.detail is not None:
            out["detail"] = self.detail
        return out


def vault_error(reason: str, message: str | None = None) -> BrainVaultError:
    return BrainVaultError(
        error_reason=reason,
        message=message or _MESSAGES.get(reason, reason),
    )
