#!/usr/bin/env python3
"""One-time migration: normalize task source: → materials (VC7-9).

Usage:
  python3 scripts/migrate_task_sources.py --dry-run
  python3 scripts/migrate_task_sources.py --apply --batch-size 5
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_agent_context import (  # noqa: E402
    DEFAULT_VAULT,
    collect_tasks,
    parse_frontmatter,
    _list_str,
)
from safe_write import backup_files, content_hash, safe_write_text  # noqa: E402
from vault_reference import (  # noqa: E402
    SECTION_SHRUTI,
    material_summary,
    resolve_path,
    section_text,
    strip_wikilink,
)

SOURCE_KIND_MAP = {
    "sembly": "sembly",
    "slack": "slack-capture",
    "email": "email",
    "gdoc": "gdoc",
}


def _infer_kind(source: str, body: str) -> str:
    low = source.lower()
    if "sembly" in low or "/sembly/" in low:
        return "sembly"
    if "slack" in low:
        return "slack-capture"
    if "email" in low or "mail.google" in low:
        return "email"
    if "docs.google" in low:
        return "gdoc"
    return "meeting-notes"


def _source_id_from_path(source: str) -> str:
    base = Path(strip_wikilink(source)).name
    return hashlib.sha256(base.encode()).hexdigest()[:16]


def _ensure_shrnuti(body: str) -> str:
    if section_text(body, SECTION_SHRUTI):
        return body
    summary = material_summary(body)
    if body.strip().startswith("#"):
        lines = body.splitlines()
        insert_at = 1
        for i, ln in enumerate(lines[1:], 1):
            if ln.startswith("## "):
                insert_at = i
                break
        block = [SECTION_SHRUTI, ""] + [f"- {ln}" if not ln.startswith("-") else ln for ln in summary.splitlines() if ln.strip()]
        return "\n".join(lines[:insert_at] + block + [""] + lines[insert_at:])
    return f"{SECTION_SHRUTI}\n\n{summary}\n\n{body}"


def migrate_task(
    vault: Path,
    task,
    *,
    dry_run: bool,
) -> dict:
    tp = vault / task.rel_path
    text = tp.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    src = fm.get("source")
    if not src or not str(src).strip():
        return {"action": "skip", "reason": "no source"}

    src_str = str(src).strip()
    if src_str.startswith("http") and "slack.com" in src_str:
        return {"action": "manual", "reason": "slack URL — nelze fetchovat"}

    source_id = _source_id_from_path(src_str)
    materials = _list_str(fm.get("materials"))
    for m in materials:
        mp = resolve_path(vault, m)
        if not mp or not mp.exists():
            continue
        try:
            mfm, _ = parse_frontmatter(mp.read_text(encoding="utf-8"))
        except OSError:
            continue
        if mfm.get("source_id") == source_id or mfm.get("source_url") == src_str:
            return {"action": "skip", "reason": "already migrated", "task": task.id}

    src_path = resolve_path(vault, src_str)
    if not src_path or not src_path.exists():
        if not src_str.startswith("http"):
            return {"action": "manual", "reason": f"unresolved source: {src_str}"}
        return {"action": "manual", "reason": f"URL source needs MCP: {src_str[:60]}"}

    try:
        src_text = src_path.read_text(encoding="utf-8")
        src_fm, src_body = parse_frontmatter(src_text)
    except OSError:
        return {"action": "error", "reason": "unreadable source"}

    source_id = src_fm.get("source_id") or _source_id_from_path(src_str)
    mat_slug_dir = vault / "02-PROJEKTY" / task.slug / "materials"
    mat_name = f"{source_id} — {Path(src_path).stem}.md"
    mat_path = mat_slug_dir / mat_name

    kind = _infer_kind(src_str, src_body)
    title = src_fm.get("title") or Path(src_path).stem
    mat_body = _ensure_shrnuti(src_body if src_body.strip() else src_text)
    mat_content = (
        f"---\n"
        f"type: material\n"
        f"material_kind: {kind}\n"
        f"source_id: {source_id}\n"
        f"source_url: \"{src_str}\"\n"
        f"projects:\n  - \"[[{task.slug}]]\"\n"
        f"title: \"{title}\"\n"
        f"materialization: ok\n"
        f"---\n\n"
        f"{mat_body.strip()}\n"
    )

    wikilink = f"[[{mat_path.stem}]]"
    materials = _list_str(fm.get("materials"))
    if wikilink not in materials and mat_path.stem not in materials:
        materials.append(wikilink)

    new_fm = dict(fm)
    new_fm["materials"] = materials
    new_fm["source"] = src_str

    import yaml

    fm_yaml = yaml.safe_dump(new_fm, allow_unicode=True, sort_keys=False).strip()
    new_task = f"---\n{fm_yaml}\n---\n\n{body.lstrip()}"

    if dry_run:
        return {
            "action": "would_migrate",
            "task": task.id,
            "material": str(mat_path.relative_to(vault)),
        }

    backup_files([tp, mat_path] if mat_path.exists() else [tp], vault)
    mat_slug_dir.mkdir(parents=True, exist_ok=True)
    safe_write_text(mat_path, mat_content, expected_hash=content_hash(mat_path.read_text(encoding="utf-8")) if mat_path.exists() else None)
    safe_write_text(tp, new_task, expected_hash=content_hash(text))
    return {"action": "migrated", "task": task.id, "material": str(mat_path.relative_to(vault))}


def backfill_material_types(vault: Path, *, dry_run: bool) -> int:
    fixed = 0
    for slug_dir in (vault / "02-PROJEKTY").iterdir():
        if not slug_dir.is_dir():
            continue
        mat_dir = slug_dir / "materials"
        if not mat_dir.exists():
            continue
        for md in mat_dir.rglob("*.md"):
            text = md.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(text)
            changed = False
            if (fm.get("type") or "").lower() != "material":
                fm["type"] = "material"
                changed = True
            if not fm.get("material_kind"):
                fm["material_kind"] = "note"
                changed = True
            if not section_text(body, SECTION_SHRUTI):
                body = _ensure_shrnuti(body)
                changed = True
            if not changed:
                continue
            import yaml

            new_text = f"---\n{yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()}\n---\n\n{body.lstrip()}"
            if dry_run:
                print(f"DRY backfill {md.relative_to(vault)}")
            else:
                backup_files([md], vault)
                safe_write_text(md, new_text, expected_hash=content_hash(text))
            fixed += 1
    return fixed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--backfill-only", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.apply and not args.backfill_only:
        args.dry_run = True

    if args.backfill_only or args.apply:
        n = backfill_material_types(args.vault, dry_run=args.dry_run)
        print(f"backfill material_kind/type/shrnutí: {n}")

    if args.backfill_only:
        return 0

    tasks = [t for t in collect_tasks(args.vault, archive=False) if t.source]
    migrated = manual = skipped = 0
    processed = 0
    for task in tasks:
        if processed >= args.batch_size and args.apply:
            break
        r = migrate_task(args.vault, task, dry_run=args.dry_run)
        action = r.get("action")
        if action == "skip":
            skipped += 1
            continue
        print(r)
        processed += 1
        if action in ("migrated", "would_migrate"):
            migrated += 1
        elif action == "manual":
            manual += 1
    print(
        f"summary: migrated={migrated} manual={manual} skipped={skipped} "
        f"processed={processed} total_with_source={len(tasks)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
