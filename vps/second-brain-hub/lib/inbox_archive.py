"""Archive INBOX captures to ``07-ARCHIV/inbox-processed/`` with co-located attachments.

Naming conventions (SSOT with n8n capture workflows):

- **email / email/sent:** ``{md_stem}__{original_filename}``
- **slack capture_n8n:** ``{YYYY-MM-DD-HHMM}-{slackFileId}-{name}`` co-located with
  ``{YYYY-MM-DD-HHMM}-_claude-capture-….md`` (shared timestamp prefix)
"""
from __future__ import annotations

import re
from pathlib import Path

CAPTURE_TS_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}-\d{4})")
INBOX_DATE_PREFIX_RE = re.compile(r"^(\d{4})-(\d{2})-")
SB_EMAIL_RE = re.compile(r"^sb-(personal|workspace)-.+\.md$", re.IGNORECASE)
# Gmail/n8n date variants: ISO, "22 Sep 2026 …", RFC2822 "Mon, 22 Sep 2026 …"
_FM_DATE_RE = re.compile(
    r'(?im)^date:\s*["\']?(?:[A-Za-z]{3},\s*)?(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})'
)
_FM_ISO_RE = re.compile(r'(?im)^date:\s*["\']?(\d{4})-(\d{2})-(\d{2})')
_MONTHS = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def capture_ts_prefix(name: str) -> str | None:
    """Return ``YYYY-MM-DD-HHMM`` prefix from capture or attachment filename."""
    m = CAPTURE_TS_PREFIX_RE.match(name)
    return m.group(1) if m else None


def email_attachment_prefix(md_name: str) -> str | None:
    if md_name.endswith(".md"):
        return md_name[:-3] + "__"
    return None


def _year_month_from_sb_email(md_path: Path) -> tuple[str, str] | None:
    """Resolve YYYY, MM for ``sb-personal-*`` / ``sb-workspace-*`` from frontmatter or mtime."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        text = ""
    m = _FM_ISO_RE.search(text)
    if m:
        return m.group(1), m.group(2)
    m = _FM_DATE_RE.search(text)
    if m:
        mon = _MONTHS.get(m.group(2).lower()[:3])
        if mon:
            return m.group(3), mon
    try:
        st = md_path.stat()
        from datetime import datetime

        dt = datetime.fromtimestamp(st.st_mtime)
        return f"{dt.year:04d}", f"{dt.month:02d}"
    except OSError:
        return None


def inbox_archive_dest(vault: Path, rel: str) -> Path:
    """Compute archive destination path for an INBOX relative path."""
    parts = Path(rel.replace("\\", "/")).parts
    name = parts[-1]
    m = INBOX_DATE_PREFIX_RE.match(name)
    if m:
        year, month = m.group(1), m.group(2)
    elif SB_EMAIL_RE.match(name):
        md_path = vault.joinpath(*parts)
        ym = _year_month_from_sb_email(md_path)
        if ym is None:
            raise ValueError(f"cannot parse date from {rel}")
        year, month = ym
    elif name.startswith("sb-personal-") or name.startswith("sb-workspace-"):
        # Co-located ``sb-personal-{tid}__file.ext``
        stem = name.split("__", 1)[0] if "__" in name else name.rsplit(".", 1)[0]
        md_name = stem if stem.endswith(".md") else f"{stem}.md"
        md_path = vault.joinpath(*parts[:-1], md_name)
        ym = _year_month_from_sb_email(md_path) if md_path.is_file() else None
        if ym is None:
            att_path = vault.joinpath(*parts)
            ym = _year_month_from_sb_email(att_path) if att_path.is_file() else None
        if ym is None:
            raise ValueError(f"cannot parse date from {rel}")
        year, month = ym
    else:
        raise ValueError(f"cannot parse date from {rel}")
    kind = parts[1] if len(parts) > 2 else "misc"
    return vault / "07-ARCHIV" / "inbox-processed" / year / month / kind / name


def list_colocated_attachments(inbox_dir: Path, md_name: str) -> list[Path]:
    """Return non-markdown files in ``inbox_dir`` belonging to ``md_name`` capture."""
    if not inbox_dir.is_dir():
        return []
    email_prefix = email_attachment_prefix(md_name)
    slack_prefix = capture_ts_prefix(md_name)
    out: list[Path] = []
    for p in sorted(inbox_dir.iterdir()):
        if not p.is_file():
            continue
        if p.name in {md_name, ".keep"}:
            continue
        if p.suffix.lower() == ".md":
            continue
        if email_prefix and p.name.startswith(email_prefix):
            out.append(p)
            continue
        if slack_prefix and p.name.startswith(slack_prefix + "-"):
            out.append(p)
    return out


def mark_processed(text: str) -> str:
    if "**ZPRACOVÁNO**" in text:
        return text
    if text.startswith("#"):
        i = text.find("\n")
        if i == -1:
            return text + " **ZPRACOVÁNO**"
        return text[:i] + " **ZPRACOVÁNO**" + text[i:]
    return "**ZPRACOVÁNO**\n\n" + text


def _move_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    src.rename(dest)


def archive_inbox_capture(
    vault: Path,
    rel: str,
    *,
    mark_md_processed: bool = True,
) -> tuple[str, list[str]]:
    """Move INBOX ``.md`` + co-located attachments to ``07-ARCHIV/inbox-processed/``.

    Returns ``(archived_md_rel, [attachment_rels...])``.
    """
    rel = rel.replace("\\", "/")
    src = vault / rel
    if not src.exists():
        raise FileNotFoundError(rel)

    dest = inbox_archive_dest(vault, rel)
    dest_rel = str(dest.relative_to(vault))
    dest.parent.mkdir(parents=True, exist_ok=True)

    if src.suffix.lower() == ".md" and mark_md_processed:
        dest.write_text(mark_processed(src.read_text(encoding="utf-8")), encoding="utf-8")
        src.unlink()
    else:
        _move_file(src, dest)

    moved_attachments: list[str] = []
    inbox_dir = src.parent
    md_name = Path(rel).name
    for att in list_colocated_attachments(inbox_dir, md_name):
        att_dest = dest.parent / att.name
        _move_file(att, att_dest)
        moved_attachments.append(str(att_dest.relative_to(vault)))

    return dest_rel, moved_attachments


def archive_orphan_inbox_attachments(vault: Path) -> list[tuple[str, str]]:
    """Move co-located INBOX attachment orphans whose ``.md`` is already archived.

    Matches slack ``YYYY-MM-DD-HHMM-*`` files to archived capture with same prefix.
    Returns list of ``(from_rel, to_rel)`` moves.
    """
    inbox_root = vault / "01-INBOX"
    if not inbox_root.is_dir():
        return []

    archive_root = vault / "07-ARCHIV" / "inbox-processed"
    archived_md_prefixes: set[str] = set()
    if archive_root.is_dir():
        for md in archive_root.rglob("*.md"):
            prefix = capture_ts_prefix(md.name)
            if prefix:
                archived_md_prefixes.add(prefix)

    moves: list[tuple[str, str]] = []
    for sub in inbox_root.iterdir():
        if not sub.is_dir():
            continue
        for p in sorted(sub.iterdir()):
            if not p.is_file() or p.name == ".keep":
                continue
            if p.suffix.lower() == ".md":
                continue
            rel = str(p.relative_to(vault)).replace("\\", "/")
            prefix = capture_ts_prefix(p.name)
            if not prefix or prefix not in archived_md_prefixes:
                continue
            dest = inbox_archive_dest(vault, rel)
            _move_file(p, dest)
            moves.append((rel, str(dest.relative_to(vault))))
    return moves


__all__ = [
    "archive_inbox_capture",
    "archive_orphan_inbox_attachments",
    "capture_ts_prefix",
    "email_attachment_prefix",
    "inbox_archive_dest",
    "list_colocated_attachments",
    "mark_processed",
]
