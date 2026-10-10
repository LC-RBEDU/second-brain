"""Detect git-clone vault that Mac scripts must not write (F1 B23/B24)."""
from __future__ import annotations

import os
from pathlib import Path


def vault_forbids_local_write(vault: Path, *, env: dict | None = None) -> bool:
    """True when vault is a git clone or SECOND_BRAIN_VAULT_READONLY=1."""
    e = env if env is not None else os.environ
    flag = (e.get("SECOND_BRAIN_VAULT_READONLY") or "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    return (Path(vault) / ".git").exists()


READONLY_MSG = (
    "Vault je git klon (nebo SECOND_BRAIN_VAULT_READONLY=1) — "
    "zápis jen přes VPS cron / GitHub web UI PR. "
    "Na Macu: git pull. Snapshot: VPS build_agent_context."
)
