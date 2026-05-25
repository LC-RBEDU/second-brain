#!/usr/bin/env python3
"""Flatten people and metrics_kpi from list-of-objects to list-of-strings.

Obsidian Properties UI does not support nested objects — they show up as
"Unsupported property type" + raw JSON. This converts:

    people:
      - role: Co-strategist
        name: "Luboš Malý"
    metrics_kpi:
      - kpi: "Foo"
        target: 3
        measured_at: "2026-09-30"

into:

    people:
      - "Luboš Malý (Co-strategist)"
    metrics_kpi:
      - "Foo → 3 (2026-09-30)"

Idempotent — strings are passed through unchanged.

Usage:
    python3 scripts/flatten_hub_frontmatter.py --dry-run
    python3 scripts/flatten_hub_frontmatter.py
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml not installed.\n")
    sys.exit(1)

DEFAULT_VAULT = Path(
    "/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN"
)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)


def flatten_person(item) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        name = item.get("name", "").strip() if item.get("name") else ""
        role = item.get("role", "").strip() if item.get("role") else ""
        if name and role:
            return f"{name} ({role})"
        return name or role or ""
    return str(item)


def flatten_kpi(item) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        kpi = item.get("kpi", "").strip() if item.get("kpi") else ""
        target = item.get("target")
        measured = item.get("measured_at", "").strip() if item.get("measured_at") else ""
        target_str = ""
        if target is not None and target != "":
            target_str = f" → {target}"
        measured_str = f" ({measured})" if measured else ""
        return f"{kpi}{target_str}{measured_str}".strip()
    return str(item)


def patch_hub(path: Path, dry_run: bool = False) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ! cannot read {path}: {e}")
        return False
    m = FRONTMATTER_RE.match(text)
    if not m:
        return False
    fm_yaml = m.group(1)
    body = m.group(2)
    try:
        fm = yaml.safe_load(fm_yaml) or {}
    except yaml.YAMLError as e:
        print(f"  ! YAML parse error in {path.name}: {e}")
        return False
    if not isinstance(fm, dict):
        return False
    if (fm.get("type") or "").lower() != "project":
        return False

    changed = False
    if isinstance(fm.get("people"), list):
        new_people = [flatten_person(p) for p in fm["people"] if p]
        new_people = [p for p in new_people if p]
        if new_people != fm["people"]:
            fm["people"] = new_people
            changed = True
    if isinstance(fm.get("metrics_kpi"), list):
        new_kpis = [flatten_kpi(k) for k in fm["metrics_kpi"] if k]
        new_kpis = [k for k in new_kpis if k]
        if new_kpis != fm["metrics_kpi"]:
            fm["metrics_kpi"] = new_kpis
            changed = True

    if not changed:
        return False

    new_yaml = yaml.safe_dump(
        fm, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    if not body.startswith("\n"):
        body = "\n" + body
    new_text = f"---\n{new_yaml}---{body}"
    if dry_run:
        print(f"  ~ {path.name} would change")
        return True
    path.write_text(new_text, encoding="utf-8")
    print(f"  ✓ {path.name} flattened")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    projekty = args.vault / "02-PROJEKTY"
    if not projekty.exists():
        sys.stderr.write(f"vault not found: {args.vault}\n")
        return 1
    hubs = sorted(projekty.glob("*.md"))
    n_changed = 0
    for hub in hubs:
        if hub.name.startswith("_"):
            continue
        if patch_hub(hub, dry_run=args.dry_run):
            n_changed += 1
    mode = "dry-run" if args.dry_run else "patched"
    print(f"\nflatten_hub_frontmatter: {n_changed}/{len(hubs)} hubs {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
