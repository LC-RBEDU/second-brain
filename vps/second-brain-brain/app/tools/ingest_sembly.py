"""ingest_sembly — deterministic MD into 01-INBOX/sembly/ (R9)."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from app.sembly_template import filename_for, render_markdown
from app.vault_deps import brain_vault

SEMBLY_DIR = "01-INBOX/sembly"


def _idempotency_key(payload: dict[str, Any]) -> str:
    raw = payload.get("id") or payload.get("meeting_id")
    if raw:
        return str(raw)
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
    return digest


def ingest_sembly(payload: dict[str, Any], *, env: dict | None = None) -> dict[str, Any]:
    env = env if env is not None else dict(os.environ)
    filename = filename_for(payload)
    rel = f"{SEMBLY_DIR}/{filename}"
    body = render_markdown(payload)
    key = _idempotency_key(payload)
    key_path = f"{SEMBLY_DIR}/.keys/{key}.path"

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
            return {
                "ok": True,
                "path": rel,
                "deduped": True,
                "idempotency_key": key,
            }
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
