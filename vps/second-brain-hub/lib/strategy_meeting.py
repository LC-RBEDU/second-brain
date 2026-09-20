"""Strategy meeting context for agent-context.json — Sembly + hub prep, not task queue."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PILLAR_TABLE_RE = re.compile(
    r"\*\*Aktuální pilíře H2.*?\*\*\s*\n\n\| Pilíř \| Obsah \|\n\|[-| ]+\|\n((?:\|.*\|\n)+)",
    re.MULTILINE,
)
OPEN_DECISIONS_RE = re.compile(
    r"\*\*Otevřená strategická rozhodnutí:\*\*\s*(.+?)(?:\n\n|\n---|\Z)",
    re.DOTALL,
)
STRATEGY_MEETING_GLOB = "*Strategická schůzka*"


def _parse_pillars(hub_body: str) -> list[dict[str, str]]:
    m = PILLAR_TABLE_RE.search(hub_body)
    if not m:
        return []
    out: list[dict[str, str]] = []
    for line in m.group(1).strip().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        name = cells[0].strip("*").strip()
        if not name or name.lower() == "pilíř":
            continue
        out.append({"name": name, "summary": cells[1].strip()})
    return out


def _parse_open_decisions(hub_body: str) -> list[str]:
    m = OPEN_DECISIONS_RE.search(hub_body)
    if not m:
        return []
    text = m.group(1).strip()
    parts = re.split(r",(?=\s*[a-záčďéěíňóřšťúůýž])", text)
    return [p.strip().rstrip(".") for p in parts if p.strip()]


def build_strategy_meeting_block(
    hub_body: str,
    *,
    latest_material_fm: dict[str, Any] | None = None,
    latest_material_rel: str | None = None,
) -> dict[str, Any]:
    pillars = _parse_pillars(hub_body)
    open_decisions = _parse_open_decisions(hub_body)

    latest: dict[str, Any] | None = None
    themes: list[str] = []
    if latest_material_fm and latest_material_rel:
        topics = latest_material_fm.get("topics") or []
        if isinstance(topics, str):
            topics = [topics]
        themes = [str(t) for t in topics]
        latest = {
            "path": latest_material_rel,
            "title": latest_material_fm.get("title") or "",
            "date": str(latest_material_fm.get("created") or latest_material_fm.get("updated") or "")[:10],
            "topics": themes,
        }

    theme_set: list[str] = []
    for item in themes + [p["name"] for p in pillars]:
        if item and item not in theme_set:
            theme_set.append(item)

    return {
        "prep_material": "02-PROJEKTY/strategy/materials/strategy-meeting-vibe.md",
        "latest_meeting": latest,
        "pillars": pillars,
        "open_decisions": open_decisions,
        "themes": theme_set,
    }


def _find_latest_strategy_meeting_material(
    materials_dir: Path,
    *,
    read_frontmatter,
) -> tuple[dict[str, Any] | None, str | None]:
    if not materials_dir.is_dir():
        return None, None
    candidates: list[tuple[str, Path]] = []
    for f in materials_dir.glob(STRATEGY_MEETING_GLOB):
        if f.name.startswith("_"):
            continue
        candidates.append((f.name, f))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[0], reverse=True)
    path = candidates[0][1]
    try:
        fm, _ = read_frontmatter(path.read_text(encoding="utf-8"))
    except OSError:
        return None, None
    rel = f"02-PROJEKTY/strategy/materials/{path.name}"
    return fm, rel


def collect_strategy_meeting_from_path(vault: Path, *, parse_frontmatter) -> dict[str, Any]:
    hub_path = vault / "02-PROJEKTY" / "Strategy.md"
    materials_dir = vault / "02-PROJEKTY" / "strategy" / "materials"
    hub_body = ""
    if hub_path.is_file():
        try:
            _, hub_body = parse_frontmatter(hub_path.read_text(encoding="utf-8"))
        except OSError:
            pass
    fm, rel = _find_latest_strategy_meeting_material(
        materials_dir, read_frontmatter=parse_frontmatter
    )
    return build_strategy_meeting_block(hub_body, latest_material_fm=fm, latest_material_rel=rel)


def collect_strategy_meeting_from_drive(vault, *, parse_frontmatter) -> dict[str, Any]:
    """DriveVault adapter — same shape as collect_strategy_meeting_from_path."""
    hub_body = ""
    try:
        text, _ = vault.read_text("02-PROJEKTY/Strategy.md")
        _, hub_body = parse_frontmatter(text)
    except Exception:
        pass

    latest_fm: dict[str, Any] | None = None
    latest_rel: str | None = None
    try:
        names = vault.list_dir("02-PROJEKTY/strategy/materials", pattern="*.md")
    except Exception:
        names = []
    # list_dir returns FileMeta, not names. "x" in a FileMeta raises TypeError.
    candidates = sorted(
        (
            meta.name
            for meta in names
            if "Strategická schůzka" in meta.name and not meta.name.startswith("_")
        ),
        reverse=True,
    )
    if candidates:
        rel = f"02-PROJEKTY/strategy/materials/{candidates[0]}"
        try:
            text, _ = vault.read_text(rel)
            latest_fm, _ = parse_frontmatter(text)
            latest_rel = rel
        except Exception:
            pass

    return build_strategy_meeting_block(
        hub_body, latest_material_fm=latest_fm, latest_material_rel=latest_rel
    )
