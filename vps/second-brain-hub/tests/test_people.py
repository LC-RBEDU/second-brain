"""Tests for multi-email person identity (people.py)."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from people import (  # noqa: E402
    Person,
    build_people_index,
    is_internal,
    load_person_from_file,
    normalize_email,
    person_emails_from_frontmatter,
    resolve_person,
)


def test_normalize_email_case_and_angles():
    assert normalize_email("  Lenka.Tureckova@Rainfellows.CZ ") == (
        "lenka.tureckova@rainfellows.cz"
    )
    assert normalize_email("Lenka <lenka@redbuttonedu.cz>") == "lenka@redbuttonedu.cz"
    assert normalize_email("—") is None


def test_resolve_primary_and_secondary(tmp_path: Path):
    md = tmp_path / "Lenka Turečková.md"
    md.write_text(
        "---\n"
        "type: person\n"
        "aliases:\n- Lenka Turečková\n"
        "email: lenka.tureckova@rainfellows.cz\n"
        "emails:\n"
        "- lenka.tureckova@rainfellows.cz\n"
        "- lenka.tureckova@redbuttonedu.cz\n"
        "---\n\n# Lenka\n",
        encoding="utf-8",
    )
    person = load_person_from_file(md)
    assert person is not None
    index = build_people_index([person])
    assert resolve_person("lenka.tureckova@rainfellows.cz", index).name == "Lenka Turečková"
    assert resolve_person("Lenka.Tureckova@redbuttonedu.cz", index).name == "Lenka Turečková"


def test_resolve_fallback_without_emails_field(tmp_path: Path):
    md = tmp_path / "Martina.md"
    md.write_text(
        "---\n"
        "type: person\n"
        "aliases:\n- Martina Mašková\n"
        "email: martina@redbuttonedu.cz\n"
        "---\n",
        encoding="utf-8",
    )
    person = load_person_from_file(md)
    index = build_people_index([person])
    assert resolve_person("martina@redbuttonedu.cz", index) is not None


def test_is_internal_via_secondary_company_address():
    person = Person(
        name="Lenka Turečková",
        path="x.md",
        email="lenka.tureckova@rainfellows.cz",
        emails=[
            "lenka.tureckova@rainfellows.cz",
            "lenka.tureckova@redbuttonedu.cz",
        ],
    )
    index = build_people_index([person])
    assert is_internal("lenka.tureckova@rainfellows.cz", index) is True
    assert is_internal("random@client.cz", index) is False


def test_is_internal_redbutton_cz_domain():
    index: dict = {}
    assert is_internal("jan@redbutton.cz", index) is True
    assert is_internal("jan@redbuttonedu.cz", index) is True


def test_email_conflict_keeps_first(caplog):
    a = Person(name="A", path="a.md", email="shared@x.cz", emails=["shared@x.cz"])
    b = Person(name="B", path="b.md", email="shared@x.cz", emails=["shared@x.cz"])
    with caplog.at_level(logging.WARNING):
        index = build_people_index([a, b])
    assert index["shared@x.cz"].name == "A"
    assert "email conflict" in caplog.text


def test_emails_missing_primary_logs(caplog):
    fm = {
        "email": "primary@x.cz",
        "emails": ["other@x.cz"],
    }
    with caplog.at_level(logging.WARNING):
        primary, emails = person_emails_from_frontmatter(fm)
    assert primary == "primary@x.cz"
    assert "primary@x.cz" in emails
    assert "mismatch" in caplog.text
