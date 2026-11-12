"""One JSON line on stdout per MCP tool call. Nothing is written to the vault."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app.auth_service import ServicePrincipal
from app.oauth_mcp_scope import OAuthPrincipal
from app.request_principal import get_brain_principal


def audit_line(tool: str, result: str) -> None:
    principal = get_brain_principal()
    if isinstance(principal, OAuthPrincipal):
        identity = principal.email
        client = principal.client_name
    elif isinstance(principal, ServicePrincipal):
        identity = "service"
        client = "service"
    elif isinstance(principal, str) and principal.startswith("oauth:"):
        identity = principal.split(":", 1)[1]
        client = "cookie"
    else:
        identity = "service" if principal == "dev" else str(principal or "")
        client = "cookie"
    print(
        json.dumps(
            {
                "identity": identity,
                "client": client,
                "tool": tool,
                "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "result": result,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
