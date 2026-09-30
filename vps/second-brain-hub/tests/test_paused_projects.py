"""SB3 — paused project hubs: hub-state skip, stale_hubs, casefold."""
from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
_REPO = Path(__file__).resolve().parents[3]
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from hub_state import (  # noqa: E402
    STALE_NARRATIVE_DAYS,
    is_narrative_stale,
    should_refresh_hub_state,
)
from today_priority import is_active_project_status  # noqa: E402


def test_is_active_project_status_paused_casefold():
    assert is_active_project_status("PAUSED") is False
    assert is_active_project_status("paused") is False
    assert is_active_project_status("Paused") is False


def test_should_refresh_hub_state_skips_paused():
    assert should_refresh_hub_state({"type": "project", "status": "paused"}) is False
    assert should_refresh_hub_state({"type": "project", "status": "PAUSED"}) is False
    assert should_refresh_hub_state({"type": "project", "status": "active"}) is True
    assert should_refresh_hub_state({"type": "project"}) is True
    assert should_refresh_hub_state({"type": "project", "status": ""}) is True
    assert should_refresh_hub_state({"type": "task", "status": "active"}) is False
    assert should_refresh_hub_state(None) is False


def test_stale_hubs_loop_skips_paused():
    """Mirror build_agent_context stale_hubs filter (B7)."""
    today = date(2026, 9, 30)
    last_act = date(2026, 1, 1)
    projects = [
        {"slug": "kratky-potlesk", "status": "paused", "updated": "2020-01-01"},
        {"slug": "rb-network", "status": "active", "updated": "2020-01-01"},
    ]
    stale_hubs: list[dict] = []
    for p in projects:
        if not is_active_project_status(p.get("status")):
            continue
        if is_narrative_stale(p.get("updated"), last_act, threshold_days=STALE_NARRATIVE_DAYS):
            stale_hubs.append({"slug": p["slug"]})
    slugs = {h["slug"] for h in stale_hubs}
    assert "kratky-potlesk" not in slugs
    assert "rb-network" in slugs
    # silence unused
    assert today.year == 2026


def test_update_hub_state_tmp_vault_skips_paused_write(tmp_path: Path):
    """Paused hub content byte-identical after update_hub_state (B9)."""
    projekty = tmp_path / "02-PROJEKTY"
    projekty.mkdir()
    (tmp_path / "07-ARCHIV" / "tasks-done").mkdir(parents=True)

    paused_body = (
        "---\n"
        "type: project\n"
        "slug: kratky-potlesk\n"
        "status: paused\n"
        "updated: 2020-01-01\n"
        "---\n"
        "# Krátký potlesk\n\n"
        "## Stav (auto)\n"
        "PLACEHOLDER_PAUSED\n\n"
        "## Cíl\n"
        "x\n"
    )
    active_body = (
        "---\n"
        "type: project\n"
        "slug: rb-network\n"
        "status: active\n"
        "updated: 2020-01-01\n"
        "---\n"
        "# Red Button Network\n\n"
        "## Stav (auto)\n"
        "PLACEHOLDER_ACTIVE\n\n"
        "## Cíl\n"
        "y\n"
    )
    paused_path = projekty / "Krátký potlesk.md"
    active_path = projekty / "Red Button Network.md"
    paused_path.write_text(paused_body, encoding="utf-8")
    active_path.write_text(active_body, encoding="utf-8")
    before_paused = paused_path.read_bytes()
    before_active = active_path.read_bytes()

    script = _REPO / "scripts" / "update_hub_state.py"
    spec = importlib.util.spec_from_file_location("update_hub_state", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    old_argv = sys.argv
    try:
        sys.argv = ["update_hub_state.py", "--vault", str(tmp_path)]
        rc = mod.main()
    finally:
        sys.argv = old_argv
    assert rc == 0
    assert paused_path.read_bytes() == before_paused
    # Positive control: active hub must be rewritten (otherwise a no-op main() would pass).
    assert active_path.read_bytes() != before_active
    assert b"PLACEHOLDER_ACTIVE" not in active_path.read_bytes()

    # Second run still identical (idempotent skip)
    before2 = paused_path.read_bytes()
    try:
        sys.argv = ["update_hub_state.py", "--vault", str(tmp_path)]
        rc2 = mod.main()
    finally:
        sys.argv = old_argv
    assert rc2 == 0
    assert paused_path.read_bytes() == before2
