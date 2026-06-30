"""Unit tests for triage_slack_relevance (no Drive I/O)."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import triage_slack_relevance as mod  # noqa: E402


def _guess_proj(text: str, rel: str) -> str:
    return "firemni-procesy"


THREAD_PASSIVE = """---
source: slack
---

**Vlákno:** Zoom licence
**Kanál:** team-it-support

> **Lukáš** 2026-06-30 10:12
> nechám to na vás, já tam vůbec přístup nemám

> **Jindřich** 2026-06-30 10:15
> @Lukáš can you cancel the old subscription?

> **Lukáš** 2026-06-30 10:16
> @Jindřich can you cancel? díky
"""

THREAD_DELAY = """**Vlákno:** DM
**Kanál:** dm-misa-gv

> **Lukáš** 2026-06-29 18:00
> delay na call, pardon — protáhl jsem call
"""

THREAD_COMMITMENT = """**Vlákno:** Strategie
**Kanál:** strategy

> **Lukáš** 2026-06-28 09:00
> musím připravit podklady pro board do pátku
"""

CAPTURE_WITH_COMMENT = """**Čas:** 2026-06-30 11:00
**Uživatel (Slack ID):** U123

## Komentář
musím domluvit follow-up s klientem do středy

## Forwardovaný obsah
> **Pavel** krátká zpráva
"""

CAPTURE_FORWARD_ONLY = """**Čas:** 2026-06-30 11:00
**Uživatel (Slack ID):** U123

## Komentář


## Forwardovaný obsah
""" + ("> **Someone** line\n" * 30)


def test_classify_thread_dump():
    rel = "01-INBOX/slack/2026-06-30_team-it-support_1781818693.549869.md"
    assert mod.classify_slack_source(rel, THREAD_PASSIVE) == "thread_dump"


def test_classify_capture_n8n():
    rel = "01-INBOX/slack/2026-06-30-1100-_claude-capture-strategy.md"
    assert mod.classify_slack_source(rel, CAPTURE_WITH_COMMENT) == "capture_n8n"


def test_passive_thread_archives():
    rel = "01-INBOX/slack/2026-06-30_team-it-support_1781818693.549869.md"
    result = mod.evaluate_slack_inbox_relevance(rel, THREAD_PASSIVE, guess_proj=_guess_proj)
    assert result is not None
    assert result.route == "archive"
    assert result.source_kind == "thread_dump"
    assert result.confidence >= 0.75


def test_delay_apology_archives():
    rel = "01-INBOX/slack/2026-06-29_dm-misa-gv_1781700000.000000.md"
    result = mod.evaluate_slack_inbox_relevance(rel, THREAD_DELAY, guess_proj=_guess_proj)
    assert result.route == "archive"


def test_commitment_routes_batch():
    rel = "01-INBOX/slack/2026-06-28_strategy_1781600000.000000.md"
    result = mod.evaluate_slack_inbox_relevance(rel, THREAD_COMMITMENT, guess_proj=_guess_proj)
    assert result.route == "batch"
    assert "musím" in result.lukas_text.lower()


def test_capture_comment_routes_batch():
    rel = "01-INBOX/slack/2026-06-30-1100-_claude-capture-strategy.md"
    result = mod.evaluate_slack_inbox_relevance(rel, CAPTURE_WITH_COMMENT, guess_proj=_guess_proj)
    assert result.route == "batch"
    assert result.source_kind == "capture_n8n"


def test_capture_forward_only_routes_deep():
    rel = "01-INBOX/slack/2026-06-30-1100-_claude-capture-forward.md"
    result = mod.evaluate_slack_inbox_relevance(rel, CAPTURE_FORWARD_ONLY, guess_proj=_guess_proj)
    assert result.route == "deep"


def test_archive_proposal_shape():
    rel = "01-INBOX/slack/2026-06-30_team-it-support_1781818693.549869.md"
    result = mod.evaluate_slack_inbox_relevance(rel, THREAD_PASSIVE, guess_proj=_guess_proj)
    pr = mod.slack_archive_proposal(rel, THREAD_PASSIVE, result)
    assert pr["proposalType"] == "archive_only"
    assert pr["kind"] == "slack_thread_archive"
    assert pr["slack_route"] == "archive"


def test_non_slack_returns_none():
    assert mod.evaluate_slack_inbox_relevance("01-INBOX/email/in.md", "body") is None
