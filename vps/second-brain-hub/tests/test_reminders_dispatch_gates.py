"""B34b — skipped / PAUSED → 0 HTTP, no attempt++."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_LIB = Path(__file__).resolve().parents[1] / "lib"
_CRON = Path(__file__).resolve().parents[1] / "cron"
for p in (_LIB, _CRON):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import reminders_dispatch as disp  # noqa: E402


def test_paused_skips_http(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("VAULT_WRITERS_PAUSED", "1")

    class _V:
        skipped = False

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    due = [
        (
            "00-System/Reminders-Pending/x.json",
            {
                "id": "r1",
                "status": "pending",
                "deliver_at": "2000-01-01T00:00:00+01:00",
                "message": "x",
                "attempt_count": 0,
            },
        )
    ]
    with patch.object(disp, "open_vault", return_value=_V()):
        with patch.object(disp, "_list_pending", return_value=due):
            with patch.object(disp, "is_due", return_value=True):
                with patch.object(disp, "deliver_chat_chain") as chain:
                    disp.main()
                    chain.assert_not_called()


def test_vault_skipped_zero_http():
    class _V:
        skipped = True
        skip_reason = "vault_dirty_start"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    with patch.object(disp, "open_vault", return_value=_V()):
        with patch.object(disp, "deliver_chat_chain") as chain:
            disp.main()
            chain.assert_not_called()
