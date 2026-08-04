#!/usr/bin/env python3
"""Sunday evening: factual weekly summary draft → 00-System/weekly/YYYY-Www-draft.md

Phase 2 migrace — vault I/O přes lib/drive_io.DriveVault.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, DriveNotFoundError, credentials_from_env  # noqa: E402

INBOX_SUBDIRS = ("slack", "sembly", "email", "daily", "Clippings")
TASKS_REL = "00-System/dashboard-tasks-source.json"
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))

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


def _today() -> date:
    return datetime.now(TZ).date()


def iso_week_label(d: date | None = None) -> str:
    d = d or _today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def count_inbox() -> int:
    vault = get_vault()
    n = 0
    for sub in INBOX_SUBDIRS:
        try:
            files = vault.list_dir(f"01-INBOX/{sub}", pattern="*.md")
        except DriveNotFoundError:
            continue
        for meta in files:
            if meta.name.startswith("README") or meta.name.startswith("._"):
                continue
            try:
                head, _ = vault.read_text(meta.rel_path)
            except DriveNotFoundError:
                continue
            if "ZPRACOVÁNO" in head[:400].upper():
                continue
            n += 1
    return n


def count_pending() -> int:
    try:
        files = get_vault().list_dir("00-System/Triage-Pending", pattern="*.json")
    except DriveNotFoundError:
        return 0
    return len(files)


def ice_score(t: dict, today: date) -> float:
    ice = t.get("ice") or {}
    i, c, e = ice.get("i", 5), ice.get("c", 5), max(ice.get("e", 5), 1)
    s = (i * c) / e
    # ASAP as a status is gone (priority model v2). This job still reads the
    # legacy v1 task source, which carries no `focus`, so ranking falls back to
    # ICE + deadline urgency only. Rewiring it onto agent-context.json is SB2.
    dl = t.get("dl")
    if dl:
        try:
            d = date.fromisoformat(str(dl)[:10])
            if d <= today:
                s += 30
            elif (d - today).days <= 2:
                s += 15
        except ValueError:
            pass
    return s


def build_draft() -> str:
    vault = get_vault()
    week = iso_week_label()
    rel = f"00-System/weekly/{week}-draft.md"
    today = _today()
    week_start = today - timedelta(days=7)

    try:
        src, _ = vault.read_json(TASKS_REL)
        if not isinstance(src, dict):
            src = {}
    except DriveNotFoundError:
        src = {}
    tasks = src.get("tasks", [])
    projects = src.get("projects", {})
    proj_order = src.get("proj_order", [])

    done_lines: list[str] = []
    for slug in proj_order:
        p = projects.get(slug) or {}
        dw = (p.get("stats") or {}).get("doneWeek", 0)
        if dw:
            done_lines.append(f"- **{p.get('name', slug)}** — {dw} položek v HOTOVO tento týden")

    open_tasks = [t for t in tasks if t.get("st") != "dn" and t.get("p") != "Waiting"]
    ranked = sorted(open_tasks, key=lambda t: ice_score(t, today), reverse=True)[:8]
    top_lines = [
        f"- `{t.get('proj')}/{t.get('id')}` {t.get('p')} dl={t.get('dl') or '—'} — {t.get('name', '')[:70]}"
        for t in ranked
    ]

    waiting = [t for t in tasks if t.get("p") == "Waiting" and t.get("st") != "dn"]
    wait_lines = [
        f"- `{t.get('proj')}/{t.get('id')}` do {t.get('waitUntil', '?')} — {t.get('name', '')[:60]}"
        for t in waiting[:12]
    ]

    overdue = []
    for t in open_tasks:
        dl = t.get("dl")
        if not dl:
            continue
        try:
            if date.fromisoformat(str(dl)[:10]) < today:
                overdue.append(t)
        except ValueError:
            pass
    overdue_lines = [
        f"- `{t.get('proj')}/{t.get('id')}` deadline {t.get('dl')} — {t.get('name', '')[:60]}"
        for t in overdue[:10]
    ]

    progress_bits = []
    for slug in proj_order:
        prog = (projects.get(slug) or {}).get("progress") or []
        if prog:
            progress_bits.append(f"### {projects.get(slug, {}).get('name', slug)}")
            for line in prog[:3]:
                progress_bits.append(f"- {line}")

    body = f"""# Týdenní shrnutí — draft {week}

**Vygenerováno:** {datetime.now(TZ).strftime("%Y-%m-%d %H:%M")} (Europe/Prague)  
**Období:** {week_start.isoformat()} – {today.isoformat()}  
**Schválení:** skill `agenda-weekly-review` → finální `{week}.md`

---

## Metriky

- INBOX nezpracovaných: **{count_inbox()}**
- Triage-Pending batchů: **{count_pending()}**
- Otevřených úkolů (bez Waiting): **{len(open_tasks)}**
- Waiting: **{len(waiting)}**
- Po termínu: **{len(overdue)}**

---

## Hotovo tento týden (z HOTOVO sekcí hubů)

{chr(10).join(done_lines) if done_lines else "- _(žádné datované HOTOVO v hubech)_"}

---

## Progress v hubech

{chr(10).join(progress_bits) if progress_bits else "- _(sekce ## Progress prázdná — doplň po schválení)_"}

---

## TOP úkoly podle skóre (návrh fokusu)

{chr(10).join(top_lines) if top_lines else "- —"}

---

## Waiting

{chr(10).join(wait_lines) if wait_lines else "- —"}

---

## Po termínu

{chr(10).join(overdue_lines) if overdue_lines else "- —"}

---

## Co povedlo / kam to posunulo / priorita příští týden

_(doplň v chatu při schvalování — tento draft je jen fakta)_

### Co se povedlo
- 

### Kam se posunulo
- 

### Priorita příští týden
1. 
2. 
3. 

---

_Viz `00-System/Memory/procesy-mrluc.md`_
"""
    vault.write_text(rel, body)
    return rel


def main() -> None:
    rel = build_draft()
    print("wrote drive://", rel)


if __name__ == "__main__":
    main()
