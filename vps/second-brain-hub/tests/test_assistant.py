"""Slack poll selection, hours, ingest pairing, draft-only Gmail body."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import assistant_ingest as ing  # noqa: E402
import assistant_window as win  # noqa: E402
import gmail_drafts as gmail  # noqa: E402
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


def test_sent_pair_closes_inbound_and_skips_draft():
    inbound = ing.InboxItem(
        rel="01-INBOX/email/a.md",
        fm={"source": "email", "gmail_thread_id": "t1", "from": "a@x.cz", "subject": "otázka?"},
        body="Můžeš se na to podívat?",
    )
    sent = ing.InboxItem(
        rel="01-INBOX/email/sent/b.md",
        fm={"source": "sent", "gmail_thread_id": "t1"},
        body="Už jsem odpověděl.",
    )
    actions = ing.plan_actions([inbound, sent])
    assert [a.op for a in actions] == ["handle"]
    assert "add_task" not in [a.op for a in actions]


def test_no_draft_without_question():
    item = ing.InboxItem(
        rel="01-INBOX/email/n.md",
        fm={"source": "email", "from": "a@x.cz"},
        body="FYI hotovo, nic po tobě nechci.",
    )
    actions = ing.plan_actions([item])
    assert actions[0].op == "skip"


def test_calendar_drop():
    item = ing.InboxItem(
        rel="01-INBOX/email/c.md",
        fm={"from": "calendar-noreply@google.com", "subject": "Invitation"},
        body="?",
    )
    assert ing.drop_email(item) is True


def test_sembly_is_deep_not_a_fake_minutes():
    item = ing.InboxItem(rel="01-INBOX/sembly/m.md", fm={"source": "sembly"}, body="přepis")
    actions = ing.plan_actions([item])
    assert actions[0].op == "deep"


def test_gmail_body_threads_and_module_does_not_send():
    body = gmail.build_reply_body(
        to="a@x.cz",
        subject="otázka",
        body="Ahoj,\n\nDíky\nL.\n",
        thread_id="thread-1",
        in_reply_to="<abc@mail.gmail.com>",
    )
    assert body["message"]["threadId"] == "thread-1"
    raw = __import__("base64").urlsafe_b64decode(body["message"]["raw"])
    assert b"In-Reply-To" in raw
    source = Path(gmail.__file__).read_text(encoding="utf-8")
    assert "drafts().send" not in source
    assert "messages().send" not in source
    assert "draft_only" in ing.SEND_POLICY_TEXT


def test_slack_draft_payload_keeps_thread_ts_string():
    payload = ing.slack_draft_payload("Ahoj, pošlu to.", "C1", "1789979263.882229", "https://slack/x")
    assert payload["thread_ts"] == "1789979263.882229"
    assert payload["draft_channel"] == "C0C3E0JFNA0"


def test_reply_address_strips_display_name():
    raw = '"\\"Lukáš Dzuroška\\" <lukas.dzuroska@redbuttonedu.cz>"'
    assert ing.reply_address(raw) == "lukas.dzuroska@redbuttonedu.cz"


def test_saved_later_is_not_a_slack_reply():
    item = ing.InboxItem(
        rel="01-INBOX/slack/later.md",
        fm={"kind": "saved_later", "channel_id": "C1", "thread_ts": "1.2"},
        body="můžeš se na to podívat?",
    )
    actions = ing.plan_actions([item])
    assert actions[0].op == "skip"
    assert actions[0].reason == "saved_later"


def test_compose_reply_uses_runner_not_a_stub():
    import reply_compose

    item = ing.InboxItem(
        rel="01-INBOX/email/a.md",
        fm={"from": "a@x.cz", "subject": "otázka"},
        body="Můžeš to poslat?",
    )
    text = reply_compose.compose_reply(item, "buď stručný", run=lambda prompt: "Ahoj,\n\nPošlu to.\n\nDíky\nL.")
    assert "Pošlu to." in text
    assert reply_compose.compose_reply(item, "", run=lambda prompt: "krátké") == ""

