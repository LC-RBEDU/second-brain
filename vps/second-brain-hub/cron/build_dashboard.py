#!/usr/bin/env python3
"""Build dashboard-data.json + Dashboard.html z vault 02-PROJEKTY (Drive API).

Phase 2 migrace: vault I/O výhradně přes lib/drive_io.DriveVault.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import logging
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_HERE = Path(__file__).resolve().parent
_WEB_DIR = _HERE.parent / "web"
_LIB = _HERE.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from drive_io import (  # noqa: E402
    DriveConflictError,
    DriveNotFoundError,
    DriveVault,
    credentials_from_env,
)

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
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

_VAULT_SINGLETON: DriveVault | None = None
log = logging.getLogger("build_dashboard")


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


# ----------------------------------------------------------------- enrich tasks


def project_prefix(name: str) -> str:
    parts: list[str] = []
    for word in (name or "").split()[:3]:
        word = word.strip()
        if word:
            parts.append(word[0].upper())
    return "".join(parts)


def task_id_suffix(task_id: str) -> str:
    if not task_id:
        return ""
    suffix = re.sub(r"^[A-Za-z]+", "", task_id)
    return suffix if suffix else task_id


def task_display_id(prefix: str, task_id: str) -> str:
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


def title_from_md(filename: str, body: str) -> str:
    for line in body.splitlines()[:30]:
        if line.startswith("# "):
            return line[2:].strip()[:120]
    stem = os.path.splitext(filename)[0]
    return stem.replace("-", " ")[:120]


# ---------------------------------------------------------------------- inbox


def list_inbox_items() -> list[dict]:
    vault = get_vault()
    items: list[dict] = []
    for sub in INBOX_SUBDIRS:
        try:
            files = vault.list_dir(f"01-INBOX/{sub}", pattern="*.md", recursive=True)
        except DriveNotFoundError:
            continue
        for meta in files:
            if meta.name.startswith("README"):
                continue
            try:
                body, _ = vault.read_text(meta.rel_path)
            except DriveNotFoundError:
                continue
            items.append(
                {
                    "path": meta.rel_path,
                    "filename": meta.name,
                    "source": sub,
                    "title": title_from_md(meta.name, body),
                }
            )
    items.sort(key=lambda it: it["path"])
    return items


def count_inbox() -> int:
    return len(list_inbox_items())


# -------------------------------------------------------------------- pending


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
    vault = get_vault()
    try:
        files = vault.list_dir("00-System/Triage-Pending", pattern="*.json")
    except DriveNotFoundError:
        return []
    items: list[dict] = []
    for meta in files:
        try:
            batch, _ = vault.read_json(meta.rel_path)
        except (DriveNotFoundError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(batch, dict):
            continue
        if batch.get("status", "open") != "open":
            continue
        proposals = batch.get("proposals") or []
        items.append(
            {
                "filename": meta.name,
                "batchId": batch.get("batchId") or meta.name.replace("-batch.json", "").replace(".json", ""),
                "created": batch.get("created"),
                "label": pending_batch_label(batch),
                "proposalCount": len(proposals),
            }
        )
    items.sort(key=lambda x: x.get("created") or "", reverse=True)
    return items


def count_pending() -> int:
    return len(list_pending_items())


# -------------------------------------------------------------------- waiting


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


# ---------------------------------------------------------------------- waiting → ASAP rewriting

TASK_HEAD_RE = re.compile(
    r"^###\s+(~~)?([A-Z]+\d+[a-z]?)\s*[—–-]\s*(.+?)(?:~~)?\s*(✅|HOTOVO)?\s*$",
    re.MULTILINE,
)
WAITING_PRIORITY_LINE_RE = re.compile(
    r"\*\*Waiting\s*\|\s*Čekat\s+do:\s*\d{4}-\d{2}-\d{2}([^*]*)\*\*",
    re.I,
)
ICE_RE = re.compile(r"ICE\s+I(\d+)\s+C(\d+)\s+E(\d+)", re.I)


def _asap_priority_line(suffix: str, block: str) -> str:
    ice_m = ICE_RE.search(suffix) or ICE_RE.search(block[:600])
    if ice_m:
        return f"**ASAP | ICE I{ice_m.group(1)} C{ice_m.group(2)} E{ice_m.group(3)}**"
    return "**ASAP**"


def _reactivate_waiting_block(block: str) -> tuple[str, bool]:
    m = WAITING_PRIORITY_LINE_RE.search(block)
    if not m:
        return block, False
    new_line = _asap_priority_line(m.group(1), block)
    return block[: m.start()] + new_line + block[m.end() :], True


def reactivate_expired_waiting_in_vault(
    tasks: list[dict], projects: dict, today: date | None = None
) -> list[dict]:
    """Po vypršení waitUntil: hub .md Waiting → ASAP (SSOT), aby šel do top priority.

    Mtime-based CAS: pokud user mezitím zapsal stejný hub v Obsidianu
    (Drive Desktop sync ~60s), reaktivace se přeskočí a další iterace
    cronu zkusí znovu.
    """
    vault = get_vault()
    today = today or prague_today()
    by_proj: dict[str, list[dict]] = {}
    for t in tasks:
        if is_expired_waiting(t, today):
            by_proj.setdefault(t.get("proj") or "", []).append(t)

    reactivated: list[dict] = []
    for proj, proj_tasks in by_proj.items():
        if not proj:
            continue
        hub_rel = (projects.get(proj) or {}).get("hubFile")
        if not hub_rel:
            continue
        try:
            text, meta = vault.read_text(hub_rel)
        except DriveNotFoundError:
            continue
        changed = False
        proj_reactivated: list[dict] = []
        for t in proj_tasks:
            tid = t.get("id") or ""
            if not tid:
                continue
            for m in TASK_HEAD_RE.finditer(text):
                if m.group(2) != tid:
                    continue
                start = m.end()
                nxt = TASK_HEAD_RE.search(text, start)
                end = nxt.start() if nxt else len(text)
                block = text[start:end]
                new_block, ok = _reactivate_waiting_block(block)
                if ok:
                    text = text[:start] + new_block + text[end:]
                    changed = True
                    proj_reactivated.append(
                        {
                            "proj": proj,
                            "id": tid,
                            "displayId": t.get("displayId") or tid,
                            "name": t.get("name") or tid,
                            "waitUntil": (t.get("waitUntil") or "")[:10],
                        }
                    )
                break
        if changed:
            try:
                vault.write_text(hub_rel, text, expect_mtime=meta.modified_time)
            except DriveConflictError as e:
                log.warning(
                    "reactivate skipped: %s changed externally during build (%s)",
                    hub_rel,
                    e,
                )
                continue
            reactivated.extend(proj_reactivated)
    return reactivated


def archive_auto_reactivated_waiting_pending(reactivated: list[dict], today: date | None = None) -> int:
    """Po automatické reaktivaci přesune odpovídající waiting-* pending batches do Triage-Applied."""
    vault = get_vault()
    today = today or prague_today()
    try:
        pending_files = vault.list_dir("00-System/Triage-Pending", pattern="*.json")
    except DriveNotFoundError:
        return 0
    by_name = {meta.name: meta for meta in pending_files}
    archived = 0
    for item in reactivated:
        proj = item.get("proj") or ""
        tid = item.get("id") or ""
        if not proj or not tid:
            continue
        prefix = f"waiting-{proj}-{tid}-"
        for name, meta in list(by_name.items()):
            if not name.startswith(prefix):
                continue
            try:
                batch, _ = vault.read_json(meta.rel_path)
            except (DriveNotFoundError, json.JSONDecodeError, ValueError):
                continue
            if not isinstance(batch, dict) or batch.get("status") != "open":
                continue
            batch["status"] = "applied"
            batch["appliedAt"] = datetime.now(TZ).isoformat()
            batch["appliedNote"] = "auto_waiting_reactivate_asap"
            applied_name = name.replace(".json", "-applied.json")
            applied_rel = f"00-System/Triage-Applied/{applied_name}"
            vault.write_json(applied_rel, batch)
            try:
                vault.delete(meta.rel_path)
            except DriveNotFoundError:
                pass
            archived += 1
            del by_name[name]
    return archived


# ---------------------------------------------------------------------- tasks


def load_tasks() -> dict:
    vault = get_vault()
    try:
        data, _ = vault.read_json("00-System/dashboard-tasks-source.json")
        if isinstance(data, dict):
            return data
    except DriveNotFoundError:
        pass
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
    pinned = sorted(
        [t for t in open_tasks if t.get("pinTop")],
        key=score,
        reverse=True,
    )
    for t in pinned:
        tid = t.get("id")
        if tid and tid in seen:
            continue
        picked.append(t)
        if tid:
            seen.add(tid)
        if len(picked) >= limit:
            return picked[:limit]
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


# ---------------------------------------------------------------------- HTML


def meta_refresh_tag() -> str:
    raw = os.environ.get("DASHBOARD_AUTO_REFRESH_SEC", "0").strip()
    if raw.lower() in ("0", "false", "no", "off"):
        return ""
    try:
        sec = max(1, int(raw))
    except ValueError:
        sec = 30
    return f'  <meta http-equiv="refresh" content="{sec}" />\n'


def build_standalone_html(payload: dict) -> str:
    css = (_WEB_DIR / "styles.css").read_text(encoding="utf-8")
    js = (_WEB_DIR / "app.js").read_text(encoding="utf-8")
    data_js = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    embed_fp = payload.get("fingerprint") or payload.get("generated") or ""
    poll_sec = os.environ.get("DASHBOARD_POLL_SEC", "60").strip() or "60"
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
window.__DASHBOARD_EMBED_FP__ = {json.dumps(embed_fp)};
window.DASHBOARD_POLL_SEC = {json.dumps(poll_sec)};</script>
  <script>
{js}
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------- calendar / sync


def _filter_calendar(data: dict) -> dict:
    fc = importlib.import_module("fetch_calendar")
    return fc.filter_calendar_payload(data)


def load_calendar() -> dict:
    """Plný Google Calendar fetch + filter, nebo cached výstup z Drive."""
    if os.environ.get("DASHBOARD_SKIP_CALENDAR", "").lower() in ("1", "true", "yes"):
        try:
            data, _ = get_vault().read_json("00-System/calendar-events.json")
            return _filter_calendar(data) if isinstance(data, dict) else {"source": "skipped", "events": []}
        except (DriveNotFoundError, json.JSONDecodeError, ValueError):
            return {"source": "skipped", "events": []}
    fc = importlib.import_module("fetch_calendar")
    try:
        payload = fc.refresh()
    except Exception as e:  # noqa: BLE001
        log.warning("fetch_calendar.refresh failed: %s", e)
        try:
            data, _ = get_vault().read_json("00-System/calendar-events.json")
            return _filter_calendar(data) if isinstance(data, dict) else {"source": "none", "events": []}
        except (DriveNotFoundError, json.JSONDecodeError, ValueError):
            return {"source": "none", "events": []}
    return payload if isinstance(payload, dict) else {"source": "none", "events": []}


def refresh_sources() -> None:
    """Sync tasks JSON from 02-PROJEKTY when markdown is newer (modulárně)."""
    try:
        sync_mod = importlib.import_module("sync_tasks_from_projekty")
    except ImportError as e:
        log.warning("sync_tasks_from_projekty unavailable: %s", e)
        return
    try:
        sync_mod.sync()
    except Exception as e:  # noqa: BLE001
        log.warning("sync_tasks_from_projekty.sync failed: %s", e)


# ---------------------------------------------------------------------- weekly review meta


def iso_week_label(d: date | None = None) -> str:
    d = d or prague_today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def weekly_review_meta() -> dict:
    vault = get_vault()
    week = iso_week_label()
    meta: dict = {"week": week}
    candidates = [
        ("draftFile", f"00-System/weekly/{week}-draft.md"),
        ("finalFile", f"00-System/weekly/{week}.md"),
        ("retroDraftFile", f"00-System/Memory/retro-{week}-draft.md"),
        ("retroFinalFile", f"00-System/Memory/retro-{week}.md"),
    ]
    for key, rel in candidates:
        if vault.exists(rel):
            meta[key] = rel
    return meta


# ---------------------------------------------------------------------- entry


def dashboard_data_fingerprint(payload: dict) -> str:
    core = {
        "inboxCount": payload.get("inboxCount"),
        "pendingCount": payload.get("pendingCount"),
        "waitingExpiredCount": payload.get("waitingExpiredCount"),
        "tasks": payload.get("tasks"),
        "waiting": payload.get("waiting"),
        "topPriority": payload.get("topPriority"),
        "eduNewsUpdated": payload.get("eduNewsUpdated"),
    }
    blob = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("BUILD_DASHBOARD_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    vault = get_vault()
    if os.environ.get("DASHBOARD_SKIP_SYNC", "").lower() not in ("1", "true", "yes"):
        refresh_sources()
    src = load_tasks()
    proj_order = src.get("proj_order", [])
    projects = src.get("projects", {})
    tasks = enrich_tasks(src.get("tasks", []), projects, proj_order)
    today = prague_today()
    waiting_expired_before = count_waiting_expired(tasks, today)
    reactivated = reactivate_expired_waiting_in_vault(tasks, projects, today)
    if reactivated:
        archive_auto_reactivated_waiting_pending(reactivated, today)
        refresh_sources()
        src = load_tasks()
        projects = src.get("projects", {})
        tasks = enrich_tasks(src.get("tasks", []), projects, proj_order)
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
        "waitingExpiredBeforeReactivate": waiting_expired_before,
        "waitingReactivated": reactivated,
        "proj_order": proj_order,
        "projects": projects,
        "tasks": tasks,
        "waiting": waiting,
        "topPriority": top_priority(tasks),
        "eduNews": src.get("eduNews", []),
        "eduNewsUpdated": src.get("eduNewsUpdated"),
        "weeklyReview": weekly_review_meta(),
        "calendar": load_calendar(),
    }
    generated = payload["generated"]
    fingerprint = dashboard_data_fingerprint(payload)
    payload["fingerprint"] = fingerprint
    vault.write_json("00-System/dashboard-data.json", payload)
    vault.write_json(
        "00-System/dashboard-build-stamp.json",
        {"generated": generated, "fingerprint": fingerprint},
    )
    print(
        "wrote drive:// 00-System/dashboard-data.json",
        "inbox=", payload["inboxCount"],
        "pending=", payload["pendingCount"],
        "waiting=", len(waiting),
        "waiting_expired=", waiting_expired,
        "waiting_reactivated=", len(reactivated),
    )
    if os.environ.get("DASHBOARD_HTML", "1") not in ("0", "false", "no"):
        html = build_standalone_html(payload)
        vault.write_text("00-System/Dashboard.html", html, mime_type="text/html")
        print("wrote drive:// 00-System/Dashboard.html")


if __name__ == "__main__":
    main()
