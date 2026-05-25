#!/usr/bin/env python3
"""Rewrite hub wikilinks to clean `[[<HubFilename>]]` form (readable display).

Display in body should be the human hub name ("M&A Odyssey"), not the slug
("ma-odyssey"). Target should be the hub charter file, not the folder
`02-PROJEKTY/<slug>/`. Best Obsidian form: `[[M&A Odyssey]]` — target = file,
display = filename without `.md`, fully readable.

Two patterns rewritten:
1. Bare `[[<slug>]]` → `[[<HubFilename>]]`     (slug-as-display, ambiguous folder/file)
2. Pipe-alias `[[<HubFilename>|<slug>]]` → `[[<HubFilename>]]`  (drop slug display)

Scope:
- All .md files under 02-PROJEKTY/ (hubs + tasks/ + materials/ + outputs)
- Frontmatter (within YAML strings) is left alone — Bases plugin uses
  `this.file.asLink()` and resolves aliases reliably for queries
- Body wikilinks rewritten only outside code fences

Idempotent — `[[<HubFilename>]]` form stays untouched on re-run.

Usage:
    python3 scripts/enforce_hub_pipe_alias.py --dry-run
    python3 scripts/enforce_hub_pipe_alias.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_VAULT = Path(
    "/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/OBSIDIAN"
)
MAPPING_PATH = Path(
    "/Users/lukascypra/My Drive (lukas@redbuttonedu.cz)/SECOND_BRAIN/scripts/migration-mapping.json"
)
FRONTMATTER_RE = re.compile(r"^(---\s*\n.*?\n---\s*\n)(.*)$", re.DOTALL)
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def load_mapping() -> dict[str, str]:
    """Return slug -> hub_filename_without_ext, only for non-skipped entries."""
    data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for entry in data:
        if entry.get("skip"):
            continue
        slug = entry["slug"]
        hub_no_ext = entry["hub_filename"].removesuffix(".md")
        out[slug] = hub_no_ext
    return out


def rewrite_body(body: str, mapping: dict[str, str]) -> tuple[str, int]:
    """Replace hub wikilinks with clean [[<HubFilename>]] form.

    Patterns rewritten:
    1. Bare `[[<slug>]]` -> `[[<HubFilename>]]`
    2. Pipe-alias `[[<HubFilename>|<slug>]]` -> `[[<HubFilename>]]`

    Skips wikilinks inside code fences. Preserves anchors `[[X#section]]`.
    """
    n_changes = 0
    code_spans: list[tuple[int, int]] = [
        (m.start(), m.end()) for m in CODE_FENCE_RE.finditer(body)
    ]

    def in_code(pos: int) -> bool:
        return any(s <= pos < e for s, e in code_spans)

    # Reverse map: hub_filename_no_ext -> slug (for matching pipe-alias form)
    hub_to_slug = {v: k for k, v in mapping.items()}

    # 1. Bare [[<slug>]] -> [[<HubFilename>]]
    bare_pattern = re.compile(r"\[\[([^\[\]\|\#/]+)\]\]")

    def replace_bare(m: re.Match) -> str:
        nonlocal n_changes
        if in_code(m.start()):
            return m.group(0)
        text = m.group(1).strip()
        # If text is a known slug, rewrite to hub filename
        hub = mapping.get(text)
        if hub:
            n_changes += 1
            return f"[[{hub}]]"
        return m.group(0)

    body = bare_pattern.sub(replace_bare, body)

    # 2. Pipe-alias [[<HubFilename>|<slug>]] -> [[<HubFilename>]]
    pipe_pattern = re.compile(r"\[\[([^\[\]\|\#]+)\|([^\[\]\|\#]+)\]\]")

    def replace_pipe(m: re.Match) -> str:
        nonlocal n_changes
        if in_code(m.start()):
            return m.group(0)
        target = m.group(1).strip()
        display = m.group(2).strip()
        # Only collapse if target is a known hub and display is its slug
        if target in hub_to_slug and hub_to_slug[target] == display:
            n_changes += 1
            return f"[[{target}]]"
        return m.group(0)

    body = pipe_pattern.sub(replace_pipe, body)
    return body, n_changes


def patch_file(path: Path, mapping: dict[str, str], dry_run: bool = False) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ! {path}: {e}")
        return 0

    fm_match = FRONTMATTER_RE.match(text)
    if fm_match:
        fm_block = fm_match.group(1)
        body = fm_match.group(2)
    else:
        fm_block = ""
        body = text

    new_body, n = rewrite_body(body, mapping)
    if n == 0:
        return 0

    new_text = fm_block + new_body
    if dry_run:
        print(f"  ~ {path.relative_to(path.parents[2]) if len(path.parents) >= 2 else path.name}: {n} link(s)")
        return n
    path.write_text(new_text, encoding="utf-8")
    rel = path.relative_to(path.parents[2]) if len(path.parents) >= 2 else path.name
    print(f"  ✓ {rel}: {n} link(s)")
    return n


def iter_target_files(vault: Path):
    projekty = vault / "02-PROJEKTY"
    if not projekty.exists():
        return
    # Hubs
    for f in sorted(projekty.glob("*.md")):
        if f.name.startswith("_"):
            continue
        yield f
    # Tasks + materials + outputs (any .md under <slug>/)
    for slug_dir in sorted(projekty.iterdir()):
        if not slug_dir.is_dir():
            continue
        for f in sorted(slug_dir.rglob("*.md")):
            yield f


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mapping = load_mapping()
    print(f"Loaded {len(mapping)} project slugs from migration-mapping.json")

    total_files = 0
    total_changes = 0
    for f in iter_target_files(args.vault):
        n = patch_file(f, mapping, dry_run=args.dry_run)
        if n:
            total_files += 1
            total_changes += n

    mode = "would patch" if args.dry_run else "patched"
    print(f"\nenforce_hub_pipe_alias: {total_changes} link(s) in {total_files} file(s) {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
