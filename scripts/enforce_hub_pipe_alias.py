#!/usr/bin/env python3
"""Rewrite bare slug wikilinks to pipe-alias form pointing at the hub charter.

Bare `[[ma-odyssey]]` relies on Obsidian alias resolution from the hub frontmatter
(`aliases: [ma-odyssey]`). When a folder of the same name exists (`02-PROJEKTY/ma-odyssey/`),
the resolution can be flaky depending on Obsidian settings (New link format,
alias cache rebuilds). Pipe-alias `[[M&A Odyssey|ma-odyssey]]` is deterministic —
it explicitly targets the hub file, display stays as the slug.

Scope:
- All .md files under 02-PROJEKTY/ (hubs + tasks/ + materials/ + outputs)
- Frontmatter (within YAML strings) is left alone — Bases plugin uses
  `this.file.asLink()` and resolves aliases reliably for queries
- Body wikilinks rewritten only when:
  - Match is `[[<slug>]]` (no pipe, no path, no anchor) — exact bare form
  - <slug> is a known project slug from migration-mapping.json
  - The wikilink isn't inside a code fence

Idempotent — pipe-alias form `[[Hub|slug]]` is left untouched on re-run.

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
    """Replace bare [[<slug>]] with [[<HubFilenameNoExt>|<slug>]] in body markdown.

    Skips wikilinks inside code fences. Preserves anything with pipe or anchor.
    """
    n_changes = 0
    code_spans: list[tuple[int, int]] = [
        (m.start(), m.end()) for m in CODE_FENCE_RE.finditer(body)
    ]

    def in_code(pos: int) -> bool:
        return any(s <= pos < e for s, e in code_spans)

    # Match exactly [[slug]] — no pipe, no /, no #, no |
    pattern = re.compile(r"\[\[([^\[\]\|\#/]+)\]\]")

    def replace(m: re.Match) -> str:
        nonlocal n_changes
        if in_code(m.start()):
            return m.group(0)
        slug = m.group(1).strip()
        hub = mapping.get(slug)
        if not hub:
            return m.group(0)
        n_changes += 1
        return f"[[{hub}|{slug}]]"

    new_body = pattern.sub(replace, body)
    return new_body, n_changes


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
