#!/usr/bin/env python3
"""Build dashboard-data.json from vault 02-PROJEKTY + optional legacy _tasks.json."""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

VAULT = Path(os.environ.get("VAULT_PATH", Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC"))
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
_WEB_DIR = Path(__file__).resolve().parents[1] / "web"
_DEFAULT_OUT = _WEB_DIR / "dashboard-data.json"
OUT_JSON = Path(os.environ.get("DASHBOARD_JSON", _DEFAULT_OUT))
_DEFAULT_HTML = VAULT / "00-System/Dashboard.html"
OUT_HTML = Path(os.environ.get("DASHBOARD_HTML", _DEFAULT_HTML))
_legacy_env = os.environ.get("LEGACY_TASKS", "").strip()
LEGACY_TASKS = Path(_legacy_env) if _legacy_env else None

INBOX_SUBDIRS = ("slack", "sembly", "email", "daily")

# Keep in sync with web/app.js PROJECT_PALETTE
PROJECT_PALETTE = [
    "#e57373",
    "#64b5f6",
    "#4db6ac",
    "#81c784",
    "#ffb74d",
    "#ba68c8",
    "#f06292",
    "#4dd0e1",
    "#aed581",
    "#ff8a65",
    "#9575cd",
    "#dce775",
    "#90a4ae",
]


def project_prefix(name: str) -> str:
    """First letter of each of the first 3 whitespace-separated words (uppercase)."""
    parts: list[str] = []
    for word in (name or "").split()[:3]:
        word = word.strip()
        if word:
            parts.append(word[0].upper())
    return "".join(parts)


def task_id_suffix(task_id: str) -> str:
    """Numeric tail after stripping leading letters (F1→1, OPS1→1, T20→20)."""
    if not task_id:
        return ""
    suffix = re.sub(r"^[A-Za-z]+", "", task_id)
    return suffix if suffix else task_id


def task_display_id(prefix: str, task_id: str) -> str:
    """Markdown id is canonical (project-prefixed, vault-unique). Display = id."""
    return task_id or prefix or ""


def project_color_hex(slug: str, proj_order: list[str]) -> str:
    if slug in proj_order:
        idx = proj_order.index(slug)
        if 0 <= idx < len(PROJECT_PALETTE):
            return PROJECT_PALETTE[idx]
    h = 0
    for ch in slug:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return PROJECT_PALETTE[abs(h) % len(PROJECT_PALETTE)]


def enrich_tasks(tasks: list[dict], projects: dict, proj_order: list[str]) -> list[dict]:
    out: list[dict] = []
    for t in tasks:
        row = dict(t)
        slug = row.get("proj") or ""
        pname = (projects.get(slug) or {}).get("name") or slug
        prefix = project_prefix(pname)
        tid = row.get("id") or ""
        row["projPrefix"] = prefix
        row["displayId"] = task_display_id(prefix, tid)
        row["projColor"] = project_color_hex(slug, proj_order)
        out.append(row)
    return out


def title_from_md(p: Path, body: str | None = None) -> str:
    text = body if body is not None else p.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines()[:30]:
        if line.startswith("# "):
            return line[2:].strip()[:120]
    return p.stem.replace("-", " ")[:120]


def list_inbox_items() -> list[dict]:
    inbox = VAULT / "01-INBOX"
    if not inbox.exists():
        return []
    items: list[dict] = []
    for sub in INBOX_SUBDIRS:
        subdir = inbox / sub
        if not subdir.is_dir():
            continue
        for p in sorted(subdir.rglob("*.md")):
            if p.name.startswith("README"):
                continue
            rel = p.relative_to(VAULT)
            body = p.read_text(encoding="utf-8", errors="ignore")
            items.append(
                {
                    "path": str(rel),
                    "filename": p.name,
                    "source": sub,
                    "title": title_from_md(p, body),
                }
            )
    return items


def count_inbox() -> int:
    return len(list_inbox_items())


def pending_batch_label(batch: dict) -> str:
    for key in ("summary", "topic", "title"):
        val = batch.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:160]
    proposals = batch.get("proposals") or []
    if proposals:
        first = proposals[0].get("title") or proposals[0].get("id") or ""
        if first:
            suffix = f" (+{len(proposals) - 1})" if len(proposals) > 1 else ""
            return f"{first[:120]}{suffix}"
    return ""


def list_pending_items() -> list[dict]:
    pending = VAULT / "00-System/Triage-Pending"
    if not pending.exists():
        return []
    items: list[dict] = []
    for f in sorted(pending.glob("*.json")):
        try:
            batch = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if batch.get("status", "open") != "open":
            continue
        proposals = batch.get("proposals") or []
        items.append(
            {
                "filename": f.name,
                "batchId": batch.get("batchId", f.stem.replace("-batch", "")),
                "created": batch.get("created"),
                "label": pending_batch_label(batch),
                "proposalCount": len(proposals),
            }
        )
    items.sort(key=lambda x: x.get("created") or "", reverse=True)
    return items


def count_pending() -> int:
    return len(list_pending_items())


def prague_today() -> date:
    return datetime.now(TZ).date()


def default_wait_until() -> str:
    return (prague_today() + timedelta(days=3)).isoformat()


def parse_wait_until(task: dict) -> date | None:
    raw = task.get("waitUntil")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def is_active_waiting(task: dict, today: date | None = None) -> bool:
    if task.get("st") == "dn" or task.get("p") != "Waiting":
        return False
    wu = parse_wait_until(task)
    if not wu:
        return False
    today = today or prague_today()
    return wu > today


def is_expired_waiting(task: dict, today: date | None = None) -> bool:
    if task.get("st") == "dn" or task.get("p") != "Waiting":
        return False
    wu = parse_wait_until(task)
    if not wu:
        return False
    today = today or prague_today()
    return wu <= today


def waiting_column(tasks: list[dict], today: date | None = None) -> list[dict]:
    today = today or prague_today()
    active = [t for t in tasks if is_active_waiting(t, today)]
    return sorted(active, key=lambda t: (t.get("waitUntil") or "", t.get("proj") or "", t.get("id") or ""))


def count_waiting_expired(tasks: list[dict], today: date | None = None) -> int:
    today = today or prague_today()
    return sum(1 for t in tasks if is_expired_waiting(t, today))


def write_expired_waiting_pending(tasks: list[dict], today: date | None = None) -> int:
    """Create Triage-Pending/waiting-<proj>-<id>-<date>.json for expired Waiting tasks."""
    today = today or prague_today()
    pending_dir = VAULT / "00-System/Triage-Pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(TZ)
    written = 0
    for t in tasks:
        if not is_expired_waiting(t, today):
            continue
        proj = t.get("proj") or "unknown"
        tid = t.get("id") or "task"
        out = pending_dir / f"waiting-{proj}-{tid}-{today.isoformat()}.json"
        if out.exists():
            try:
                prev = json.loads(out.read_text(encoding="utf-8"))
                if prev.get("status", "open") != "open":
                    continue
            except json.JSONDecodeError:
                pass
            continue
        display = t.get("displayId") or tid
        name = t.get("name") or tid
        wu = (t.get("waitUntil") or "")[:10]
        extend_until = default_wait_until()
        batch = {
            "batchId": f"waiting-{proj}-{tid}-{today.isoformat()}",
            "status": "open",
            "created": now.isoformat(),
            "type": "waiting_expired",
            "summary": f"{display} — {name} (čekání vypršelo {wu})",
            "taskRef": {"proj": proj, "id": tid, "name": name, "waitUntil": wu},
            "proposals": [
                {
                    "id": "extend",
                    "action": "waiting_extend",
                    "title": "Čekat dál (+3 dny od dneška)",
                    "suggestedProj": proj,
                    "waitUntil": extend_until,
                    "notes": f"V markdownu: **Waiting | Čekat do: {extend_until}**",
                },
                {
                    "id": "reactivate",
                    "action": "waiting_reactivate",
                    "title": "Vrátit do práce (odstranit Waiting řádek, nastavit prioritu)",
                    "suggestedProj": proj,
                    "priority": "Next",
                    "notes": "Zachovat dl a ICE beze změny; upravit jen prioritu v 02-PROJEKTY.",
                },
            ],
        }
        out.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
        written += 1
    return written


def load_tasks() -> dict:
    legacy = LEGACY_TASKS or (VAULT / "00-System/dashboard-tasks-source.json")
    if Path(legacy).exists():
        return json.loads(Path(legacy).read_text(encoding="utf-8"))
    # Minimal fallback
    return {"version": 1, "updated": str(date.today()), "proj_order": [], "projects": {}, "tasks": []}


def top_priority(tasks: list, limit: int = 3) -> list:
    today = date.today()

    def score(t: dict) -> float:
        if t.get("st") == "dn":
            return -1.0
        ice = t.get("ice") or {}
        i, c, e = ice.get("i", 5), ice.get("c", 5), max(ice.get("e", 5), 1)
        s = (i * c) / e
        if t.get("p") == "ASAP":
            s += 50
        dl = t.get("dl")
        if dl:
            try:
                d = date.fromisoformat(dl[:10])
                if d <= today:
                    s += 30
                elif (d - today).days <= 2:
                    s += 15
            except ValueError:
                pass
        return s

    open_tasks = [t for t in tasks if t.get("st") != "dn" and t.get("p") != "Waiting"]
    ranked = sorted(open_tasks, key=score, reverse=True)
    picked: list[dict] = []
    seen: set[str] = set()
    for t in ranked:
        tid = t.get("id")
        if tid and tid in seen:
            continue
        picked.append(t)
        if tid:
            seen.add(tid)
        if len(picked) >= limit:
            return picked[:limit]

    if len(picked) < limit:
        asap_pool = sorted(
            [t for t in open_tasks if t.get("p") == "ASAP" and t.get("id") not in seen],
            key=score,
            reverse=True,
        )
        for t in asap_pool:
            tid = t.get("id")
            if tid and tid in seen:
                continue
            picked.append(t)
            if tid:
                seen.add(tid)
            if len(picked) >= limit:
                break

    return picked[:limit]


def meta_refresh_tag() -> str:
    """file:// fallback: full page reload when standalone HTML has no fetch API."""
    raw = os.environ.get("DASHBOARD_AUTO_REFRESH_SEC", "30").strip()
    if raw.lower() in ("0", "false", "no", "off"):
        return ""
    try:
        sec = max(1, int(raw))
    except ValueError:
        sec = 30
    return f'  <meta http-equiv="refresh" content="{sec}" />\n'


def build_standalone_html(payload: dict) -> str:
    """Single .html file (embedded CSS/JS/data) — open via Finder, no http.server."""
    css = (_WEB_DIR / "styles.css").read_text(encoding="utf-8")
    js = (_WEB_DIR / "app.js").read_text(encoding="utf-8")
    data_js = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    poll_sec = os.environ.get("DASHBOARD_POLL_SEC", "10").strip() or "10"
    idx = (_WEB_DIR / "index.html").read_text(encoding="utf-8")
    start = idx.index("<body>") + len("<body>")
    end = idx.index("</body>")
    body = idx[start:end].strip()
    body = re.sub(r'<link[^>]+styles\.css[^>]*>\s*', "", body)
    body = re.sub(r'<script src="app\.js"></script>', "", body)
    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#1a1d23" />
{meta_refresh_tag()}  <title>Second Brain Dashboard</title>
  <style>
{css}
  </style>
</head>
<body>
{body}
  <script>window.__DASHBOARD_DATA__ = {data_js};
window.DASHBOARD_POLL_SEC = {json.dumps(poll_sec)};</script>
  <script>
{js}
  </script>
</body>
</html>
"""



def _filter_calendar(data: dict) -> dict:
    import sys

    cron_dir = Path(__file__).resolve().parent
    if str(cron_dir) not in sys.path:
        sys.path.insert(0, str(cron_dir))
    from fetch_calendar import filter_calendar_payload

    return filter_calendar_payload(data)


def load_calendar() -> dict:
    """Plný Google Calendar (SA jako RB Universe) nebo cache calendar-events.json."""
    if os.environ.get("DASHBOARD_SKIP_CALENDAR", "").lower() in ("1", "true", "yes"):
        cached = VAULT / "00-System/calendar-events.json"
        if cached.exists():
            try:
                return _filter_calendar(json.loads(cached.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
        return {"source": "skipped", "events": []}
    cal_script = Path(__file__).resolve().parent / "fetch_calendar.py"
    if cal_script.exists():
        import subprocess
        import sys

        subprocess.run([sys.executable, str(cal_script)], check=False)
    cached = VAULT / "00-System/calendar-events.json"
    if cached.exists():
        try:
            return _filter_calendar(json.loads(cached.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    return {"source": "none", "events": []}


def refresh_sources() -> None:
    """Sync tasks JSON from 02-PROJEKTY when markdown is newer."""
    sync_script = Path(__file__).resolve().parent / "sync_tasks_from_projekty.py"
    if sync_script.exists():
        import subprocess
        import sys

        subprocess.run([sys.executable, str(sync_script)], check=False)


def dashboard_file_url(path: Path | None = None) -> str:
    p = (path or OUT_HTML).resolve()
    from urllib.parse import quote

    return "file://" + quote(str(p).replace("\\", "/"), safe="/:")


def main() -> None:
    if os.environ.get("DASHBOARD_SKIP_SYNC", "").lower() not in ("1", "true", "yes"):
        refresh_sources()
    src = load_tasks()
    proj_order = src.get("proj_order", [])
    projects = src.get("projects", {})
    tasks = enrich_tasks(src.get("tasks", []), projects, proj_order)
    today = prague_today()
    expired_written = write_expired_waiting_pending(tasks, today)
    waiting = waiting_column(tasks, today)
    waiting_expired = count_waiting_expired(tasks, today)
    payload = {
        "version": 2,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "inboxCount": count_inbox(),
        "inboxItems": list_inbox_items(),
        "pendingCount": count_pending(),
        "pendingItems": list_pending_items(),
        "waitingExpiredCount": waiting_expired,
        "waitingExpiredWritten": expired_written,
        "proj_order": proj_order,
        "projects": projects,
        "tasks": tasks,
        "waiting": waiting,
        "topPriority": top_priority(tasks),
        "eduNews": src.get("eduNews", []),
        "eduNewsUpdated": src.get("eduNewsUpdated"),
        "calendar": load_calendar(),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    vault_system = VAULT / "00-System"
    vault_system.mkdir(parents=True, exist_ok=True)
    vault_data = vault_system / "dashboard-data.json"
    vault_stamp = vault_system / "dashboard-build-stamp.json"
    generated = payload["generated"]
    vault_data.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    vault_stamp.write_text(
        json.dumps({"generated": generated}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        "wrote",
        OUT_JSON,
        "inbox=",
        payload["inboxCount"],
        "pending=",
        payload["pendingCount"],
        "waiting=",
        len(waiting),
        "waiting_expired=",
        waiting_expired,
    )
    print("wrote", vault_data)
    print("wrote", vault_stamp)
    if os.environ.get("DASHBOARD_HTML", "1") not in ("0", "false", "no"):
        OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
        OUT_HTML.write_text(build_standalone_html(payload), encoding="utf-8")
        print("wrote", OUT_HTML)
        print("open", dashboard_file_url(OUT_HTML))


if __name__ == "__main__":
    main()
