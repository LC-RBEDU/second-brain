"""OAuth discovery documents. No authentication and no SQLite."""
from __future__ import annotations

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["oauth-mcp-metadata"])


def public_base() -> str:
    return (os.environ.get("BRAIN_PUBLIC_URL") or "").strip().rstrip("/")


def resource_url() -> str:
    return f"{public_base()}/mcp/"


def www_authenticate() -> str:
    base = public_base()
    return (
        'Bearer realm="brain", '
        f'resource_metadata="{base}/.well-known/oauth-protected-resource/mcp", '
        'scope="brain:read brain:write"'
    )


def protected_resource() -> dict[str, object]:
    return {
        "resource": resource_url(),
        "authorization_servers": [public_base()],
        "scopes_supported": ["brain:read", "brain:write"],
        "bearer_methods_supported": ["header"],
    }


def authorization_server() -> dict[str, object]:
    base = public_base()
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/mcp/authorize",
        "token_endpoint": f"{base}/oauth/mcp/token",
        "registration_endpoint": f"{base}/oauth/mcp/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "client_id_metadata_document_supported": True,
    }


@router.get("/.well-known/oauth-protected-resource")
@router.get("/.well-known/oauth-protected-resource/mcp")
def oauth_protected_resource() -> JSONResponse:
    return JSONResponse(protected_resource())


@router.get("/.well-known/oauth-authorization-server")
def oauth_authorization_server() -> JSONResponse:
    return JSONResponse(authorization_server())
