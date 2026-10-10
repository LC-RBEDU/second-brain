"""T2 — OAuth callback rstrip (B37) + allowlist + service token."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.auth_google import email_allowed, oauth_callback_url  # noqa: E402
from app.auth_service import (  # noqa: E402
    authenticate_service_token,
    reject_human_api_key,
)


def test_oauth_callback_rstrip():
    assert (
        oauth_callback_url("https://brain.example.com/")
        == "https://brain.example.com/oauth/callback"
    )
    assert (
        oauth_callback_url("https://brain.example.com")
        == "https://brain.example.com/oauth/callback"
    )


def test_allowlist():
    assert email_allowed("lukas@redbuttonedu.cz")
    assert email_allowed("Lukas.Cypra@gmail.com")
    assert not email_allowed("other@example.com")


def test_service_token():
    env = {"BRAIN_SERVICE_TOKEN": "secret-token"}
    assert authenticate_service_token("secret-token", env=env) is not None
    assert authenticate_service_token("wrong", env=env) is None
    assert authenticate_service_token(None, env=env) is None


def test_reject_human_api_key_header():
    assert reject_human_api_key("X-API-Key", "abc") is True
    assert reject_human_api_key("Authorization", "Bearer x") is False
