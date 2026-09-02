"""Epic / user-story / task hierarchy helpers (opt-in per project).

Vault convention (RB Universe first, other projects via hub ``hierarchy: true``
or presence of at least one ``type: epic`` in that slug's tasks/):

- ``type: epic``  — outcome, months-long; no focus; never auto-Done from checkboxes/GitHub
- ``type: story`` — deliverable user value; owns ICE / focus / status; children = checkbox ``ID-N``
- ``type: task``  — legacy / flat work item (default when type missing)

Parent link: story frontmatter ``parent: '[[RBU23 — Title]]'`` (wikilink to epic file).
"""
from __future__ import annotations

import re
from typing import Any

TYPE_EPIC = "epic"
TYPE_STORY = "story"
TYPE_TASK = "task"

HIERARCHY_TYPES = frozenset({TYPE_EPIC, TYPE_STORY, TYPE_TASK})

# Slugs that always use hierarchy (even before first epic exists).
DEFAULT_HIERARCHY_SLUGS = frozenset({"rb-universe-development"})

PARENT_ID_RE = re.compile(
    r"\[\[(?P<id>[A-Za-z]+\d+[a-z]?)(?:\s*[—–-].*?)?\]\]"
)
BARE_ID_RE = re.compile(r"^([A-Za-z]+\d+[a-z]?)$")
CLOSES_RE = re.compile(
    r"(?i)\b(?:closes|fixes|resolves)\s+(?P<ref>RBU\d+(?:-\d+[a-z]?)?)\b"
)
SUBTASK_REF_RE = re.compile(r"^(?P<id>[A-Za-z]+\d+[a-z]?)-(?P<num>\d+)(?P<suffix>[A-Za-z]*)?$")


def _task_get(task: Any, key: str, default=None):
    if isinstance(task, dict):
        return task.get(key, default)
    fm = getattr(task, "frontmatter", None)
    if isinstance(fm, dict) and key in fm:
        return fm.get(key, default)
    return getattr(task, key, default)


def normalise_work_type(value: Any) -> str:
    """Return epic|story|task. Missing/unknown → task (legacy)."""
    s = str(value or "").strip().lower()
    if s in HIERARCHY_TYPES:
        return s
    return TYPE_TASK


def work_type_of(task: Any) -> str:
    return normalise_work_type(_task_get(task, "type") or _task_get(task, "work_type"))


def is_epic(task: Any) -> bool:
    return work_type_of(task) == TYPE_EPIC


def is_story(task: Any) -> bool:
    return work_type_of(task) == TYPE_STORY


def is_focusable(task: Any) -> bool:
    """Epics never enter focus / top_priority queues."""
    return not is_epic(task)


def parse_parent_id(value: Any) -> str | None:
    """Extract parent task ID from wikilink or bare ID."""
    if value is None:
        return None
    if isinstance(value, list):
        for item in value:
            pid = parse_parent_id(item)
            if pid:
                return pid
        return None
    s = str(value).strip()
    if not s or s.lower() in {"null", "none", ""}:
        return None
    m = PARENT_ID_RE.search(s)
    if m:
        return m.group("id")
    m = BARE_ID_RE.match(s)
    if m:
        return m.group(1)
    # Filename-style "RBU23 — Title"
    m = re.match(r"^([A-Za-z]+\d+[a-z]?)\s*[—–-]", s)
    if m:
        return m.group(1)
    return None


def parent_id_of(task: Any) -> str | None:
    return parse_parent_id(_task_get(task, "parent"))


def project_uses_hierarchy(
    slug: str,
    *,
    hub_frontmatter: dict[str, Any] | None = None,
    slug_has_epic: bool = False,
) -> bool:
    """Whether hierarchy rules apply for this project slug."""
    if slug in DEFAULT_HIERARCHY_SLUGS:
        return True
    fm = hub_frontmatter or {}
    if fm.get("hierarchy") is True or str(fm.get("hierarchy") or "").lower() in {
        "true",
        "1",
        "yes",
    }:
        return True
    return bool(slug_has_epic)


def parse_closes_refs(text: str) -> list[str]:
    """Return unique Closes/Fixes/Resolves refs (story ID or ID-N), order preserved."""
    seen: set[str] = set()
    out: list[str] = []
    for m in CLOSES_RE.finditer(text or ""):
        ref = m.group("ref")
        # Normalise letter suffix case
        key = ref.upper() if "-" not in ref else ref
        if "-" in ref:
            base, _, rest = ref.partition("-")
            key = f"{base.upper()}-{rest}"
        else:
            key = ref.upper()
            # RBU62 from closes — keep canonical casing RBU…
            m2 = re.match(r"^([A-Za-z]+)(\d+[a-z]?)$", ref)
            if m2:
                key = f"{m2.group(1).upper()}{m2.group(2)}"
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def split_subtask_ref(ref: str) -> tuple[str, str] | None:
    """'RBU62-1' → ('RBU62', '1'); story-only ref → None."""
    m = SUBTASK_REF_RE.match(ref.strip())
    if not m:
        return None
    num = m.group("num") + (m.group("suffix") or "")
    return m.group("id"), num


def checkbox_line_for_subtask(body: str, task_id: str, num: str) -> tuple[int, str] | None:
    """Find checkbox line index and full line for **ID-N** in body."""
    pat = re.compile(
        rf"^(\s*-\s+\[)([ xX])(\]\s+\*\*{re.escape(task_id)}-{re.escape(num)}\*\*.*)$",
        re.MULTILINE,
    )
    m = pat.search(body or "")
    if not m:
        return None
    # Line number for callers that rewrite by lines
    start = m.start()
    line_idx = body[:start].count("\n")
    return line_idx, m.group(0)


def mark_checkbox_done(body: str, task_id: str, num: str) -> tuple[str, bool]:
    """Flip ``- [ ] **ID-N**`` to ``[x]``. Returns (new_body, changed)."""
    pat = re.compile(
        rf"^(\s*-\s+\[)([ ])(\]\s+\*\*{re.escape(task_id)}-{re.escape(num)}\*\*)",
        re.MULTILINE,
    )

    def repl(m: re.Match) -> str:
        return f"{m.group(1)}x{m.group(3)}"

    new_body, n = pat.subn(repl, body or "", count=1)
    return new_body, n > 0
