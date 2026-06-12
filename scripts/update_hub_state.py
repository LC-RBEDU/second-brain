#!/usr/bin/env python3
"""Local: refresh ## Stav (auto) blocks in project hub charters.

Usage:
    python3 scripts/update_hub_state.py
    python3 scripts/update_hub_state.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pip install pyyaml\n")
    sys.exit(1)

_LIB = Path(__file__).resolve().parents[1] / "vps" / "second-brain-hub" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from hub_state import build_state_content, upsert_state_in_hub_body  # noqa: E402
from today_priority import today_score  # noqa: noqa — used via hub_state

DEFAULT_VAULT = Path(
    os.environ.get(
        "SECOND_BRAIN_VAULT",
        str(Path.home() / "My Drive (lukas@redbuttonedu.cz)" / "SECOND_BRAIN" / "OBSIDIAN"),
    )
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)


def _parse_hub(text: str) -> tuple[dict, str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text, ""
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm if isinstance(fm, dict) else {}, m.group(1), m.group(2)


class _Task:
    def __init__(self, fm: dict, rel_path: str, slug: str):
        self.frontmatter = fm
        self.rel_path = rel_path
        self.slug = slug
        self.task_id = str(fm.get("id") or "")
        self.status = str(fm.get("status") or "Next")

    @property
    def id(self):
        return self.task_id


def collect_tasks(vault: Path, archive: bool = False) -> list[_Task]:
    base = vault / ("07-ARCHIV/tasks-done" if archive else "02-PROJEKTY")
    out: list[_Task] = []
    if not base.exists():
        return out
    for slug_dir in sorted(base.iterdir()):
        if not slug_dir.is_dir():
            continue
        slug = slug_dir.name
        tasks_dir = slug_dir if archive else slug_dir / "tasks"
        if not tasks_dir.exists():
            continue
        for tf in tasks_dir.glob("*.md"):
            m = FRONTMATTER_RE.match(tf.read_text(encoding="utf-8"))
            if not m:
                continue
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                continue
            if not isinstance(fm, dict):
                continue
            out.append(_Task(fm, str(tf.relative_to(vault)), slug))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    vault = args.vault
    if not vault.exists():
        sys.stderr.write(f"ERROR: vault not found: {vault}\n")
        return 1

    now = datetime.now()
    today = now.date()
    generated_at = now.isoformat(timespec="minutes")

    active = collect_tasks(vault, archive=False)
    archived = collect_tasks(vault, archive=True)

    updated = 0
    projekty = vault / "02-PROJEKTY"
    for hub in sorted(projekty.glob("*.md")):
        if hub.name.startswith("_"):
            continue
        text = hub.read_text(encoding="utf-8")
        fm, fm_yaml, body = _parse_hub(text)
        if (fm.get("type") or "").lower() != "project":
            continue
        slug = str(fm.get("slug") or hub.stem)
        hub_updated = fm.get("updated")
        if hub_updated is not None:
            hub_updated = str(hub_updated)[:10]

        inner, _ = build_state_content(
            slug, active, archived, today,
            hub_updated=hub_updated,
            generated_at=generated_at,
        )
        new_body = upsert_state_in_hub_body(body, inner)
        if new_body == body:
            continue
        if args.dry_run:
            print(f"would update {hub.name}")
            updated += 1
            continue
        hub.write_text(f"---\n{fm_yaml}---\n{new_body}", encoding="utf-8")
        updated += 1
        print(f"  ✓ {hub.name}")

    print(f"update_hub_state: updated={updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
