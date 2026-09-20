"""Person identity by e-mail — multi-address matching for vault ``lide/``.

``email`` stays the primary address; optional ``emails`` lists every address
for the same person. Matching is case-insensitive and whitespace-trimmed.

``is_internal`` treats company domains (``redbuttonedu.cz``, ``redbutton.cz``)
and anyone who has at least one address on those domains as internal — so
Lenka Turečková writing from Rainfellows still counts as org-internal for
meeting classification.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

log = logging.getLogger(__name__)

COMPANY_DOMAINS = frozenset({"redbuttonedu.cz", "redbutton.cz"})
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL)


@dataclass
class Person:
    name: str
    path: str
    email: str | None = None
    emails: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    org: str | None = None
    role: str | None = None

    def all_emails(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for raw in [self.email, *self.emails]:
            norm = normalize_email(raw)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            out.append(norm)
        return out


def normalize_email(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if not s or s in {"—", "-", "n/a", "none", '""'}:
        return None
    # Strip mailto: and display-name wrappers: "Name <a@b.c>"
    if "<" in s and ">" in s:
        inner = re.search(r"<([^>]+)>", s)
        if inner:
            s = inner.group(1).strip()
    if s.startswith("mailto:"):
        s = s[7:].strip()
    if "@" not in s:
        return None
    return s


def email_domain(email: str | None) -> str | None:
    norm = normalize_email(email)
    if not norm or "@" not in norm:
        return None
    return norm.rsplit("@", 1)[-1]


def is_company_domain(email: str | None) -> bool:
    domain = email_domain(email)
    return domain in COMPANY_DOMAINS if domain else False


def _parse_frontmatter(text: str) -> dict[str, Any]:
    if yaml is None:
        return {}
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return fm if isinstance(fm, dict) else {}


def person_emails_from_frontmatter(fm: dict[str, Any]) -> tuple[str | None, list[str]]:
    """Return (primary, all_emails) with primary always included when present."""
    primary = normalize_email(fm.get("email"))
    raw_emails = fm.get("emails")
    emails_field_set = raw_emails is not None and raw_emails != [] and raw_emails != "[]"
    if isinstance(raw_emails, str):
        raw_emails = [raw_emails]
    if not raw_emails:
        raw_emails = []
    all_addrs: list[str] = []
    seen: set[str] = set()
    for raw in raw_emails:
        norm = normalize_email(raw)
        if norm and norm not in seen:
            seen.add(norm)
            all_addrs.append(norm)
    if primary and primary not in seen:
        if emails_field_set:
            log.warning(
                "person emails mismatch: primary %s not in emails %s",
                primary,
                all_addrs,
            )
        all_addrs.insert(0, primary)
        seen.add(primary)
    elif primary is None and all_addrs:
        primary = all_addrs[0]
    return primary, all_addrs


def load_person_from_file(path: Path) -> Person | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    fm = _parse_frontmatter(text)
    if (fm.get("type") or "").lower() != "person":
        return None
    primary, emails = person_emails_from_frontmatter(fm)
    aliases = fm.get("aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    name = path.stem
    if aliases:
        name = str(aliases[0])
    return Person(
        name=name,
        path=str(path),
        email=primary,
        emails=emails,
        aliases=[str(a) for a in aliases],
        org=str(fm.get("org") or "") or None,
        role=str(fm.get("role") or "") or None,
    )


def build_people_index(
    people: Iterable[Person],
) -> dict[str, Person]:
    """Map normalized email → Person. Duplicate addresses log a warning; first wins."""
    index: dict[str, Person] = {}
    for person in people:
        for addr in person.all_emails():
            if addr in index and index[addr].name != person.name:
                log.warning(
                    "email conflict: %s claimed by %s and %s — keeping %s",
                    addr,
                    index[addr].name,
                    person.name,
                    index[addr].name,
                )
                continue
            index.setdefault(addr, person)
    return index


def load_people_index(lide_dir: Path) -> dict[str, Person]:
    if not lide_dir.is_dir():
        return {}
    people: list[Person] = []
    for path in sorted(lide_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        person = load_person_from_file(path)
        if person:
            people.append(person)
    return build_people_index(people)


def resolve_person(email: str, people_index: dict[str, Person]) -> Person | None:
    """Find a person file by any of their addresses."""
    norm = normalize_email(email)
    if not norm:
        return None
    return people_index.get(norm)


def is_internal(email: str, people_index: dict[str, Person]) -> bool:
    """True if address is on a company domain, or belongs to someone who has one.

    Used by meeting-prep: external consultants with an EDU mailbox count as
    internal project participants.
    """
    norm = normalize_email(email)
    if not norm:
        return False
    if is_company_domain(norm):
        return True
    person = people_index.get(norm)
    if person is None:
        return False
    return any(is_company_domain(addr) for addr in person.all_emails())
