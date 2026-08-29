"""Unit tests for reminders scheduling helpers."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import reminders as mod  # noqa: E402

TZ = ZoneInfo("Europe/Prague")


def test_build_reminder_future():
    deliver = datetime.now(TZ) + timedelta(hours=2)
    r = mod.build_reminder(message="Ping Domču", deliver_at=deliver, task_ref="S12-16 — test")
    assert r["status"] == "pending"
    assert r["message"] == "Ping Domču"
    assert r["task_ref"].startswith("S12-16")
    assert r["id"].endswith(f"-rem-{r['id'].split('-rem-')[-1]}")


def test_is_due_only_pending():
    deliver = datetime.now(TZ) - timedelta(minutes=1)
    r = {
        "status": "pending",
        "deliver_at": mod.format_deliver_at(deliver, tz=TZ),
        "message": "x",
    }
    assert mod.is_due(r, datetime.now(TZ), tz=TZ) is True
    r["status"] = "sent"
    assert mod.is_due(r, datetime.now(TZ), tz=TZ) is False


def test_format_slack_text_with_task_ref():
    text = mod.format_slack_text(
        {"message": "Ahoj", "task_ref": "S12-16 — H2 rozpočty — urgovat Domču"}
    )
    assert "Ahoj" in text
    assert "S12-16" in text
