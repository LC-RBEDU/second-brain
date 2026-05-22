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
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, DriveNotFoundError, credentials_from_env  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))

INBOX_SUBDIRS = ("slack", "sembly", "email", "daily")

SLUG_HINTS = [
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
    ("inspirace", "obecna-inspirace"),
    ("exponential", "exponential-summit"),
    ("vibe", "vibe-coding"),
]

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
    for i, (rel, body) in enumerate(items, 1):
        name = rel.rsplit("/", 1)[-1]
        proposals.append(
            {
                "id": f"p{i}",
                "action": "add_task",
                "title": title_from_file(name, body),
                "suggestedProj": guess_proj(body, rel),
                "priority": "Next",
                "ice": [7, 6, 5],
                "notes": "",
                "subtasks": [],
                "sourceFile": rel,
            }
        )

    batch = {
        "batchId": batch_id,
        "status": "open",
        "created": now.isoformat(),
        "sourceFiles": [pr["sourceFile"] for pr in proposals],
        "proposals": proposals,
    }
    out_rel = f"00-System/Triage-Pending/{batch_id}-batch.json"
    vault.write_json(out_rel, batch)

    summary_rel = f"00-System/Triage-Pending/{batch_id}-summary.md"
    lines = [
        f"# Triage batch {batch_id}\n",
        f"**Počet návrhů:** {len(proposals)}\n",
        "| ID | Návrh | Projekt |",
        "|----|-------|---------|",
    ]
    for pr in proposals:
        lines.append(f"| {pr['id']} | {pr['title'][:60]} | {pr['suggestedProj']} |")
    lines.append("\nSchválení: v Cursoru `schval pending triáž`\n")
    vault.write_text(summary_rel, "\n".join(lines))
    print("wrote drive://", out_rel, "proposals=", len(proposals))


if __name__ == "__main__":
    main()
