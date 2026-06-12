"""Generate ## Stav (auto) marker blocks for project hub charters.

Marker delimiters:
  <!-- SB:STATE:BEGIN -->
  ...
  <!-- SB:STATE:END -->

Staleness: hub frontmatter `updated` older than last task activity by
STALE_NARRATIVE_DAYS → warning in block + entry in stale_hubs[].
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta
from typing import Any, Protocol

from today_priority import today_score as calc_today_score

STATE_BEGIN = "<!-- SB:STATE:BEGIN -->"
STATE_END = "<!-- SB:STATE:END -->"
STATE_SECTION = "## Stav (auto)"
STALE_NARRATIVE_DAYS = 14
STALE_AREA_WEEKS = 3

STATE_BLOCK_RE = re.compile(
    rf"({re.escape(STATE_SECTION)}\s*\n{re.escape(STATE_BEGIN)}\s*\n)"
    rf"(.*?)"
    rf"(\n{re.escape(STATE_END)})",
    re.DOTALL,
)


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
        if _task_get(t, "status") != "Done"
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
        if _task_get(t, "status") not in ("ASAP", "Next"):
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

    lines: list[str] = []
    if generated_at:
        lines.append(f"_Aktualizováno: {generated_at}_")
    lines.append("")
    lines.append(
        f"**Otevřené:** {len(open_tasks)} "
        f"(ASAP {status_counts.get('ASAP', 0)}, "
        f"Next {status_counts.get('Next', 0)}, "
        f"Waiting {status_counts.get('Waiting', 0)}, "
        f"Backlog {status_counts.get('Backlog', 0)})"
    )

    if top3:
        lines.append("")
        lines.append("**TOP 3 (score):**")
        for t, ts in top3:
            tid = _task_get(t, "id") or _task_get(t, "task_id") or "?"
            title = (_task_get(t, "title") or "")[:55]
            lines.append(f"- **{tid}** — {title} (score {ts})")

    if nearest:
        dl, t = nearest
        tid = _task_get(t, "id") or "?"
        title = (_task_get(t, "title") or "")[:50]
        lines.append("")
        lines.append(f"**Nejbližší deadline:** {dl.isoformat()} — **{tid}** — {title}")

    if blocked:
        lines.append("")
        lines.append(f"**Blokované ({len(blocked)}):**")
        for t in blocked[:5]:
            tid = _task_get(t, "id") or "?"
            bb = _task_get(t, "blocked_by") or []
            bb_s = ", ".join(str(x) for x in bb[:3])
            lines.append(f"- **{tid}** ← {bb_s}")

    if done_recent:
        lines.append("")
        lines.append(f"**Recently done (7 dní):** {len(done_recent)}")
        for t in done_recent[:3]:
            tid = _task_get(t, "id") or "?"
            title = (_task_get(t, "title") or "")[:50]
            lines.append(f"- **{tid}** — {title}")

    if last_activity:
        lines.append("")
        lines.append(f"**Poslední aktivita tasku:** {last_activity.isoformat()}")

    if stale:
        lines.append("")
        lines.append(
            "⚠ **Kontext může být zastaralý** — "
            f"hub `updated` je starší než poslední pohyb tasků "
            f"(>{STALE_NARRATIVE_DAYS} dní)."
        )

    return "\n".join(lines), stale


def wrap_state_block(inner: str) -> str:
    return f"{STATE_SECTION}\n{STATE_BEGIN}\n{inner}\n{STATE_END}"


def upsert_state_in_hub_body(body: str, inner: str) -> str:
    block = wrap_state_block(inner)
    if STATE_BEGIN in body and STATE_END in body:
        return STATE_BLOCK_RE.sub(
            rf"\1{inner}\3",
            body,
            count=1,
        )
    # Insert after first heading block (after # Title)
    m = re.search(r"^(#\s+.+\n\n)", body, re.MULTILINE)
    if m:
        pos = m.end()
        return body[:pos] + block + "\n\n" + body[pos:]
    return block + "\n\n" + body


def ensure_state_section_exists(body: str) -> str:
    if STATE_BEGIN in body:
        return body
    return upsert_state_in_hub_body(body, "_Generuje cron — první běh pending._")
