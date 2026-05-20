#!/usr/bin/env python3
"""Merge task fields from 02-Projekty/*.md into dashboard-tasks-source.json (preserve ICE/ch)."""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import os

VAULT = Path(os.environ.get("VAULT_PATH", Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC"))
TASKS_JSON = Path(
    os.environ.get("LEGACY_TASKS", VAULT / "00-System/dashboard-tasks-source.json")
)

ACC_MAP = {
    "strategy": "r",
    "firemni-procesy": "r",
    "rb-universe-development": "r",
    "finance": "te",
    "ma-odyssey": "am",
    "operations": "gr",
    "pipedrive-a-dalsi-nastroje": "gr",
    "obecna-inspirace": "gr",
    "exponential-summit": "am",
    "kratky-potlesk": "gr",
    "vibe-coding": "te",
    "rb-network": "gr",
    "sales-a-business-development": "r",
    "owners": "r",
    "osobni": "gr",
}

PRIORITY_RE = re.compile(r"\b(ASAP|Q1|Q2|Next|Backlog)\b", re.I)
WAITING_RE = re.compile(
    r"\*\*Waiting\s*\|\s*Čekat\s+do:\s*(\d{4}-\d{2}-\d{2})\s*\*\*",
    re.I,
)
WAITING_MARK_RE = re.compile(r"\*\*Waiting\b", re.I)
DATE_RE = re.compile(r"\*\*Vrátit se\*\*:\s*(\d{4}-\d{2}-\d{2})")
DEADLINE_RE = re.compile(r"Deadline\s+(\d{4}-\d{2}-\d{2})", re.I)
ICE_RE = re.compile(r"ICE\s+I(\d+)\s+C(\d+)\s+E(\d+)", re.I)
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
TASK_HEAD_RE = re.compile(
    r"^###\s+(~~)?([A-Z]+\d+[a-z]?)\s*[—–-]\s*(.+?)(?:~~)?\s*(✅|HOTOVO)?\s*$",
    re.MULTILINE,
)
HOTOVO_SECTION_RE = re.compile(r"^##\s+.*HOTOVO", re.MULTILINE | re.I)
HOTOVO_ITEM_RE = re.compile(
    r"^-\s+\*\*([A-Z]+\d+[a-z]?)\*\*\s*[—–-]\s*(.+)$",
    re.MULTILINE,
)
INLINE_TASK_RE = re.compile(
    r"^-\s+\[([ x])\]\s+\*\*([A-Z]+\d+[a-z]?)(?:\s+\[([^\]]+)\])?\*\*\s*(.+)$",
    re.MULTILINE,
)
CHECK_RE = re.compile(r"^-\s+\[([ x])\]\s+(.+)$", re.MULTILINE)
URL_RE = re.compile(r"https?://[^\s\)>\]]+")
SOURCE_RE = re.compile(r"^_Zdroj:\s*(.+)$", re.MULTILINE)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
SLUG_RE = re.compile(r"^\*\*Slug\*\*:\s*`([^`]+)`", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+Téma:\s*(.+)$", re.MULTILINE)


def _prague_today() -> date:
    return datetime.now(TZ).date()


def _default_wait_until() -> str:
    return (_prague_today() + timedelta(days=3)).isoformat()


def _waiting_from(block: str) -> tuple[str | None, str | None]:
    """Return (priority, waitUntil ISO) when task block is in Waiting state."""
    m = WAITING_RE.search(block)
    if m:
        return "Waiting", m.group(1)
    if WAITING_MARK_RE.search(block):
        return "Waiting", _default_wait_until()
    return None, None


PRIORITY_LINE_RE = re.compile(r"^\*\*([^*]+)\*\*\s*$", re.MULTILINE)


def _priority_from(text: str) -> str:
    waiting_p, _ = _waiting_from(text)
    if waiting_p:
        return waiting_p
    # Only look at the first **...** priority line — avoids matching Q1/Q2 in heading or body prose
    pl = PRIORITY_LINE_RE.search(text)
    search_in = pl.group(1) if pl else text
    m = PRIORITY_RE.search(search_in)
    if not m:
        return "Next"
    p = m.group(1)
    if p.upper() == "ASAP":
        return "ASAP"
    if p.upper() == "Q1":
        return "ASAP"
    if p.upper() == "Q2":
        return "Next"
    return p


def _deadline_from(block: str) -> str | None:
    m = DATE_RE.search(block)
    if m:
        return m.group(1)
    m = DEADLINE_RE.search(block)
    return m.group(1) if m else None


def _ice_from(block: str) -> dict | None:
    """Parse 'ICE I8 C7 E6' anywhere in the block. None if missing."""
    m = ICE_RE.search(block)
    if not m:
        return None
    return {"i": int(m.group(1)), "c": int(m.group(2)), "e": int(m.group(3))}


def _parse_hotovo_section(text: str) -> dict[str, str]:
    """Task ids marked done in ## … HOTOVO bullets (- **O1** — name ✅)."""
    m = HOTOVO_SECTION_RE.search(text)
    if not m:
        return {}
    section = text[m.start() :]
    next_h2 = re.search(r"^##\s+", section[1:], re.MULTILINE)
    if next_h2:
        section = section[: next_h2.start() + 1]
    out: dict[str, str] = {}
    for hm in HOTOVO_ITEM_RE.finditer(section):
        tid = hm.group(1)
        name = hm.group(2).strip()
        name = re.sub(r"\s*✅.*$", "", name).strip()
        name = re.sub(r"\s*_\([^)]*\)_\s*$", "", name).strip()
        out[tid] = name
    return out


def _is_source_only_line(line: str) -> bool:
    """↗ odkazy / čisté zdroje bez číslování subtasku."""
    s = line.strip()
    if s.startswith("↗"):
        return True
    if re.match(r"^https?://", s, re.I):
        return True
    bare = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    bare = URL_RE.sub("", bare).strip(" :—–-")
    if URL_RE.search(s) and len(bare) < 4:
        return True
    return False


def _parse_checklist(block: str) -> list[dict]:
    out = []
    num = 0
    for m in CHECK_RE.finditer(block):
        line = m.group(2).strip()
        if line.startswith("**") and "—" in line[:20]:
            continue
        entry: dict = {"t": line, "d": m.group(1).lower() == "x"}
        urls = URL_RE.findall(line)
        if urls:
            entry["url"] = urls[0]
        if _is_source_only_line(line):
            entry["source"] = True
        else:
            num += 1
            entry["n"] = num
        out.append(entry)
    return out


def _parse_source(block: str) -> dict:
    """First https URL from _Zdroj: line (markdown link or bare URL)."""
    m = SOURCE_RE.search(block)
    if not m:
        return {}
    line = m.group(1).strip()
    for label, url in MD_LINK_RE.findall(line):
        if url.startswith("http"):
            out: dict = {"sourceUrl": url}
            if label.strip():
                out["sourceLabel"] = label.strip()
            return out
    urls = URL_RE.findall(line)
    if urls:
        return {"sourceUrl": urls[0], "sourceLabel": "Zdroj"}
    return {}


def _parse_file(path: Path) -> tuple[str, str, list[dict], dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    hotovo = _parse_hotovo_section(text)
    slug_m = SLUG_RE.search(text)
    slug = slug_m.group(1) if slug_m else path.stem
    title_m = TITLE_RE.search(text)
    title = title_m.group(1).strip() if title_m else slug
    tasks: list[dict] = []

    for m in TASK_HEAD_RE.finditer(text):
        tid, name = m.group(2), m.group(3).strip()
        if m.group(1) or m.group(4):
            st = "dn"
        else:
            st = "wt"
        start = m.end()
        nxt = TASK_HEAD_RE.search(text, start)
        block = text[start : nxt.start() if nxt else len(text)]
        ch = _parse_checklist(block)
        head_and_block = m.group(0) + "\n" + block[:400]
        waiting_p, wait_until = _waiting_from(head_and_block)
        if waiting_p:
            st = "wt"
        elif ch and all(c["d"] for c in ch):
            st = "dn"
        task_row: dict = {
            "id": tid,
            "name": name,
            "p": waiting_p or _priority_from(head_and_block),
            "dl": _deadline_from(block),
            "st": st,
            "ch": ch,
        }
        if waiting_p:
            task_row["waitUntil"] = wait_until or _default_wait_until()
        ice = _ice_from(head_and_block)
        if ice:
            task_row["ice"] = ice
        task_row.update(_parse_source(block))
        tasks.append(task_row)

    for m in INLINE_TASK_RE.finditer(text):
        done = m.group(1).lower() == "x"
        tid, name = m.group(2), m.group(4).strip()
        p = _priority_from(m.group(3) or "")
        tasks.append(
            {
                "id": tid,
                "name": name,
                "p": p,
                "dl": None,
                "st": "dn" if done else "wt",
                "ch": [],
            }
        )

    return slug, title, tasks, hotovo


def _newest_projekty_mtime() -> float:
    proj = VAULT / "02-PROJEKTY"
    if not proj.is_dir():
        return 0.0
    return max((p.stat().st_mtime for p in proj.glob("*.md")), default=0.0)


def needs_sync() -> bool:
    if not TASKS_JSON.exists():
        return True
    return _newest_projekty_mtime() > TASKS_JSON.stat().st_mtime


def sync(force: bool = False) -> bool:
    if not force and not needs_sync():
        return False
    data = (
        json.loads(TASKS_JSON.read_text(encoding="utf-8"))
        if TASKS_JSON.exists()
        else {"version": 1, "proj_order": [], "projects": {}, "tasks": []}
    )
    by_id = {(t.get("proj"), t.get("id")): t for t in data.get("tasks", [])}
    proj_order: list[str] = list(data.get("proj_order", []))
    seen_keys: set[tuple[str, str]] = set()

    for md in sorted((VAULT / "02-PROJEKTY").glob("*.md")):
        if md.name.startswith("_") or md.name.startswith("._"):
            continue
        slug, title, parsed, hotovo = _parse_file(md)
        if slug not in proj_order:
            proj_order.append(slug)
        proj = data.setdefault("projects", {}).setdefault(
            slug,
            {
                "name": title,
                "acc": ACC_MAP.get(slug, "gr"),
                "watch": [],
                "materials": [],
                "done": [],
            },
        )
        proj["name"] = title
        for pt in parsed:
            key = (slug, pt["id"])
            seen_keys.add(key)
            existing = by_id.get(key)
            if existing:
                existing["name"] = pt["name"]
                existing["p"] = pt["p"]
                existing["st"] = pt["st"]
                if pt["p"] == "Waiting":
                    existing["waitUntil"] = pt.get("waitUntil") or _default_wait_until()
                else:
                    existing.pop("waitUntil", None)
                existing["dl"] = pt["dl"]  # md is SSOT (None if removed)
                if pt.get("ice"):
                    existing["ice"] = pt["ice"]
                existing["ch"] = pt["ch"]  # md is SSOT (empty list if removed)
                if pt.get("sourceUrl"):
                    existing["sourceUrl"] = pt["sourceUrl"]
                    if pt.get("sourceLabel"):
                        existing["sourceLabel"] = pt["sourceLabel"]
                else:
                    existing.pop("sourceUrl", None)
                    existing.pop("sourceLabel", None)
            else:
                new_t = {
                    "p": pt["p"],
                    "id": pt["id"],
                    "st": pt["st"],
                    "proj": slug,
                    "dl": pt["dl"],
                    "ice": pt.get("ice") or {"i": 5, "c": 5, "e": 5},
                    "name": pt["name"],
                    "ch": pt["ch"],
                }
                if pt["p"] == "Waiting":
                    new_t["waitUntil"] = pt.get("waitUntil") or _default_wait_until()
                data.setdefault("tasks", []).append(new_t)
                by_id[key] = new_t

        for tid, hname in hotovo.items():
            key = (slug, tid)
            seen_keys.add(key)
            existing = by_id.get(key)
            if existing:
                existing["st"] = "dn"
                if hname:
                    existing["name"] = hname
            else:
                new_t = {
                    "p": "Next",
                    "id": tid,
                    "st": "dn",
                    "proj": slug,
                    "dl": None,
                    "ice": {"i": 5, "c": 5, "e": 5},
                    "name": hname or tid,
                    "ch": [],
                }
                data.setdefault("tasks", []).append(new_t)
                by_id[key] = new_t

    # Prune orphans: tasks in JSON but no longer in any md (md is SSOT)
    before = len(data.get("tasks", []))
    data["tasks"] = [
        t for t in data.get("tasks", []) if (t["proj"], t["id"]) in seen_keys
    ]
    pruned = before - len(data["tasks"])
    if pruned:
        print(f"pruned {pruned} orphaned tasks (no longer in md)")

    data["proj_order"] = proj_order
    data["updated"] = str(date.today())
    TASKS_JSON.parent.mkdir(parents=True, exist_ok=True)
    TASKS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def main() -> None:
    if sync(force="--force" in __import__("sys").argv):
        print("synced", TASKS_JSON)
    else:
        print("skip (projekty not newer than json)")


if __name__ == "__main__":
    main()
