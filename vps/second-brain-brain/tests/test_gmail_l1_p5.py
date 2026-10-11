"""T6 — Gmail L1 P5 caps."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.gmail_client import BODY_CAP, INBOX_META_CAP, list_l1  # noqa: E402


def test_inbox_cap_and_sent_thread_join():
    def fetcher(mailbox: str, label: str):
        if label == "INBOX":
            return [
                {
                    "id": f"i{n}",
                    "thread_id": f"t{n}",
                    "date": f"2026-10-{n:02d}",
                    "subject": f"S{n}",
                    "body": "x",
                }
                for n in range(1, INBOX_META_CAP + 20)
            ]
        # SENT: only t1 and orphan
        return [
            {"id": "s1", "thread_id": "t1", "date": "2026-10-01", "subject": "re"},
            {"id": "s9", "thread_id": "orphan", "date": "2026-10-01", "subject": "x"},
        ]

    result = list_l1(mailboxes=("workspace",), fetcher=fetcher)
    assert result.error_reason is None
    inbox = [m for m in result.messages if m.label == "INBOX"]
    sent = [m for m in result.messages if m.label == "SENT"]
    assert len(inbox) == INBOX_META_CAP
    assert {m.thread_id for m in sent} == {"t1"}
    assert result.bodies_fetched <= BODY_CAP
