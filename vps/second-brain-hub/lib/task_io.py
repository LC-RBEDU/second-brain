"""Task file I/O for Second Brain v2 file-per-task architecture.

Each task lives in:
- 02-PROJEKTY/<slug>/tasks/<ID>-<slugify(title)>.md (active)
- 07-ARCHIV/tasks-done/<slug>/<ID>-<slugify(title)>.md (archived)

YAML frontmatter is the SSOT for status, ICE, deadline, waitUntil, materials.
Body contains operativní kroky (checkboxes), poznámky / log, optional recurring/extra blocks.

This module provides parse/serialize helpers and iterators over all tasks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Iterator

import yaml

from drive_io import DriveVault, DriveNotFoundError, FileMeta

PROJEKTY_DIR = "02-PROJEKTY"
ARCHIV_DIR = "07-ARCHIV/tasks-done"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)
ID_RE = re.compile(r"^([A-Z]+\d+[a-z]?)")


@dataclass
class ParsedTask:
    rel_path: str
    frontmatter: dict[str, Any]
    body: str
    meta: FileMeta | None = None

    @property
    def task_id(self) -> str:
        return self.frontmatter.get("id") or ""

    @property
    def slug(self) -> str:
        return self.frontmatter.get("slug") or ""

    @property
    def status(self) -> str:
        return self.frontmatter.get("status") or "Next"

    @property
    def is_done(self) -> bool:
        return self.status == "Done"


def parse_task_text(text: str, rel_path: str = "", meta: FileMeta | None = None) -> ParsedTask:
    """Parse task .md → frontmatter dict + body str."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return ParsedTask(rel_path=rel_path, frontmatter={}, body=text, meta=meta)
    fm_yaml = m.group(1)
    body = m.group(2)
    try:
        fm = yaml.safe_load(fm_yaml) or {}
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError:
        fm = {}
    return ParsedTask(rel_path=rel_path, frontmatter=fm, body=body, meta=meta)


def serialize_task(frontmatter: dict[str, Any], body: str) -> str:
    """frontmatter dict + body → task .md text."""
    fm_yaml = yaml.safe_dump(
        frontmatter,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    return f"---\n{fm_yaml}---\n{body}"


def iter_active_tasks(vault: DriveVault) -> Iterator[ParsedTask]:
    """Iter over 02-PROJEKTY/<slug>/tasks/*.md, parse each."""
    for slug_dir_meta in vault.list_dir(PROJEKTY_DIR):
        if not slug_dir_meta.is_folder:
            continue
        slug = slug_dir_meta.name
        tasks_rel = f"{PROJEKTY_DIR}/{slug}/tasks"
        try:
            files = vault.list_dir(tasks_rel, pattern="*.md")
        except DriveNotFoundError:
            continue
        for meta in files:
            try:
                text, m = vault.read_text(meta.rel_path)
            except DriveNotFoundError:
                continue
            yield parse_task_text(text, rel_path=meta.rel_path, meta=m)


def iter_archive_tasks(vault: DriveVault, slug: str | None = None) -> Iterator[ParsedTask]:
    """Iter over 07-ARCHIV/tasks-done/<slug>/*.md."""
    base = ARCHIV_DIR
    if slug:
        base = f"{ARCHIV_DIR}/{slug}"
        try:
            files = vault.list_dir(base, pattern="*.md")
        except DriveNotFoundError:
            return
        for meta in files:
            try:
                text, m = vault.read_text(meta.rel_path)
            except DriveNotFoundError:
                continue
            yield parse_task_text(text, rel_path=meta.rel_path, meta=m)
        return

    try:
        slug_dirs = vault.list_dir(ARCHIV_DIR)
    except DriveNotFoundError:
        return
    for slug_meta in slug_dirs:
        if not slug_meta.is_folder:
            continue
        yield from iter_archive_tasks(vault, slug_meta.name)


def update_task(
    vault: DriveVault,
    task: ParsedTask,
    *,
    new_status: str | None = None,
    new_frontmatter: dict[str, Any] | None = None,
    body_append: str | None = None,
    today_str: str | None = None,
) -> bool:
    """CAS-aware patch of task frontmatter / body. Returns True on success.

    Preserves existing frontmatter keys; only overwrites those passed in
    `new_frontmatter` (or `new_status`).
    """
    fm = dict(task.frontmatter)
    if new_status:
        fm["status"] = new_status
    if new_frontmatter:
        fm.update(new_frontmatter)
    if today_str:
        fm["updated"] = today_str

    body = task.body
    if body_append:
        if not body.endswith("\n"):
            body += "\n"
        body += body_append
        if not body.endswith("\n"):
            body += "\n"

    text = serialize_task(fm, body)
    try:
        vault.write_text(
            task.rel_path,
            text,
            expect_mtime=task.meta.modified_time if task.meta else None,
        )
        return True
    except Exception as e:
        # DriveConflictError or transient — caller may retry
        print(f"  ! conflict on {task.rel_path}: {e}")
        return False


def all_checkboxes_done(body: str) -> bool:
    """Return True if body has at least 1 checkbox and all are [x] (case-insensitive)."""
    boxes = re.findall(r"^-\s+\[([ xX])\]\s+", body, re.MULTILINE)
    if not boxes:
        return False
    return all(b.lower() == "x" for b in boxes)


def parse_iso_date(value: Any) -> date | None:
    """Robust ISO date parser (handles datetime.date, datetime.datetime, str)."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None
