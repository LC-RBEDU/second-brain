"""T6b — L2 only Inbox."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.errors import BrainClientError  # noqa: E402
from app.gmail_client import GmailMessage, assert_l2_inbox_only  # noqa: E402


def test_sent_rejected():
    msg = GmailMessage(
        id="1", thread_id="t", mailbox="workspace", label="SENT", date="", subject=""
    )
    with pytest.raises(BrainClientError) as ei:
        assert_l2_inbox_only(msg)
    assert ei.value.error_reason == "l2_sent_forbidden"


def test_inbox_ok():
    msg = GmailMessage(
        id="1", thread_id="t", mailbox="workspace", label="INBOX", date="", subject=""
    )
    assert_l2_inbox_only(msg)
