"""get_context — warm read or sync rebuild in one request session (R15 / A45)."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from agent_context_build import (  # noqa: E402
    OUTPUT_CHARTERS_REL,
    OUTPUT_LIGHT_REL,
    OUTPUT_REL,
    build_and_write_context_bundle,
)
from drive_io import DriveNotFoundError  # noqa: E402

from app.context_freshness import needs_rebuild  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402

def _read_json(vault: Any, rel: str) -> dict[str, Any] | None:
    try:
        data, _ = vault.read_json(rel)
    except DriveNotFoundError:
        return None
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def get_context(*, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Return full agent-context snapshot; rebuild when §3 says so.

    Tip ahead + needs_rebuild → 503 vault_tip_ahead (no stale TOP).
    """
    # Probe freshness under read mode first (tip ahead OK for warm).
    with brain_vault(mode="read", env=env) as vault:
        full = _read_json(vault, OUTPUT_REL)
        light = _read_json(vault, OUTPUT_LIGHT_REL)
        charters = _read_json(vault, OUTPUT_CHARTERS_REL)
        rebuild = needs_rebuild(full, light, charters)
        if not rebuild:
            assert full is not None
            # Warm size guard (plan §3 ≤256 KB) — return as-is; oversized rare.
            return {"mode": "warm", "context": full}

    # needs_rebuild — mutate/rebuild gates (tip/PUSH) apply.
    with brain_vault(mode="rebuild", env=env) as vault:
        snapshot = build_and_write_context_bundle(vault, side_failure="raise")
        light2 = _read_json(vault, OUTPUT_LIGHT_REL)
        charters2 = _read_json(vault, OUTPUT_CHARTERS_REL)
        if needs_rebuild(snapshot, light2, charters2):
            raise RuntimeError("post-rebuild verify failed (trio timestamps)")
        return {"mode": "rebuild", "context": snapshot}
