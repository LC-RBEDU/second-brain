"""T9 — external propose targets dm/gdm/channel."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.batch_store import clear_for_tests  # noqa: E402
from app.tools.external_propose_apply import external_propose  # noqa: E402


def test_targets_in_payload():
    clear_for_tests()
    out = external_propose(
        [
            {
                "id": "1",
                "action": "send",
                "payload": {"target": "channel"},
            }
        ]
    )
    assert out["items"][0]["target"] == "channel"
    assert out["mutated"] is False
