"""Generate ## Stav (auto) marker blocks for project hub charters.

Marker delimiters use Obsidian comment syntax, which Obsidian hides in both
Reading and Live Preview mode (unlike HTML comments, which stay visible while
editing):

  %%SB:STATE:BEGIN%%
  ...
  %%SB:STATE:END%%

The markers are load-bearing — they tell the cron which slice of the charter it
may overwrite. Legacy `<!-- SB:STATE:BEGIN -->` blocks are still recognised so
old hubs get migrated on the next run.

Task references are emitted as `[[<ID>]]` wikilinks; every task carries its ID
in `aliases`, so the bare ID resolves to the task file.

Staleness: hub frontmatter `updated` older than last task activity by
STALE_NARRATIVE_DAYS → warning in block + entry in stale_hubs[].
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta
from typing import Any, Protocol

from focus import STATUS_DOING, STATUS_NEXT, is_focus_current, is_terminal
from today_priority import today_score as calc_today_score

STATE_BEGIN = "%%SB:STATE:BEGIN%%"
STATE_END = "%%SB:STATE:END%%"
LEGACY_STATE_BEGIN = "<!-- SB:STATE:BEGIN -->"
LEGACY_STATE_END = "<!-- SB:STATE:END -->"
STATE_SECTION = "## Stav (auto)"
STALE_NARRATIVE_DAYS = 14
STALE_AREA_WEEKS = 3

_ANY_BEGIN = rf"(?:{re.escape(STATE_BEGIN)}|{re.escape(LEGACY_STATE_BEGIN)})"
_ANY_END = rf"(?:{re.escape(STATE_END)}|{re.escape(LEGACY_STATE_END)})"

STATE_BLOCK_RE = re.compile(
    rf"({re.escape(STATE_SECTION)}\s*\n){_ANY_BEGIN}\s*\n"
    rf"(.*?)"
    rf"\n{_ANY_END}",
    re.DOTALL,
)


def _task_stem(task: Any) -> str:
    """Filename without extension, when the task carries its path.

    `rel_path` is an attribute on ParsedTask, not a frontmatter key, so it is
    read directly instead of through `_task_get`.
    """
    if isinstance(task, dict):
        rel = task.get("rel_path") or ""
    else:
        rel = getattr(task, "rel_path", "") or ""
    if not rel:
        return ""
    return str(rel).rsplit("/", 1)[-1].removesuffix(".md")


def _task_link(task: Any, task_id: str) -> str:
    """Wikilink to a task, displayed as the bare ID.

    The link always targets the full filename, never the bare `[[ID]]`. An ID
    alias is not unique enough: archived instances of recurring tasks keep the
    base ID in their `aliases`, and any stray note called `S23.md` anywhere in
    the vault outranks the alias, so `[[S23]]` silently lands on the wrong file.

    The `|` is escaped because these links sit inside markdown tables.
    """
    if not task_id or task_id == "?":
        return "—"
    stem = _task_stem(task)
    if stem and stem != task_id:
        return f"[[{stem}\\|{task_id}]]"
    return f"[[{task_id}]]"


def _cell(text: str) -> str:
    """Escape a value so it survives inside a markdown table cell."""
    return str(text).replace("|", r"\|").strip()


class TaskLike(Protocol):
    @property
    def slug(self) -> str: ...
    @property
    def status(self) -> str: ...
    @property
    def task_id(self) -> str: ...
    @property
    def frontmatter(self) -> dict[str, Any]: ...


def _task_get(task: Any, key: str, default=None):
    if isinstance(task, dict):
        return task.get(key, default)
    fm = getattr(task, "frontmatter", None) or {}
    if key in ("id", "title", "deadline", "updated", "blocked_by", "status", "slug"):
        if hasattr(task, key):
            v = getattr(task, key, None)
            if v is not None:
                return v
        if isinstance(fm, dict):
            alt = {"task_id": "id"}.get(key, key)
            return fm.get(alt, fm.get(key, default))
    if isinstance(fm, dict):
        return fm.get(key, default)
    return default


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _priority_score(task: Any) -> float:
    ps = _task_get(task, "priority_score")
    if ps is not None:
        return float(ps)
    i = int(_task_get(task, "ice_i", 5) or 5)
    c = int(_task_get(task, "ice_c", 5) or 5)
    e = max(int(_task_get(task, "ice_e", 5) or 5), 1)
    return round((i * c) / e, 2)


def tasks_for_slug(all_tasks: list[Any], slug: str) -> list[Any]:
    return [t for t in all_tasks if _task_get(t, "slug") == slug]


def open_tasks_for_slug(all_tasks: list[Any], slug: str) -> list[Any]:
    return [
        t
        for t in tasks_for_slug(all_tasks, slug)
        if not is_terminal(_task_get(t, "status"))
    ]


def compute_last_task_activity(tasks: list[Any]) -> date | None:
    latest: date | None = None
    for t in tasks:
        d = _parse_date(_task_get(t, "updated"))
        if d and (latest is None or d > latest):
            latest = d
    return latest


def is_narrative_stale(
    hub_updated: str | None,
    last_task_activity: date | None,
    *,
    threshold_days: int = STALE_NARRATIVE_DAYS,
) -> bool:
    if not last_task_activity:
        return False
    hub_d = _parse_date(hub_updated)
    if hub_d is None:
        return True
    return (last_task_activity - hub_d).days >= threshold_days


def build_state_content(
    slug: str,
    all_tasks: list[Any],
    archived_tasks: list[Any],
    today: date,
    *,
    hub_updated: str | None = None,
    generated_at: str | None = None,
) -> tuple[str, bool]:
    """Return (markdown inner content, is_stale)."""
    open_tasks = open_tasks_for_slug(all_tasks, slug)
    status_counts = Counter(_task_get(t, "status") for t in open_tasks)

    scored: list[tuple[Any, float]] = []
    for t in open_tasks:
        if _task_get(t, "status") not in (STATUS_DOING, STATUS_NEXT):
            continue
        ps = _priority_score(t)
        ts = calc_today_score(ps, _task_get(t, "deadline"), today)
        scored.append((t, ts))
    scored.sort(key=lambda x: -x[1])
    top3 = scored[:3]

    deadlines: list[tuple[date, Any]] = []
    for t in open_tasks:
        dl = _parse_date(_task_get(t, "deadline"))
        if dl and dl >= today:
            deadlines.append((dl, t))
    deadlines.sort(key=lambda x: x[0])
    nearest = deadlines[0] if deadlines else None

    blocked = [
        t
        for t in open_tasks
        if _task_get(t, "blocked_by")
    ]

    week_ago = today - timedelta(days=7)
    done_recent: list[Any] = []
    for t in all_tasks + archived_tasks:
        if _task_get(t, "slug") != slug:
            continue
        if _task_get(t, "status") != "Done":
            continue
        d = _parse_date(_task_get(t, "updated"))
        if d and d >= week_ago:
            done_recent.append(t)
    done_recent.sort(
        key=lambda t: str(_task_get(t, "updated") or "")[:10],
        reverse=True,
    )

    all_slug_tasks = tasks_for_slug(all_tasks, slug) + [
        t for t in archived_tasks if _task_get(t, "slug") == slug
    ]
    last_activity = compute_last_task_activity(all_slug_tasks)
    stale = is_narrative_stale(hub_updated, last_activity)

    focused = [t for t in open_tasks if is_focus_current(_task_get(t, "focus"), today)]

    lines: list[str] = []

    # Header callout — counts plus the two dates worth seeing at a glance.
    lines.append(
        f"> [!abstract] Otevřené: {len(open_tasks)} — "
        f"Doing {status_counts.get('Doing', 0)} · "
        f"Next {status_counts.get('Next', 0)} · "
        f"Waiting {status_counts.get('Waiting', 0)} · "
        f"Backlog {status_counts.get('Backlog', 0)}"
    )
    meta: list[str] = []
    if last_activity:
        meta.append(f"Poslední aktivita tasku **{last_activity.isoformat()}**")
    if nearest:
        dl, t = nearest
        meta.append(
            f"nejbližší deadline **{dl.isoformat()}** "
            f"({_task_link(t, _task_get(t, 'id') or '?')})"
        )
    if meta:
        lines.append("> " + " · ".join(meta))
    if stale:
        lines.append(
            "> ⚠ **Kontext může být zastaralý** — hub `updated` je starší "
            f"než poslední pohyb tasků (>{STALE_NARRATIVE_DAYS} dní)."
        )

    def table(header: str, cols: list[str], rows: list[list[str]]) -> None:
        if not rows:
            return
        lines.append("")
        lines.append(f"**{header}**")
        lines.append("")
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["---"] * len(cols)) + "|")
        for row in rows:
            lines.append("| " + " | ".join(row) + " |")

    def id_title(t: Any) -> tuple[str, str]:
        tid = _task_get(t, "id") or _task_get(t, "task_id") or "?"
        return _task_link(t, tid), _cell(_task_get(t, "title") or "")

    table(
        "Ve fokusu tento týden",
        ["ID", "Název", "Stav"],
        [[*id_title(t), _cell(_task_get(t, "status") or "")] for t in focused[:5]],
    )

    table(
        "TOP 3 podle skóre",
        ["ID", "Název", "Skóre"],
        [[*id_title(t), str(ts)] for t, ts in top3],
    )

    table(
        "Blokované",
        ["ID", "Název", "Čeká na"],
        [
            [
                *id_title(t),
                _cell(", ".join(str(x) for x in (_task_get(t, "blocked_by") or [])[:3])),
            ]
            for t in blocked[:5]
        ],
    )

    table(
        "Hotovo za posledních 7 dní",
        ["ID", "Název", "Datum"],
        [
            [*id_title(t), _cell(str(_task_get(t, "updated") or "")[:10])]
            for t in done_recent[:3]
        ],
    )

    if generated_at:
        lines.append("")
        lines.append(f"_Aktualizováno {generated_at.replace('T', ' ')}_")

    return "\n".join(lines), stale


def wrap_state_block(inner: str) -> str:
    return f"{STATE_SECTION}\n{STATE_BEGIN}\n{inner}\n{STATE_END}"


def has_state_block(body: str) -> bool:
    """True for both the current `%%` markers and the legacy HTML comments."""
    return bool(STATE_BLOCK_RE.search(body))


def upsert_state_in_hub_body(body: str, inner: str) -> str:
    block = wrap_state_block(inner)
    match = STATE_BLOCK_RE.search(body)
    if match:
        # Drop every existing block, then put one back where the first one was.
        # A charter can end up with duplicates when an older build of this
        # module — which only recognised the HTML markers — runs against a hub
        # that has already been migrated to `%%`.
        head = body[: match.start()]
        tail = STATE_BLOCK_RE.sub("", body[match.start():]).lstrip("\n")
        return f"{head}{block}\n\n{tail}" if tail else f"{head}{block}\n"
    # Insert after first heading block (after # Title)
    m = re.search(r"^(#\s+.+\n\n)", body, re.MULTILINE)
    if m:
        pos = m.end()
        return body[:pos] + block + "\n\n" + body[pos:]
    return block + "\n\n" + body


def ensure_state_section_exists(body: str) -> str:
    if has_state_block(body):
        return body
    return upsert_state_in_hub_body(body, "_Generuje cron — první běh pending._")
