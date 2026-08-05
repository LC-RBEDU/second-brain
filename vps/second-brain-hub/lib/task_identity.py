"""Task identity: one ID, one meaning, spelled the same in all three places.

A task announces who it is three times — `id:` + `title:` in frontmatter, the
filename, and the H1. Nothing keeps them in sync, and both ways they can drift
have already cost an afternoon of repair:

* **Two tasks claiming one ID.** A wikilink carries the ID *and* the title, so
  once `PD4` means two different things, no tool can repair links after a
  rename — it cannot tell which `PD4` a link meant. Eight such collisions were
  found in August 2026, all created by hand during triage.
* **Filename drifting from title.** Renaming a note in Obsidian rewrites the
  filename and every inbound link, but leaves `title:` untouched. The task then
  reads one way in Bases and another in the file tree, and the next automated
  rename links to a name nobody uses.

Both are cheap to detect and expensive to discover late, so they belong in the
context snapshot next to stale charters.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

SEPARATOR = " — "  # em dash U+2014

# Filenames rotated by lifecycle_recurring: <ID>-YYYY-MM-DD.md
ROTATION_RE = re.compile(r"^[A-Z]+\d+-\d{4}-\d{2}-\d{2}$")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def sanitize_title(title: str) -> str:
    """Filesystem- and Drive-safe rendering of a title.

    Mirrors `scripts/rename_tasks_to_human_filenames.sanitize_title`; kept as a
    copy because lib/ ships to the VPS without scripts/.
    """
    if not title:
        return ""
    s = title
    for ch in "\n\t\r":
        s = s.replace(ch, " ")
    s = s.replace(":", " ").replace("/", " -").replace("\\", " -")
    s = s.replace("?", "").replace("*", "")
    s = s.replace("<", "\u2039").replace(">", "\u203a")
    s = s.replace("|", "-").replace('"', "'")
    s = "".join(ch for ch in s if ord(ch) >= 0x20)
    return re.sub(r" +", " ", s).strip()


def expected_stem(task_id: str, title: str) -> str:
    sanitized = sanitize_title(title)
    return f"{task_id}{SEPARATOR}{sanitized}" if sanitized else task_id


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip()


def strip_wikilinks(text: str) -> str:
    """`[[Jan Mašek|Honzou]]` → `Honzou`, `[[Jan Mašek]]` → `Jan Mašek`."""
    return WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), text)


@dataclass(frozen=True)
class IdentityIssue:
    kind: str  # "duplicate_id" | "filename_drift"
    task_id: str
    detail: str
    paths: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"kind": self.kind, "id": self.task_id, "detail": self.detail, "paths": list(self.paths)}


def find_duplicate_ids(tasks) -> list[IdentityIssue]:
    """IDs claimed by more than one *task* — counted by distinct title.

    A ritual legitimately spreads one ID over many files: the live instance
    plus every archived rotation (`OS6-2026-08-05.md`). They all carry the same
    `title:`, because `lifecycle_recurring` copies it forward, so counting
    distinct titles collapses them into the one task they are — while still
    catching an unrelated task that grabs a ritual's ID, which counting
    non-rotation files alone would miss.

    Renaming a ritual leaves older rotations under the previous title and will
    raise a false positive until they age out. That trade is deliberate: a
    false positive costs a glance, and the false negative it replaces cost an
    afternoon of untangling links by hand.
    """
    claims: dict[str, dict[str, list[str]]] = {}
    for t in tasks:
        if t.id:
            claims.setdefault(t.id, {}).setdefault(_norm(t.title), []).append(t.rel_path)

    issues = []
    for task_id, by_title in sorted(claims.items()):
        if len(by_title) < 2:
            continue
        paths = [p for group in by_title.values() for p in group]
        issues.append(IdentityIssue(
            kind="duplicate_id",
            task_id=task_id,
            detail=(
                f"{len(by_title)} různé úkoly se hlásí k ID {task_id} — "
                "odkaz na ně nelze automaticky opravit"
            ),
            paths=tuple(sorted(paths)),
        ))
    return issues


def _stem(rel_path: str) -> str:
    return rel_path.rsplit("/", 1)[-1].removesuffix(".md")


def find_filename_drift(tasks) -> list[IdentityIssue]:
    """Tasks whose filename no longer renders their title."""
    issues = []
    for t in tasks:
        stem = _stem(t.rel_path)
        if not t.id or not t.title or ROTATION_RE.match(stem):
            continue
        want = expected_stem(t.id, t.title)
        if _norm(stem) != _norm(want):
            issues.append(IdentityIssue(
                kind="filename_drift",
                task_id=t.id,
                detail=f"soubor „{stem}\" ≠ title „{t.title}\"",
                paths=(t.rel_path,),
            ))
    return issues


def check_task_identity(tasks) -> list[dict]:
    """Both checks, ready for the `health` section of agent-context."""
    issues = find_duplicate_ids(tasks) + find_filename_drift(tasks)
    return [i.to_dict() for i in issues]
