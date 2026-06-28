#!/usr/bin/env python3
"""Legacy idempotent patch: ensure ## Zdroje dat exists; merge sources frontmatter.

Convention (2026-05): per-project `workspace:` and `sources: google-workspace` are
deprecated. SSOT for URLs = hub ## Zdroje dat table. GWS is global (bootstrap).

Usage:
  python3 scripts/patch_hub_sources.py
  python3 scripts/patch_hub_sources.py --dry-run
  python3 scripts/patch_hub_sources.py --strip-workspace   # remove workspace: blocks
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HUBS = REPO / "OBSIDIAN" / "02-PROJEKTY"

# slug -> optional sources tags (URLs live in ## Zdroje dat table only)
HUB_CONFIG: dict[str, dict] = {
    "finance": {
        "sources": ["rb-mcp", "notebooklm", "allfred", "wise", "revolut"],
    },
    "strategy": {
        "sources": ["notebooklm"],
    },
    "owners": {
        "sources": ["notebooklm"],
    },
    "ma-odyssey": {
        "sources": [],
    },
    "operations": {
        "sources": ["procesni-architekt"],
    },
    "sales-a-business-development": {
        "sources": ["notebooklm", "pipedrive"],
    },
    "exponential-summit": {
        "sources": ["allfred", "tito"],
    },
    "rb-universe-development": {
        "sources": ["rb-mcp", "procesni-architect", "github", "hostinger", "google-cloud", "coolify"],
    },
    "pipedrive-a-dalsi-nastroje": {
        "sources": ["rb-mcp", "pipedrive", "make"],
    },
    "vibe-coding": {
        "sources": ["github"],
    },
    "osobni": {
        "sources": ["github"],
    },
    "kratky-potlesk": {
        "sources": ["github", "google-cloud", "wedos"],
    },
    "rb-network": {
        "sources": [],
    },
}

ZDROJE_HEADER = "## Zdroje dat"
WORKSPACE_BLOCK_RE = re.compile(
    r"^workspace:\n(?:  .*\n)*",
    re.MULTILINE,
)
GWS_TABLE_ROW_RE = re.compile(
    r"^\| Google Workspace \|.*\|\s*\n"
    r"|^\| Google Drive \| `workspace:.*\|\s*\n",
    re.MULTILINE,
)


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


def _strip_workspace_from_fm_raw(fm_raw: str) -> str:
    out = WORKSPACE_BLOCK_RE.sub("", fm_raw)
    lines = out.splitlines()
    cleaned: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("sources:"):
            cleaned.append(line)
            i += 1
            while i < len(lines) and lines[i].startswith("- "):
                tag = lines[i][2:].strip()
                if tag != "google-workspace":
                    cleaned.append(lines[i])
                i += 1
            continue
        cleaned.append(line)
        i += 1
    return "\n".join(cleaned).strip()


def _render_frontmatter_block(fm_raw: str, cfg: dict) -> str:
    sources = [s for s in (cfg.get("sources") or []) if s != "google-workspace"]
    fm_raw = _strip_workspace_from_fm_raw(fm_raw)

    lines = fm_raw.splitlines()
    out: list[str] = []
    replaced_sources = False
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
        out.append(line)
        i += 1

    if not replaced_sources and sources:
        insert_at = len(out)
        for j, ln in enumerate(out):
            if ln.startswith("updated:"):
                insert_at = j + 1
        out[insert_at:insert_at] = ["sources:", *[f"- {s}" for s in sources]]

    return "\n".join(out)


def _strip_zdroje_gws_rows(body: str) -> str:
    return GWS_TABLE_ROW_RE.sub("", body)


def patch_hub(path: Path, cfg: dict | None, dry_run: bool, strip_workspace: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    fm, body, fm_raw = _parse_frontmatter(text)
    slug = fm.get("slug", "").strip()
    if not slug:
        return False

    new_fm_raw = fm_raw
    if cfg:
        new_fm_raw = _render_frontmatter_block(fm_raw, cfg)
    elif strip_workspace:
        new_fm_raw = _strip_workspace_from_fm_raw(fm_raw)

    new_body = _strip_zdroje_gws_rows(body) if strip_workspace else body

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
    ap.add_argument(
        "--strip-workspace",
        action="store_true",
        help="Remove workspace: + google-workspace from all project hubs",
    )
    args = ap.parse_args()
    if not HUBS.is_dir():
        print(f"ERROR: {HUBS} missing", file=sys.stderr)
        return 1
    n = 0
    for hub_path in sorted(HUBS.glob("*.md")):
        text = hub_path.read_text(encoding="utf-8")
        if not text.startswith("---") or "type: project" not in text.split("---", 2)[1]:
            continue
        m = re.search(r"^slug:\s*(\S+)", text, re.M)
        slug = m.group(1) if m else ""
        cfg = HUB_CONFIG.get(slug) if slug in HUB_CONFIG else None
        if not cfg and not args.strip_workspace:
            continue
        if patch_hub(hub_path, cfg, args.dry_run, strip_workspace=args.strip_workspace or bool(cfg)):
            n += 1
    print(f"patch_hub_sources: {n} hub(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
