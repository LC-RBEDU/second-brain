#!/usr/bin/env python3
"""F7.2: Recurring task rotation — when a recurring task hits status: Done,
archive current instance and create the next one with reset body + new deadline.

Recurring tasks live as `02-PROJEKTY/<slug>/tasks/<ID> — <Title>.md`
(human-readable filename, em-dash U+2014; title is stable across rotations
so the filename does not change). Recurring detection is done via the
`recurring:` block in frontmatter (NOT via filename pattern — works
regardless of whether the file is named `<ID>.md` (legacy) or
`<ID> — <Title>.md` (post-F-fundamental refactor).

Frontmatter:
    recurring:
      frequency: weekly | monthly | every-n-days | weekday | last-weekday-before-day
      interval: 42                     # for every-n-days
      weekday: thursday                # for weekly | weekday | last-weekday-before-day
      day: 15                          # for last-weekday-before-day (cutoff day of month)
      reset_body_sections: ["## Operativní kroky", "## Poznámky / log"]
      preserve_body_sections: ["## Kontext"]
    extra_module: edu_news             # optional, calls lifecycle_extra_<module>.py clear

The `last-weekday-before-day` frequency is useful for monthly rituals that
must land on a specific weekday before a fixed monthly anchor (e.g. CFO
commentary must arrive on the last Friday before the strategic meeting,
which is held on the 15th of every month). The next deadline is the
largest date in the next month where that anchor has not yet passed,
restricted to (a) the configured weekday and (b) day-of-month ≤ (day - 1).

Workflow per Done recurring task:
1. Move current file (e.g. `<ID> — <Title>.md`) to
   `07-ARCHIV/tasks-done/<slug>/<ID>-<YYYY-MM-DD>.md` (rotation archive
   keeps date-suffixed name so multiple instances coexist in history).
2. Compute next deadline from frequency rule.
3. Create new instance at the original `task.rel_path` with:
   - status: Waiting (or ASAP if waitUntil already passed)
   - waitUntil = next_deadline - 1 day
   - deadline = next_deadline
   - reset body sections (Operativní kroky, Poznámky / log) cleared, preserved sections kept
   - frontmatter `created` updated, `updated` = today
4. If `extra_module: <name>` present, post-call `lifecycle_extra_<name>.py --reset`
   (out of scope here — handled by separate scripts wired in crontab).

Idempotent — re-running on Already-rotated task does nothing (status no longer Done).
"""
from __future__ import annotations

import calendar
import os
import re
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, DriveNotFoundError, credentials_from_env  # noqa: E402
from task_io import (  # noqa: E402
    iter_active_tasks,
    parse_task_text,
    serialize_task,
    parse_iso_date,
    ARCHIV_DIR,
)

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))

WEEKDAY_MAP = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}


def compute_next_deadline(rec: dict, last_deadline: Optional[date], today: date) -> date:
    """Compute next deadline based on recurring rule."""
    freq = (rec.get("frequency") or "").lower().strip()
    base = last_deadline or today

    if freq == "monthly":
        # Same day-of-month, next month
        d = base
        if d.month == 12:
            return d.replace(year=d.year + 1, month=1)
        try:
            return d.replace(month=d.month + 1)
        except ValueError:
            # e.g. Jan 31 → Feb 28
            for day in range(28, 32):
                try:
                    return d.replace(month=d.month + 1, day=min(day, 28))
                except ValueError:
                    continue
            return d.replace(month=d.month + 1, day=28)

    if freq == "weekly":
        wd_name = (rec.get("weekday") or "").lower().strip()
        wd = WEEKDAY_MAP.get(wd_name)
        if wd is None:
            return base + timedelta(days=7)
        # Next occurrence of weekday after today
        days_ahead = (wd - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    if freq == "every-n-days":
        try:
            interval = int(rec.get("interval") or 7)
        except (ValueError, TypeError):
            interval = 7
        return today + timedelta(days=interval)

    if freq == "weekday":
        wd_name = (rec.get("weekday") or "").lower().strip()
        wd = WEEKDAY_MAP.get(wd_name, 3)  # default thursday
        days_ahead = (wd - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    if freq == "last-weekday-before-day":
        wd_name = (rec.get("weekday") or "").lower().strip()
        wd = WEEKDAY_MAP.get(wd_name)
        try:
            day = int(rec.get("day") or 0)
        except (ValueError, TypeError):
            day = 0
        if wd is None or day < 2:
            # Misconfigured — fallback to +30 days so the task still rotates.
            return today + timedelta(days=30)
        return next_last_weekday_before_day(today, day, wd)

    # Unknown frequency — fallback to +7 days
    return today + timedelta(days=7)


def _last_weekday_before_day_in_month(
    year: int, month: int, day: int, weekday_idx: int
) -> Optional[date]:
    """Largest date in (year, month) with `date.weekday() == weekday_idx`
    and day-of-month ≤ (day - 1). Returns None if no such date exists
    (only happens for pathological inputs like day ≤ 1).

    Caps the cutoff at the actual length of the month so that
    `day` values larger than the month length (e.g. day=31 in February)
    still yield a sensible answer.
    """
    if day < 2:
        return None
    days_in_month = calendar.monthrange(year, month)[1]
    cutoff = min(day - 1, days_in_month)
    # cutoff ≥ 1 because day ≥ 2.
    # weekday occurs at most every 7 days, so scanning back at most 6 days finds it.
    for offset in range(7):
        d = cutoff - offset
        if d < 1:
            return None
        candidate = date(year, month, d)
        if candidate.weekday() == weekday_idx:
            return candidate
    return None


def next_last_weekday_before_day(today: date, day: int, weekday_idx: int) -> date:
    """Next strictly-future date matching the `last-weekday-before-day` rule.

    Walks forward month by month starting from `today.month` and returns
    the first match strictly later than `today`. Bounded by 14 months to
    avoid infinite loops on impossible inputs (would also catch a bug).
    """
    year, month = today.year, today.month
    for _ in range(14):
        candidate = _last_weekday_before_day_in_month(year, month, day, weekday_idx)
        if candidate is not None and candidate > today:
            return candidate
        month += 1
        if month > 12:
            month = 1
            year += 1
    raise ValueError(
        f"last-weekday-before-day: no valid date found within 14 months "
        f"of {today.isoformat()} (day={day}, weekday_idx={weekday_idx})"
    )


def reset_body(body: str, reset_sections: list[str], preserve_sections: list[str], task_id: str = "") -> str:
    """Clear specified ## sections, keep preserved ones.

    Subtask placeholder in `## Operativní kroky` uses the convention
    `**<ID>-N**` prefix (1-indexed). If `task_id` is empty, falls back to
    unprefixed placeholder.
    """
    sections: dict[str, list[str]] = {}
    current = "_HEADER"
    sections[current] = []

    for line in body.splitlines():
        if line.startswith("## "):
            current = line.strip()
            sections[current] = [line]
        else:
            sections[current].append(line)

    out_lines: list[str] = []
    for sec, lines in sections.items():
        if sec == "_HEADER":
            out_lines.extend(lines)
            continue
        if sec in reset_sections:
            out_lines.append(sec)
            if sec == "## Operativní kroky":
                prefix = f"**{task_id}-1** " if task_id else ""
                out_lines.append(f"- [ ] {prefix}(next instance — doplň operativní kroky)")
            elif sec == "## Poznámky / log":
                out_lines.append(f"- {datetime.now(TZ).date().isoformat()}: New recurring instance.")
            out_lines.append("")
        else:
            out_lines.extend(lines)

    return "\n".join(out_lines)


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)

    today = datetime.now(TZ).date()
    today_str = today.isoformat()
    rotated = 0
    skipped = 0

    for task in iter_active_tasks(vault):
        if not task.is_done:
            continue
        rec = task.frontmatter.get("recurring")
        if not rec or not isinstance(rec, dict):
            continue

        slug = task.slug or "unknown"
        task_id = task.task_id
        if not task_id:
            print(f"  ! skipping recurring task without id: {task.rel_path}")
            continue

        # 1. Archive current instance
        archive_filename = f"{task_id}-{today_str}.md"
        archive_path = f"{ARCHIV_DIR}/{slug}/{archive_filename}"
        vault.mkdir_p(f"{ARCHIV_DIR}/{slug}")

        try:
            existing = vault.stat(archive_path)
            if existing:
                print(f"  - archive exists: {archive_path}")
        except DriveNotFoundError:
            pass

        # 2. Compute next deadline
        last_dl = parse_iso_date(task.frontmatter.get("deadline"))
        next_dl = compute_next_deadline(rec, last_dl, today)
        next_wu = next_dl - timedelta(days=1)

        # 3. Reset body
        reset_sections = rec.get("reset_body_sections") or [
            "## Operativní kroky",
            "## Poznámky / log",
        ]
        preserve_sections = rec.get("preserve_body_sections") or []
        new_body = reset_body(task.body, reset_sections, preserve_sections, task_id=task_id)

        # 4. Build new frontmatter
        new_fm = dict(task.frontmatter)
        new_fm["status"] = "Waiting" if next_wu > today else "ASAP"
        new_fm["deadline"] = next_dl.isoformat()
        new_fm["waitUntil"] = next_wu.isoformat() if new_fm["status"] == "Waiting" else None
        new_fm["updated"] = today_str
        new_fm["created"] = today_str
        new_text = serialize_task(new_fm, new_body)

        # 5. Move current → archive, then write new at original path
        try:
            vault.move(task.rel_path, archive_path)
        except Exception as e:
            print(f"  ! archive move failed: {e}")
            skipped += 1
            continue

        try:
            vault.write_text(task.rel_path, new_text)
        except Exception as e:
            print(f"  ! new instance write failed: {e}")
            skipped += 1
            continue

        rotated += 1
        print(
            f"  ↻ {task.rel_path}: archived {today_str}, next deadline {next_dl.isoformat()}, "
            f"status={new_fm['status']}"
        )

        extra = task.frontmatter.get("extra_module")
        if extra:
            print(f"    extra_module: {extra} (handled by lifecycle_extra_{extra}.py)")

    print(f"lifecycle_recurring: rotated={rotated}, skipped={skipped}")


if __name__ == "__main__":
    main()
