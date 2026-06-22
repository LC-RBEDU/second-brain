"""Unit testy pro `triage_complexity.is_complex_source`.

Pokrývají subdir-based, size-based, content-based pravidla a override
komentář v hlavičce souboru.
"""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import triage_complexity as mod  # noqa: E402


def _generate_long_body(words: int) -> str:
    """Helper — generuje body s ``words`` slovy v jednom dlouhém odstavci."""
    return "lorem " * words


# ---------------------------------------------------------------------------
# Subdir-based
# ---------------------------------------------------------------------------


def test_sembly_subdir_is_always_deep():
    rel = "01-INBOX/sembly/2026-05-23-board-meeting.md"
    body = "# Meeting\n\nKrátké shrnutí.\n"
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any("sembly" in r for r in reasons)


def test_sembly_with_empty_body_still_deep_edge_case():
    """Edge case — Sembly s prázdným tělem (transcript se nevygeneroval).

    Pravidlo subdir má precedenci; uživatel v DEEP flow může pak rozhodnout
    o archivaci. Reportováno explicitně, aby šlo do batch summary.
    """
    rel = "01-INBOX/sembly/2026-05-23-empty.md"
    complex_, reasons = mod.is_complex_source(rel, "")
    assert complex_ is True
    assert "sembly subdir" in reasons


def test_sent_email_subdir_never_deep_even_when_long():
    """Sent email fast-path (commitment extraction) — defenzivní vrstva.

    `triage_run.py` má brance `is_sent_email` před voláním této funkce,
    ale heuristika nezávisle vrátí False, aby šel test izolovaně.
    """
    rel = "01-INBOX/email/sent/2026-05-23-long-mail.md"
    body = "## Title\n\n" + _generate_long_body(1200)
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is False
    assert any("sent" in r for r in reasons)


# ---------------------------------------------------------------------------
# Size-based
# ---------------------------------------------------------------------------


def test_short_slack_ping_is_not_deep():
    rel = "01-INBOX/slack/2026-05-25-ping.md"
    body = "# Slack ping\n\nNějaká drobnost na potvrzení.\n"
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is False
    assert reasons == []


def test_word_count_above_threshold_is_deep():
    rel = "01-INBOX/Clippings/2026-05-25-long-article.md"
    body = "# Article\n\n" + _generate_long_body(1000)
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any(r.startswith("word_count=") for r in reasons)


def test_line_count_above_threshold_is_deep():
    rel = "01-INBOX/daily/2026-05-25.md"
    lines = ["- bod {}".format(i) for i in range(120)]
    body = "# Daily\n\n" + "\n".join(lines)
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any(r.startswith("line_count=") for r in reasons)


# ---------------------------------------------------------------------------
# Content-based
# ---------------------------------------------------------------------------


def test_many_headings_trigger_deep():
    rel = "01-INBOX/Clippings/2026-05-25-structured.md"
    body = (
        "# Top\n\n## One\nA\n\n## Two\nB\n\n## Three\nC\n\n"
        "Tady končíme.\n"
    )
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any("H2/H3 headings" in r for r in reasons)


def test_many_open_checkboxes_trigger_deep():
    rel = "01-INBOX/slack/2026-05-25-plan.md"
    body = (
        "# Plán\n\n"
        "- [ ] první\n"
        "- [ ] druhá\n"
        "- [ ] třetí\n"
        "- [ ] čtvrtá\n"
        "- [ ] pátá\n"
        "- [ ] šestá\n"
    )
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any("open checkboxes" in r for r in reasons)


def test_closed_checkboxes_do_not_trigger_deep():
    rel = "01-INBOX/slack/2026-05-25-done.md"
    body = (
        "# Hotovo\n\n"
        "- [x] první\n- [x] druhá\n- [x] třetí\n- [x] čtvrtá\n- [x] pátá\n"
    )
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is False
    assert reasons == []


def test_signal_phrase_action_items_triggers_deep():
    rel = "01-INBOX/Clippings/2026-05-25-meeting-notes.md"
    body = "# Notes\n\nKrátké notes.\n\n## Action items\n\n- foo\n"
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any("signal phrases" in r for r in reasons)


def test_signal_phrase_czech_zavery_triggers_deep():
    rel = "01-INBOX/slack/2026-05-25-call-summary.md"
    body = "# Call\n\nDiskuse.\n\n## Závěry\n\n1. ...\n"
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any("signal phrases" in r for r in reasons)


# ---------------------------------------------------------------------------
# Override
# ---------------------------------------------------------------------------


def test_override_simple_disables_otherwise_deep_source():
    """Long Clipping s `<!-- triage:simple -->` musí jít do BATCH."""
    rel = "01-INBOX/Clippings/2026-05-25-long-article.md"
    body = "<!-- triage:simple -->\n# Article\n\n" + _generate_long_body(1500)
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is False
    assert any("override" in r and "simple" in r for r in reasons)


def test_override_deep_forces_short_source_into_deep():
    rel = "01-INBOX/slack/2026-05-25-short.md"
    body = "<!-- triage:deep -->\n# Short note\n\nMalá poznámka.\n"
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any("override" in r and "deep" in r for r in reasons)


def test_override_in_frontmatter_block_still_wins():
    """Edge case — override v komentáři uvnitř/za YAML frontmatterem.

    YAML komentář je ``#`` ale HTML komentář v souboru jde mimo YAML
    (před/za blok). Hledáme `<!-- triage:* -->` v celém těle, takže
    i komentář **za** frontmatterem se uplatní.
    """
    rel = "01-INBOX/sembly/2026-05-25-meeting.md"
    body = (
        "---\n"
        "source: sembly\n"
        "duration: 45min\n"
        "---\n\n"
        "<!-- triage:simple -->\n"
        "# Schůzka\n\nKrátké poznámky.\n"
    )
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is False
    assert any("override" in r for r in reasons)


# ---------------------------------------------------------------------------
# Composite / sanity
# ---------------------------------------------------------------------------


def test_long_clipping_with_many_headings_lists_all_reasons():
    rel = "01-INBOX/Clippings/2026-05-25-deep-article.md"
    sections = "\n\n".join(
        f"## Section {i}\n\n" + _generate_long_body(200) for i in range(12)
    )
    body = "# Article\n\n" + sections
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any(r.startswith("word_count=") for r in reasons)
    assert any("H2/H3 headings" in r for r in reasons)


def test_attachments_section_triggers_deep():
    rel = "01-INBOX/email/2026-06-17-with-files.md"
    body = (
        "# Email\n\n## Tělo\n\nKrátký mail.\n\n"
        "## Přílohy\n\n"
        "- [report.pdf](https://drive.google.com/file/d/abc/view) — application/pdf, 1.2 MB\n"
    )
    complex_, reasons = mod.is_complex_source(rel, body)
    assert complex_ is True
    assert any("Přílohy" in r for r in reasons)


def test_has_attachments_markers_helper():
    body = "## Přílohy\n\n- [x.pdf](https://example.com)\n"
    assert mod.has_attachments_markers(body) is True
    assert mod.has_attachments_markers("# No attachments\n") is False
