"""Watchlist enroll / ignore / versioning for slack_poll_core."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import slack_poll_core as poll  # noqa: E402

TZ = ZoneInfo("Europe/Prague")


def test_im_flattens_to_channel_zero():
    match = {
        "channel": {"id": "D1", "name": "user", "is_im": True},
        "ts": "200.2",
        "thread_ts": "200.1",
        "text": "hi",
    }
    hit = poll.hit_from_match(match, "to_me")
    assert hit is not None
    assert hit.kind == "dm"
    assert hit.thread_ts == poll.FLAT_THREAD_TS


def test_mpim_with_thread_keeps_root():
    match = {
        "channel": {"id": "C0C0", "name": "gdm", "is_mpim": True},
        "ts": "1789675591.963599",
        "permalink": "https://x/archives/C0C0/p1789675591963599?thread_ts=1789453970.360699",
        "text": "reply",
    }
    hit = poll.hit_from_match(match, "to_me")
    assert hit is not None
    assert hit.kind == "gdm"
    assert hit.thread_ts == "1789453970.360699"


def test_mpim_flat_uses_zero():
    match = {
        "channel": {"id": "C0C0", "name": "gdm", "is_mpim": True},
        "ts": "10.0",
        "text": "hi",
    }
    hit = poll.hit_from_match(match, "from_me")
    assert hit is not None
    assert hit.thread_ts == poll.FLAT_THREAD_TS


def test_channel_mention_keeps_thread_ts():
    match = {
        "channel": {"id": "C1", "name": "general", "is_im": False},
        "ts": "200.2",
        "thread_ts": "200.1",
        "text": "<@U> look",
    }
    hit = poll.hit_from_match(match, "mention")
    assert hit is not None
    assert hit.thread_ts == "200.1"
    assert hit.kind == "mention"


def test_b3_archive_does_not_clear_watch():
    state = poll.PollState(bootstrapped=True)
    hit = poll.ThreadHit("C1", "gdm", poll.FLAT_THREAD_TS, "10.0", "gdm")
    poll.enroll_watch(state, hit, seed_latest_ts="10.0", reason="gdm")
    key = poll.thread_key("C1", poll.FLAT_THREAD_TS)
    assert key in state.watch
    assert state.watch[key].ignored is False
    # Simulating archive: only touch seen/rel, not ignored
    state.watch[key].rel = ""
    assert state.watch[key].ignored is False


def test_b4_ignore_stops_refetch():
    state = poll.PollState(bootstrapped=True)
    hit = poll.ThreadHit("C1", "gdm", poll.FLAT_THREAD_TS, "10.0", "gdm")
    poll.enroll_watch(state, hit, seed_latest_ts="10.0")
    poll.mark_ignored(state, "C1", poll.FLAT_THREAD_TS)
    entry = state.watch[poll.thread_key("C1", poll.FLAT_THREAD_TS)]
    assert entry.ignored is True
    assert poll.should_refetch(entry, "99.0") is False
    assert poll.select_watch_batch(state) == []


def test_b5_newer_ts_triggers_refetch():
    entry = poll.WatchEntry(kind="gdm", reason="gdm", latest_ts="10.0", ignored=False)
    assert poll.should_refetch(entry, "10.0") is False
    assert poll.should_refetch(entry, "11.0") is True


def test_enroll_seed_not_wall_clock_and_no_flood():
    state = poll.PollState(bootstrapped=True)
    hit = poll.ThreadHit("C1", "gdm", poll.FLAT_THREAD_TS, "50.0", "gdm")
    entry = poll.enroll_watch(state, hit, seed_latest_ts="50.0")
    assert entry.latest_ts == "50.0"
    # Re-enroll with older seed must not reset
    poll.enroll_watch(state, hit, seed_latest_ts="40.0")
    assert state.watch[poll.thread_key("C1", poll.FLAT_THREAD_TS)].latest_ts == "50.0"


def test_next_version_and_filename():
    entry = poll.WatchEntry(kind="dm", reason="dm", latest_ts="1", max_v=2)
    assert poll.next_version(entry) == 3
    assert poll.next_version(entry, scanned_max=5) == 6
    name = poll.inbox_filename_vN(
        datetime(2026, 9, 23, 12, tzinfo=TZ),
        "pavel-kata",
        "1789453970.360699",
        3,
    )
    assert name == "2026-09-23_pavel-kata_1789453970.360699_v3.md"


def test_max_version_from_names():
    names = [
        "2026-09-17_gdm_1789453970.360699_v1.md",
        "2026-09-23_gdm_1789453970.360699_v3.md",
        "other_111.0_v9.md",
    ]
    assert poll.max_version_from_names(names, "C1", "1789453970.360699") == 3


def test_format_includes_verze():
    hit = poll.ThreadHit("C1", "gdm", "1789453970.360699", "11.0", "gdm", permalink="https://x")
    md = poll.format_thread_markdown(
        hit,
        [{"user": "U1", "ts": "11.0", "text": "hello"}],
        {"U1": "Káťa"},
        tz=TZ,
        version=3,
    )
    assert "**Verze:** v3 ← AKTUÁLNÍ" in md
    assert "**Thread TS:** 1789453970.360699" in md


def test_discover_skips_channel_from_to_me():
    grouped = {
        "to_me": [
            {
                "channel": {"id": "Cchan", "name": "pub", "is_im": False, "is_mpim": False},
                "ts": "9.0",
                "text": "hi",
            },
            {
                "channel": {"id": "D1", "name": "u", "is_im": True},
                "ts": "10.0",
                "text": "dm",
            },
        ]
    }
    hits = poll.discover_hits(grouped)
    assert len(hits) == 1
    assert hits[0].channel_id == "D1"
    assert hits[0].thread_ts == poll.FLAT_THREAD_TS


def test_merge_history_and_replies():
    history = [{"ts": "1.0", "text": "parent", "reply_count": 1}]
    replies = {"1.0": [{"ts": "1.0", "text": "parent"}, {"ts": "2.0", "text": "reply"}]}
    merged = poll.merge_channel_history_with_replies(history, replies)
    assert [m["ts"] for m in merged] == ["1.0", "2.0"]
    assert poll.newest_ts(merged) == "2.0"


def test_ignored_re_enroll_noop():
    state = poll.PollState(bootstrapped=True)
    hit = poll.ThreadHit("C1", "gdm", poll.FLAT_THREAD_TS, "10.0", "gdm")
    poll.enroll_watch(state, hit, seed_latest_ts="10.0")
    poll.mark_ignored(state, "C1", poll.FLAT_THREAD_TS)
    again = poll.enroll_watch(state, hit, seed_latest_ts="20.0")
    assert again.ignored is True


def test_boost_ts_prioritizes_batch():
    state = poll.PollState(bootstrapped=True)
    old = poll.ThreadHit("Cold", "a", poll.FLAT_THREAD_TS, "10.0", "dm")
    hot = poll.ThreadHit("Chot", "b", poll.FLAT_THREAD_TS, "50.0", "dm")
    poll.enroll_watch(state, old, seed_latest_ts="10.0")
    poll.enroll_watch(state, hot, seed_latest_ts="50.0")
    # Both already dumped — boost wins among captured
    state.watch[poll.thread_key("Cold", poll.FLAT_THREAD_TS)].latest_ts = "90.0"
    state.watch[poll.thread_key("Cold", poll.FLAT_THREAD_TS)].rel = "x.md"
    state.watch[poll.thread_key("Chot", poll.FLAT_THREAD_TS)].latest_ts = "50.0"
    state.watch[poll.thread_key("Chot", poll.FLAT_THREAD_TS)].rel = "y.md"
    poll.enroll_watch(
        state,
        poll.ThreadHit("Chot", "b", poll.FLAT_THREAD_TS, "95.0", "dm"),
        seed_latest_ts="50.0",
    )
    batch = poll.select_watch_batch(state, limit=2)
    assert batch[0] == poll.thread_key("Chot", poll.FLAT_THREAD_TS)
    assert state.watch[batch[0]].boost_ts == "95.0"
    poll.advance_watch(state, batch[0], latest_ts="95.0", rel="y2.md", version=2)
    assert state.watch[batch[0]].boost_ts == ""


def test_empty_rel_outranks_newer_captured():
    """First dump must not starve behind newer already-captured watches (QA finding)."""
    state = poll.PollState(bootstrapped=True)
    stale = poll.ThreadHit("Cstale", "old", "111.0", "10.0", "gdm")
    fresh = poll.ThreadHit("Cfresh", "new", poll.FLAT_THREAD_TS, "99.0", "dm")
    poll.enroll_watch(state, stale, seed_latest_ts="10.0")
    poll.enroll_watch(state, fresh, seed_latest_ts="99.0")
    state.watch[poll.thread_key("Cfresh", poll.FLAT_THREAD_TS)].rel = "already.md"
    # stale still has empty rel
    batch = poll.select_watch_batch(state, limit=1)
    assert batch[0] == poll.thread_key("Cstale", "111.0")
