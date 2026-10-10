"""Google OAuth authorize + callback (R5 / B37) — session cookie for humans."""
from __future__ import annotations

import os
import secrets
from typing import Annotated

import httpx
from fastapi import APIRouter, Cookie, HTTPException, Query, Response
from itsdangerous import BadSignature, URLSafeSerializer

from app.auth_google import (
    ALLOWLIST,
    authorize_url,
    email_allowed,
    load_oauth_config,
)

router = APIRouter(tags=["oauth"])

_COOKIE = "sb_brain_session"
_STATE_COOKIE = "sb_oauth_state"


def _serializer() -> URLSafeSerializer:
    secret = (os.environ.get("BRAIN_SESSION_SECRET") or "").strip()
    if not secret:
        secret = (os.environ.get("BRAIN_SERVICE_TOKEN") or "dev-only-insecure").strip()
    return URLSafeSerializer(secret, salt="sb-brain-session")


def _cookie_secure(public_url: str) -> bool:
    """Secure cookies on https prod; off when BRAIN_ALLOW_NO_PUSH (http TestClient)."""
    if (os.environ.get("BRAIN_ALLOW_NO_PUSH") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return False
    return public_url.startswith("https")


def read_session_email(cookie: str | None) -> str | None:
    if not cookie:
        return None
    try:
        data = _serializer().loads(cookie)
    except BadSignature:
        return None
    email = str(data.get("email") or "").strip().lower()
    if not email_allowed(email):
        return None
    return email


@router.get("/oauth/authorize")
def oauth_authorize(response: Response) -> Response:
    cfg = load_oauth_config()
    if not cfg.client_id or not cfg.public_url:
        raise HTTPException(500, "GOOGLE_CLIENT_ID / BRAIN_PUBLIC_URL not configured")
    state = secrets.token_urlsafe(24)
    response = Response(status_code=302)
    response.headers["Location"] = authorize_url(
        client_id=cfg.client_id,
        redirect_uri=cfg.callback_url,
        state=state,
    )
    response.set_cookie(
        _STATE_COOKIE,
        state,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(cfg.public_url),
        max_age=600,
    )
    return response


@router.get("/oauth/callback")
async def oauth_callback(
    response: Response,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    oauth_state: Annotated[str | None, Cookie(alias=_STATE_COOKIE)] = None,
) -> Response:
    if not code or not state or not oauth_state or state != oauth_state:
        raise HTTPException(400, "invalid OAuth state")
    cfg = load_oauth_config()
    token_url = "https://oauth2.googleapis.com/token"
    async with httpx.AsyncClient(timeout=20.0) as client:
        tok = await client.post(
            token_url,
            data={
                "code": code,
                "client_id": cfg.client_id,
                "client_secret": cfg.client_secret,
                "redirect_uri": cfg.callback_url,
                "grant_type": "authorization_code",
            },
        )
        if tok.status_code != 200:
            raise HTTPException(401, "token exchange failed")
        access = tok.json().get("access_token")
        ui = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access}"},
        )
        if ui.status_code != 200:
            raise HTTPException(401, "userinfo failed")
        email = str(ui.json().get("email") or "").strip().lower()

    if not email_allowed(email):
        raise HTTPException(
            403,
            f"email not on allowlist (allowed: {', '.join(sorted(ALLOWLIST))})",
        )

    body = (
        f"<html><body><p>OK — přihlášen jako {email}. "
        "Session cookie nastavená; MCP/REST mohou pokračovat.</p></body></html>"
    )
    out = Response(content=body, media_type="text/html")
    out.set_cookie(
        _COOKIE,
        _serializer().dumps({"email": email}),
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(cfg.public_url),
        max_age=60 * 60 * 24 * 30,
    )
    out.delete_cookie(_STATE_COOKIE)
    return out


@router.get("/oauth/me")
def oauth_me(
    session: Annotated[str | None, Cookie(alias=_COOKIE)] = None,
) -> dict[str, str]:
    email = read_session_email(session)
    if not email:
        raise HTTPException(401, "not signed in")
    return {"email": email, "audit": f"oauth:{email}"}
