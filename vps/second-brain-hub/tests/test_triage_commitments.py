"""Unit tests for triage_commitments (no Drive I/O)."""
from __future__ import annotations

import sys
from pathlib import Path

_CRON = Path(__file__).resolve().parents[1] / "cron"
if str(_CRON) not in sys.path:
    sys.path.insert(0, str(_CRON))

import triage_commitments as mod  # noqa: E402


def _guess_proj(text: str, rel_path: str) -> str:
    if "finance" in text.lower():
        return "finance"
    return "firemni-procesy"


SENT_SAMPLE = """---
source: sent
messageId: abc123
to: klient@example.com
subject: Faktura a termín
date: 2026-05-20T14:30:00+02:00
from: lukas@redbuttonedu.cz
---

# Email: Faktura a termín

**Source**: sent
**To**: klient@example.com
**Date**: 20. 5. 2026 14:30

## Tělo

Dobrý den, fakturu pošlu do pátku a domluvím se s účetní na DPH.
Děkuji.
"""


def test_is_sent_email_by_path_and_frontmatter():
    assert mod.is_sent_email("01-INBOX/email/sent/2026-05-20-test.md", "")
    assert mod.is_sent_email("01-INBOX/email/x.md", SENT_SAMPLE)
    assert not mod.is_sent_email("01-INBOX/email/incoming.md", "# Email\n\n**From**: other")


def test_heuristic_extract_finds_commitments():
    out = mod.heuristic_extract(
        "01-INBOX/email/sent/2026-05-20-test.md",
        SENT_SAMPLE,
        guess_proj=_guess_proj,
    )
    assert len(out) >= 1
    assert all(p["kind"] == "commitment" for p in out)
    assert all(p["action"] == "add_task" for p in out)
    titles = " ".join(p["title"].lower() for p in out)
    assert "pošlu" in titles or "domluvím" in titles


def test_heuristic_confidence_range():
    out = mod.heuristic_extract(
        "01-INBOX/email/sent/x.md",
        SENT_SAMPLE,
        guess_proj=_guess_proj,
    )
    for p in out:
        assert 0.0 < p["confidence"] <= 1.0
        assert p["sourceFile"].endswith(".md")
        assert "citace" in p["notes"].lower() or "odeslaný" in p["notes"].lower()


def test_heuristic_skips_neutral_sent_email():
    neutral = """---
source: sent
messageId: xyz
subject: Díky
---

## Tělo

Děkuji za schůzku, bylo to fajn. Hezký den.
"""
    out = mod.heuristic_extract("01-INBOX/email/sent/thanks.md", neutral, guess_proj=_guess_proj)
    assert out == []


def test_email_body_text_strips_frontmatter():
    body = mod.email_body_text(SENT_SAMPLE)
    assert "messageId" not in body
    assert "pošlu do pátku" in body


def test_extract_commitments_non_sent_returns_empty():
    incoming = "# Email\n\n## Tělo\n\nPošlu report zítra."
    assert mod.extract_commitments("01-INBOX/email/in.md", incoming, guess_proj=_guess_proj) == []
