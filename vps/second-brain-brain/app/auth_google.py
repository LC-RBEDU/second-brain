"""Google OAuth IdP for human MCP/REST clients (R5 / B37)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlencode

ALLOWLIST: frozenset[str] = frozenset(
    {
        "lukas@redbuttonedu.cz",
        "lukas.cypra@gmail.com",
    }
)


@dataclass(frozen=True)
class OAuthConfig:
    client_id: str
    client_secret: str
    public_url: str

    @property
    def callback_url(self) -> str:
        """B37 — always rstrip BRAIN_PUBLIC_URL before /oauth/callback."""
        return oauth_callback_url(self.public_url)


def oauth_callback_url(brain_public_url: str) -> str:
    base = (brain_public_url or "").strip().rstrip("/")
    if not base:
        raise ValueError("BRAIN_PUBLIC_URL is empty")
    return f"{base}/oauth/callback"


def load_oauth_config(env: Mapping[str, str] | None = None) -> OAuthConfig:
    env_map = env if env is not None else os.environ
    return OAuthConfig(
        client_id=(env_map.get("GOOGLE_CLIENT_ID") or "").strip(),
        client_secret=(env_map.get("GOOGLE_CLIENT_SECRET") or "").strip(),
        public_url=(env_map.get("BRAIN_PUBLIC_URL") or "").strip(),
    )


def email_allowed(email: str) -> bool:
    return (email or "").strip().lower() in {e.lower() for e in ALLOWLIST}


def authorize_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    scope: str = "openid email profile",
) -> str:
    qs = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{qs}"
