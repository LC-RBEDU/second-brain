"""NEW-3 — mailbox propose rejects SENT."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.batch_store import clear_for_tests  # noqa: E402
from app.errors import BrainClientError  # noqa: E402
from app.tools.mailbox_propose_apply import mailbox_propose  # noqa: E402


def test_sent_label_rejected():
    clear_for_tests()
    with pytest.raises(BrainClientError) as ei:
        mailbox_propose([{"id": "1", "action": "archive", "label": "SENT"}])
    assert ei.value.error_reason == "l2_sent_forbidden"


def test_inbox_ok():
    clear_for_tests()
    out = mailbox_propose([{"id": "1", "action": "archive", "label": "INBOX"}])
    assert out["batch_id"]
