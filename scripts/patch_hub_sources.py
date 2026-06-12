#!/usr/bin/env python3
"""One-shot / idempotent patch: sources frontmatter + ## Zdroje dat for project hubs.

Usage:
  python3 scripts/patch_hub_sources.py
  python3 scripts/patch_hub_sources.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HUBS = REPO / "OBSIDIAN" / "02-PROJEKTY"

# slug -> config (skip allfred + firemni-procesy — already patched manually)
HUB_CONFIG: dict[str, dict] = {
    "finance": {
        "sources": ["rb-mcp", "google-workspace"],
        "workspace": {"calendar": [], "gmail": ["label:finance"], "drive": []},
        "zdroje_rows": [
            ("RB Universe MCP", "`sources: rb-mcp`", "Fakturoid/FIO sync, interní finance data"),
            ("Google Workspace", "`workspace:` frontmatter", "Mail finance, Drive podklady"),
        ],
    },
    "strategy": {
        "sources": ["google-workspace"],
        "workspace": {"calendar": [], "gmail": [], "drive": []},
        "zdroje_rows": [
            ("Google Workspace", "`workspace:` frontmatter", "Strategické materiály, kalendář"),
        ],
    },
    "owners": {
        "sources": ["google-workspace"],
        "workspace": {
            "calendar": ["Owners meetingy"],
            "gmail": ["label:owners"],
            "drive": [],
        },
        "zdroje_rows": [
            ("Google Workspace", "`workspace:` frontmatter", "Owners meetingy, mail threads"),
        ],
    },
    "ma-odyssey": {
        "sources": ["google-workspace"],
        "workspace": {"calendar": [], "gmail": ["label:odyssey"], "drive": []},
        "zdroje_rows": [
            ("Google Workspace", "`workspace:` frontmatter", "Odyssey mail/kalendář"),
        ],
    },
    "operations": {
        "sources": ["google-workspace", "procesni-architekt"],
        "workspace": {"calendar": [], "gmail": [], "drive": []},
        "zdroje_rows": [
            ("Google Workspace", "`workspace:` frontmatter", "Provozní schůzky, mail"),
            ("Procesní architekt", "`sources: procesni-architekt`", "Existující firemní procesy (MCP)"),
        ],
    },
    "sales-a-business-development": {
        "sources": ["rb-mcp", "google-workspace", "procesni-architekt"],
        "workspace": {"calendar": [], "gmail": ["label:sales"], "drive": []},
        "zdroje_rows": [
            ("RB Universe MCP", "`sources: rb-mcp`", "CRM data, sales org"),
            ("Google Workspace", "`workspace:` frontmatter", "Obchodní mail, schůzky"),
            ("Procesní architekt", "`sources: procesni-architekt`", "Sales/delivery procesy"),
        ],
    },
    "exponential-summit": {
        "sources": ["google-workspace"],
        "workspace": {"calendar": [], "gmail": [], "drive": []},
        "zdroje_rows": [
            ("Google Workspace", "`workspace:` frontmatter", "Summit materiály, koordinace"),
        ],
    },
    "rb-universe-development": {
        "sources": ["rb-mcp", "procesni-architekt"],
        "zdroje_rows": [
            ("RB Universe MCP", "`sources: rb-mcp`", "Dev API, interní moduly"),
            ("Procesní architekt", "`sources: procesni-architekt`", "Import/export procesů"),
        ],
    },
    "pipedrive-a-dalsi-nastroje": {
        "sources": ["rb-mcp"],
        "zdroje_rows": [
            ("RB Universe MCP", "`sources: rb-mcp`", "Pipedrive sync, integrace"),
        ],
    },
    "vibe-coding": {
        "sources": ["google-workspace"],
        "workspace": {"calendar": [], "gmail": [], "drive": []},
        "zdroje_rows": [
            ("Google Workspace", "`workspace:` frontmatter", "Experimenty, odkazy"),
        ],
    },
    "osobni": {
        "sources": [],
        "zdroje_rows": [],
    },
    "kratky-potlesk": {
        "sources": [],
        "zdroje_rows": [],
    },
    "rb-network": {
        "sources": ["google-workspace"],
        "workspace": {"calendar": [], "gmail": ["from:@redbutton.cz"], "drive": []},
        "zdroje_rows": [
            ("Google Workspace", "`workspace:` frontmatter", "Network mail, koordinace"),
        ],
    },
}

ZDROJE_HEADER = "## Zdroje dat"


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str, str]:
    if not text.startswith("---"):
        return {}, text, ""
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text, ""
    fm_raw = text[3:end].strip()
    rest = text[end + 4 :].lstrip("\n")
    fm: dict[str, str] = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, rest, fm_raw


def _build_zdroje_section(rows: list[tuple[str, str, str]]) -> str:
    if not rows:
        return (
            f"{ZDROJE_HEADER}\n\n"
            "_Zatím bez externích zdrojů — doplň `sources:` ve frontmatteru podle potřeby._\n"
        )
    lines = [
        ZDROJE_HEADER,
        "",
        "| Zdroj | Pointer | K čemu |",
        "|-------|---------|--------|",
    ]
    for z, p, k in rows:
        lines.append(f"| {z} | {p} | {k} |")
    lines.append("")
    return "\n".join(lines)


def _render_frontmatter_block(fm_raw: str, slug: str, cfg: dict) -> str:
    """Insert or replace sources/workspace in frontmatter YAML block."""
    sources = cfg.get("sources") or []
    workspace = cfg.get("workspace")

    lines = fm_raw.splitlines()
    out: list[str] = []
    skip_until_next_key = False
    replaced_sources = False
    replaced_workspace = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("sources:"):
            out.append("sources:")
            if sources:
                for s in sources:
                    out.append(f"- {s}")
            else:
                out.append("[]")
            replaced_sources = True
            i += 1
            while i < len(lines) and lines[i].startswith("- "):
                i += 1
            continue
        if line.startswith("workspace:"):
            out.append("workspace:")
            if workspace:
                for key, vals in workspace.items():
                    if vals:
                        out.append(f"  {key}:")
                        for v in vals:
                            out.append(f'  - "{v}"')
                    else:
                        out.append(f"  {key}: []")
            else:
                out.append("  calendar: []")
                out.append("  gmail: []")
                out.append("  drive: []")
            replaced_workspace = True
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or lines[i].strip() == ""):
                i += 1
            continue
        out.append(line)
        i += 1

    if not replaced_sources:
        # insert before closing --- (after updated: or open_tasks_count)
        insert_at = len(out)
        for j, ln in enumerate(out):
            if ln.startswith("updated:"):
                insert_at = j + 1
        src_lines = ["sources:"]
        if sources:
            src_lines.extend(f"- {s}" for s in sources)
        else:
            src_lines.append("[]")
        out[insert_at:insert_at] = src_lines

    if workspace is not None and not replaced_workspace:
        insert_at = len(out)
        for j, ln in enumerate(out):
            if ln.startswith("sources:"):
                insert_at = j + 1
                while insert_at < len(out) and out[insert_at].startswith("- "):
                    insert_at += 1
        ws_lines = ["workspace:"]
        for key, vals in (workspace or {}).items():
            if vals:
                ws_lines.append(f"  {key}:")
                for v in vals:
                    ws_lines.append(f'  - "{v}"')
            else:
                ws_lines.append(f"  {key}: []")
        out[insert_at:insert_at] = ws_lines

    return "\n".join(out)


def patch_hub(path: Path, cfg: dict, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    fm, body, fm_raw = _parse_frontmatter(text)
    slug = fm.get("slug", "").strip()
    if not slug:
        return False

    if ZDROJE_HEADER in body:
        has_zdroje = True
    else:
        has_zdroje = False

    new_fm_raw = _render_frontmatter_block(fm_raw, slug, cfg)
    zdroje = _build_zdroje_section(cfg.get("zdroje_rows") or [])

    if has_zdroje:
        new_body = body
    else:
        # insert before ## Otevřené otázky or ## Materiály or end
        for anchor in ("## Otevřené otázky", "## Materiály", "## Výstupy", "## Recently done"):
            if anchor in body:
                new_body = body.replace(anchor, zdroje + "\n" + anchor, 1)
                break
        else:
            new_body = body.rstrip() + "\n\n" + zdroje

    new_text = f"---\n{new_fm_raw}\n---\n{new_body}"
    if new_text == text:
        return False
    if dry_run:
        print(f"would patch: {path.name}")
        return True
    path.write_text(new_text, encoding="utf-8")
    print(f"patched: {path.name}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not HUBS.is_dir():
        print(f"ERROR: {HUBS} missing", file=sys.stderr)
        return 1
    n = 0
    for hub_path in sorted(HUBS.glob("*.md")):
        text = hub_path.read_text(encoding="utf-8")
        m = re.search(r"^slug:\s*(\S+)", text, re.M)
        if not m:
            continue
        slug = m.group(1)
        if slug not in HUB_CONFIG:
            continue
        if patch_hub(hub_path, HUB_CONFIG[slug], args.dry_run):
            n += 1
    print(f"patch_hub_sources: {n} hub(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
