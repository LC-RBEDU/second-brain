#!/usr/bin/env python3
"""Task hygiene audit — PREVIEW ONLY, no writes.

Scans 02-PROJEKTY/<slug>/tasks/*.md (live) + 07-ARCHIV/tasks-done/<slug>/*.md
(archive) and detects:
  K1 — ID collisions (same `id` across 2+ files)
  K2 — Cross-project prefix mismatch (id prefix != slug's id_prefix in mapping)
  K3 — Title fuzzy duplicity (ratio >= 0.7, same slug live tasks)
  K4 — Lifecycle anomalies (missing id/title/slug, status Done not archived, etc.)

Outputs a structured markdown report to stdout.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

VAULT = Path(os.environ.get("SECOND_BRAIN_VAULT") or os.environ.get("SB_VAULT_PATH") or (Path.home() / "GitHub" / "second-brain-vault"))
OBS = VAULT
PROJ_DIR = OBS / "02-PROJEKTY"
ARCH_DIR = OBS / "07-ARCHIV" / "tasks-done"
MAPPING_PATH = OBS / "00-System" / "migration-mapping.json"

FRESH_THRESHOLD_SECS = 5 * 60  # skip tasks edited < 5 min ago (apply DEEP race)


def load_mapping() -> dict[str, dict[str, Any]]:
    with MAPPING_PATH.open(encoding="utf-8") as f:
        rows = json.load(f)
    return {r["slug"]: r for r in rows}


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    """Returns (frontmatter_dict, body_text, error)."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return None, "", f"read_error: {e}"
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text, "no_frontmatter"
    raw = m.group(1)
    body = text[m.end():]
    try:
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return None, body, "frontmatter_not_dict"
        return data, body, None
    except yaml.YAMLError as e:
        return None, body, f"yaml_error: {e}".replace("\n", " ")[:200]


WORD_RE = re.compile(r"\w+", re.UNICODE)
CZECH_STOPWORDS = {
    "a", "i", "o", "u", "v", "z", "k", "s", "se", "si", "do", "na", "po", "pro",
    "od", "ve", "ze", "že", "by", "to", "ten", "ta", "je", "jsi", "jsme", "jsou",
    "být", "and", "or", "the", "of", "for", "in", "to", "with", "ze", "že",
    "také", "ale", "nebo", "už", "jak", "co", "kdo", "kde", "kdy", "proč",
    "—", "-",
}


def normalize_title(title: str) -> str:
    """Strip recurring suffix, emoji, leading prefix, lowercase."""
    if not title:
        return ""
    t = title
    t = re.sub(r"♻️.*$", "", t)
    t = re.sub(r"\s*\(.*?\)\s*$", "", t)
    t = t.lower().strip()
    return t


def title_tokens(title: str) -> set[str]:
    norm = normalize_title(title)
    words = {w for w in WORD_RE.findall(norm)}
    return {w for w in words if w not in CZECH_STOPWORDS and len(w) >= 2}


def title_similarity(a: str, b: str) -> float:
    """Combined ratio: max(SequenceMatcher, Jaccard tokens)."""
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    seq = SequenceMatcher(None, na, nb).ratio()
    ta, tb = title_tokens(a), title_tokens(b)
    if not ta or not tb:
        jacc = 0.0
    else:
        jacc = len(ta & tb) / len(ta | tb)
    return max(seq, jacc)


def collect_tasks() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Walks PROJ_DIR and ARCH_DIR, returns (live, archive) task records."""
    live: list[dict[str, Any]] = []
    archive: list[dict[str, Any]] = []

    if PROJ_DIR.is_dir():
        for slug_dir in sorted(PROJ_DIR.iterdir()):
            if not slug_dir.is_dir():
                continue
            tasks_dir = slug_dir / "tasks"
            if not tasks_dir.is_dir():
                continue
            for md in sorted(tasks_dir.glob("*.md")):
                rec = read_task(md, source="live", folder_slug=slug_dir.name)
                if rec:
                    live.append(rec)

    if ARCH_DIR.is_dir():
        for slug_dir in sorted(ARCH_DIR.iterdir()):
            if not slug_dir.is_dir():
                continue
            for md in sorted(slug_dir.glob("*.md")):
                rec = read_task(md, source="archive", folder_slug=slug_dir.name)
                if rec:
                    archive.append(rec)

    return live, archive


def read_task(md: Path, *, source: str, folder_slug: str) -> dict[str, Any] | None:
    stat = md.stat()
    age_secs = time.time() - stat.st_mtime
    fm, body, err = parse_frontmatter(md)
    return {
        "path": md,
        "rel": str(md.relative_to(VAULT)),
        "filename": md.name,
        "source": source,
        "folder_slug": folder_slug,
        "mtime": stat.st_mtime,
        "age_secs": age_secs,
        "fresh": age_secs < FRESH_THRESHOLD_SECS,
        "fm": fm,
        "body": body,
        "yaml_error": err,
    }


def id_prefix(task_id: str) -> str:
    m = re.match(r"^([A-Z]+)\d+", task_id or "")
    return m.group(1) if m else ""


def id_num(task_id: str) -> int | None:
    m = re.match(r"^[A-Z]+(\d+)", task_id or "")
    return int(m.group(1)) if m else None


def is_recurring_archive(filename: str) -> bool:
    """Recurring archive convention: <ID>-YYYY-MM-DD.md (allowed)."""
    return bool(re.match(r"^[A-Z]+\d+-\d{4}-\d{2}-\d{2}\.md$", filename))


def short(p: str) -> str:
    """Shorten path for report — drop OBSIDIAN/ prefix."""
    return p.replace("OBSIDIAN/", "")


# ──────────────────────────────────────────────────────────────────────────────


def audit() -> None:
    mapping = load_mapping()
    live, archive = collect_tasks()
    all_tasks = live + archive

    # Find orphan/unmapped project folders
    orphan_folders: list[dict[str, Any]] = []
    if PROJ_DIR.is_dir():
        for slug_dir in sorted(PROJ_DIR.iterdir()):
            if not slug_dir.is_dir():
                continue
            slug = slug_dir.name
            tasks_dir = slug_dir / "tasks"
            task_count = (
                len(list(tasks_dir.glob("*.md"))) if tasks_dir.is_dir() else 0
            )
            if slug not in mapping:
                orphan_folders.append({
                    "slug": slug,
                    "task_count": task_count,
                    "has_tasks_dir": tasks_dir.is_dir(),
                })

    fresh_skipped = [t for t in all_tasks if t["fresh"]]
    fresh_paths = {t["rel"] for t in fresh_skipped}

    scan_ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── K1: ID collisions ──────────────────────────────────────────────────
    id_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in all_tasks:
        if t["yaml_error"]:
            continue
        if t["rel"] in fresh_paths:
            continue
        fm = t["fm"] or {}
        tid = (fm.get("id") or "").strip()
        if tid:
            id_index[tid].append(t)
    collisions = {tid: ts for tid, ts in id_index.items() if len(ts) >= 2}

    # ── K2: Cross-project prefix mismatch ──────────────────────────────────
    mismatches: list[dict[str, Any]] = []
    for t in all_tasks:
        if t["yaml_error"]:
            continue
        if t["rel"] in fresh_paths:
            continue
        fm = t["fm"] or {}
        tid = (fm.get("id") or "").strip()
        slug = (fm.get("slug") or "").strip() or t["folder_slug"]
        if not tid or not slug:
            continue
        if slug not in mapping:
            continue
        expected = mapping[slug]["id_prefix"]
        actual = id_prefix(tid)
        if actual and actual != expected:
            # Folder vs frontmatter slug mismatch sub-case
            mismatches.append({
                "task": t,
                "id": tid,
                "fm_slug": fm.get("slug"),
                "folder_slug": t["folder_slug"],
                "expected_prefix": expected,
                "actual_prefix": actual,
            })

    # Folder vs frontmatter slug mismatch
    folder_fm_slug_mismatch: list[dict[str, Any]] = []
    for t in all_tasks:
        if t["yaml_error"]:
            continue
        if t["rel"] in fresh_paths:
            continue
        fm = t["fm"] or {}
        fm_slug = (fm.get("slug") or "").strip()
        folder = t["folder_slug"]
        if fm_slug and folder and fm_slug != folder:
            folder_fm_slug_mismatch.append({
                "task": t,
                "fm_slug": fm_slug,
                "folder_slug": folder,
                "id": (fm.get("id") or "").strip(),
            })

    # ── K3: Title duplicity (live, both same-slug AND cross-project) ───────
    title_pairs_same: list[dict[str, Any]] = []
    title_pairs_cross: list[dict[str, Any]] = []
    live_titled = [
        t for t in live
        if not t["yaml_error"]
        and t["rel"] not in fresh_paths
        and ((t["fm"] or {}).get("title") or "").strip()
    ]
    seen_pairs: set[tuple[str, str]] = set()
    for i in range(len(live_titled)):
        for j in range(i + 1, len(live_titled)):
            a, b = live_titled[i], live_titled[j]
            ratio = title_similarity(
                a["fm"].get("title", ""), b["fm"].get("title", "")
            )
            if ratio < 0.7:
                continue
            key = tuple(sorted((a["rel"], b["rel"])))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            entry = {
                "a": a,
                "b": b,
                "ratio": round(ratio, 3),
                "same_slug": a["folder_slug"] == b["folder_slug"],
            }
            if entry["same_slug"]:
                entry["slug"] = a["folder_slug"]
                title_pairs_same.append(entry)
            else:
                title_pairs_cross.append(entry)

    # Also: same `source:` field across 2+ live tasks (any slug)
    source_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in live:
        if t["yaml_error"] or t["rel"] in fresh_paths:
            continue
        fm = t["fm"] or {}
        src = (fm.get("source") or "").strip()
        if src and src not in {"manual", "INBOX", "inbox", "slack"}:
            source_groups[src].append(t)
    source_dupes = {k: v for k, v in source_groups.items() if len(v) >= 2}

    # ── K4: Lifecycle anomalies ────────────────────────────────────────────
    anomalies: list[dict[str, Any]] = []
    for t in all_tasks:
        if t["rel"] in fresh_paths:
            continue
        if t["yaml_error"]:
            anomalies.append({"task": t, "kind": "yaml_error", "detail": t["yaml_error"]})
            continue
        fm = t["fm"] or {}
        if not fm.get("id"):
            anomalies.append({"task": t, "kind": "missing_id", "detail": ""})
        if not fm.get("title"):
            anomalies.append({"task": t, "kind": "missing_title", "detail": ""})
        slug = fm.get("slug")
        if not slug:
            anomalies.append({"task": t, "kind": "missing_slug", "detail": ""})
        elif slug not in mapping:
            anomalies.append({"task": t, "kind": "invalid_slug", "detail": f"slug={slug}"})

        # Done in live for > 90 days
        if t["source"] == "live":
            status = (fm.get("status") or "").strip()
            if status == "Done":
                done_at = fm.get("done_at") or fm.get("doneAt") or fm.get("completed_at")
                anomalies.append({
                    "task": t,
                    "kind": "done_in_live",
                    "detail": f"done_at={done_at!r}",
                })

        # Recurring filename anomaly
        if fm.get("recurring"):
            fn = t["filename"]
            if t["source"] == "live":
                # canonical: <ID> — <Title>.md OR <ID>.md
                if not re.match(r"^[A-Z]+\d+( — .+)?\.md$", fn) and not re.match(
                    r"^[A-Z]+\d+\.md$", fn
                ):
                    anomalies.append({
                        "task": t,
                        "kind": "recurring_filename_non_canonical",
                        "detail": fn,
                    })

    # ── Render report ─────────────────────────────────────────────────────
    lines: list[str] = []
    P = lines.append

    P(f"# Task hygiene audit — {scan_ts}")
    P("")
    P("## Souhrn")
    P(f"- Skenováno: {len(all_tasks)} tasků ({len(live)} live + {len(archive)} archive)")
    P(f"- Projekty (folders): {len({t['folder_slug'] for t in all_tasks})}")
    P(f"- Skipped (mtime < 5 min, in-flight DEEP apply): {len(fresh_skipped)}")
    P(f"- **K1 — ID kolize:** {len(collisions)}")
    P(f"- **K2 — Cross-project prefix mismatch:** {len(mismatches)}"
      f" (+ {len(folder_fm_slug_mismatch)} folder↔frontmatter slug mismatch)")
    P(f"- **K3 — Title duplicity (ratio ≥ 0.7):** "
      f"{len(title_pairs_same)} same-slug + {len(title_pairs_cross)} cross-project"
      f" (+ {len(source_dupes)} skupin se stejným `source:`)")
    P(f"- **K4 — Lifecycle anomalie:** {len(anomalies)}")
    P(f"- **Orphan/unmapped project folders:** {len(orphan_folders)}")
    P("")

    if orphan_folders:
        P("### Orphan project folders (ne v migration-mapping.json)")
        for of in orphan_folders:
            P(f"- `02-PROJEKTY/{of['slug']}/` — tasks: {of['task_count']},"
              f" has_tasks_dir: {of['has_tasks_dir']}")
        P("")

    if fresh_skipped:
        P("> Skipped recently modified files (in-flight apply DEEP):")
        for t in fresh_skipped:
            age = int(t["age_secs"])
            P(f"> - `{short(t['rel'])}` (age {age}s)")
        P("")

    # ── K1
    P("## Kategorie 1 — ID kolize")
    P("")
    if not collisions:
        P("_Žádné nalezeny._")
    else:
        for tid, ts in sorted(collisions.items()):
            P(f"### ID `{tid}` × {len(ts)} souborů")
            for t in ts:
                fm = t["fm"] or {}
                status = fm.get("status", "?")
                title = (fm.get("title") or "")[:80]
                P(f"- `{short(t['rel'])}` ({t['source']}, status: {status})"
                  f" — {title}")
            # Heuristic recommendation
            slugs = {(t['fm'] or {}).get('slug') for t in ts}
            sources = {t['source'] for t in ts}
            if len(slugs) == 1 and sources == {"live"}:
                P("**Doporučení:** REAL collision — 2 live tasky se stejným ID v stejném"
                  " projektu. Renumber novější na další volné `<prefix><N>`.")
            elif sources == {"live", "archive"} or sources == {"archive", "live"}:
                P("**Doporučení:** live vs archive — pokud jsou různá témata, OK"
                  " (archive = historie). Pokud stejné, ARCHIVE je správné, live je"
                  " duplicate → smazat live.")
            else:
                P("**Doporučení:** zkontroluj témata; pokud stejná, sloučit; jinak re-ID.")
            P("")

    # ── K2
    P("## Kategorie 2 — Cross-project prefix mismatch")
    P("")
    if not mismatches and not folder_fm_slug_mismatch:
        P("_Žádné nalezeny._")
    else:
        for m in mismatches:
            t = m["task"]
            fm = t["fm"] or {}
            P(f"### `{t['filename']}` v `{t['folder_slug']}/`")
            P(f"- **Path:** `{short(t['rel'])}`")
            P(f"- **Frontmatter:** `id: {m['id']}`, `slug: {m['fm_slug']!r}`,"
              f" `project: {fm.get('project')!r}`")
            P(f"- **Status:** {fm.get('status', '?')}")
            P(f"- **Mismatch:** folder/slug `{m['folder_slug']}` má prefix"
              f" `{m['expected_prefix']}`, ID `{m['id']}` má prefix `{m['actual_prefix']}`.")
            other = next(
                (k for k, v in mapping.items() if v["id_prefix"] == m["actual_prefix"]),
                None,
            )
            if other:
                P(f"- **Hypotéza:** task patří do projektu `{other}` (prefix"
                  f" `{m['actual_prefix']}`), byl chybně umístěn / migrován.")
            P("")
        if folder_fm_slug_mismatch:
            P("### Folder ↔ frontmatter slug mismatch")
            for fm_mm in folder_fm_slug_mismatch:
                t = fm_mm["task"]
                P(f"- `{short(t['rel'])}` — folder `{fm_mm['folder_slug']}`,"
                  f" frontmatter `slug: {fm_mm['fm_slug']}`, ID `{fm_mm['id']}`")
            P("")

    # ── K3
    P("## Kategorie 3 — Title duplicity (ratio ≥ 0.7)")
    P("")
    if title_pairs_cross:
        P("### Cross-project (různé slugy, podezření na rozdvojený task)")
        P("")
        title_pairs_cross.sort(key=lambda p: -p["ratio"])
        for p in title_pairs_cross:
            a, b = p["a"], p["b"]
            P(f"#### `{a['folder_slug']}` × `{b['folder_slug']}` (ratio {p['ratio']})")
            for x in (a, b):
                fm = x["fm"] or {}
                P(f"- `{short(x['rel'])}` — id `{fm.get('id')}`, status"
                  f" `{fm.get('status')}`")
                P(f"  - title: {fm.get('title')!r}")
                src = fm.get("source") or ""
                if src:
                    P(f"  - source: `{src[:120]}`")
            P("")
    if title_pairs_same:
        P("### Same-slug (jeden projekt, podezření na near-duplicate)")
        P("")
        title_pairs_same.sort(key=lambda p: -p["ratio"])
        for p in title_pairs_same:
            a, b = p["a"], p["b"]
            P(f"#### Pár (slug `{p['slug']}`, ratio {p['ratio']})")
            for x in (a, b):
                fm = x["fm"] or {}
                P(f"- `{x['filename']}` — id `{fm.get('id')}`, status"
                  f" `{fm.get('status')}`, source `{fm.get('source')}`")
                P(f"  - title: {fm.get('title')!r}")
            P("")
    if not title_pairs_same and not title_pairs_cross:
        P("_Žádné nalezeny._")

    if source_dupes:
        P("### Stejný `source:` field (různé tasky, kandidáti na cron+manual race)")
        for src, ts in source_dupes.items():
            P(f"- `source: {src}` × {len(ts)}:")
            for t in ts:
                fm = t["fm"] or {}
                P(f"  - `{short(t['rel'])}` — id `{fm.get('id')}`, title"
                  f" {(fm.get('title') or '')[:60]!r}")
        P("")

    # ── K4
    P("## Kategorie 4 — Lifecycle anomalie")
    P("")
    if not anomalies:
        P("_Žádné nalezeny._")
    else:
        by_kind: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for a in anomalies:
            by_kind[a["kind"]].append(a)
        for kind in sorted(by_kind):
            ts = by_kind[kind]
            P(f"### `{kind}` × {len(ts)}")
            for a in ts:
                t = a["task"]
                fm = t["fm"] or {}
                extra = f" — {a['detail']}" if a.get("detail") else ""
                P(f"- `{short(t['rel'])}` (id `{fm.get('id')}`,"
                  f" status `{fm.get('status')}`){extra}")
            P("")

    # ── Apply table
    P("## Doporučení k apply (preview)")
    P("")
    P("| # | Akce | Cíl | Důvod | User confirm |")
    P("|---|------|-----|-------|--------------|")
    n = 0
    # K1 recommendations
    for tid, ts in sorted(collisions.items()):
        slugs = {(t['fm'] or {}).get('slug') for t in ts}
        sources = {t['source'] for t in ts}
        if len(slugs) == 1 and sources == {"live"}:
            n += 1
            paths = "; ".join(short(t["rel"]) for t in ts)
            P(f"| {n} | RE-ID | jedna z `{paths}` | K1 collision in live |  |")
        elif {"live", "archive"} == sources:
            live_t = next(t for t in ts if t["source"] == "live")
            n += 1
            P(f"| {n} | REVIEW | `{short(live_t['rel'])}` | K1 live vs archive, ověřit téma |  |")
    # K2 recommendations
    for m in mismatches:
        t = m["task"]
        other = next(
            (k for k, v in mapping.items() if v["id_prefix"] == m["actual_prefix"]),
            None,
        )
        n += 1
        if other:
            P(f"| {n} | MOVE/RE-ID | `{short(t['rel'])}` → `{other}/` nebo re-ID na"
              f" `{m['expected_prefix']}<N>` | K2 mismatch (prefix `{m['actual_prefix']}`"
              f" patří `{other}`) |  |")
        else:
            P(f"| {n} | RE-ID | `{short(t['rel'])}` na `{m['expected_prefix']}<N>` |"
              f" K2 mismatch |  |")
    # K3 recommendations
    for p in title_pairs_cross:
        a, b = p["a"], p["b"]
        n += 1
        P(f"| {n} | REVIEW/MERGE | `{a['folder_slug']}/{a['filename']}` ↔"
          f" `{b['folder_slug']}/{b['filename']}` | K3 cross-project duplicate"
          f" (ratio {p['ratio']}) |  |")
    for p in title_pairs_same:
        a, b = p["a"], p["b"]
        n += 1
        P(f"| {n} | REVIEW/MERGE | `{a['filename']}` ↔ `{b['filename']}` | K3"
          f" same-slug near-duplicate (ratio {p['ratio']}, slug `{p['slug']}`) |  |")
    # K4 anomalies (only those needing action)
    for a in anomalies:
        if a["kind"] in {"done_in_live"}:
            continue  # cron handles
        if a["kind"] in {"missing_id", "missing_title", "missing_slug",
                         "invalid_slug", "yaml_error",
                         "recurring_filename_non_canonical"}:
            n += 1
            t = a["task"]
            P(f"| {n} | FIX | `{short(t['rel'])}` | K4 {a['kind']} {a['detail']} |  |")

    P("")
    P("---")
    P("_Scan timestamp: " + scan_ts + " — pokud paralelní subagent dodělal "
      "nové tasky (F20/F21/MO10/OWN5/S11/S12/AF10/RBU*/VC8), tento scan je nezachytil._")

    sys.stdout.write("\n".join(lines))


if __name__ == "__main__":
    audit()
