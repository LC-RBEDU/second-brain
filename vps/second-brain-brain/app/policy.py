"""Server-side write policy (focus allow for authenticated callers; Stav cron-owned)."""
from __future__ import annotations

from dataclasses import dataclass

from app.auth_service import ServicePrincipal


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""


def allow_focus_write(principal: ServicePrincipal | str | None) -> PolicyDecision:
    """Allow focus mutate for oauth / service / local dev (A1)."""
    if principal is None:
        return PolicyDecision(False, "focus_write_auth_required")
    if isinstance(principal, ServicePrincipal):
        return PolicyDecision(True)
    if isinstance(principal, str) and (
        principal.startswith("oauth:") or principal == "dev"
    ):
        return PolicyDecision(True)
    return PolicyDecision(False, "focus_write_auth_required")


FOCUS_PROPOSAL_MESSAGE = "napiš propose_focus, po ano apply_focus"


def deny_focus_write() -> PolicyDecision:
    """Direct focus writes are refused. The caller proposes, then applies."""
    return PolicyDecision(False, FOCUS_PROPOSAL_MESSAGE)


def deny_stav_auto_write() -> PolicyDecision:
    """B7 — ## Stav (auto) is cron-owned."""
    return PolicyDecision(False, "Stav (auto) is hub-cron owned")
