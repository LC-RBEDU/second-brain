#!/usr/bin/env python3
"""F6.1: Auto-flip task/story status → Done when all checkboxes are [x].

Scans 02-PROJEKTY/<slug>/tasks/*.md, parses frontmatter + body, finds tasks where:
- status not in (Done, Cancelled) — a cancelled task stays cancelled even
  when its checkboxes are all ticked
- ``type`` is not ``epic`` — epics are closed only by a human
- body has ≥1 checkbox in `## Operativní kroky` and all are checked

Patches frontmatter status: Done + updated: today, appends log line.
CAS-aware: skip on conflict (user is editing).

Idempotent — re-running does not double-flip.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from vault_factory import open_vault  # noqa: E402
from github_rbu_closes import story_has_open_child  # noqa: E402
from hierarchy import is_epic, is_story  # noqa: E402
from task_io import iter_active_tasks, update_task, all_checkboxes_done  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def should_auto_done(task: Any, tasks: list[Any]) -> bool:
    """A story with an open child task stays open even when every box is [x]."""
    if task.is_terminal or is_epic(task):
        return False
    story_id = str(task.frontmatter.get("id") or "")
    if is_story(task) and story_has_open_child(tasks, story_id):
        return False
    return all_checkboxes_done(task.body)


def main() -> None:
    with open_vault() as vault:
        today = datetime.now(TZ).date().isoformat()
        flipped = 0
        skipped = 0
        skipped_epic = 0

        tasks = list(iter_active_tasks(vault))
        for task in tasks:
            if task.is_terminal:
                continue
            if is_epic(task):
                # Epics never auto-close from checkbox state.
                if all_checkboxes_done(task.body):
                    skipped_epic += 1
                continue
            if not should_auto_done(task, tasks):
                if is_story(task) and story_has_open_child(tasks, str(task.frontmatter.get("id") or "")):
                    skipped += 1
                    print(f"  - {task.rel_path} stays open (child task)")
                continue

            log = f"- {today}: Done — auto (všechny operativní kroky [x]). [lifecycle_done_from_checkboxes]\n"
            ok = update_task(
                vault,
                task,
                new_status="Done",
                today_str=today,
                body_append=log,
            )
            if ok:
                flipped += 1
                print(f"  ✓ {task.rel_path} → Done")
            else:
                skipped += 1

        print(
            f"lifecycle_done_from_checkboxes: flipped={flipped}, "
            f"conflicts/skipped={skipped}, epic_skipped={skipped_epic}"
        )


if __name__ == "__main__":
    main()
