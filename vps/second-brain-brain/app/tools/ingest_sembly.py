"""ingest_sembly — deterministic MD into 01-INBOX/sembly/ (R9)."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from app.sembly_template import _meeting_blob, filename_for, render_markdown
from app.vault_deps import brain_vault

SEMBLY_DIR = "01-INBOX/sembly"
_SAFE = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")


def _fs_safe(raw: str) -> str:
    return "".join(ch if ch in _SAFE else "_" for ch in raw) or "unknown"


def _idempotency_key(payload: dict[str, Any]) -> str:
    blob = _meeting_blob(payload)
    for cand in (
        payload.get("id"),
        payload.get("meeting_id"),
        blob.get("id"),
        blob.get("meeting_id"),
    ):
        if cand is None:
            continue
        text = str(cand).strip()
        if text:
            return _fs_safe(text)
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
    return _fs_safe(digest)


def ingest_sembly(payload: dict[str, Any], *, env: dict | None = None) -> dict[str, Any]:
    env = env if env is not None else dict(os.environ)
    body = render_markdown(payload)
    key = _idempotency_key(payload)
    key_path = f"{SEMBLY_DIR}/.keys/{key}.path"
    key12 = key[:12]
    cand = filename_for(payload)
    stem = cand[:-3] if cand.endswith(".md") else cand
    rel = f"{SEMBLY_DIR}/{cand}"

    with brain_vault(mode="mutate", env=env) as vault:
        if vault.exists(key_path):
            text, _ = vault.read_text(key_path)
            return {
                "ok": True,
                "path": (text or "").strip() or rel,
                "deduped": True,
                "idempotency_key": key,
            }
        if vault.exists(rel):
            cand = f"{stem}-{key12}.md"
            rel = f"{SEMBLY_DIR}/{cand}"
            n = 2
            while vault.exists(rel):
                cand = f"{stem}-{key12}-{n}.md"
                rel = f"{SEMBLY_DIR}/{cand}"
                n += 1
        vault.mkdir_p(SEMBLY_DIR)
        vault.mkdir_p(f"{SEMBLY_DIR}/.keys")
        vault.write_text(rel, body)
        vault.write_text(key_path, rel + "\n")
    return {
        "ok": True,
        "path": rel,
        "deduped": False,
        "idempotency_key": key,
    }
