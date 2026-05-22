#!/usr/bin/env python3
"""Refresh EDU news topic suggestions (OPS2) z MrLUC vault aktivity.

Phase 2 migrace — vault I/O přes lib/drive_io.DriveVault. Hub
markdown přepis chráněn mtime CAS (pokud user mezitím upravil
operations.md v Obsidianu, refresh se přeskočí).

Reads completed work (HOTOVO), high-progress tasks, merges into
00-System/edu-news-topics.json, syncs eduNews into
00-System/dashboard-tasks-source.json, updates Operations.md OPS2
checklist, then rebuilds dashboard via build_dashboard.main().

Usage:
  python3 edu_news_refresh.py           # refresh (default)
  python3 edu_news_refresh.py --clear   # po nahrání EDU news (nastaví cycleStartedAt)
  python3 edu_news_refresh.py --dry-run # candidates, žádné writes
"""
from __future__ import annotations

import importlib
import json
import logging
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_HERE = Path(__file__).resolve().parent
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

TASKS_REL = "00-System/dashboard-tasks-source.json"
TOPICS_REL = "00-System/edu-news-topics.json"
OPERATIONS_REL = "02-PROJEKTY/Operations.md"
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))

MAX_TOPICS = int(os.environ.get("EDU_NEWS_MAX", "5"))
LOOKBACK_DAYS = int(os.environ.get("EDU_NEWS_LOOKBACK_DAYS", "7"))

EXCLUDE_SLUGS = frozenset(
    s.strip()
    for s in os.environ.get(
        "EDU_NEWS_EXCLUDE_SLUGS", "osobni,owners"
    ).split(",")
    if s.strip()
)

EXCLUDE_NAME_RE = re.compile(
    r"\b(osobní|soukrom|daňové přiznání|přiznání fy|manžel|rodin)\b",
    re.I,
)

HOTOVO_SECTION_RE = re.compile(r"^##\s+Recently moved to HOTOVO", re.MULTILINE | re.I)
HOTOVO_HEAD_RE = re.compile(
    r"^###\s+([A-Z]+\d+[a-z]?)\s*[—–-]\s*(.+?)\s*✅\s*$",
    re.MULTILINE,
)
DATE_ISO_RE = re.compile(r"_\(\s*(\d{4}-\d{2}-\d{2})\s*\)_")
DATE_CZ_RE = re.compile(r"_\(\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\s*\)_")
HOTOVO_INLINE_CZ_RE = re.compile(
    r"(?:přesunuto do HOTOVO|HOTOVO|smazáno)\s+(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})",
    re.I,
)

POSITIVE_RE = re.compile(
    r"\b(nasazen|spuštěn|opraven|hotov|dokončen|rollout|integrac|formulář|universe|rb universe|proces|tým|akadem)\b",
    re.I,
)

OPS2_TOPICS_MARKER = re.compile(
    r"<!-- edu-news-topics:start -->.*?<!-- edu-news-topics:end -->",
    re.DOTALL,
)

log = logging.getLogger("edu_news_refresh")
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


def _cycle_start_date(state: dict) -> date | None:
    """Datum začátku EDU news cyklu (po --clear / natočení videa)."""
    raw = state.get("cycleStartedAt")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ).date()
    except ValueError:
        return None


def _effective_hotovo_cutoff(today: date, state: dict) -> date:
    """Lookback window, but never před cycleStartedAt (po vyčištění topics)."""
    base = today - timedelta(days=LOOKBACK_DAYS)
    started = _cycle_start_date(state)
    if started is None:
        return base
    return max(base, started)


def _parse_hotovo_date(block: str) -> date | None:
    m = DATE_ISO_RE.search(block)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass
    m = DATE_CZ_RE.search(block)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    m = HOTOVO_INLINE_CZ_RE.search(block)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    return None


def _slug_title(name: str, text: str) -> tuple[str, str]:
    slug_m = re.search(r"^\*\*Slug\*\*:\s*`([^`]+)`", text, re.MULTILINE)
    title_m = re.search(r"^#\s+Téma:\s*(.+)$", text, re.MULTILINE)
    stem = os.path.splitext(name)[0]
    slug = slug_m.group(1) if slug_m else stem
    title = title_m.group(1).strip() if title_m else slug
    return slug, title


def collect_hotovo_candidates(cutoff: date) -> list[dict]:
    vault = get_vault()
    out: list[dict] = []
    try:
        hubs = vault.list_dir("02-PROJEKTY", pattern="*.md")
    except DriveNotFoundError:
        return out
    for meta in sorted(hubs, key=lambda m: m.name):
        if meta.name.startswith("_") or meta.name.startswith("._"):
            continue
        text, _ = vault.read_text(meta.rel_path)
        slug, proj_name = _slug_title(meta.name, text)
        if slug in EXCLUDE_SLUGS:
            continue
        m = HOTOVO_SECTION_RE.search(text)
        if not m:
            continue
        section = text[m.start() :]
        nxt = re.search(r"^##\s+(?!Recently)", section[1:], re.MULTILINE)
        if nxt:
            section = section[: nxt.start() + 1]
        for hm in HOTOVO_HEAD_RE.finditer(section):
            tid, title = hm.group(1), hm.group(2).strip()
            start = hm.end()
            nxt_h = HOTOVO_HEAD_RE.search(section, start)
            block = section[start : nxt_h.start() if nxt_h else len(section)]
            completed = _parse_hotovo_date(block)
            if completed is None:
                continue
            if completed < cutoff:
                continue
            if EXCLUDE_NAME_RE.search(title):
                continue
            one_liner = re.sub(r"\s+", " ", block.strip().split("\n")[0] if block.strip() else "")
            one_liner = re.sub(r"_\([^)]*\)_", "", one_liner).strip()[:200]
            if not one_liner:
                one_liner = title
            out.append(
                {
                    "key": key,
                    "title": title,
                    "oneLiner": one_liner,
                    "proj": slug,
                    "projName": proj_name,
                    "taskId": tid,
                    "source": "hotovo",
                    "completed": completed.isoformat(),
                    "kind": "done",
                }
            )
    return out


def _progress_done_count(task: dict) -> int:
    actionable = [c for c in (task.get("ch") or []) if not c.get("source")]
    return sum(1 for c in actionable if c.get("d"))


def build_progress_baseline(tasks: list[dict]) -> dict[str, int]:
    """Snapshot rozpracovaných úkolů při --clear (nesmí se hned znovu nabídnout)."""
    baseline: dict[str, int] = {}
    for t in tasks:
        if t.get("st") == "dn" or t.get("p") in ("Waiting", "Backlog"):
            continue
        slug = t.get("proj") or ""
        if slug in EXCLUDE_SLUGS:
            continue
        name = t.get("name") or ""
        if EXCLUDE_NAME_RE.search(name):
            continue
        ch = t.get("ch") or []
        actionable = [c for c in ch if not c.get("source")]
        if len(actionable) < 2:
            continue
        done_n = _progress_done_count(t)
        ratio = done_n / len(actionable)
        if ratio < 0.5:
            continue
        ice = t.get("ice") or {}
        i, c, e = ice.get("i", 5), ice.get("c", 5), max(ice.get("e", 5), 1)
        if (i * c) / e < 5.0:
            continue
        tid = t.get("id") or ""
        baseline[f"{slug}:{tid}"] = done_n
    return baseline


def collect_progress_candidates(
    tasks: list[dict],
    *,
    progress_baseline: dict[str, int] | None = None,
) -> list[dict]:
    out: list[dict] = []
    for t in tasks:
        if t.get("st") == "dn" or t.get("p") in ("Waiting", "Backlog"):
            continue
        slug = t.get("proj") or ""
        if slug in EXCLUDE_SLUGS:
            continue
        name = t.get("name") or ""
        if EXCLUDE_NAME_RE.search(name):
            continue
        ch = t.get("ch") or []
        actionable = [c for c in ch if not c.get("source")]
        if len(actionable) < 2:
            continue
        done_n = _progress_done_count(t)
        ratio = done_n / len(actionable)
        if ratio < 0.5:
            continue
        ice = t.get("ice") or {}
        i, c, e = ice.get("i", 5), ice.get("c", 5), max(ice.get("e", 5), 1)
        if (i * c) / e < 5.0:
            continue
        tid = t.get("id") or ""
        key = f"{slug}:{tid}"
        if progress_baseline is not None:
            prev_done = progress_baseline.get(key)
            if prev_done is not None and done_n <= prev_done:
                continue
        out.append(
            {
                "key": f"{slug}:{tid}",
                "title": name,
                "oneLiner": f"Rozpracováno ({done_n}/{len(actionable)} kroků) — {slug}",
                "proj": slug,
                "projName": slug,
                "taskId": tid,
                "source": "progress",
                "completed": None,
                "kind": "progress",
            }
        )
    return out


def score_topic(topic: dict, today: date) -> float:
    ice = topic.get("ice") or {}
    i, c, e = ice.get("i", 5), ice.get("c", 5), max(ice.get("e", 5), 1)
    s = (i * c) / e
    text = f"{topic.get('title', '')} {topic.get('oneLiner', '')}"
    if POSITIVE_RE.search(text):
        s += 3.0
    if topic.get("kind") == "done":
        s += 8.0
        comp = topic.get("completed")
        if comp:
            try:
                d = date.fromisoformat(comp[:10])
                age = (today - d).days
                if age <= 2:
                    s += 6.0
                elif age <= LOOKBACK_DAYS:
                    s += 3.0
            except ValueError:
                pass
    elif topic.get("kind") == "progress":
        s += 2.0
    slug = topic.get("proj") or ""
    if slug in ("rb-universe-development", "firemni-procesy", "strategy"):
        s += 1.5
    return s


def attach_ice(topics: list[dict], tasks: list[dict]) -> None:
    by_key = {(t.get("proj"), t.get("id")): t for t in tasks}
    for topic in topics:
        ice = (by_key.get((topic.get("proj"), topic.get("taskId"))) or {}).get("ice")
        if ice:
            topic["ice"] = ice


def merge_topics(
    existing: list[dict],
    fresh: list[dict],
    *,
    min_completed: date | None = None,
) -> list[dict]:
    by_key: dict[str, dict] = {}
    for t in existing:
        k = t.get("key")
        if k:
            by_key[k] = t
    for t in fresh:
        k = t.get("key")
        if not k:
            continue
        if min_completed and t.get("kind") == "done":
            comp = t.get("completed")
            if comp:
                try:
                    if date.fromisoformat(comp[:10]) < min_completed:
                        continue
                except ValueError:
                    pass
        prev = by_key.get(k)
        if prev:
            prev.update({kk: vv for kk, vv in t.items() if vv is not None})
            prev["updated"] = datetime.now(TZ).isoformat(timespec="seconds")
        else:
            t["added"] = datetime.now(TZ).isoformat(timespec="seconds")
            by_key[k] = t
    return list(by_key.values())


def rank_topics(
    topics: list[dict],
    tasks: list[dict],
    *,
    hotovo_cutoff: date | None = None,
) -> list[dict]:
    today = _prague_today()
    cutoff = hotovo_cutoff or (today - timedelta(days=LOOKBACK_DAYS))
    attach_ice(topics, tasks)
    filtered: list[dict] = []
    for t in topics:
        if t.get("proj") in EXCLUDE_SLUGS:
            continue
        if EXCLUDE_NAME_RE.search(t.get("title", "")):
            continue
        if t.get("kind") == "done":
            comp = t.get("completed")
            if comp:
                try:
                    if date.fromisoformat(comp[:10]) < cutoff:
                        continue
                except ValueError:
                    pass
        t["score"] = round(score_topic(t, today), 2)
        filtered.append(t)
    filtered.sort(key=lambda x: (-x.get("score", 0), x.get("proj", ""), x.get("taskId", "")))
    return filtered[:MAX_TOPICS]


def load_tasks_data() -> dict:
    vault = get_vault()
    try:
        data, _ = vault.read_json(TASKS_REL)
        if isinstance(data, dict):
            return data
    except DriveNotFoundError:
        pass
    return {"version": 1, "proj_order": [], "projects": {}, "tasks": []}


def load_topics_state() -> dict:
    vault = get_vault()
    try:
        data, _ = vault.read_json(TOPICS_REL)
        if isinstance(data, dict):
            return data
    except DriveNotFoundError:
        pass
    return {"version": 1, "topics": []}


def save_topics_state(
    topics: list[dict],
    *,
    cycle_started_at: str | None = None,
    progress_baseline: dict[str, int] | None = None,
    preserve_cycle: bool = True,
) -> None:
    prev = load_topics_state() if preserve_cycle else {}
    payload: dict = {
        "version": 1,
        "updated": datetime.now(TZ).isoformat(timespec="seconds"),
        "topics": topics,
    }
    csa = cycle_started_at if cycle_started_at is not None else prev.get("cycleStartedAt")
    if csa:
        payload["cycleStartedAt"] = csa
    bl = progress_baseline if progress_baseline is not None else prev.get("progressBaseline")
    if bl:
        payload["progressBaseline"] = bl
    get_vault().write_json(TOPICS_REL, payload)


def sync_to_tasks_json(topics: list[dict]) -> None:
    vault = get_vault()
    data = load_tasks_data()
    data["eduNews"] = [
        {
            "title": t["title"],
            "oneLiner": t.get("oneLiner", ""),
            "proj": t.get("proj", ""),
            "taskId": t.get("taskId", ""),
            "source": t.get("source", ""),
            "score": t.get("score"),
        }
        for t in topics
    ]
    data["eduNewsUpdated"] = datetime.now(TZ).isoformat(timespec="seconds")
    vault.write_json(TASKS_REL, data)


def patch_operations_md(topics: list[dict]) -> bool:
    """Update OPS2 EDU-news block in Operations.md with mtime CAS.

    Returns True only on a successful write that changed content.
    """
    vault = get_vault()
    try:
        text, meta = vault.read_text(OPERATIONS_REL)
    except DriveNotFoundError:
        return False
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    if topics:
        lines = [f"**Návrhy témat** _(auto {now})_:"]
        for t in topics:
            pid = t.get("taskId") or "—"
            pname = t.get("projName") or t.get("proj") or ""
            line = t.get("oneLiner") or t.get("title", "")
            lines.append(f"- [ ] **{pid}** ({pname}) — {line}")
    else:
        lines = [
            f"**Návrhy témat** _(vyčištěno {now})_:",
            "- _(sbírám témata pro příští EDU news)_",
        ]
    block = (
        "<!-- edu-news-topics:start -->\n"
        + "\n".join(lines)
        + "\n<!-- edu-news-topics:end -->"
    )
    if OPS2_TOPICS_MARKER.search(text):
        new_text = OPS2_TOPICS_MARKER.sub(block, text)
    else:
        new_text = text.replace(
            "_Témata: viz checklist v agenda-canvas (OPS2)_",
            block,
        )
    if new_text == text:
        return False
    try:
        vault.write_text(OPERATIONS_REL, new_text, expect_mtime=meta.modified_time)
    except DriveConflictError as e:
        log.warning("operations.md changed externally during patch (%s) — skipping", e)
        return False
    return True


def llm_rerank(candidates: list[dict]) -> list[dict] | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key or len(candidates) <= MAX_TOPICS:
        return None
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    brief = [
        {
            "key": c["key"],
            "title": c["title"],
            "oneLiner": c.get("oneLiner", ""),
            "proj": c.get("proj"),
            "kind": c.get("kind"),
        }
        for c in candidates[:20]
    ]
    prompt = (
        "Vyber max "
        f"{MAX_TOPICS} témat pro 30s firemní EDU news video. "
        "Kritéria: zajímavé pro celou firmu, raději hotové/viditelný posun než čisté plány, "
        "ne osobní finance. Vrať POUZE JSON pole klíčů `key` seřazených od nejlepšího.\n\n"
        f"Kandidáti:\n{json.dumps(brief, ensure_ascii=False, indent=2)}"
    )
    body = json.dumps(
        {
            "model": model,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        print("edu_news: LLM skip:", e, file=sys.stderr)
        return None
    content = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            content += block.get("text", "")
    m = re.search(r"\[[\s\S]*?\]", content)
    if not m:
        return None
    try:
        keys = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(keys, list):
        return None
    by_key = {c["key"]: c for c in candidates}
    ordered = [by_key[k] for k in keys if k in by_key]
    for c in candidates:
        if c not in ordered:
            ordered.append(c)
    return ordered[:MAX_TOPICS]


def rebuild_dashboard() -> None:
    bd = importlib.import_module("build_dashboard")
    bd.main()


def clear_all() -> None:
    now = datetime.now(TZ).isoformat(timespec="seconds")
    tasks = load_tasks_data().get("tasks", [])
    baseline = build_progress_baseline(tasks)
    save_topics_state(
        [],
        cycle_started_at=now,
        progress_baseline=baseline,
        preserve_cycle=False,
    )
    sync_to_tasks_json([])
    patch_operations_md([])
    print(
        f"edu_news: cleared topics (cycleStartedAt={now}, "
        f"progressBaseline={len(baseline)})"
    )


def refresh(*, dry_run: bool = False) -> list[dict]:
    today = _prague_today()
    state = load_topics_state()
    cutoff = _effective_hotovo_cutoff(today, state)
    tasks_data = load_tasks_data()
    tasks = tasks_data.get("tasks", [])

    baseline = state.get("progressBaseline") or {}
    fresh = collect_hotovo_candidates(cutoff)
    fresh.extend(collect_progress_candidates(tasks, progress_baseline=baseline or None))
    merged = merge_topics(state.get("topics", []), fresh, min_completed=cutoff)
    ranked = rank_topics(merged, tasks, hotovo_cutoff=cutoff)
    llm = llm_rerank(merged)
    if llm is not None:
        ranked = llm

    print(f"edu_news: {len(fresh)} new signals, {len(merged)} merged, top {len(ranked)}")
    for t in ranked:
        print(f"  [{t.get('score')}] {t.get('taskId')} {t.get('title', '')[:60]}")

    if dry_run:
        return ranked

    save_topics_state(ranked)
    sync_to_tasks_json(ranked)
    if patch_operations_md(ranked):
        print("edu_news: updated drive://", OPERATIONS_REL)
    rebuild_dashboard()
    return ranked


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("EDU_NEWS_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    argv = sys.argv[1:]
    if "--clear" in argv:
        if "--dry-run" in argv:
            print("edu_news: --clear (dry-run, no writes)")
            return
        clear_all()
        if "--no-build" not in argv:
            rebuild_dashboard()
        return
    refresh(dry_run="--dry-run" in argv)


if __name__ == "__main__":
    main()
