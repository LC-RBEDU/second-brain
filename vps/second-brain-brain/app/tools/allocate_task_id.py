"""allocate_task_id — non-reserving preview (A43)."""
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

from task_id_allocate import next_id, with_level  # noqa: E402

from app.vault_deps import brain_vault  # noqa: E402


def allocate_task_id(
    slug: str,
    *,
    level: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    with brain_vault(mode="read", env=env) as vault:
        tid, where = next_id(vault, slug)
        if level:
            tid = with_level(tid, level)
        return {"id": tid, "ceiling_source": where, "reserving": False}
