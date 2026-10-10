"""Unit tests for reminders scheduling helpers (incl. A51 / T15)."""
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
    assert r["attempt_count"] == 0
    assert r["message"] == "Ping Domču"
    assert r["task_ref"].startswith("S12-16")
    assert r["id"].endswith(f"-rem-{r['id'].split('-rem-')[-1]}")


def test_is_due_pending_and_legacy_failed():
    deliver = datetime.now(TZ) - timedelta(minutes=1)
    r = {
        "status": "pending",
        "deliver_at": mod.format_deliver_at(deliver, tz=TZ),
        "message": "x",
    }
    now = datetime.now(TZ)
    assert mod.is_due(r, now, tz=TZ) is True
    r["status"] = "failed"
    assert mod.is_due(r, now, tz=TZ) is True
    r["status"] = "sent"
    assert mod.is_due(r, now, tz=TZ) is False


def test_is_due_respects_next_attempt_at():
    deliver = datetime.now(TZ) - timedelta(hours=1)
    future = datetime.now(TZ) + timedelta(minutes=30)
    r = {
        "status": "pending",
        "deliver_at": mod.format_deliver_at(deliver, tz=TZ),
        "next_attempt_at": mod.format_deliver_at(future, tz=TZ),
        "message": "x",
    }
    assert mod.is_due(r, datetime.now(TZ), tz=TZ) is False
    r["next_attempt_at"] = mod.format_deliver_at(
        datetime.now(TZ) - timedelta(minutes=1), tz=TZ
    )
    assert mod.is_due(r, datetime.now(TZ), tz=TZ) is True


def test_reminder_error_dual_read():
    assert mod.reminder_error({"last_error": "a", "error": "b"}) == "a"
    assert mod.reminder_error({"error": "b"}) == "b"
    assert mod.reminder_error({}) is None


def test_failed_dir_constant():
    assert mod.FAILED_DIR == "00-System/Reminders-Failed"


def test_format_slack_text_with_task_ref():
    text = mod.format_slack_text(
        {"message": "Ahoj", "task_ref": "S12-16 — H2 rozpočty — urgovat Domču"}
    )
    assert "Ahoj" in text
    assert "S12-16" in text
