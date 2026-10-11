"""Apply-route auth gate (R17 / C1) — service 403; oauth 501 post-F3."""
from __future__ import annotations

from app.auth_service import ServicePrincipal
from app.errors import BrainClientError


def gate_brain_apply(principal: ServicePrincipal | str) -> None:
    """Raise before any Brain-side mutate apply.

    - ServicePrincipal → 403 human_oauth_required
    - oauth:{email} → 501 oauth_brain_apply_post_f3
    - other → 401/403
    """
    if isinstance(principal, ServicePrincipal):
        raise BrainClientError(
            message="Brain apply requires human OAuth (post-F3). Use client apply.",
            status_code=403,
            error_reason="human_oauth_required",
        )
    if isinstance(principal, str) and principal.startswith("oauth:"):
        raise BrainClientError(
            message="OAuth Brain apply is post-F3 debt. Use client apply after propose.",
            status_code=501,
            error_reason="oauth_brain_apply_post_f3",
        )
    if principal == "dev":
        raise BrainClientError(
            message="Brain apply requires human OAuth (post-F3). Use client apply.",
            status_code=403,
            error_reason="human_oauth_required",
        )
    raise BrainClientError(
        message="authentication required for apply",
        status_code=401,
        error_reason="auth_required",
    )
