"""Gmail drafts.create only. This module has no send method on purpose.

`gmail.compose` can send. send-policy.yaml is draft_only and the code path
never calls drafts.send or messages.send.
"""
from __future__ import annotations

import base64
import json
import os
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"


def credentials_from_env(env: dict | None = None) -> Credentials | None:
    env = env if env is not None else os.environ
    raw = (env.get("GOOGLE_GMAIL_OAUTH_JSON") or "").strip()
    if not raw:
        return None
    info = json.loads(raw)
    scopes = info.get("scopes") or [COMPOSE_SCOPE]
    # Refuse a token that was minted only for Drive.
    if COMPOSE_SCOPE not in scopes and "https://mail.google.com/" not in scopes:
        if not any("gmail" in s for s in scopes):
            return None
    return Credentials(
        token=None,
        refresh_token=info["refresh_token"],
        token_uri=info.get("token_uri") or "https://oauth2.googleapis.com/token",
        client_id=info["client_id"],
        client_secret=info["client_secret"],
        scopes=scopes,
    )


def build_reply_body(
    *,
    to: str,
    subject: str,
    body: str,
    thread_id: str,
    in_reply_to: str = "",
    references: str = "",
) -> dict:
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if in_reply_to:
        msgid = in_reply_to if in_reply_to.startswith("<") else f"<{in_reply_to.strip('<>')}>"
        message["In-Reply-To"] = msgid
        message["References"] = references or msgid
    message.set_content(body)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    payload: dict = {"message": {"raw": raw}}
    if thread_id:
        payload["message"]["threadId"] = thread_id
    return payload


def create_reply_draft(creds: Credentials, body: dict) -> str:
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    draft = service.users().drafts().create(userId="me", body=body).execute()
    return str(draft.get("id") or "")
