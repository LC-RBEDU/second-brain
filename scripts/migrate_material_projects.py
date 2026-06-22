#!/usr/bin/env python3
"""Migrate legacy material frontmatter `project:` → `projects:` (M:N).

Idempotent — skips files that already have `projects:`.

Usage:
  python3 scripts/migrate_material_projects.py --dry-run
  python3 scripts/migrate_material_projects.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit(1)

DEFAULT_VAULT = Path.home() / "My Drive (lukas@redbuttonedu.cz)" / "SECOND_BRAIN" / "OBSIDIAN"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def migrate_file(path: Path, dry_run: bool) -> bool:
    # Tasks keep `project:` — only migrate material/attachment notes.
    rel = str(path)
    if "/tasks/" in rel.replace("\\", "/"):
        return False
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return False
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return False
    if not isinstance(fm, dict):
        return False
    mat_type = (fm.get("type") or "").lower()
    in_materials = "/materials/" in rel.replace("\\", "/") or rel.replace("\\", "/").startswith("05-RESOURCES/")
    if mat_type not in ("material", "attachment") and not in_materials:
        return False
    if fm.get("projects"):
        return False
    legacy = fm.get("project")
    if not legacy:
        return False
    if isinstance(legacy, list):
        fm["projects"] = legacy
    else:
        val = str(legacy).strip()
        fm["projects"] = [val if val.startswith("[[") else f"[[{val}]]"]
    del fm["project"]
    new_fm = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    new_text = f"---\n{new_fm}\n---\n{m.group(2)}"
    if dry_run:
        print(f"DRY {path}")
    else:
        path.write_text(new_text, encoding="utf-8")
        print(f"OK {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    n = 0
    for base in (args.vault / "02-PROJEKTY", args.vault / "05-RESOURCES"):
        if not base.exists():
            continue
        for md in base.rglob("*.md"):
            if migrate_file(md, args.dry_run):
                n += 1
    print(f"migrate_material_projects: {n} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
