"""Slack Later poll selection and active window."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import assistant_window as win  # noqa: E402
import slack_poll_core as poll  # noqa: E402

TZ = ZoneInfo("Europe/Prague")


def test_active_window_08_to_24():
    assert win.in_active_window(datetime(2026, 9, 20, 7, 59, tzinfo=TZ)) is False
    assert win.in_active_window(datetime(2026, 9, 20, 8, 0, tzinfo=TZ)) is True
    assert win.in_active_window(datetime(2026, 9, 20, 23, 59, tzinfo=TZ)) is True
    assert win.in_active_window(datetime(2026, 9, 20, 0, 0, tzinfo=TZ)) is False


def test_bootstrap_does_not_select_history():
    state = poll.PollState()
    assert state.bootstrapped is False
    hits = poll.select_threads(
        {"mention": [{"channel": {"id": "C1", "name": "general"}, "ts": "10.1", "text": "hi"}]},
        state,
        now=datetime(2026, 9, 20, 9, tzinfo=TZ),
    )
    assert hits == []
    booted = poll.bootstrap_state(datetime(2026, 9, 20, 9, tzinfo=TZ))
    assert booted.bootstrapped is True
    assert float(booted.watermark_ts) > 1_000_000


def test_selects_full_thread_not_seen_again():
    state = poll.bootstrap_state(datetime(2026, 9, 1, 9, tzinfo=TZ))
    state.watermark_ts = "100"
    match = {
        "channel": {"id": "C1", "name": "general"},
        "ts": "200.2",
        "thread_ts": "200.1",
        "text": "<@U> look",
        "permalink": "https://slack.test/p",
    }
    hits = poll.select_threads({"mention": [match]}, state, now=datetime(2026, 9, 20, 9, tzinfo=TZ))
    assert len(hits) == 1
    assert hits[0].thread_ts == "200.1"
    md = poll.format_thread_markdown(
        hits[0],
        [
            {"user": "U1", "ts": "200.1", "text": "context before the tag"},
            {"user": "U2", "ts": "200.2", "text": "<@U014AEZD72S> can you?"},
        ],
        {"U1": "Anna", "U2": "Petr"},
        tz=TZ,
    )
    assert "context before the tag" in md
    assert "can you?" in md
    assert "kind: mention" in md
    assert "**Vlákno:**" in md
    poll.advance_seen(state, hits[0], "01-INBOX/slack/x.md")
    again = poll.select_threads({"mention": [match]}, state, now=datetime(2026, 9, 20, 9, tzinfo=TZ))
    assert again == []


def test_select_threads_newest_first():
    state = poll.bootstrap_state(datetime(2026, 9, 1, 9, tzinfo=TZ))
    state.watermark_ts = "100"
    older = {
        "channel": {"id": "C1", "name": "a"},
        "ts": "150.0",
        "thread_ts": "150.0",
        "text": "old",
    }
    newer = {
        "channel": {"id": "C2", "name": "b"},
        "ts": "300.0",
        "thread_ts": "300.0",
        "text": "new",
    }
    hits = poll.select_threads(
        {"dm": [older, newer]},
        state,
        now=datetime(2026, 9, 20, 9, tzinfo=TZ),
    )
    assert [h.latest_ts for h in hits] == ["300.0", "150.0"]


def test_permalink_thread_ts_beats_reply_ts():
    match = {
        "channel": {"id": "C1", "name": "priority"},
        "ts": "1789970417.435419",
        "permalink": "https://slack.test/archives/C1/p1789970417435419?thread_ts=1789561381.924319",
        "text": "saved",
    }
    hit = poll.hit_from_match(match, "saved_later")
    assert hit is not None
    assert hit.thread_ts == "1789561381.924319"
    assert hit.latest_ts == "1789970417.435419"
