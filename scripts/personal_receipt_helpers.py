#!/usr/bin/env python3
"""Smoke helpers for personal payment docs pipeline (T1–T18 checklist)."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

from invoice_duzp import parse_invoice_text  # noqa: E402
from payment_doc import (  # noqa: E402
    b0_should_keep,
    extract_b4_pdf_urls,
    is_payment_doc,
    load_payment_config,
)

VAULT = ROOT / "OBSIDIAN"
MANIFEST = VAULT / "00-System" / "Personal-Docs-Uploaded" / "manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def manifest_has(*, thread_id: str | None = None, vs: str | None = None, sha: str | None = None) -> bool:
    if not MANIFEST.is_file():
        return False
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for it in data.get("items") or []:
        if thread_id and it.get("threadId") == thread_id and sha and it.get("sha256") == sha:
            return True
        if vs and it.get("vs") == vs:
            return True
    return False


def append_manifest(item: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    data = {"version": 1, "items": []}
    if MANIFEST.is_file():
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data.setdefault("items", []).append(item)
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def agent_log(line: str) -> None:
    log_dir = VAULT / "00-System" / "Agent-Log"
    log_dir.mkdir(parents=True, exist_ok=True)
    month = date.today().strftime("%Y-%m")
    path = log_dir / f"{month}.md"
    if not path.is_file():
        path.write_text(f"# Agent-Log {month}\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"- {date.today().isoformat()} {line}\n")


if __name__ == "__main__":
    cfg = load_payment_config(VAULT)
    print("config_root", cfg.get("drive_root_folder_id"))
    print(
        "b1_alza",
        is_payment_doc(from_header="Alza", subject="vyúčtování AlzaNEO", body=""),
    )
    print(
        "b0_inline",
        b0_should_keep(filename="x.png", mime="image/png", size=100, disposition="inline"),
    )
    print(
        "b4",
        extract_b4_pdf_urls('<a href="https://x/a.pdf">Stáhnout fakturu</a>', is_payment=True),
    )
