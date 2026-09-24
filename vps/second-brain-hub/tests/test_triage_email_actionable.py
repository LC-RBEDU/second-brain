"""Tests for inbound e-mail actionable → must propose task."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import triage_email_actionable as mod  # noqa: E402

JANA_DPH = """---
source: email
mailbox: personal
from: "\\"Jana Kočová\\" <janakocova9@gmail.com>"
subject: "DPH 8/2026"
---
# Email: DPH 8/2026

Za srpen Vám vychází daňová povinnost ve výši 20 876 Kč.

Údaje k platbě:

Číslo účtu: 705-77628031/0710

Variabilní symbol: 7802085764

Datum splatnosti: 25.9.2026
"""


def test_jana_dph_must_propose_task():
    rel = "01-INBOX/email/2026-09-23-0851-jana-kocova-dph-8-2026.md"
    r = mod.evaluate_email_actionable(
        rel, JANA_DPH, known_emails={"janakocova9@gmail.com"}
    )
    assert r.must_propose_task is True
    assert r.deadline_hint == "2026-09-25"
    assert r.is_personal_mailbox is True
    assert r.is_payment_obligation is True
    assert r.amount_czk == "20876"
    assert r.account == "705-77628031/0710"
    assert r.vs == "7802085764"
    assert mod.email_must_propose_task(rel, JANA_DPH, lide_dir=None) is True
    steps = mod.payment_solo_steps("OS11", r)
    assert "20876" in steps[0]
    assert "7802085764" in steps[0]


def test_strong_signal_without_known_or_personal():
    """B1 izolovaně — workspace from, known set bez odesílatele, bez personal."""
    body = """---
mailbox: workspace
from: Someone <x@example.com>
---
Daňová povinnost 10 000 Kč. Datum splatnosti: 1.10.2026
"""
    r = mod.evaluate_email_actionable(
        "01-INBOX/email/2026-10-01-tax.md",
        body,
        known_emails={"other@example.com"},
    )
    assert r.must_propose_task is True
    assert r.is_personal_mailbox is False


def test_noreply_bulk_not_forced():
    body = """---
mailbox: personal
from: News <noreply@shop.example>
---
Datum splatnosti: 1.10.2026 — faktura v příloze newsletteru
"""
    r = mod.evaluate_email_actionable(
        "01-INBOX/email/sb-personal-news.md",
        body,
        known_emails=set(),
    )
    assert r.must_propose_task is False
    assert r.is_bulk is True


def test_sent_subdir_skipped():
    r = mod.evaluate_email_actionable(
        "01-INBOX/email/sent/2026-09-01-foo.md",
        JANA_DPH,
        known_emails={"janakocova9@gmail.com"},
    )
    assert r.must_propose_task is False


def test_soft_ask_from_known_contact():
    body = """---
from: "Jana Kočová" <janakocova9@gmail.com>
mailbox: workspace
---
Prosím Tě o potvrzení podkladů do pátku.
"""
    r = mod.evaluate_email_actionable(
        "01-INBOX/email/2026-09-01-jana.md",
        body,
        known_emails={"janakocova9@gmail.com"},
    )
    assert r.must_propose_task is True


def test_fyi_without_action_not_forced():
    body = """---
mailbox: personal
from: Friend <friend@example.com>
---
Ahoj, jen FYI — hezký víkend.
"""
    r = mod.evaluate_email_actionable(
        "01-INBOX/email/sb-personal-fyi.md",
        body,
        known_emails={"friend@example.com"},
    )
    assert r.must_propose_task is False


def test_enforce_rewrites_archive_only():
    pr = {
        "proposalType": "archive_only",
        "sourceFile": "01-INBOX/email/jana-dph.md",
        "id": "p1",
    }
    fixed = mod.enforce_actionable_on_proposal(pr, "01-INBOX/email/jana-dph.md", JANA_DPH)
    assert fixed["proposalType"] == "add_task"
    assert fixed["agent"] == "solo"
    assert fixed["deadline"] == "2026-09-25"


def test_enforce_rewrites_deep_analysis():
    pr = {
        "proposalType": "deep_analysis",
        "requires_deep_analysis": True,
        "sourceFile": "01-INBOX/email/jana-dph.md",
        "id": "p2",
    }
    fixed = mod.enforce_actionable_on_proposal(pr, "01-INBOX/email/jana-dph.md", JANA_DPH)
    assert fixed["proposalType"] == "add_task"
    assert "requires_deep_analysis" not in fixed
