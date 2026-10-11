"""T7c — Brain apply + oauth → 501 post-F3."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.auth_apply import gate_brain_apply  # noqa: E402
from app.errors import BrainClientError  # noqa: E402


def test_oauth_501():
    try:
        gate_brain_apply("oauth:lukas@redbuttonedu.cz")
        assert False
    except BrainClientError as exc:
        assert exc.status_code == 501
        assert exc.error_reason == "oauth_brain_apply_post_f3"
