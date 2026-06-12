#!/usr/bin/env python3
"""LLM triage via Cursor headless CLI (VPS cron).

1. List unprocessed INBOX via DriveVault (skip if empty).
2. If CURSOR_API_KEY + cursor-agent available → run agent with triage prompt.
3. Write pending batch JSON to 00-System/Triage-Pending/ (same schema as triage_run.py).

Fallback: if CLI unavailable, only log inbox count (use manual triage in Cursor).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
_CRON = Path(__file__).resolve().parent
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
if str(_CRON) not in sys.path:
    sys.path.insert(0, str(_CRON))

from drive_io import DriveVault, credentials_from_env  # noqa: E402
from triage_run import (  # noqa: E402
    INBOX_SUBDIRS,
    _open_pending_source_files,
    iter_inbox_items,
)

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))

TRIAGE_PROMPT = """You are triaging INBOX items for MrLUC Second Brain v2 vault.

For each source file, output ONE JSON object per line (JSONL) with fields:
- proposalType: add_task | update_task | archive_only | deep_analysis | add_person | update_person | area_log
- sourceFile: path from input
- title, suggestedProj (slug), priority, ice [i,c,e]
- target_path, frontmatter, body (for add_task — v2 file-per-task)
- person_name, person_patch (for update_person)
- area_slug, log_entry (for area_log — zodpovědnostní postřeh bez akce)
- requires_deep_analysis, deep_reasons (if complex)

Rules:
- Lukáš-only tasks (see agenda-triage skill)
- Complex sources → deep_analysis
- Unknown people → add_person; new info about known → update_person
- Reference-only → save to 05-RESOURCES with topics, not task
- Responsibility note without action → area_log to matching area ## Log rozhodnutí

Output ONLY JSONL, no markdown fences.
"""


def _find_cursor_agent() -> str | None:
    for name in ("cursor-agent", "agent"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _run_llm(sources: list[tuple[str, str]]) -> list[dict]:
    api_key = (os.environ.get("CURSOR_API_KEY") or "").strip()
    agent = _find_cursor_agent()
    if not api_key or not agent:
        return []

    payload = {
        "sources": [
            {"path": rel, "preview": body[:4000]}
            for rel, body in sources
        ]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f, ensure_ascii=False)
        payload_path = f.name

    cmd = [
        agent,
        "--model", "auto",
        "--print",
        "--output-format", "text",
        TRIAGE_PROMPT + f"\n\nINPUT:\n{json.dumps(payload, ensure_ascii=False)}",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, "CURSOR_API_KEY": api_key},
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"triage_llm_run: agent failed: {e}")
        return []
    finally:
        Path(payload_path).unlink(missing_ok=True)

    if proc.returncode != 0:
        print(f"triage_llm_run: agent exit {proc.returncode}: {proc.stderr[:500]}")
        return []

    proposals: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        try:
            proposals.append(json.loads(line))
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", line)
            if m:
                try:
                    proposals.append(json.loads(m.group(0)))
                except json.JSONDecodeError:
                    pass
    return proposals


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)
    vault.mkdir_p("00-System/Triage-Pending")

    items = iter_inbox_items(vault)
    pending_sources = _open_pending_source_files(vault)
    if pending_sources:
        items = [(r, b) for r, b in items if r not in pending_sources]

    if not items:
        print("triage_llm_run: no inbox files")
        return

    print(f"triage_llm_run: inbox={len(items)}")
    proposals = _run_llm(items)

    if not proposals:
        print("triage_llm_run: LLM unavailable or empty — run manual triage in Cursor")
        return

    now = datetime.now(TZ)
    batch_id = now.strftime("%Y-%m-%d-%H%M")
    for i, pr in enumerate(proposals, 1):
        pr.setdefault("id", f"p{i}")

    batch = {
        "batchId": batch_id,
        "status": "open",
        "created": now.isoformat(),
        "source": "triage_llm_run",
        "sourceFiles": [pr.get("sourceFile") for pr in proposals if pr.get("sourceFile")],
        "proposals": proposals,
    }
    out_rel = f"00-System/Triage-Pending/{batch_id}-batch.json"
    vault.write_json(out_rel, batch)
    print(f"triage_llm_run: wrote drive://{out_rel} proposals={len(proposals)}")


if __name__ == "__main__":
    main()
