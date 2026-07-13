"""Unit tests for inbox_archive (local Path vault)."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import inbox_archive as mod  # noqa: E402


def test_list_colocated_slack_attachments(tmp_path: Path):
    slack = tmp_path / "01-INBOX" / "slack"
    slack.mkdir(parents=True)
    md = "2026-07-01-0907-_claude-capture-strategy-delivery-tooling.md"
    att = "2026-07-01-0907-F0BEE2P7Q6N-Product Vision.docx"
    other = "2026-07-01-0914-F0BEAQDV71B-Hackathon.docx"
    (slack / md).write_text("# capture\n", encoding="utf-8")
    (slack / att).write_bytes(b"docx")
    (slack / other).write_bytes(b"docx2")
    found = mod.list_colocated_attachments(slack, md)
    assert [p.name for p in found] == [att]


def test_list_colocated_email_attachments(tmp_path: Path):
    sent = tmp_path / "01-INBOX" / "email" / "sent"
    sent.mkdir(parents=True)
    md = "2026-07-01-1621-sent-jan@redbutton.cz-podklady.md"
    att = "2026-07-01-1621-sent-jan@redbutton.cz-podklady__invoice.pdf"
    (sent / md).write_text("---\nsource: sent\n---\n", encoding="utf-8")
    (sent / att).write_bytes(b"pdf")
    found = mod.list_colocated_attachments(sent, md)
    assert [p.name for p in found] == [att]


def test_archive_inbox_capture_moves_md_and_attachments(tmp_path: Path):
    slack = tmp_path / "01-INBOX" / "slack"
    slack.mkdir(parents=True)
    md = "2026-07-01-0907-_claude-capture-test.md"
    att = "2026-07-01-0907-F123-demo.docx"
    (slack / md).write_text("# Title\n\nbody\n", encoding="utf-8")
    (slack / att).write_bytes(b"docx")

    md_rel, atts = mod.archive_inbox_capture(tmp_path, f"01-INBOX/slack/{md}")

    assert md_rel == f"07-ARCHIV/inbox-processed/2026/07/slack/{md}"
    assert len(atts) == 1
    assert not (slack / md).exists()
    assert not (slack / att).exists()
    archived_md = tmp_path / md_rel
    assert archived_md.exists()
    assert "**ZPRACOVÁNO**" in archived_md.read_text(encoding="utf-8")
    assert (archived_md.parent / att).exists()


def test_archive_orphan_attachments(tmp_path: Path):
    slack_in = tmp_path / "01-INBOX" / "slack"
    arch = tmp_path / "07-ARCHIV" / "inbox-processed" / "2026" / "06" / "slack"
    arch.mkdir(parents=True)
    slack_in.mkdir(parents=True)
    md = "2026-06-29-1921-_claude-capture-antivarc.md"
    att = "2026-06-29-1921-F0BBBHXG4CF-NDA.docx"
    (arch / md).write_text("# archived\n", encoding="utf-8")
    (slack_in / att).write_bytes(b"docx")

    moves = mod.archive_orphan_inbox_attachments(tmp_path)
    assert len(moves) == 1
    assert not (slack_in / att).exists()
    assert (arch / att).exists()
