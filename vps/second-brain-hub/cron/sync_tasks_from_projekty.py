#!/usr/bin/env python3
"""Merge task fields from 02-PROJEKTY/*.md into dashboard-tasks-source.json
(preserve ICE, čekání, sources). Phase 2 migrace — vault I/O přes
DriveVault místo lokální VAULT_PATH.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, DriveNotFoundError, credentials_from_env  # noqa: E402

TASKS_REL = "00-System/dashboard-tasks-source.json"
PROJEKTY_REL = "02-PROJEKTY"

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
    "allfred": "te",
}

PRIORITY_RE = re.compile(r"\b(ASAP|Q1|Q2|Next|Backlog)\b", re.I)
WAITING_RE = re.compile(
    r"\*\*Waiting\s*\|\s*Čekat\s+do:\s*(\d{4}-\d{2}-\d{2})(?:[^*]*)?\*\*",
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
HOTOVO_HEAD_RE = re.compile(
    r"^###\s+([A-Z]+\d+[a-z]?)\s*[—–-]\s*(.+?)\s*✅\s*$",
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
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
HOTOVO_DATE_RE = re.compile(r"_\((\d{4}-\d{2}-\d{2})\)_")


_VAULT_SINGLETON: DriveVault | None = None


def get_vault() -> DriveVault:
    global _VAULT_SINGLETON
    if _VAULT_SINGLETON is None:
        root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
        if not root_id:
            raise RuntimeError(
                "VAULT_DRIVE_ID env not set — Drive vault folder ID is required."
            )
        creds, _mode = credentials_from_env()
        _VAULT_SINGLETON = DriveVault(root_id, credentials=creds)
    return _VAULT_SINGLETON


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
TOP_PIN_RE = re.compile(r"📌\s*TOP|TOP\s*pin", re.I)


def _pin_top_from(text: str) -> bool:
    pl = PRIORITY_LINE_RE.search(text)
    search_in = pl.group(1) if pl else text
    return bool(TOP_PIN_RE.search(search_in))


def _priority_from(text: str) -> str:
    waiting_p, _ = _waiting_from(text)
    if waiting_p:
        return waiting_p
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
    m = ICE_RE.search(block)
    if not m:
        return None
    return {"i": int(m.group(1)), "c": int(m.group(2)), "e": int(m.group(3))}


def _parse_hotovo_section(text: str) -> dict[str, str]:
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
    for hm in HOTOVO_HEAD_RE.finditer(section):
        tid = hm.group(1)
        name = hm.group(2).strip()
        if tid not in out:
            out[tid] = name
    return out


def _hotovo_dates_this_week(text: str) -> int:
    m = HOTOVO_SECTION_RE.search(text)
    if not m:
        return 0
    section = text[m.start() :]
    next_h2 = re.search(r"^##\s+", section[1:], re.MULTILINE)
    if next_h2:
        section = section[: next_h2.start() + 1]
    cutoff = _prague_today() - timedelta(days=7)
    n = 0
    for hm in HOTOVO_ITEM_RE.finditer(section):
        block = hm.group(0)
        dm = HOTOVO_DATE_RE.search(block)
        if dm:
            try:
                if date.fromisoformat(dm.group(1)) >= cutoff:
                    n += 1
            except ValueError:
                pass
    return n


def _section_content(text: str, *names: str) -> str:
    names_l = {n.lower() for n in names}
    parts = list(H2_RE.finditer(text))
    for i, m in enumerate(parts):
        if m.group(1).strip().lower() in names_l:
            start = m.end()
            end = parts[i + 1].start() if i + 1 < len(parts) else len(text)
            return text[start:end].strip()
    return ""


def _context_snippet(kontext: str, limit: int = 400) -> str:
    chunks: list[str] = []
    for line in kontext.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith(">"):
            s = s.lstrip("> ").strip()
        chunks.append(s)
    joined = " ".join(chunks)
    if len(joined) <= limit:
        return joined.strip()
    return joined[: limit - 1].rstrip() + "…"


def _parse_bullets(section: str, max_items: int = 12) -> list[str]:
    out: list[str] = []
    for line in section.splitlines():
        s = line.strip()
        if s.startswith("- ") and not re.match(r"^-\s+\[[ x]\]", s):
            out.append(s[2:].strip())
        if len(out) >= max_items:
            break
    return out


def _parse_materials_section(section: str) -> list[dict]:
    out: list[dict] = []
    for line in section.splitlines():
        s = line.strip()
        if not s.startswith("-"):
            continue
        linked = False
        for label, url in MD_LINK_RE.findall(s):
            if url.startswith("http"):
                out.append({"label": (label or url).strip(), "url": url})
                linked = True
        if not linked:
            um = URL_RE.search(s)
            if um:
                out.append({"label": s[:80], "url": um.group(0)})
        if len(out) >= 20:
            break
    return out


def _parse_project_hub(text: str, slug: str) -> dict:
    kontext = _section_content(text, "Kontext")
    return {
        "contextSnippet": _context_snippet(kontext) if kontext else "",
        "openQuestions": _parse_bullets(
            _section_content(text, "Otevřené otázky", "Otevřené otázky / čeká na data")
        ),
        "materials": _parse_materials_section(
            _section_content(text, "Materiály", "Materiály a poznámky")
        ),
        "progress": _parse_bullets(_section_content(text, "Progress")),
        "outputFolder": f"02-PROJEKTY/{slug}/",
    }


def _is_source_only_line(line: str) -> bool:
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


def _parse_text(name: str, text: str) -> tuple[str, str, list[dict], dict[str, str]]:
    """Parse a hub markdown body. Returns (slug, title, tasks, hotovo_map)."""
    hotovo = _parse_hotovo_section(text)
    slug_m = SLUG_RE.search(text)
    stem = os.path.splitext(name)[0]
    slug = slug_m.group(1) if slug_m else stem
    title_m = TITLE_RE.search(text)
    title = title_m.group(1).strip() if title_m else slug
    tasks: list[dict] = []

    for m in TASK_HEAD_RE.finditer(text):
        tid, tname = m.group(2), m.group(3).strip()
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
            "name": tname,
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
        if _pin_top_from(head_and_block):
            task_row["pinTop"] = True
        task_row.update(_parse_source(block))
        tasks.append(task_row)

    for m in INLINE_TASK_RE.finditer(text):
        done = m.group(1).lower() == "x"
        tid, tname = m.group(2), m.group(4).strip()
        p = _priority_from(m.group(3) or "")
        tasks.append(
            {
                "id": tid,
                "name": tname,
                "p": p,
                "dl": None,
                "st": "dn" if done else "wt",
                "ch": [],
            }
        )

    return slug, title, tasks, hotovo


def _list_hubs(vault: DriveVault) -> list:
    """Return list of FileMeta for 02-PROJEKTY/*.md (excluding underscore files)."""
    out = []
    for meta in vault.list_dir(PROJEKTY_REL, pattern="*.md"):
        if meta.name.startswith("_") or meta.name.startswith("._"):
            continue
        out.append(meta)
    return sorted(out, key=lambda m: m.name)


def _newest_projekty_mtime(vault: DriveVault) -> datetime:
    hubs = _list_hubs(vault)
    if not hubs:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    return max(m.modified_time for m in hubs)


def needs_sync(vault: DriveVault | None = None) -> bool:
    vault = vault or get_vault()
    try:
        meta = vault.stat(TASKS_REL)
    except DriveNotFoundError:
        return True
    return _newest_projekty_mtime(vault) > meta.modified_time


def sync(force: bool = False) -> bool:
    vault = get_vault()
    if not force and not needs_sync(vault):
        return False
    try:
        data, _ = vault.read_json(TASKS_REL)
        if not isinstance(data, dict):
            data = {"version": 1, "proj_order": [], "projects": {}, "tasks": []}
    except DriveNotFoundError:
        data = {"version": 1, "proj_order": [], "projects": {}, "tasks": []}

    by_id = {(t.get("proj"), t.get("id")): t for t in data.get("tasks", [])}
    proj_order: list[str] = list(data.get("proj_order", []))
    seen_keys: set[tuple[str, str]] = set()

    for meta in _list_hubs(vault):
        text, _ = vault.read_text(meta.rel_path)
        slug, title, parsed, hotovo = _parse_text(meta.name, text)
        if slug not in proj_order:
            proj_order.append(slug)
        proj = data.setdefault("projects", {}).setdefault(
            slug,
            {
                "name": title,
                "acc": ACC_MAP.get(slug, "gr"),
            },
        )
        proj["name"] = title
        hub_meta = _parse_project_hub(text, slug)
        proj.update(hub_meta)
        proj["hubFile"] = f"02-PROJEKTY/{meta.name}"
        proj.pop("watch", None)
        proj.pop("done", None)
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
                existing["dl"] = pt["dl"]
                if pt.get("ice"):
                    existing["ice"] = pt["ice"]
                existing["ch"] = pt["ch"]
                if pt.get("sourceUrl"):
                    existing["sourceUrl"] = pt["sourceUrl"]
                    if pt.get("sourceLabel"):
                        existing["sourceLabel"] = pt["sourceLabel"]
                else:
                    existing.pop("sourceUrl", None)
                    existing.pop("sourceLabel", None)
                if pt.get("pinTop"):
                    existing["pinTop"] = True
                else:
                    existing.pop("pinTop", None)
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
                if pt.get("pinTop"):
                    new_t["pinTop"] = True
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

        slug_tasks = [t for t in data.get("tasks", []) if t.get("proj") == slug]
        open_tasks = [t for t in slug_tasks if t.get("st") != "dn"]
        proj["stats"] = {
            "open": len(open_tasks),
            "waiting": sum(1 for t in open_tasks if t.get("p") == "Waiting"),
            "asap": sum(1 for t in open_tasks if t.get("p") == "ASAP"),
            "doneWeek": _hotovo_dates_this_week(text),
        }

    before = len(data.get("tasks", []))
    data["tasks"] = [
        t for t in data.get("tasks", []) if (t["proj"], t["id"]) in seen_keys
    ]
    pruned = before - len(data["tasks"])
    if pruned:
        print(f"pruned {pruned} orphaned tasks (no longer in md)")

    data["proj_order"] = proj_order
    data["updated"] = str(date.today())
    vault.write_json(TASKS_REL, data)
    return True


def main() -> None:
    if sync(force="--force" in sys.argv):
        print("synced drive://", TASKS_REL)
    else:
        print("skip (projekty not newer than json)")


if __name__ == "__main__":
    main()
