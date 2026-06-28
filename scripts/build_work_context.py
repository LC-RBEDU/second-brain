#!/usr/bin/env python3
"""Build work-context bundles with progressive layering (VC7-7).

Project-scoped (persisted):
  python3 scripts/build_work_context.py <slug>
  python3 scripts/build_work_context.py --all

Task-scoped (ephemeral stdout):
  python3 scripts/build_work_context.py --task <ID>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("ERROR: pip3 install pyyaml\n")
    sys.exit(1)

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from build_agent_context import (  # noqa: E402
    DEFAULT_VAULT,
    HUB_TITLE_RE,
    TaskInfo,
    collect_projects,
    collect_tasks,
    parse_frontmatter,
    _list_str,
)
from vault_reference import (  # noqa: E402
    MAX_LAYER_B_CHARS,
    MAX_LAYER_B_NODES,
    extract_references_from_material,
    extract_references_from_task,
    load_reference_index,
    material_summary,
    parse_wikilinks,
    resolve_path,
    section_text,
    strip_wikilink,
)

MAX_BODY_CHARS = 500_000  # overall cap for persisted bundles; layer A uncapped per focus task


@dataclass
class GraphNode:
    key: str
    rel_path: str | None = None
    node_type: str = "unknown"
    layer: str = "B"  # A | B
    discovered_from: str = ""
    relevance: float = 0.0
    summary: str = ""
    full_body: str = ""
    error: str = ""


@dataclass
class AssemblyResult:
    lines: list[str] = field(default_factory=list)
    layer_a: list[str] = field(default_factory=list)
    layer_b: list[str] = field(default_factory=list)
    omitted_budget: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _task_by_id(vault: Path, task_id: str) -> TaskInfo | None:
    for t in collect_tasks(vault, archive=False) + collect_tasks(vault, archive=True):
        if t.id == task_id:
            return t
    return None


def _hub_for_slug(vault: Path, slug: str) -> tuple[Path, dict, str] | None:
    for hub in (vault / "02-PROJEKTY").glob("*.md"):
        try:
            text = hub.read_text(encoding="utf-8")
        except OSError:
            continue
        fm, body = parse_frontmatter(text)
        if (fm.get("type") or "").lower() != "project":
            continue
        if (fm.get("slug") or hub.stem) == slug:
            return hub, fm, body
    return None


def _relevance_score(
    *,
    same_project: bool,
    explicit_material: bool,
    in_body: bool,
    updated: str | None,
    task_priority: float,
    hop: int,
) -> float:
    score = 100.0 - hop * 15
    if same_project:
        score += 30
    if explicit_material:
        score += 25
    if in_body:
        score += 10
    if updated:
        score += 5
    score += min(task_priority, 20)
    return score


def _resolve_key_to_path(vault: Path, key: str, ref_index: dict) -> Path | None:
    key = strip_wikilink(key)
    nodes = ref_index.get("nodes", {})
    for nid, meta in nodes.items():
        if nid == key or Path(meta.get("rel_path", "")).stem == key:
            p = vault / meta["rel_path"]
            if p.exists():
                return p
    return resolve_path(vault, key)


def _expand_graph(
    vault: Path,
    *,
    seeds: list[tuple[str, str, float]],
    focus_slug: str,
    focus_task_id: str | None,
    ref_index: dict,
    max_hops: int = 6,
    max_nodes: int = 120,
) -> dict[str, GraphNode]:
    graph: dict[str, GraphNode] = {}
    q: deque[tuple[str, str, int, float]] = deque()
    enqueued: set[str] = set()

    for key, discovered_from, rel in seeds:
        k = strip_wikilink(key)
        if k and k not in enqueued:
            enqueued.add(k)
            q.append((k, discovered_from, 0, rel))

    while q and len(graph) < max_nodes:
        key, discovered_from, hop, rel = q.popleft()
        if not key or key in graph:
            continue
        if hop > max_hops:
            continue

        path = _resolve_key_to_path(vault, key, ref_index)
        if not path or not path.exists():
            graph[key] = GraphNode(
                key=key,
                discovered_from=discovered_from,
                error=f"nerozpoznáno: {key}",
            )
            continue

        try:
            rel_path = str(path.relative_to(vault))
        except ValueError:
            rel_path = str(path)

        in_archive = "/07-ARCHIV/" in rel_path
        if in_archive and hop > 1:
            continue

        try:
            raw = path.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(raw)
        except (OSError, UnicodeDecodeError) as e:
            graph[key] = GraphNode(key=key, rel_path=rel_path, error=str(e))
            continue

        node_type = str(fm.get("type") or "unknown").lower()
        slug = fm.get("slug") or ""
        is_focus = focus_task_id and key == focus_task_id
        is_focus_material = focus_task_id and any(
            strip_wikilink(m) == key or Path(rel_path).stem == strip_wikilink(m)
            for t in [focus_task_id]
            for m in (_task_materials(vault, focus_task_id) or [])
        )

        layer = "A" if is_focus or (hop == 0 and node_type == "task" and key == focus_task_id) else "B"
        if node_type == "task" and key == focus_task_id:
            layer = "A"
        elif node_type == "material" and focus_task_id:
            mats = _task_materials(vault, focus_task_id) or []
            if any(strip_wikilink(m) in (key, Path(rel_path).stem) for m in mats):
                layer = "A"

        same_project = str(slug) == focus_slug or focus_slug in rel_path
        node = GraphNode(
            key=key,
            rel_path=rel_path,
            node_type=node_type,
            layer=layer,
            discovered_from=discovered_from,
            relevance=rel,
            full_body=body,
            summary=material_summary(body) if node_type in ("material", "attachment") else material_summary(body, 2000),
        )
        graph[key] = node

        if node_type == "task":
            refs = extract_references_from_task(fm, body)
        elif node_type in ("material", "attachment"):
            refs = extract_references_from_material(fm, body)
        else:
            refs = parse_wikilinks(body)

        for ref in refs:
            rk = strip_wikilink(ref)
            if not rk or rk in enqueued:
                continue
            enqueued.add(rk)
            child_rel = _relevance_score(
                same_project=same_project,
                explicit_material=rk in _list_str(fm.get("materials")),
                in_body=rk in body,
                updated=fm.get("updated"),
                task_priority=0,
                hop=hop + 1,
            )
            q.append((rk, key, hop + 1, child_rel))

        for back_src in ref_index.get("backlinks", {}).get(key, [])[:20]:
            bk = strip_wikilink(back_src)
            if bk and bk not in enqueued:
                enqueued.add(bk)
                q.append((bk, f"backlink:{key}", hop + 1, rel - 5))

    return graph


def _task_materials(vault: Path, task_id: str) -> list[str] | None:
    t = _task_by_id(vault, task_id)
    return t.materials if t else None


def assemble_context(
    vault: Path,
    *,
    slug: str,
    focus_task_id: str | None = None,
) -> AssemblyResult:
    result = AssemblyResult()
    ref_index = load_reference_index(vault)
    hub_data = _hub_for_slug(vault, slug)
    if not hub_data:
        result.errors.append(f"Neznámý slug: {slug}")
        return result

    hub_path, hub_fm, hub_body = hub_data
    title_m = HUB_TITLE_RE.search(hub_body)
    title = title_m.group(1).strip() if title_m else hub_path.stem

    lines = [
        "---",
        f"slug: {slug}",
        f"focus_task: {focus_task_id or ''}",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        "type: work-context",
        "---",
        "",
        f"# Work context — {title}",
        "",
    ]

    # Layer A — charter
    for sec in (
        "## Cíl",
        "## Scope",
        "## Definition of done",
        "## People",
        "## Kontext",
        "## Zdroje dat",
        "## Otevřené otázky",
    ):
        content = section_text(hub_body, sec)
        if content:
            lines.extend([sec, "", content, ""])
            result.layer_a.append(sec)

    active = [t for t in collect_tasks(vault, archive=False) if t.slug == slug and t.status != "Done"]

    seeds: list[tuple[str, str, float]] = []
    if focus_task_id:
        seeds.append((focus_task_id, "focus", 200.0))
        t = _task_by_id(vault, focus_task_id)
        if t:
            for m in t.materials or []:
                seeds.append((strip_wikilink(m), focus_task_id, 180.0))
            if t.source:
                seeds.append((strip_wikilink(str(t.source)), focus_task_id, 170.0))
    else:
        for t in active:
            seeds.append((t.id, "project-active", 50.0 + t.priority_score))

    graph = _expand_graph(
        vault,
        seeds=seeds,
        focus_slug=slug,
        focus_task_id=focus_task_id,
        ref_index=ref_index,
    )

    # Promote focus task + its materials to layer A
    if focus_task_id:
        if focus_task_id in graph:
            graph[focus_task_id].layer = "A"
        t = _task_by_id(vault, focus_task_id)
        if t:
            for m in t.materials or []:
                mk = strip_wikilink(m)
                if mk in graph:
                    graph[mk].layer = "A"
                for k, n in graph.items():
                    if n.rel_path and mk in (k, Path(n.rel_path).stem):
                        n.layer = "A"

    lines.extend(["## Vrstva A — plný kontext", ""])

    if focus_task_id and focus_task_id in graph:
        n = graph[focus_task_id]
        if n.full_body:
            lines.extend([f"### Task {focus_task_id}", "", n.full_body, ""])
            result.layer_a.append(focus_task_id)
    elif not focus_task_id:
        lines.extend(["### Aktivní tasky (těla)", ""])
        for t in sorted(active, key=lambda x: x.id):
            tp = vault / t.rel_path
            if not tp.exists():
                continue
            try:
                _, body = parse_frontmatter(tp.read_text(encoding="utf-8"))
            except OSError:
                continue
            lines.extend([f"#### {t.id} — {t.title}", "", body.strip(), ""])
            result.layer_a.append(t.id)

    layer_b_nodes = sorted(
        [n for n in graph.values() if n.layer == "B" and not n.error],
        key=lambda n: -n.relevance,
    )
    b_chars = 0
    b_count = 0
    lines.extend(["## Vrstva B — souhrn + pointer", ""])
    for n in layer_b_nodes:
        if b_count >= MAX_LAYER_B_NODES:
            result.omitted_budget.append(n.key)
            continue
        block = f"### {n.key}\n\n**Cesta:** `{n.rel_path}`\n**Objeveno z:** {n.discovered_from}\n\n{n.summary}\n"
        if b_chars + len(block) > MAX_LAYER_B_CHARS:
            result.omitted_budget.append(n.key)
            continue
        lines.append(block)
        b_chars += len(block)
        b_count += 1
        result.layer_b.append(n.key)

    for n in graph.values():
        if n.error:
            result.errors.append(f"{n.key}: {n.error}")

    lines.extend(["## Inclusion report", ""])
    lines.append(f"- Vrstva A ({len(result.layer_a)}): {', '.join(result.layer_a[:20])}")
    lines.append(f"- Vrstva B ({len(result.layer_b)}): {', '.join(result.layer_b[:20])}")
    if result.omitted_budget:
        lines.append(f"- Vynecháno (rozpočet): {', '.join(result.omitted_budget[:30])}")
    if result.errors:
        lines.extend(["", "## Nevyřešené / chyby", ""])
        for e in result.errors:
            lines.append(f"- {e}")

    result.lines = lines
    return result


def build_work_context_md(vault: Path, slug: str) -> str | None:
    asm = assemble_context(vault, slug=slug, focus_task_id=None)
    if asm.errors and not asm.lines:
        return None
    text = "\n".join(asm.lines)
    if len(text) > MAX_BODY_CHARS:
        text = text[: MAX_BODY_CHARS - 40] + "\n\n… _(celkový strop)_\n"
    return text


def build_task_context_md(vault: Path, task_id: str) -> str | None:
    t = _task_by_id(vault, task_id)
    if not t:
        return None
    asm = assemble_context(vault, slug=t.slug, focus_task_id=task_id)
    return "\n".join(asm.lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", nargs="?", default="")
    parser.add_argument("--task", metavar="ID", default="", help="Task-scoped ephemeral bundle")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.task:
        md = build_task_context_md(args.vault, args.task)
        if not md:
            sys.stderr.write(f"ERROR: task not found: {args.task}\n")
            return 1
        print(md)
        return 0

    out_dir = args.vault / "00-System" / "Work-Context"
    slugs: list[str] = []
    if args.all:
        slugs = [p.slug for p in collect_projects(args.vault) if p.status in ("active", "")]
    elif args.slug:
        slugs = [args.slug]
    else:
        parser.print_help()
        return 1

    n = 0
    for slug in slugs:
        md = build_work_context_md(args.vault, slug)
        if not md:
            sys.stderr.write(f"SKIP unknown slug: {slug}\n")
            continue
        out = out_dir / f"{slug}.md"
        stale = out_dir / f"{slug}.stale"
        if stale.exists():
            stale.unlink(missing_ok=True)
        if args.dry_run:
            print(f"DRY {out}: {len(md)} chars")
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            out.write_text(md, encoding="utf-8")
            print(f"work-context: {slug} → {out.relative_to(args.vault)}")
        n += 1
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
