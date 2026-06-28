#!/usr/bin/env python3
"""Scaffold a new project hub from topic-template-v2.md.

Usage:
  python3 scripts/create_project_hub.py --slug my-project --hub-name "My Project" \\
    --area "03-AREAS/Technologie a nástroje" --id-prefix MP --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VAULT = REPO / "OBSIDIAN"
TEMPLATE = VAULT / "00-System" / "Templates" / "topic-template-v2.md"
MAPPING = REPO / "scripts" / "migration-mapping.json"
PROJEKTY = VAULT / "02-PROJEKTY"
AREAS = VAULT / "03-AREAS"


def _load_template_body() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    if not text.startswith("---"):
        sys.exit("ERROR: topic-template-v2.md missing frontmatter")
    end = text.find("\n---", 3)
    body = text[end + 4 :].lstrip("\n")
    cut = body.find("\n<!--")
    if cut >= 0:
        body = body[:cut].rstrip() + "\n"
    return body


def _hub_template(slug: str, hub_name: str, area: str, today: str) -> str:
    area_link = area if area.startswith("[[") else f'"[[{area}]]"'
    return f"""---
type: project
slug: {slug}
aliases:
- {slug}
status: active
area: {area_link}
open_tasks_count: 0
created: {today}
updated: {today}
---

"""


def _substitute_body(body: str, slug: str, hub_name: str) -> str:
    body = body.replace("<Lidský název projektu>", hub_name)
    body = body.replace("<slug>", slug)
    body = re.sub(
        r"\| _\(příklad\)_.*\|\n(\| _\(příklad\)_.*\|\n){2}",
        "| _(doplň)_ | | |\n",
        body,
    )
    return body


def _basename_collision(hub_name: str) -> Path | None:
    hub_base = hub_name
    area_path = AREAS / f"{hub_base}.md"
    if area_path.is_file():
        return area_path
    return None


def _append_mapping(
    slug: str,
    hub_filename: str,
    hub_name: str,
    id_prefix: str,
    area: str,
    dry_run: bool,
) -> None:
    area_val = area if area.startswith("[[") else f"[[{area}]]"
    entry = {
        "slug": slug,
        "hub_filename": hub_filename,
        "czech_name": hub_name,
        "id_prefix": id_prefix,
        "area": area_val,
    }
    data = json.loads(MAPPING.read_text(encoding="utf-8"))
    if any(e.get("slug") == slug for e in data):
        print(f"  mapping: slug {slug} already in migration-mapping.json")
        return
    data.append(entry)
    if dry_run:
        print(f"  would append to migration-mapping.json: {entry}")
        return
    MAPPING.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"  appended migration-mapping.json: {slug} → {id_prefix}")


def create_project(
    slug: str,
    hub_name: str,
    area: str,
    id_prefix: str,
    dry_run: bool,
    skip_mapping: bool,
    skip_rebuild: bool,
) -> int:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        print(f"ERROR: invalid slug {slug!r} (kebab-case latin only)", file=sys.stderr)
        return 1
    if not re.fullmatch(r"[A-Z0-9]{2,4}", id_prefix):
        print(f"ERROR: invalid id_prefix {id_prefix!r} (2–4 uppercase alnum)", file=sys.stderr)
        return 1

    hub_filename = f"{hub_name}.md"
    hub_path = PROJEKTY / hub_filename
    slug_dir = PROJEKTY / slug

    if hub_path.exists():
        print(f"ERROR: hub already exists: {hub_path}", file=sys.stderr)
        return 1
    if slug_dir.exists():
        print(f"ERROR: slug folder already exists: {slug_dir}", file=sys.stderr)
        return 1

    collision = _basename_collision(hub_name)
    if collision:
        print(
            f"ERROR: basename collision — {hub_name}.md vs {collision.relative_to(VAULT)}. "
            "Rename area with suffix ' (oblast)' or pick different hub name.",
            file=sys.stderr,
        )
        return 1

    today = date.today().isoformat()
    fm_and_title = _hub_template(slug, hub_name, area, today)
    body = _substitute_body(_load_template_body(), slug, hub_name)
    content = fm_and_title + body

    dirs = [
        slug_dir / "tasks",
        slug_dir / "materials",
        slug_dir / "outputs",
    ]

    print(f"Hub: {hub_path.relative_to(VAULT)}")
    print(f"Dirs: {[str(d.relative_to(VAULT)) for d in dirs]}")
    if dry_run:
        print("\n--- preview (first 40 lines) ---")
        print("\n".join(content.splitlines()[:40]))
        print("...")
    else:
        hub_path.write_text(content, encoding="utf-8")
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        print(f"created: {hub_path.name}")

    if not skip_mapping:
        _append_mapping(slug, hub_filename, hub_name, id_prefix, area, dry_run)

    if not dry_run and not skip_rebuild:
        subprocess.run(
            [sys.executable, str(REPO / "scripts" / "build_agent_context.py")],
            check=False,
        )
        subprocess.run(
            [sys.executable, str(REPO / "scripts" / "build_work_context.py"), slug],
            check=False,
        )

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold new project hub from topic-template-v2")
    ap.add_argument("--slug", required=True, help="kebab-case project slug")
    ap.add_argument("--hub-name", required=True, help='Human hub title, e.g. "My Project"')
    ap.add_argument(
        "--area",
        required=True,
        help='Area path or wikilink, e.g. "03-AREAS/Technologie a nástroje"',
    )
    ap.add_argument("--id-prefix", required=True, help="Task ID prefix, e.g. MNP")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-mapping", action="store_true")
    ap.add_argument("--skip-rebuild", action="store_true")
    args = ap.parse_args()
    return create_project(
        slug=args.slug,
        hub_name=args.hub_name,
        area=args.area,
        id_prefix=args.id_prefix.upper(),
        dry_run=args.dry_run,
        skip_mapping=args.skip_mapping,
        skip_rebuild=args.skip_rebuild,
    )


if __name__ == "__main__":
    sys.exit(main())
