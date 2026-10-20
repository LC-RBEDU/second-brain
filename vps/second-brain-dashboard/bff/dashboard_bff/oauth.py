"""Google OAuth for the dashboard cookie. Same client as Brain, own redirect URI."""

from __future__ import annotations

import os
import secrets
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import Cookie, FastAPI, HTTPException, Query, Response

from dashboard_bff.app import ALLOWED_EMAIL, COOKIE, sign_session

STATE_COOKIE = "sb_dashboard_oauth_state"


def callback_url(public_url: str) -> str:
    base = (public_url or "").strip().rstrip("/")
    if not base:
        raise ValueError("DASHBOARD_PUBLIC_URL is empty")
    return f"{base}/oauth/callback"


def _public_url() -> str:
    return (os.environ.get("DASHBOARD_PUBLIC_URL") or "").strip()


def _secure(public_url: str) -> bool:
    return public_url.startswith("https")


def attach_oauth(app: FastAPI) -> None:
    @app.get("/oauth/authorize")
    def oauth_authorize() -> Response:
        client_id = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
        public = _public_url()
        if not client_id or not public:
            raise HTTPException(500, "GOOGLE_CLIENT_ID / DASHBOARD_PUBLIC_URL not configured")
        state = secrets.token_urlsafe(24)
        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": callback_url(public),
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "online",
                "prompt": "select_account",
            }
        )
        response = Response(status_code=302)
        response.headers["Location"] = f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
        response.set_cookie(
            STATE_COOKIE,
            state,
            httponly=True,
            samesite="lax",
            secure=_secure(public),
            max_age=600,
        )
        return response

    @app.get("/oauth/callback")
    async def oauth_callback(
        code: Annotated[str | None, Query()] = None,
        state: Annotated[str | None, Query()] = None,
        oauth_state: Annotated[str | None, Cookie(alias=STATE_COOKIE)] = None,
    ) -> Response:
        if not code or not state or not oauth_state or state != oauth_state:
            raise HTTPException(400, "invalid OAuth state")
        public = _public_url()
        client_id = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
        client_secret = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
        async with httpx.AsyncClient(timeout=20.0) as client:
            token = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": callback_url(public),
                    "grant_type": "authorization_code",
                },
            )
            if token.status_code != 200:
                raise HTTPException(401, "token exchange failed")
            access = token.json().get("access_token")
            userinfo = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access}"},
            )
            if userinfo.status_code != 200:
                raise HTTPException(401, "userinfo failed")
            email = str(userinfo.json().get("email") or "").strip().lower()
        if email != ALLOWED_EMAIL:
            raise HTTPException(403, "forbidden")
        out = Response(status_code=302)
        out.headers["Location"] = "/"
        out.set_cookie(
            COOKIE,
            sign_session(email, app.state.secret),
            httponly=True,
            samesite="lax",
            secure=_secure(public),
            max_age=60 * 60 * 24 * 30,
        )
        out.delete_cookie(STATE_COOKIE)
        return out
