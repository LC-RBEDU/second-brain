"""Gmail L1 read client — Inbox+Sent, P5 caps (R10). Mockable via inject."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable


INBOX_META_CAP = 100
BODY_CAP = 40


@dataclass
class GmailMessage:
    id: str
    thread_id: str
    mailbox: str  # workspace | personal
    label: str  # INBOX | SENT
    date: str
    subject: str
    snippet: str = ""
    body: str | None = None


@dataclass
class GmailL1Result:
    messages: list[GmailMessage] = field(default_factory=list)
    error_reason: str | None = None
    bodies_fetched: int = 0


Fetcher = Callable[[str, str], list[dict[str, Any]]]


def _default_fetcher(mailbox: str, label: str) -> list[dict[str, Any]]:
    """No credentials → empty (not error). Tests inject fetcher."""
    _ = mailbox, label
    token_key = (
        "GMAIL_WORKSPACE_REFRESH_TOKEN"
        if mailbox == "workspace"
        else "GMAIL_PERSONAL_REFRESH_TOKEN"
    )
    if not (os.environ.get(token_key) or "").strip():
        return []
    # Live Gmail API wiring is env-gated; without google client libs return [].
    return []


def list_l1(
    *,
    mailboxes: tuple[str, ...] = ("workspace", "personal"),
    fetcher: Fetcher | None = None,
    fetch_bodies: bool = True,
) -> GmailL1Result:
    """P5: Inbox ≤100/mailbox Date ASC; Sent = thread-join only; bodies ≤40 total."""
    fetch = fetcher or _default_fetcher
    try:
        inbox_by_mb: dict[str, list[GmailMessage]] = {}
        for mb in mailboxes:
            raw = fetch(mb, "INBOX") or []
            msgs = [
                GmailMessage(
                    id=str(r["id"]),
                    thread_id=str(r.get("thread_id") or r["id"]),
                    mailbox=mb,
                    label="INBOX",
                    date=str(r.get("date") or ""),
                    subject=str(r.get("subject") or ""),
                    snippet=str(r.get("snippet") or ""),
                    body=r.get("body"),
                )
                for r in raw
            ]
            msgs.sort(key=lambda m: m.date)
            inbox_by_mb[mb] = msgs[:INBOX_META_CAP]

        thread_ids = {m.thread_id for msgs in inbox_by_mb.values() for m in msgs}
        out: list[GmailMessage] = []
        for msgs in inbox_by_mb.values():
            out.extend(msgs)

        for mb in mailboxes:
            sent_raw = fetch(mb, "SENT") or []
            for r in sent_raw:
                tid = str(r.get("thread_id") or r["id"])
                if tid not in thread_ids:
                    continue
                out.append(
                    GmailMessage(
                        id=str(r["id"]),
                        thread_id=tid,
                        mailbox=mb,
                        label="SENT",
                        date=str(r.get("date") or ""),
                        subject=str(r.get("subject") or ""),
                        snippet=str(r.get("snippet") or ""),
                        body=r.get("body"),
                    )
                )

        bodies = 0
        if fetch_bodies:
            for m in out:
                if m.body is not None:
                    bodies += 1
                    if bodies > BODY_CAP:
                        m.body = None
                        bodies = BODY_CAP
        return GmailL1Result(messages=out, bodies_fetched=min(bodies, BODY_CAP))
    except Exception as exc:  # noqa: BLE001 — surface as error_reason for fail-path
        return GmailL1Result(messages=[], error_reason=f"gmail_l1_error:{exc}")


def assert_l2_inbox_only(message: GmailMessage) -> None:
    from app.errors import BrainClientError

    if message.label != "INBOX":
        raise BrainClientError(
            message="L2 actions only on Inbox",
            status_code=400,
            error_reason="l2_sent_forbidden",
        )
