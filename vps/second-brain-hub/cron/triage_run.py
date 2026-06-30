#!/usr/bin/env python3
"""Scan 01-INBOX (Drive) and write Triage-Pending batch JSON (semi-auto;
approve in Cursor).

Waiting tasks with expired waitUntil are auto-reactivated to ASAP in hub
markdown by build_dashboard.py (then re-synced to dashboard JSON).
Approve in Cursor via agenda-triage PENDING mode — not processed by
this script.

Phase 2 migrace: Veškerý vault I/O probíhá přes lib/drive_io.DriveVault.
Env: VAULT_DRIVE_ID + GOOGLE_DRIVE_OAUTH_JSON (preferred) /
GOOGLE_DRIVE_SA_JSON (fallback).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
_CRON = Path(__file__).resolve().parent
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
if str(_CRON) not in sys.path:
    sys.path.insert(0, str(_CRON))

from drive_io import DriveVault, DriveNotFoundError, credentials_from_env  # noqa: E402
from triage_commitments import (  # noqa: E402
    extract_commitments,
    is_sent_email,
    normalize_proposal,
    purge_dropped_sent_inbox,
    sent_archive_only_proposal,
    sent_business_action_proposal,
)
from triage_complexity import is_complex_source  # noqa: E402
from triage_slack_relevance import (  # noqa: E402
    enrich_proposal_with_slack_meta,
    evaluate_slack_inbox_relevance,
    is_slack_inbox,
    slack_archive_proposal,
)

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))

INBOX_SUBDIRS = ("slack", "sembly", "email", "daily", "Clippings")

PROPOSAL_TYPE_LABELS = {
    "add_task": "Vytažení úkolu",
    "update_task": "Změna stavu úkolu / projektu",
    "archive_only": "Přesun do HOTOVO (bez nového úkolu)",
    "deep_analysis": "Komplexní materiál — DEEP analysis required",
}

DEEP_PLACEHOLDER_BODY = (
    "DEEP analysis required — open in agenda-triage DEEP mode.\n\n"
    "Tento návrh je meta-proposal: zdroj je komplexní (delší materiál, "
    "více headingů / akčních bodů, nebo Sembly přepis). Po otevření v "
    "DEEP režimu skill rozseká zdroj na konkrétní tasky a materiály."
)

SLUG_HINTS = [
    ("ninjabot", "pipedrive-a-dalsi-nastroje"),
    ("rb-universe", "rb-universe-development"),
    ("universe", "rb-universe-development"),
    ("pipedrive", "pipedrive-a-dalsi-nastroje"),
    ("finance", "finance"),
    ("finan", "finance"),
    ("strategy", "strategy"),
    ("strateg", "strategy"),
    ("proces", "firemni-procesy"),
    ("operations", "operations"),
    ("odyssey", "ma-odyssey"),
    ("potlesk", "kratky-potlesk"),
    ("exponential", "exponential-summit"),
    ("vibe", "vibe-coding"),
    ("allfred", "allfred"),
    ("alfred", "allfred"),
    ("owners", "owners"),
    ("network", "rb-network"),
    ("sales", "sales-a-business-development"),
    ("osobni", "osobni"),
    ("osobní", "osobni"),
]

MAPPING_REL = "00-System/migration-mapping.json"

_MAPPING_CACHE: dict[str, dict] | None = None


def load_mapping(vault: DriveVault) -> dict[str, dict]:
    """Load slug → {hub_filename, id_prefix, area} from vault.

    Used to generate target_path + frontmatter for v2 file-per-task proposals.
    """
    global _MAPPING_CACHE
    if _MAPPING_CACHE is not None:
        return _MAPPING_CACHE
    try:
        data, _ = vault.read_json(MAPPING_REL)
    except DriveNotFoundError:
        _MAPPING_CACHE = {}
        return _MAPPING_CACHE
    out: dict[str, dict] = {}
    if isinstance(data, list):
        for entry in data:
            slug = (entry.get("slug") or "").strip()
            if slug:
                out[slug] = entry
    _MAPPING_CACHE = out
    return out


EM_DASH = "\u2014"
SEPARATOR = f" {EM_DASH} "


def _sanitize_title(title: str) -> str:
    """Filesystem + Google-Drive safe rendering of a human-readable title.

    Mirrors `scripts/rename_tasks_to_human_filenames.sanitize_title` and the
    spec in `00-System/Templates/filename-normalization.md`. Preserves
    diacritics and emoji; only replaces FS-hostile chars.
    """
    if not title:
        return ""
    s = title
    s = s.replace("\n", " ").replace("\t", " ").replace("\r", " ")
    s = s.replace(":", " ")
    s = s.replace("/", " -")
    s = s.replace("\\", " -")
    s = s.replace("?", "")
    s = s.replace("*", "")
    s = s.replace("<", "\u2039")
    s = s.replace(">", "\u203a")
    s = s.replace("|", "-")
    s = s.replace('"', "'")
    s = "".join(ch for ch in s if ord(ch) >= 0x20)
    s = re.sub(r" +", " ", s).strip()
    return s


def _task_filename(task_id: str, title: str) -> str:
    """Human-readable task filename: `<ID> — <Title>.md`."""
    sanitized = _sanitize_title(title or "")
    if sanitized:
        return f"{task_id}{SEPARATOR}{sanitized}.md"
    return f"{task_id}.md"


def next_id_for_slug(vault: DriveVault, slug: str, prefix: str) -> str:
    """Scan tasks/ + 07-ARCHIV/tasks-done/<slug>/ for max ID with prefix, return prefix+(max+1)."""
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)[a-z]?")
    max_n = 0
    for rel in (
        f"02-PROJEKTY/{slug}/tasks",
        f"07-ARCHIV/tasks-done/{slug}",
    ):
        try:
            files = vault.list_dir(rel, pattern="*.md")
        except DriveNotFoundError:
            continue
        for meta in files:
            m = pattern.match(meta.name)
            if m:
                try:
                    n = int(m.group(1))
                    if n > max_n:
                        max_n = n
                except ValueError:
                    pass
    return f"{prefix}{max_n + 1}"


def build_v2_proposal(
    vault: DriveVault,
    rel: str,
    body: str,
    title: str,
    slug: str,
    priority: str = "Next",
    ice: tuple[int, int, int] = (7, 6, 5),
    source: str = "",
    deadline: str | None = None,
    wait_until: str | None = None,
) -> dict:
    """Build a v2 add_task proposal with target_path, frontmatter, body."""
    mapping = load_mapping(vault)
    entry = mapping.get(slug, {})
    prefix = entry.get("id_prefix") or _default_prefix_for(slug)
    new_id = next_id_for_slug(vault, slug, prefix)
    filename = _task_filename(new_id, title)
    target_path = f"02-PROJEKTY/{slug}/tasks/{filename}"
    hub_basename = (entry.get("hub_filename") or "").removesuffix(".md") or slug

    body_md = (
        f"# {new_id} — {title}\n\n"
        f"**Z:** {source or rel}\n\n"
        f"## Operativní kroky\n"
        f"- [ ] **{new_id}-1** (doplň při schválení)\n\n"
        f"## Poznámky / log\n"
        f"- {datetime.now(TZ).date().isoformat()}: Vytvořeno z INBOX `{rel}` (triage_run.py)\n"
    )

    return {
        "proposalType": "add_task",
        "target_path": target_path,
        "frontmatter": {
            "id": new_id,
            "type": "task",
            "title": title,
            "project": f"[[{hub_basename}]]",
            "slug": slug,
            "aliases": [new_id],
            "status": priority,
            "ice_i": ice[0],
            "ice_c": ice[1],
            "ice_e": ice[2],
            "deadline": deadline,
            "waitUntil": wait_until,
            "materials": [],
            "source": source or "",
            "blocked_by": [],
        },
        "body": body_md,
        "title": title,
        "suggestedProj": slug,
        "priority": priority,
        "ice": list(ice),
        "sourceFile": rel,
        "archiveAfterApply": True,
        "kind": "inbox",
    }


def _default_prefix_for(slug: str) -> str:
    """Fallback ID prefix from slug acronym."""
    parts = re.split(r"[-_]", slug)
    if len(parts) == 1:
        return slug[:2].upper() or "X"
    return "".join(p[0].upper() for p in parts[:3] if p)


def build_deep_proposal(
    rel: str,
    title: str,
    slug: str,
    reasons: list[str],
) -> dict:
    """Meta-proposal pro komplexní zdroj — DEEP route v agenda-triage.

    Záměrně nemá ``target_path`` ani ``frontmatter`` — apply z PENDINGu na
    něj nesmí sáhnout. Skill `agenda-triage` v PENDING režimu detekuje
    ``requires_deep_analysis: true`` a otevře DEEP flow s pre-loaded
    ``sourceFile``.
    """
    return {
        "action": "deep_analysis",
        "proposalType": "deep_analysis",
        "kind": "deep",
        "requires_deep_analysis": True,
        "deep_reasons": list(reasons),
        "title": title,
        "suggestedProj": slug,
        "priority": "Next",
        "ice": [7, 6, 5],
        "target_path": None,
        "frontmatter": None,
        "body": DEEP_PLACEHOLDER_BODY,
        "sourceFile": rel,
        "archiveAfterApply": True,
        "notes": "Komplexní materiál — DEEP analysis required. Důvody: "
        + "; ".join(reasons),
        "subtasks": [],
    }

# How much of each file to read when checking the ZPRACOVÁNO marker.
_HEADER_PROBE_BYTES = 400

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


def guess_proj(text: str, rel_path: str) -> str:
    low = (text + " " + rel_path).lower()
    for needle, slug in SLUG_HINTS:
        if needle in low:
            return slug
    parts = rel_path.split("/")
    if "slack" in parts:
        return "firemni-procesy"
    if "sembly" in parts:
        return "strategy"
    if "email" in parts:
        return "finance"
    if "daily" in parts:
        return "firemni-procesy"
    if "Clippings" in parts:
        return "firemni-procesy"
    return "firemni-procesy"


def title_from_file(name: str, body: str) -> str:
    for line in body.splitlines()[:30]:
        if line.startswith("# "):
            return line[2:].strip()[:120]
    m = re.search(r"capture[:\s]+(.+)", body, re.I)
    if m:
        return m.group(1).strip()[:120]
    stem = os.path.splitext(name)[0]
    return stem.replace("-", " ")[:120]


def _open_pending_source_files(vault: DriveVault) -> set[str]:
    """sourceFile paths already in an open Triage-Pending batch."""
    sources: set[str] = set()
    try:
        batches = vault.list_dir("00-System/Triage-Pending", pattern="*-batch.json")
    except DriveNotFoundError:
        return sources
    for meta in batches:
        try:
            data, _ = vault.read_json(meta.rel_path)
        except DriveNotFoundError:
            continue
        if data.get("status") != "open":
            continue
        for rel in data.get("sourceFiles") or []:
            if rel:
                sources.add(rel)
        for pr in data.get("proposals") or []:
            rel = pr.get("sourceFile")
            if rel:
                sources.add(rel)
    return sources


def iter_inbox_items(vault: DriveVault) -> list[tuple[str, str]]:
    """Return list of (rel_path, body) for unprocessed INBOX .md files.

    Skipped:
      * README*.md
      * files whose first ~400 bytes contain "ZPRACOVÁNO" marker
    """
    items: list[tuple[str, str]] = []
    for sub in INBOX_SUBDIRS:
        sub_rel = f"01-INBOX/{sub}"
        try:
            files = vault.list_dir(sub_rel, pattern="*.md", recursive=True)
        except DriveNotFoundError:
            continue
        for meta in files:
            if meta.name.startswith("README"):
                continue
            try:
                body, _ = vault.read_text(meta.rel_path)
            except DriveNotFoundError:
                continue
            if "ZPRACOVÁNO" in body[:_HEADER_PROBE_BYTES]:
                continue
            items.append((meta.rel_path, body))
    return items


def main() -> None:
    vault = get_vault()
    vault.mkdir_p("00-System/Triage-Pending")

    items = iter_inbox_items(vault)
    items = purge_dropped_sent_inbox(vault, items)
    pending_sources = _open_pending_source_files(vault)
    if pending_sources:
        before = len(items)
        items = [(rel, body) for rel, body in items if rel not in pending_sources]
        skipped = before - len(items)
        if skipped:
            print("skip inbox already in open pending batch:", skipped)

    if not items:
        print("no inbox files to triage")
        return

    items.sort(key=lambda it: it[0])

    now = datetime.now(TZ)
    batch_id = now.strftime("%Y-%m-%d-%H%M")
    proposals = []
    pid = 0
    for rel, body in items:
        if is_sent_email(rel, body):
            sent = extract_commitments(rel, body, guess_proj=guess_proj)
            if sent:
                for pr in sent:
                    pid += 1
                    pr = dict(pr)
                    pr["id"] = f"p{pid}"
                    proposals.append(pr)
            else:
                biz = sent_business_action_proposal(rel, body, guess_proj=guess_proj)
                if biz:
                    pid += 1
                    pr = dict(biz)
                    pr["id"] = f"p{pid}"
                    proposals.append(pr)
                    print("sent business-action proposal:", rel)
                else:
                    pid += 1
                    pr = sent_archive_only_proposal(rel, body)
                    pr["id"] = f"p{pid}"
                    proposals.append(pr)
                    print("sent archive_only proposal:", rel)
            continue

        name = rel.rsplit("/", 1)[-1]
        pid += 1
        title = title_from_file(name, body)
        slug = guess_proj(body, rel)

        if is_slack_inbox(rel):
            relevance = evaluate_slack_inbox_relevance(
                rel, body, guess_proj=guess_proj
            )
            if relevance:
                if relevance.route == "archive":
                    pr = slack_archive_proposal(rel, body, relevance)
                    pr["id"] = f"p{pid}"
                    proposals.append(normalize_proposal(pr))
                    print("slack archive:", rel, "reasons=", relevance.reasons)
                    continue
                if relevance.route == "deep":
                    reasons = list(relevance.reasons)
                    complex_, complex_reasons = is_complex_source(rel, body)
                    if complex_:
                        for r in complex_reasons:
                            if r not in reasons:
                                reasons.append(r)
                    deep = build_deep_proposal(
                        rel=rel, title=title, slug=slug, reasons=reasons
                    )
                    deep = enrich_proposal_with_slack_meta(deep, relevance)
                    deep["id"] = f"p{pid}"
                    proposals.append(deep)
                    print("slack deep:", rel, "reasons=", relevance.reasons)
                    continue
                v2_proposal = build_v2_proposal(
                    vault=vault,
                    rel=rel,
                    body=body,
                    title=title,
                    slug=slug,
                    priority="Next",
                    ice=(7, 6, 5),
                    source=rel,
                )
                normalized = normalize_proposal(
                    {
                        "id": f"p{pid}",
                        "action": "add_task",
                        "title": title,
                        "suggestedProj": slug,
                        "priority": "Next",
                        "ice": [7, 6, 5],
                        "notes": "",
                        "subtasks": [],
                        "sourceFile": rel,
                    }
                )
                normalized.update(v2_proposal)
                normalized = enrich_proposal_with_slack_meta(normalized, relevance)
                normalized["id"] = f"p{pid}"
                proposals.append(normalized)
                print("slack batch:", rel, "reasons=", relevance.reasons)
                continue

        complex_, reasons = is_complex_source(rel, body)
        if complex_:
            deep = build_deep_proposal(rel=rel, title=title, slug=slug, reasons=reasons)
            deep["id"] = f"p{pid}"
            proposals.append(deep)
            print("deep candidate:", rel, "reasons=", reasons)
            continue

        v2_proposal = build_v2_proposal(
            vault=vault,
            rel=rel,
            body=body,
            title=title,
            slug=slug,
            priority="Next",
            ice=(7, 6, 5),
            source=rel,
        )
        normalized = normalize_proposal(
            {
                "id": f"p{pid}",
                "action": "add_task",
                "title": title,
                "suggestedProj": slug,
                "priority": "Next",
                "ice": [7, 6, 5],
                "notes": "",
                "subtasks": [],
                "sourceFile": rel,
            }
        )
        normalized.update(v2_proposal)
        normalized["id"] = f"p{pid}"
        proposals.append(normalized)

    if not proposals:
        print("no proposals after filtering (sent emails may lack commitments)")
        return

    batch = {
        "batchId": batch_id,
        "status": "open",
        "created": now.isoformat(),
        "sourceFiles": [pr["sourceFile"] for pr in proposals],
        "proposals": proposals,
    }
    out_rel = f"00-System/Triage-Pending/{batch_id}-batch.json"
    vault.write_json(out_rel, batch)

    deep_proposals = [pr for pr in proposals if pr.get("requires_deep_analysis")]
    slack_archive_proposals = [
        pr for pr in proposals if pr.get("kind") == "slack_thread_archive"
    ]
    simple_count = len(proposals) - len(deep_proposals)

    summary_rel = f"00-System/Triage-Pending/{batch_id}-summary.md"
    lines = [
        f"# Triage batch {batch_id}\n",
        f"**Počet návrhů:** {len(proposals)} "
        f"(simple: {simple_count}, DEEP: {len(deep_proposals)}, "
        f"Slack archiv: {len(slack_archive_proposals)})\n",
    ]
    if slack_archive_proposals:
        lines.append("## Slack — archiv (bez tasku)\n")
        lines.append(
            "Vlákna s Lukášovou interakcí bez actionable commitmentu — "
            "po schválení jen přesun do HOTOVO.\n"
        )
        for pr in slack_archive_proposals:
            reasons = pr.get("slack_relevance_reasons") or []
            reasons_s = "; ".join(reasons) if reasons else "—"
            lines.append(f"- `{pr.get('sourceFile', '')}` — {reasons_s}")
        lines.append("")
    if deep_proposals:
        lines.append("## DEEP candidates\n")
        lines.append(
            "Tyto zdroje vyžadují DEEP analysis (skill `agenda-triage` "
            "v DEEP režimu) — z jednoho zdroje vznikne víc tasků/materiálů.\n"
        )
        for pr in deep_proposals:
            reasons = pr.get("deep_reasons") or []
            reasons_s = "; ".join(reasons) if reasons else "—"
            lines.append(f"- `{pr.get('sourceFile', '')}` — {reasons_s}")
        lines.append("")
    lines.append("## Návrhy\n")
    for pr in proposals:
        ptype = pr.get("proposalType") or "add_task"
        label = PROPOSAL_TYPE_LABELS.get(ptype, ptype)
        kind = pr.get("kind") or "inbox"
        conf = pr.get("confidence")
        conf_s = f", confidence {conf:.2f}" if isinstance(conf, (int, float)) else ""
        archive = pr.get("archiveAfterApply", True)
        arch_s = "ano" if archive else "ne"
        proj = pr.get("suggestedProj") or "—"
        src = pr.get("sourceFile", "")
        target = pr.get("target_path") or "—"
        lines.extend(
            [
                f"### {pr['id']} — `{src}`",
                f"- **Doporučení:** {label} (`{ptype}`)",
                f"- **Název:** {pr.get('title', '')[:120]}",
                f"- **Projekt:** {proj}",
                f"- **Cíl (v2):** `{target}`",
                f"- **Priorita:** {pr.get('priority') or '—'}",
                f"- **Podtyp:** {kind}{conf_s}",
                f"- **Po schválení archivovat zdroj:** {arch_s}",
                "",
            ]
        )
    lines.append("Schválení: v Cursoru `schval pending triáž` / `apply batch`\n")
    vault.write_text(summary_rel, "\n".join(lines))
    print("wrote drive://", out_rel, "proposals=", len(proposals))


if __name__ == "__main__":
    main()
