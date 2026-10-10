#!/usr/bin/env python3
"""F8.2 (VPS): Build agent-context.json (+ light + charters) from vault.

Cron runs every 15 min during workhours (07-22). See deploy/crontab.
Logic lives in lib/agent_context_build.py (shared with Brain).
"""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from vault_factory import open_vault  # noqa: E402
from agent_context_build import build_and_write_context_bundle  # noqa: E402


def main() -> None:
    with open_vault() as vault:
        build_and_write_context_bundle(vault, side_failure="warn")


if __name__ == "__main__":
    main()
