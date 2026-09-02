#!/usr/bin/env python3
"""Preview / apply Epic→Story hierarchy migration for RB Universe.

Default is dry-run (prints plan + writes docs/rbu-hierarchy-migration-preview.md).
Use ``--apply`` only after human approval — mutates vault task frontmatter.

Strategy (chosen variant):
- Keep RBU23, RBU7, RBU27 IDs; set ``type: epic`` (roadmap containers).
- All other open RBU files → ``type: story``.
- Wire ``parent:`` wikilinks from the six thematic groups.
- Hub ``RB Universe development.md`` gets ``hierarchy: true``.

Remaining epic checkbox work stays on the epic body for now (human can split
into new story IDs later with next_task_id.py). Auto-Done never closes epics.

Usage:
  python3 scripts/migrate_rbu_hierarchy.py
  python3 scripts/migrate_rbu_hierarchy.py --apply \\
    --vault "/Users/.../SECOND_BRAIN/OBSIDIAN"
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
DEFAULT_VAULT = Path.home() / "My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN"
PREVIEW_OUT = REPO / "docs" / "rbu-hierarchy-migration-preview.md"
SLUG = "rb-universe-development"
HUB_NAME = "RB Universe development.md"

# Epic IDs (keep number; flip type).
EPICS = {
    "RBU23": "Lidé a kontakty — karty externistů / NDA / brand",
    "RBU7": "Delivery / PM feature v Universe",
    "RBU27": "Těžba entit z nahrávek a integrace",
}

# story_id → parent epic id (None = standalone story / platform)
PARENTS: dict[str, str | None] = {
    # under RBU23
    "RBU61": "RBU23",
    "RBU21": "RBU23",
    "RBU18": "RBU23",
    "RBU57": "RBU23",
    # under RBU7
    "RBU16": "RBU7",
    "RBU44": "RBU7",
    # under RBU27
    "RBU6": "RBU27",
    "RBU49": "RBU27",
    # standalone stories
    "RBU58": None,  # Finance pohled
    "RBU62": None,  # Procesní architekt MCP
    "RBU60": None,  # Platforma / Traefik
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)


def parse_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, m.group(2)


def serialize(fm: dict, body: str) -> str:
    dump = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{dump}---\n{body}"


def parent_wikilink(epic_id: str, tasks_dir: Path) -> str:
    matches = list(tasks_dir.glob(f"{epic_id} — *.md")) + list(tasks_dir.glob(f"{epic_id}.md"))
    if matches:
        stem = matches[0].stem
        return f"[[{stem}]]"
    return f"[[{epic_id}]]"


def plan_changes(tasks_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(tasks_dir.glob("*.md")):
        fm, body = parse_md(path)
        tid = str(fm.get("id") or "")
        if not tid.startswith("RBU"):
            continue
        title = str(fm.get("title") or path.stem)
        old_type = str(fm.get("type") or "task")
        old_parent = fm.get("parent")
        if tid in EPICS:
            new_type = "epic"
            new_parent = None
            note = EPICS[tid]
        else:
            new_type = "story"
            parent_id = PARENTS.get(tid)
            new_parent = parent_wikilink(parent_id, tasks_dir) if parent_id else None
            note = f"parent → {parent_id}" if parent_id else "standalone story"
        rows.append(
            {
                "id": tid,
                "path": path,
                "title": title,
                "old_type": old_type,
                "new_type": new_type,
                "old_parent": old_parent,
                "new_parent": new_parent,
                "note": note,
                "fm": fm,
                "body": body,
            }
        )
    return rows


def render_preview(rows: list[dict], today: str) -> str:
    lines = [
        f"# RBU hierarchy migration preview ({today})",
        "",
        "Dry-run plán. Zápis jen po `--apply` a tvém `ano`.",
        "",
        "## Strategie",
        "",
        "- **RBU23, RBU7, RBU27** → `type: epic` (stejné ID)",
        "- Ostatní otevřené RBU → `type: story` + `parent:` dle skupiny",
        "- Hub → `hierarchy: true`",
        "- Epic checkboxy se zatím nerozřezávají na nová story ID (další iterace)",
        "",
        "## Diff",
        "",
        "| ID | Title | type | parent | poznámka |",
        "|----|-------|------|--------|----------|",
    ]
    for r in rows:
        parent = r["new_parent"] or "—"
        lines.append(
            f"| {r['id']} | {r['title']} | `{r['old_type']}` → `{r['new_type']}` "
            f"| {parent} | {r['note']} |"
        )
    lines.extend(
        [
            "",
            "## Skupiny",
            "",
            "1. **Lidé a kontakty** — epic RBU23 ← RBU61, RBU21, RBU18, RBU57",
            "2. **Delivery / PM** — epic RBU7 ← RBU16, RBU44",
            "3. **Těžba / integrace** — epic RBU27 ← RBU6, RBU49",
            "4. **Finance pohled** — story RBU58 (standalone)",
            "5. **Procesní architekt** — story RBU62 (standalone)",
            "6. **Platforma** — story RBU60 (standalone)",
            "",
        ]
    )
    return "\n".join(lines)


def apply_row(row: dict, today: str) -> None:
    fm = dict(row["fm"])
    fm["type"] = row["new_type"]
    if row["new_parent"]:
        fm["parent"] = row["new_parent"]
    elif "parent" in fm:
        # Epics / standalone — clear stale parent
        fm["parent"] = None
    fm["updated"] = today
    body = row["body"]
    log_line = (
        f"- {today}: Hierarchy migration — type `{row['new_type']}`"
        + (f", parent {row['new_parent']}" if row["new_parent"] else "")
        + ". [migrate_rbu_hierarchy]\n"
    )
    if "## Poznámky / log" in body:
        body = body.rstrip() + "\n" + log_line
    else:
        body = body.rstrip() + "\n\n## Poznámky / log\n" + log_line
    row["path"].write_text(serialize(fm, body), encoding="utf-8")


def patch_hub(hub_path: Path, today: str) -> None:
    fm, body = parse_md(hub_path)
    fm["hierarchy"] = True
    fm["updated"] = today
    hub_path.write_text(serialize(fm, body), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", type=Path, default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    vault = args.vault or Path(os_env_vault())
    tasks_dir = vault / "02-PROJEKTY" / SLUG / "tasks"
    hub_path = vault / "02-PROJEKTY" / HUB_NAME
    today = date.today().isoformat()

    if not tasks_dir.is_dir():
        # Still emit preview from PARENTS/EPICS constants for cloud / docs
        print(f"Vault tasks dir missing: {tasks_dir}")
        print("Writing constant-based preview only.")
        rows = [
            {
                "id": tid,
                "title": note,
                "old_type": "task",
                "new_type": "epic",
                "new_parent": None,
                "note": note,
            }
            for tid, note in EPICS.items()
        ]
        for tid, parent in PARENTS.items():
            rows.append(
                {
                    "id": tid,
                    "title": "(file not in this environment)",
                    "old_type": "task",
                    "new_type": "story",
                    "new_parent": f"[[{parent}]]" if parent else None,
                    "note": f"parent → {parent}" if parent else "standalone story",
                }
            )
        rows.sort(key=lambda r: r["id"])
        preview = render_preview(rows, today)
        PREVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
        PREVIEW_OUT.write_text(preview, encoding="utf-8")
        print(preview)
        print(f"\nWrote {PREVIEW_OUT}")
        if args.apply:
            print("ERROR: --apply requires vault with tasks/", file=sys.stderr)
            return 1
        return 0

    rows = plan_changes(tasks_dir)
    preview = render_preview(rows, today)
    PREVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_OUT.write_text(preview, encoding="utf-8")
    print(preview)
    print(f"\nWrote {PREVIEW_OUT}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply after approval.")
        return 0

    for row in rows:
        apply_row(row, today)
        print(f"  ✓ {row['path'].name}")
    if hub_path.is_file():
        patch_hub(hub_path, today)
        print(f"  ✓ hub hierarchy: true → {hub_path.name}")
    print(f"Applied {len(rows)} task files.")
    return 0


def os_env_vault() -> str:
    import os

    return os.environ.get("VAULT_PATH") or str(DEFAULT_VAULT)


if __name__ == "__main__":
    raise SystemExit(main())
