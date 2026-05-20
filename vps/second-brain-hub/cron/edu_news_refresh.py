#!/usr/bin/env python3
"""Refresh EDU news topic suggestions (OPS2) from MrLUC vault activity.

Reads completed work (HOTOVO), high-progress tasks, merges into
00-System/edu-news-topics.json, syncs eduNews into dashboard-tasks-source.json,
updates operations.md checklist, then rebuilds dashboard.

Usage:
  python3 edu_news_refresh.py           # refresh (default)
  python3 edu_news_refresh.py --clear   # after recording EDU news
  python3 edu_news_refresh.py --dry-run # print candidates, no writes
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

VAULT = Path(
    os.environ.get(
        "VAULT_PATH",
        Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC",
    )
)
TASKS_JSON = Path(
    os.environ.get("LEGACY_TASKS", VAULT / "00-System/dashboard-tasks-source.json")
)
TOPICS_JSON = VAULT / "00-System/edu-news-topics.json"
OPERATIONS_MD = VAULT / "02-PROJEKTY/operations.md"
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

POSITIVE_RE = re.compile(
    r"\b(nasazen|spuštěn|opraven|hotov|dokončen|rollout|integrac|formulář|universe|rb universe|proces|tým|akadem)\b",
    re.I,
)

OPS2_TOPICS_MARKER = re.compile(
    r"<!-- edu-news-topics:start -->.*?<!-- edu-news-topics:end -->",
    re.DOTALL,
)


def _prague_today() -> date:
    return datetime.now(TZ).date()


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
    return None


def _slug_title(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    slug_m = re.search(r"^\*\*Slug\*\*:\s*`([^`]+)`", text, re.MULTILINE)
    title_m = re.search(r"^#\s+Téma:\s*(.+)$", text, re.MULTILINE)
    slug = slug_m.group(1) if slug_m else path.stem
    title = title_m.group(1).strip() if title_m else slug
    return slug, title


def collect_hotovo_candidates(cutoff: date) -> list[dict]:
    out: list[dict] = []
    proj_dir = VAULT / "02-PROJEKTY"
    if not proj_dir.is_dir():
        return out
    for md in sorted(proj_dir.glob("*.md")):
        if md.name.startswith("_") or md.name.startswith("._"):
            continue
        slug, proj_name = _slug_title(md)
        if slug in EXCLUDE_SLUGS:
            continue
        text = md.read_text(encoding="utf-8")
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
            if completed and completed < cutoff:
                continue
            if EXCLUDE_NAME_RE.search(title):
                continue
            one_liner = re.sub(r"\s+", " ", block.strip().split("\n")[0] if block.strip() else "")
            one_liner = re.sub(r"_\([^)]*\)_", "", one_liner).strip()[:200]
            if not one_liner:
                one_liner = title
            out.append(
                {
                    "key": f"{slug}:{tid}",
                    "title": title,
                    "oneLiner": one_liner,
                    "proj": slug,
                    "projName": proj_name,
                    "taskId": tid,
                    "source": "hotovo",
                    "completed": (completed or _prague_today()).isoformat(),
                    "kind": "done",
                }
            )
    return out


def collect_progress_candidates(tasks: list[dict]) -> list[dict]:
    """Tasks with most subtasks done and decent ICE — good 'work in progress' stories."""
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
        done_n = sum(1 for c in actionable if c.get("d"))
        ratio = done_n / len(actionable)
        if ratio < 0.5:
            continue
        ice = t.get("ice") or {}
        i, c, e = ice.get("i", 5), ice.get("c", 5), max(ice.get("e", 5), 1)
        if (i * c) / e < 5.0:
            continue
        tid = t.get("id") or ""
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


def merge_topics(existing: list[dict], fresh: list[dict]) -> list[dict]:
    by_key: dict[str, dict] = {}
    for t in existing:
        k = t.get("key")
        if k:
            by_key[k] = t
    for t in fresh:
        k = t.get("key")
        if not k:
            continue
        prev = by_key.get(k)
        if prev:
            prev.update({kk: vv for kk, vv in t.items() if vv is not None})
            prev["updated"] = datetime.now(TZ).isoformat(timespec="seconds")
        else:
            t["added"] = datetime.now(TZ).isoformat(timespec="seconds")
            by_key[k] = t
    return list(by_key.values())


def rank_topics(topics: list[dict], tasks: list[dict]) -> list[dict]:
    today = _prague_today()
    cutoff = today - timedelta(days=LOOKBACK_DAYS)
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
    if TASKS_JSON.exists():
        return json.loads(TASKS_JSON.read_text(encoding="utf-8"))
    return {"version": 1, "proj_order": [], "projects": {}, "tasks": []}


def load_topics_state() -> dict:
    if TOPICS_JSON.exists():
        try:
            return json.loads(TOPICS_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"version": 1, "topics": []}


def save_topics_state(topics: list[dict]) -> None:
    TOPICS_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "updated": datetime.now(TZ).isoformat(timespec="seconds"),
        "topics": topics,
    }
    TOPICS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_to_tasks_json(topics: list[dict]) -> None:
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
    TASKS_JSON.parent.mkdir(parents=True, exist_ok=True)
    TASKS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def patch_operations_md(topics: list[dict]) -> bool:
    if not OPERATIONS_MD.exists():
        return False
    text = OPERATIONS_MD.read_text(encoding="utf-8")
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
    OPERATIONS_MD.write_text(new_text, encoding="utf-8")
    return True


def llm_rerank(candidates: list[dict]) -> list[dict] | None:
    """Optional Anthropic re-rank when ANTHROPIC_API_KEY is set."""
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
    cron_dir = Path(__file__).resolve().parent
    if str(cron_dir) not in sys.path:
        sys.path.insert(0, str(cron_dir))
    import build_dashboard

    build_dashboard.main()


def clear_all() -> None:
    save_topics_state([])
    sync_to_tasks_json([])
    patch_operations_md([])
    print("edu_news: cleared topics")


def refresh(*, dry_run: bool = False) -> list[dict]:
    today = _prague_today()
    cutoff = today - timedelta(days=LOOKBACK_DAYS)
    tasks_data = load_tasks_data()
    tasks = tasks_data.get("tasks", [])

    fresh = collect_hotovo_candidates(cutoff)
    fresh.extend(collect_progress_candidates(tasks))
    state = load_topics_state()
    merged = merge_topics(state.get("topics", []), fresh)
    ranked = rank_topics(merged, tasks)
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
        print("edu_news: updated", OPERATIONS_MD)
    rebuild_dashboard()
    return ranked


def main() -> None:
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
