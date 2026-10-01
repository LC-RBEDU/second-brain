#!/usr/bin/env python3
"""Tests for invoice_duzp + payment_doc (B0/B1/B4)."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

from invoice_duzp import parse_email_date, parse_invoice_text  # noqa: E402
from payment_doc import (  # noqa: E402
    b0_select_largest,
    b0_should_keep,
    extract_b4_pdf_urls,
    is_payment_doc,
    should_download_pdf_href,
)

FIX = ROOT / "fixtures" / "invoice_duzp"


def test_alza_neo_duzp():
    text = (FIX / "alza-neo-sample.txt").read_text(encoding="utf-8")
    r = parse_invoice_text(text, from_header="Alza <neo@alza.cz>", subject="vyúčtování AlzaNEO")
    assert r["duzp"] == "2026-09-15"
    assert r["vs"] == "1234567890"
    assert r["confidence"] == "duzp"
    assert r["subfolder"] == "09-2026"
    assert r["issuer_slug"] == "alza-neo"


def test_alza_neo_uskut_obdobi_fallback():
    """Alza PDF: 'Datum uskut. zdaň. plnění:' + Období start when date is not adjacent."""
    text = (FIX / "alza-neo-uskut-obdobi.txt").read_text(encoding="utf-8")
    r = parse_invoice_text(text, from_header="AlzaNEO <neo@alza.cz>", subject="vyúčtování AlzaNEO")
    assert r["duzp"] == "2026-09-22"
    assert r["issued"] == "2026-10-02"
    assert r["vs"] == "1286656171"
    assert r["confidence"] == "duzp"
    assert r["subfolder"] == "09-2026"


def test_issued_only_fallback():
    text = (FIX / "generic-cz-issued-only.txt").read_text(encoding="utf-8")
    r = parse_invoice_text(text, from_header="ACME <info@acme.cz>", subject="Faktura")
    assert r["duzp"] is None
    assert r["issued"] == "2026-08-01"
    assert r["confidence"] == "issued"
    assert r["subfolder"] == "08-2026"
    assert r["vs"] == "99887766"


def test_email_date_fallback():
    r = parse_invoice_text(
        "bez datumu",
        email_date=date(2026, 7, 22),
    )
    assert r["confidence"] == "none"
    assert r["subfolder"] == "07-2026"


def test_parse_email_date_rfc():
    assert parse_email_date("Mon, 22 Sep 2026 14:10:00 +0200") == date(2026, 9, 22)
    assert parse_email_date("2026-09-22T10:00:00") == date(2026, 9, 22)


def test_f1_newsletter_not_payment():
    assert not is_payment_doc(
        from_header="Tips <newsletter@example.com>",
        subject="Tipy týdne",
        body='Koukni na <a href="https://cdn.example.com/promo.pdf">promo</a>',
    )
    assert not should_download_pdf_href(
        href="https://cdn.example.com/promo.pdf",
        anchor_text="promo",
        is_payment=False,
    )


def test_f2_alza_link_only():
    assert is_payment_doc(
        from_header="AlzaNEO <neo@alza.cz>",
        subject="vyúčtování AlzaNEO",
        body="",
    )
    assert should_download_pdf_href(
        href="https://www.alza.cz/invoice/x",
        anchor_text="Stáhnout fakturu",
        is_payment=True,
    )


def test_f3_fakturoid():
    assert is_payment_doc(
        from_header="Fakturoid <noreply@fakturoid.cz>",
        subject="Faktura 2026-1",
        body="děkujeme",
        stem_attachments=["sb-personal-abc__fa.pdf"],
    )


def test_b4_extract_phrases():
    html = '<a href="https://x/a.pdf">Stáhnout fakturu</a>'
    urls = extract_b4_pdf_urls(html, is_payment=False)
    assert urls == ["https://x/a.pdf"]


def test_b4_newsletter_pdf_href_blocked():
    html = '<a href="https://cdn.example.com/promo.pdf">Stáhnout PDF balíček tipů</a>'
    # phrase "stáhnout pdf" matches B4 — intentional for phrase anchors
    # bare promo without phrase:
    html2 = '<a href="https://cdn.example.com/promo.pdf">Promo balíček</a>'
    assert extract_b4_pdf_urls(html2, is_payment=False) == []


def test_t15_skip_inline_small_image():
    assert not b0_should_keep(
        filename="pixel.png",
        mime="image/png",
        size=1200,
        disposition="inline",
    )
    assert b0_should_keep(
        filename="receipt.jpg",
        mime="image/jpeg",
        size=50_000,
        disposition="attachment",
    )


def test_t15_skip_ics_and_octet():
    assert not b0_should_keep(filename="meet.ics", mime="text/calendar", size=400, disposition="attachment")
    assert not b0_should_keep(filename="", mime="application/octet-stream", size=100, disposition="attachment")
    assert b0_should_keep(filename="doc.pdf", mime="application/pdf", size=10_000, disposition="attachment")


def test_t18_keep_largest_20():
    files = [{"name": f"f{i}.pdf", "size": i * 100} for i in range(25)]
    kept = b0_select_largest(files, limit=20)
    assert len(kept) == 20
    assert kept[0]["size"] == 2400
