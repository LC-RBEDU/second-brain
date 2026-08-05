#!/usr/bin/env python3
"""Report — and optionally repair — tasks whose identity has come apart.

    python3 scripts/check_task_identity.py            # report, exit 1 if anything found
    python3 scripts/check_task_identity.py --fix      # rename files to match title, rewrite links

Checks the two ways a task can stop being one thing (see
`vps/second-brain-hub/lib/task_identity.py` for why each one hurts):

* **duplicate_id** — two tasks claiming one ID. Never auto-fixed: choosing
  which one keeps the ID is a judgement about what the links meant, and
  guessing wrong is what created the mess in the first place.
* **filename_drift** — filename no longer renders `title:`. Auto-fixable,
  because `title:` is the SSOT and the filename is derived from it.

Renaming a task file also has to rewrite every wikilink pointing at it, since
links carry the whole `<ID> — <Title>` stem. Doing that by hand in a throwaway
loop is how rotated ritual instances (`OPS2-2026-06-01.md`, six of them) once
got renamed onto the same filename and overwrote each other — hence the
rotation guard lives in the library and every caller goes through it.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pyyaml not installed. Run: pip3 install --user --break-system-packages pyyaml\n")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "OBSIDIAN"
sys.path.insert(0, str(ROOT / "vps" / "second-brain-hub" / "lib"))

from task_identity import (  # noqa: E402
    ROTATION_RE,
    check_task_identity,
    expected_stem,
)


@dataclass
class Task:
    id: str
    title: str
    rel_path: str


def load_tasks() -> list[Task]:
    tasks = []
    globs = [VAULT.glob("02-PROJEKTY/*/tasks/*.md"), VAULT.glob("07-ARCHIV/tasks-done/*/*.md")]
    for g in globs:
        for p in g:
            m = re.match(r"^---\s*\n(.*?\n)---", p.read_text(encoding="utf-8", errors="ignore"), re.S)
            if not m:
                continue
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                continue
            if fm.get("id"):
                tasks.append(Task(str(fm["id"]), str(fm.get("title") or ""), str(p.relative_to(VAULT))))
    return tasks


def repair_filename_drift(issues: list[dict]) -> int:
    """Rename drifted files to match their title and rewrite inbound links."""
    corpus = [p for p in VAULT.rglob("*.md") if ".git" not in str(p)]
    fixed = 0
    for issue in issues:
        if issue["kind"] != "filename_drift":
            continue
        path = VAULT / issue["paths"][0]
        if not path.exists():
            continue
        if ROTATION_RE.match(path.stem):
            continue  # ritual rotation — its name is the rotation date, not the title
        m = re.match(r"^---\s*\n(.*?\n)---", path.read_text(encoding="utf-8"), re.S)
        fm = yaml.safe_load(m.group(1)) or {}
        want = expected_stem(str(fm["id"]), str(fm.get("title") or ""))
        target = path.with_name(f"{want}.md")
        if target.exists() and target != path:
            print(f"  ! {issue['id']}: „{want}\" už existuje — přeskakuji, vyřeš ručně")
            continue

        old_stem = path.stem
        path.rename(target)
        links = 0
        for q in corpus:
            if not q.exists() or q == path:
                continue
            text = original = q.read_text(encoding="utf-8", errors="ignore")
            text = text.replace(f"[[{old_stem}", f"[[{want}")
            if text != original:
                q.write_text(text, encoding="utf-8")
                links += 1
        print(f"  ✓ {issue['id']}: → „{want}\" (odkazů přepsáno {links})")
        fixed += 1
    return fixed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fix", action="store_true", help="opravit filename_drift (duplicity nikdy automaticky)")
    args = ap.parse_args()

    issues = check_task_identity(load_tasks())
    dups = [i for i in issues if i["kind"] == "duplicate_id"]
    drift = [i for i in issues if i["kind"] == "filename_drift"]

    if dups:
        print(f"✗ duplicitní ID: {len(dups)} — vyřeš ručně (přečísluj tu variantu, na kterou vede míň odkazů)")
        for i in dups:
            print(f"  {i['id']}")
            for p in i["paths"]:
                print(f"    {p}")

    if drift:
        print(f"{'✗' if not args.fix else '→'} rozjetý název souboru vs. title: {len(drift)}")
        if args.fix:
            repair_filename_drift(drift)
        else:
            for i in drift:
                print(f"  {i['id']}: {i['detail']}")
            print("\n  spusť s --fix pro srovnání podle title")

    if not issues:
        print("✓ identita úkolů je v pořádku (žádné duplicitní ID, názvy souborů sedí s title)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
