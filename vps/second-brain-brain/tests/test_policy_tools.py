"""Policy — update_task focus denied; set_focus allow path covered in test_set_focus."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.errors import BrainClientError  # noqa: E402
from app.tools.update_task import update_task  # noqa: E402


def test_update_task_focus_denied():
    with pytest.raises(BrainClientError) as ei:
        update_task(path="02-PROJEKTY/x/tasks/T.md", patch={"focus": "2026-W42"})
    assert ei.value.status_code == 403
    assert "set_focus" in ei.value.message.lower() or "focus" in ei.value.message.lower()
