#!/usr/bin/env python3
"""One-shot hygiene after VC11 source migration (2026-06-28).

1. Clear task source: where materials resolve
2. Rename MO5/MO7 primary materials to {hash} — stem convention
3. Archive 01-INBOX captures referenced by tasks → 07-ARCHIV/inbox-processed
4. Fix RBU23 empty materials entry
5. Add projects: to 05-RESOURCES without project linkage
6. Add ## Otevřené otázky to Second Brain hub charter

Usage:
  python3 scripts/finalize_migration_hygiene.py --dry-run
  python3 scripts/finalize_migration_hygiene.py --apply
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path

import yaml

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_agent_context import DEFAULT_VAULT, collect_tasks, parse_frontmatter  # noqa: E402
from safe_write import backup_files, content_hash, safe_write_text  # noqa: E402
from vault_reference import resolve_path, strip_wikilink  # noqa: E402

INBOX_TASK_SOURCES = [
    "01-INBOX/sembly/2026-06-25-1002-summit-prodej-vstupenek.md",
    "01-INBOX/sembly/2026-06-25-1227-google-meet-6-25-2026.md",
    "01-INBOX/sembly/2026-06-04-1420-dominik-luk.md",
    "01-INBOX/slack/2026-06-04-1329-_claude-capture-firemn-procesy-gdpr-evidence-jako-zcela-nov-task-b.md",
    "01-INBOX/slack/2026-06-01-1236-_claude-capture-sales-a-business-development-pprava-rozen-rmcovky-.md",
    "01-INBOX/slack/2026-06-10-1045-_claude-capture-odpovdt-na-dotaznk-equilibrium-red-button-networkh.md",
    "01-INBOX/slack/2026-06-16-1440-_claude-capture-rb-universe-doplnit-monosti-filtrovn-do-pehled-fin.md",
    "01-INBOX/sembly/2026-06-26-0949-rb-sales-feed-refresh.md",
    "01-INBOX/sembly/2026-06-26-0845-procesn-mapa-v-universe.md",
    "01-INBOX/sembly/2026-06-11-1007-google-meet-6-11-2026.md",
    "01-INBOX/sembly/2026-06-16-1440-lubo-luk-1-1.md",
    "01-INBOX/sembly/2026-06-23-1003-google-meet-6-23-2026.md",
    "01-INBOX/slack/2026-06-16-1430-_claude-capture-finance-pprava-plnu-reijnch-nkladne-jsou-nov-nahir.md",
    "01-INBOX/slack/2026-06-24-0912-_claude-capture-finance-kol-provit-ve-finannm-pehledu-pohledy-na-h.md",
    "01-INBOX/slack/2026-06-22-0936-_claude-capture-strategy-peklopit-pln-order-entry-do-plnu-revenue-.md",
    "01-INBOX/slack/2026-05-29-1421-_claude-capture-strategy-shrnut-a-koly-dle-zpisu.md",
    "01-INBOX/slack/2026-06-16-1441-_claude-capture-strategy-antischwarz-pipravit-strukturu-tmat-kterc.md",
]

MA_ODYSSEY_RENAMES = (
    (
        "02-PROJEKTY/ma-odyssey/materials/2026-04-29 — Plaud schůzka Odyssey právník DD (transcript).md",
        "2026-04-29 — Plaud schůzka Odyssey právník DD (transcript).md",
    ),
    (
        "02-PROJEKTY/ma-odyssey/materials/2026-05-13 — Email EDU ODY deal Lokajíček (vlákno).md",
        "2026-05-13 — Email EDU ODY deal Lokajíček (vlákno).md",
    ),
)


def _source_id_from_name(filename: str) -> str:
    return hashlib.sha256(filename.encode()).hexdigest()[:16]


def _inbox_archive_dest(vault: Path, rel: str) -> Path:
    parts = Path(rel).parts
    name = parts[-1]
    m = re.match(r"(\d{4})-(\d{2})-", name)
    if not m:
        raise ValueError(f"cannot parse date from {rel}")
    year, month = m.group(1), m.group(2)
    kind = parts[1] if len(parts) > 2 else "misc"
    return vault / "07-ARCHIV" / "inbox-processed" / year / month / kind / name


def _resource_projects(rel: str, fm: dict) -> list[str]:
    rel = rel.replace("\\", "/")
    topics = " ".join(str(t) for t in (fm.get("topics") or [])).lower()
    title = str(fm.get("title") or "").lower()
    cat = str(fm.get("category") or "").lower()

    if "komunity" in rel or "equilibrium" in topics or "equilibrium" in title:
        return ["[[RB Network]]"]
    if rel.startswith("05-RESOURCES/profil-rb-edu/"):
        return ["[[Strategy]]"]
    if rel.startswith("05-RESOURCES/smlouvy/"):
        return ["[[Firemní procesy]]"]
    if rel.startswith("05-RESOURCES/vzdelavani/"):
        return ["[[AI & Vibe coding]]"]
    if rel.startswith("05-RESOURCES/inspirace/"):
        ai_markers = ("claude", "anthropic", "ai ", "notebooklm", "vibe", "agent")
        blob = f"{rel} {title} {cat}".lower()
        if any(m in blob for m in ai_markers):
            return ["[[AI & Vibe coding]]"]
        return ["[[Second Brain]]"]
    return ["[[Second Brain]]"]


def _replace_path_refs(vault: Path, old: str, new: str, *, dry_run: bool) -> int:
    count = 0
    for md in vault.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        if old not in text:
            continue
        count += 1
        if not dry_run:
            safe_write_text(md, text.replace(old, new), expected_hash=content_hash(text))
    return count


def _dump_task(fm: dict, body: str) -> str:
    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{fm_yaml}\n---\n\n{body.lstrip()}"


def clear_task_sources(vault: Path, *, dry_run: bool) -> int:
    cleared = 0
    for task in collect_tasks(vault, archive=False) + collect_tasks(vault, archive=True):
        tp = vault / task.rel_path
        text = tp.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        if "source" not in fm:
            continue
        src = fm.get("source")
        mats = [m for m in (fm.get("materials") or []) if str(m).strip()]
        if src and str(src).strip() and mats:
            broken = False
            for m in mats:
                mp = resolve_path(vault, str(m))
                if not mp or not mp.exists():
                    sys.stderr.write(f"WARN skip clear source (broken material): {task.id}\n")
                    broken = True
                    break
            if broken:
                continue
        del fm["source"]
        cleared += 1
        if not dry_run:
            backup_files([tp], vault)
            safe_write_text(tp, _dump_task(fm, body), expected_hash=content_hash(text))
    return cleared


def rename_ma_materials(vault: Path, *, dry_run: bool) -> list[tuple[str, str]]:
    renames: list[tuple[str, str]] = []
    for rel, stem in MA_ODYSSEY_RENAMES:
        old_path = vault / rel
        if not old_path.exists():
            sys.stderr.write(f"WARN missing material: {rel}\n")
            continue
        sid = _source_id_from_name(stem)
        new_name = f"{sid} — {stem}"
        new_rel = str(old_path.parent.relative_to(vault) / new_name)
        renames.append((rel, new_rel))
        if dry_run:
            continue
        text = old_path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        fm["source_id"] = sid
        new_text = f"---\n{yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()}\n---\n\n{body.lstrip()}"
        new_path = vault / new_rel
        backup_files([old_path], vault)
        new_path.parent.mkdir(parents=True, exist_ok=True)
        safe_write_text(new_path, new_text)
        old_path.unlink()
    old_stems = [Path(r[0]).stem for r in MA_ODYSSEY_RENAMES]
    for old_stem, (_, new_rel) in zip(old_stems, renames, strict=True):
        new_stem = Path(new_rel).stem
        _replace_path_refs(vault, old_stem, new_stem, dry_run=dry_run)
    return renames


def archive_inbox_captures(vault: Path, *, dry_run: bool) -> list[tuple[str, str]]:
    moves: list[tuple[str, str]] = []
    for rel in INBOX_TASK_SOURCES:
        src = vault / rel
        dest = _inbox_archive_dest(vault, rel)
        new_rel = str(dest.relative_to(vault))
        if src.exists():
            if not dry_run:
                backup_files([src], vault)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    if dest.read_bytes() != src.read_bytes():
                        sys.stderr.write(f"WARN dest differs, keeping archive: {new_rel}\n")
                    src.unlink()
                else:
                    shutil.move(str(src), str(dest))
        elif not dest.exists():
            sys.stderr.write(f"WARN inbox missing (no archive): {rel}\n")
            continue
        moves.append((rel, new_rel))
        if not dry_run:
            _replace_path_refs(vault, rel, new_rel, dry_run=False)
    return moves


def fix_rbu23(vault: Path, *, dry_run: bool) -> bool:
    rel = "02-PROJEKTY/rb-universe-development/tasks/RBU23 — MVP karet externistů v RB Universe.md"
    tp = vault / rel
    text = tp.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    mats = [m for m in (fm.get("materials") or []) if str(m).strip()]
    changed = len(mats) != len(fm.get("materials") or [])
    fm["materials"] = mats
    if "source" in fm:
        del fm["source"]
        changed = True
    new_body = body.replace("**Z:**  + ", "**Z:** ")
    if new_body != body:
        changed = True
        body = new_body
    if changed and not dry_run:
        backup_files([tp], vault)
        safe_write_text(tp, _dump_task(fm, body), expected_hash=content_hash(text))
    return changed


def link_resources(vault: Path, *, dry_run: bool) -> int:
    fixed = 0
    res_root = vault / "05-RESOURCES"
    for md in res_root.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        end = text.index("---", 3)
        fm = yaml.safe_load(text[3:end]) or {}
        if fm.get("projects"):
            continue
        rel = str(md.relative_to(vault))
        fm["projects"] = _resource_projects(rel, fm)
        new_text = f"---\n{yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()}\n---\n{text[end + 3:]}"
        fixed += 1
        if not dry_run:
            backup_files([md], vault)
            safe_write_text(md, new_text, expected_hash=content_hash(text))
    return fixed


def fix_second_brain_charter(vault: Path, *, dry_run: bool) -> bool:
    hub = vault / "02-PROJEKTY" / "Second Brain.md"
    text = hub.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if "## Otevřené otázky" in body:
        return False
    marker = "## Materiály"
    section = "## Otevřené otázky\n\n_(žádné teď)_\n\n"
    if marker not in body:
        body = body.rstrip() + f"\n\n{section}"
    else:
        body = body.replace(marker, section + marker, 1)
    if not dry_run:
        backup_files([hub], vault)
        safe_write_text(hub, _dump_task(fm, body), expected_hash=content_hash(text))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry_run = args.dry_run or not args.apply
    if not args.vault.exists():
        sys.stderr.write(f"ERROR: vault not found: {args.vault}\n")
        return 1

    print(f"mode: {'dry-run' if dry_run else 'apply'}")
    n_src = clear_task_sources(args.vault, dry_run=dry_run)
    print(f"cleared task source: {n_src}")
    renames = rename_ma_materials(args.vault, dry_run=dry_run)
    print(f"ma-odyssey material renames: {len(renames)}")
    for o, n in renames:
        print(f"  {o} -> {n}")
    moves = archive_inbox_captures(args.vault, dry_run=dry_run)
    print(f"inbox archived: {len(moves)}")
    for o, n in moves:
        print(f"  {o} -> {n}")
    rbu = fix_rbu23(args.vault, dry_run=dry_run)
    print(f"rbu23 fixed: {rbu}")
    n_res = link_resources(args.vault, dry_run=dry_run)
    print(f"resources projects added: {n_res}")
    sb = fix_second_brain_charter(args.vault, dry_run=dry_run)
    print(f"second brain charter: {sb}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
