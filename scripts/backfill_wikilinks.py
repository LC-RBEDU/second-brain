#!/usr/bin/env python3
"""One-off wikilink backfill for OBSIDIAN vault."""
from __future__ import annotations

import os

import re
from pathlib import Path

VAULT = Path(os.environ.get("SECOND_BRAIN_VAULT") or os.environ.get("SB_VAULT_PATH") or (Path.home() / "GitHub" / "second-brain-vault"))
HUB_DIR = VAULT / "02-PROJEKTY"

SKIP_PARTS = {".obsidian", "__pycache__"}

# hub stem -> display path for wikilink (02-PROJEKTY/Finance)
HUB_LINK: dict[str, str] = {}
# slug folder -> hub stem
SLUG_TO_HUB: dict[str, str] = {}
# task id -> (hub_stem, heading without ###)
TASK_LINK: dict[str, tuple[str, str]] = {}

TASK_HEADING_RE = re.compile(
    r"^###\s+((?:F|RBU|PD|AF|S|MO|P|OI)\d+)\s+—\s+(.+?)\s*$",
    re.MULTILINE,
)
SLUG_RE = re.compile(r"^\*\*Slug\*\*:\s*`([^`]+)`", re.MULTILINE)

# Already wikilinked path
WL_RE = re.compile(r"\[\[[^\]]+\]\]")


def load_hubs() -> None:
    for md in HUB_DIR.glob("*.md"):
        if md.name.startswith("_") or md.name == "DEPRECATED.md":
            continue
        stem = md.stem
        text = md.read_text(encoding="utf-8")
        HUB_LINK[stem] = f"02-PROJEKTY/{stem}"
        m = SLUG_RE.search(text)
        if m:
            SLUG_TO_HUB[m.group(1)] = stem
        for tm in TASK_HEADING_RE.finditer(text):
            tid, title = tm.group(1), tm.group(2).strip()
            TASK_LINK[tid] = (stem, f"{tid} — {title}")


def protect_wikilinks(text: str) -> tuple[str, list[str]]:
    store: list[str] = []

    def repl(m: re.Match[str]) -> str:
        store.append(m.group(0))
        return f"\x00WL{len(store) - 1}\x00"

    return WL_RE.sub(repl, text), store


def restore_wikilinks(text: str, store: list[str]) -> str:
    for i, w in enumerate(store):
        text = text.replace(f"\x00WL{i}\x00", w)
    return text


def link_path(path: str, alias: str | None = None) -> str:
    p = path.replace(".md", "").rstrip("/")
    if alias and alias != p.split("/")[-1]:
        return f"[[{p}|{alias}]]"
    return f"[[{p}]]"


def normalize_legacy(text: str) -> str:
    text = text.replace("02-Projekty/", "02-PROJEKTY/")
    text = text.replace("02-projekty/", "02-PROJEKTY/")
    text = text.replace("07-Archiv/", "07-ARCHIV/")
    text = text.replace("04-Vystupy/", "02-PROJEKTY/")
    return text


def replace_hub_md_paths(text: str) -> str:
    for stem in sorted(HUB_LINK, key=len, reverse=True):
        # 02-PROJEKTY/Finance.md or with backticks
        for pat in (
            rf"`02-PROJEKTY/{re.escape(stem)}\.md`",
            rf"02-PROJEKTY/{re.escape(stem)}\.md",
            rf"`02-PROJEKTY/{re.escape(stem)}`",
        ):
            text = re.sub(pat, link_path(HUB_LINK[stem]), text)
    return text


def replace_slug_paths(text: str) -> str:
    for slug, stem in sorted(SLUG_TO_HUB.items(), key=lambda x: len(x[0]), reverse=True):
        # path like 02-PROJEKTY/finance/foo.md
        pattern = rf"(`?)(02-PROJEKTY/{re.escape(slug)}/[^\s`\)\]]+\.md)\1?"

        def repl(m: re.Match[str]) -> str:
            raw = m.group(2).replace(".md", "")
            return link_path(raw)

        text = re.sub(pattern, repl, text)
        # folder-only references in backticks
        text = re.sub(
            rf"`02-PROJEKTY/{re.escape(slug)}/`",
            link_path(f"02-PROJEKTY/{slug}/"),
            text,
        )
    return text


def replace_bare_hubs(text: str) -> str:
    for stem in sorted(HUB_LINK, key=len, reverse=True):
        # vůči Finance, téma Finance — only if not already inside link
        pat = rf"(?<!\[)(?<!\w)02-PROJEKTY/{re.escape(stem)}(?!\w)(?![\]\|])"
        text = re.sub(pat, link_path(HUB_LINK[stem]), text)
    return text


def replace_task_ids(text: str) -> str:
    """Link task IDs only outside ### headings (variant B). Longest IDs first."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        if line.lstrip().startswith("### "):
            out.append(line)
            continue
        chunk = line
        for tid, (stem, heading) in sorted(TASK_LINK.items(), key=lambda x: len(x[0]), reverse=True):
            hub = HUB_LINK[stem]
            target = f"[[{hub}#{heading}]]"
            pat = rf"(?<![#\w\[]){re.escape(tid)}(?!\s*—)(?![^\[]*\]\])"
            chunk = re.sub(pat, target, chunk)
        out.append(chunk)
    return "".join(out)


def replace_index_memory_paths(text: str) -> str:
    text = re.sub(
        r"`00-System/Index\.md`",
        "[[00-System/Index]]",
        text,
    )
    text = re.sub(
        r"00-System/Index\.md",
        "[[00-System/Index]]",
        text,
    )
    for name in (
        "agenda-system",
        "about-me",
        "jak-ctu-mrluc",
        "vault-gdrive-migration",
        "anti-ai-writing-tools",
    ):
        text = re.sub(
            rf"`00-System/Memory/{name}\.md`",
            f"[[00-System/Memory/{name}]]",
            text,
        )
        text = re.sub(
            rf"00-System/Memory/{name}\.md",
            f"[[00-System/Memory/{name}]]",
            text,
        )
    return text


def process_file(path: Path) -> bool:
    raw = path.read_text(encoding="utf-8")
    text, wl_store = protect_wikilinks(raw)
    text = normalize_legacy(text)
    text = replace_hub_md_paths(text)
    text = replace_slug_paths(text)
    text = replace_bare_hubs(text)
    text = replace_index_memory_paths(text)
    text = replace_task_ids(text)
    text = restore_wikilinks(text, wl_store)
    if text != raw:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    load_hubs()
    print(f"Hubs: {len(HUB_LINK)}, tasks: {len(TASK_LINK)}, slugs: {len(SLUG_TO_HUB)}")
    changed: list[str] = []
    for md in sorted(VAULT.rglob("*.md")):
        if any(p in SKIP_PARTS for p in md.parts):
            continue
        if process_file(md):
            changed.append(str(md.relative_to(VAULT)))
    print(f"Updated {len(changed)} files")
    for c in changed[:40]:
        print(f"  {c}")
    if len(changed) > 40:
        print(f"  ... +{len(changed) - 40} more")


if __name__ == "__main__":
    main()
