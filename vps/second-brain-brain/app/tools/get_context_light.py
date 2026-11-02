"""get_context_light — warm read of agent-context-light.json only (F4 / R8).

Never rebuilds. Freshness trio (full+light+charters); stale/missing → 503.
"""
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
)
from drive_io import DriveNotFoundError  # noqa: E402

from app.context_freshness import needs_rebuild  # noqa: E402
from app.errors import vault_error  # noqa: E402
from app.tools.sembly_pending import attach_sembly_pending  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402


def _read_json(vault: Any, rel: str) -> dict[str, Any] | None:
    try:
        data, _ = vault.read_json(rel)
    except DriveNotFoundError:
        return None
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def get_context_light(*, env: dict[str, str] | None = None) -> dict[str, Any]:
    with brain_vault(mode="read", env=env) as vault:
        full = _read_json(vault, OUTPUT_REL)
        light = _read_json(vault, OUTPUT_LIGHT_REL)
        charters = _read_json(vault, OUTPUT_CHARTERS_REL)
        if needs_rebuild(full, light, charters):
            raise vault_error(
                "context_light_stale",
                "agent-context-light.json missing or freshness trio mismatch; "
                "rebuild via get_context / cron — light endpoint does not rebuild",
            )
        assert light is not None
        attach_sembly_pending(light, vault, env=env)
        return {"mode": "warm", "context": light}
