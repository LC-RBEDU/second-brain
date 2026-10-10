"""B6 — set_focus denied via policy."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.errors import BrainClientError  # noqa: E402
from app.tools.set_focus import set_focus  # noqa: E402


def test_set_focus_denied():
    with pytest.raises(BrainClientError) as ei:
        set_focus()
    assert ei.value.status_code == 403
    assert "focus" in ei.value.message.lower()
