"""T7 — in-memory batch store."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.batch_store import clear_for_tests, create_batch, get_batch  # noqa: E402


def test_create_and_get_batch():
    clear_for_tests()
    b = create_batch(
        "mailbox",
        [{"id": "1", "action": "archive"}, {"id": "2", "action": "send"}],
        principal="service",
    )
    got = get_batch(b.batch_id)
    assert got is not None
    assert got.items[0].reversible is True
    assert got.items[1].reversible is False


def test_unknown_batch_none():
    clear_for_tests()
    assert get_batch("missing") is None
