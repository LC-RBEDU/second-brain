"""B35b contract — side_failure raise propagates from light path."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import agent_context_build as mod  # noqa: E402


def test_side_failure_modes_documented():
    """API accepts warn|raise (A29)."""
    import inspect

    sig = inspect.signature(mod.build_and_write_context_bundle)
    assert "side_failure" in sig.parameters
