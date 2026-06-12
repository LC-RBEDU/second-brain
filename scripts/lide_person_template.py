"""F6.4 person file template — shared by migrate_lide_persons.py and sync_lide_people.py."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

SECTIONS_ORDER = [
    "## Témata",
    "## Projekty a tasky",
    "## Zmínky a materiály",
    "## Log",
]

DEFAULT_SECTION_BODY = {
    "## Témata": "- _(doplň)_",
    "## Projekty a tasky": "- _(doplň wikilinks na huby)_",
    "## Log": "- _(prázdné)_",
}

EMPTY_MENTIONS_TABLE = (
    "| Datum | Typ | Odkaz | Kontext |\n"
    "|-------|-----|-------|--------|\n"
    "| — | — | — | _(sync_lide_people.py doplní)_ |\n"
)


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end < 0:
        return "", text
    return text[3:end].strip(), text[end + 4 :].lstrip("\n")


def parse_frontmatter(fm: str) -> dict:
    data: dict = {}
    key: str | None = None
    for line in fm.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - ") and key == "aliases":
            data.setdefault("aliases", []).append(line[4:].strip())
            continue
        if line.startswith("  - ") and key == "topics":
            data.setdefault("topics", []).append(line[4:].strip())
            continue
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            key = k.strip()
            val = v.strip()
            if key in ("aliases", "topics", "significant_dates", "projects"):
                if val == "[]":
                    data[key] = []
                elif val:
                    data[key] = [val]
            else:
                data[key] = val.strip('"')
    return data


def extract_section(body: str, header: str) -> tuple[str, str]:
    pattern = re.compile(rf"^{re.escape(header)}\s*\n(.*?)(?=^## |\Z)", re.M | re.S)
    m = pattern.search(body)
    if not m:
        return body, ""
    content = m.group(1).strip()
    new_body = body[: m.start()] + body[m.end() :]
    new_body = re.sub(r"\n{3,}", "\n\n", new_body).strip()
    return new_body, content


def parse_person_body(body: str) -> tuple[str, str | None, dict[str, str]]:
    """Return (title, přezdívka line or None, sections dict)."""
    sections: dict[str, str] = {}
    remaining = body
    for hdr in SECTIONS_ORDER:
        remaining, content = extract_section(remaining, hdr)
        if content:
            sections[hdr] = content

    title = ""
    nickname: str | None = None
    for line in remaining.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("*Přezdívka"):
            nickname = line.strip()
    return title, nickname, sections


def build_frontmatter(
    person: str,
    *,
    existing: dict | None = None,
    known_meta: dict | None = None,
    nicknames: list[str] | None = None,
) -> str:
    existing = existing or {}
    known_meta = known_meta or {}
    today = date.today().isoformat()

    aliases: list[str] = []
    if person not in aliases:
        aliases.append(person)
    for a in existing.get("aliases") or []:
        if a not in aliases:
            aliases.append(a)
    for nick in nicknames or []:
        if nick not in aliases:
            aliases.append(nick)

    role = existing.get("role") or known_meta.get("role") or "—"
    if role in ("—", "-", ""):
        role = known_meta.get("role") or "—"

    org = existing.get("org") or known_meta.get("org") or "Red Button EDU"
    email = existing.get("email") or known_meta.get("email") or "—"
    phone = existing.get("phone") if existing.get("phone") is not None else '""'
    if phone == "":
        phone = '""'
    slack = existing.get("slack") or known_meta.get("slack") or '""'
    if slack == "":
        slack = '""'
    birthday = existing.get("birthday") if existing.get("birthday") is not None else '""'
    if birthday == "":
        birthday = '""'

    sig = existing.get("significant_dates")
    sig_line = "significant_dates: []" if not sig or sig == "[]" else f"significant_dates: {sig}"

    projects = existing.get("projects") or known_meta.get("projects")
    if isinstance(projects, list):
        if projects:
            proj_lines = ["projects:"] + [f'- "{p}"' if not str(p).startswith('"') else f"- {p}" for p in projects]
            proj_block = "\n".join(proj_lines)
        else:
            proj_block = "projects: []"
    elif projects and projects != "[]":
        proj_block = f"projects: {projects}"
    else:
        proj_block = "projects: []"

    topics = existing.get("topics")
    if isinstance(topics, list) and topics:
        topic_lines = ["topics:"] + [f"  - {t}" for t in topics]
        topic_block = "\n".join(topic_lines)
    else:
        topic_block = "topics:\n  - lide"

    updated = existing.get("updated") or today

    alias_lines = "\n".join(f"- {a}" for a in aliases)
    return (
        f"type: person\n"
        f"aliases:\n{alias_lines}\n"
        f"role: {role}\n"
        f"org: {org}\n"
        f"email: {email}\n"
        f"phone: {phone}\n"
        f"slack: {slack}\n"
        f"birthday: {birthday}\n"
        f"{sig_line}\n"
        f"{proj_block}\n"
        f"{topic_block}\n"
        f"updated: {updated}\n"
    )


def format_mentions_table(rows: list[dict]) -> str:
    lines = [
        "| Datum | Typ | Odkaz | Kontext |",
        "|-------|-----|-------|--------|",
    ]
    for r in rows:
        k = r["kontext"].replace("|", "\\|")
        lines.append(f"| {r['date']} | {r['typ']} | {r['link']} | {k} |")
    if len(lines) == 2:
        lines.append("| — | — | — | zatím žádné zmínky ve vaultu |")
    return "\n".join(lines) + "\n"


def build_person_document(
    person: str,
    *,
    sections: dict[str, str] | None = None,
    mentions_rows: list[dict] | None = None,
    existing_fm: dict | None = None,
    known_meta: dict | None = None,
    nicknames: list[str] | None = None,
    nickname_line: str | None = None,
) -> str:
    sections = sections or {}
    fm_yaml = build_frontmatter(
        person,
        existing=existing_fm,
        known_meta=known_meta,
        nicknames=nicknames,
    )
    parts = [f"---\n{fm_yaml}---\n\n", f"# {person}\n\n"]
    if nickname_line:
        parts.append(f"{nickname_line}\n\n")
    elif nicknames:
        parts.append(f"*Přezdívka:* {', '.join(nicknames)}\n\n")

    for hdr in SECTIONS_ORDER:
        parts.append(f"{hdr}\n\n")
        if hdr == "## Zmínky a materiály":
            if mentions_rows is not None:
                parts.append(format_mentions_table(mentions_rows) + "\n")
            elif hdr in sections and sections[hdr]:
                parts.append(sections[hdr] + "\n\n")
            else:
                parts.append(EMPTY_MENTIONS_TABLE + "\n")
        elif hdr in sections and sections[hdr]:
            parts.append(sections[hdr] + "\n\n")
        else:
            parts.append(DEFAULT_SECTION_BODY[hdr] + "\n\n")

    return "".join(parts).rstrip() + "\n"


def normalize_person_file(
    path: Path,
    *,
    mentions_rows: list[dict] | None = None,
    known_meta: dict | None = None,
    nicknames: list[str] | None = None,
) -> str:
    text = path.read_text(encoding="utf-8")
    fm_raw, body = split_frontmatter(text)
    existing_fm = parse_frontmatter(fm_raw) if fm_raw else {}
    _, nickname_line, sections = parse_person_body(body)
    person = path.stem
    return build_person_document(
        person,
        sections=sections,
        mentions_rows=mentions_rows,
        existing_fm=existing_fm,
        known_meta=known_meta,
        nicknames=nicknames,
        nickname_line=nickname_line,
    )
