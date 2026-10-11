"""T7b — Brain apply + service → 403."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.auth_apply import gate_brain_apply  # noqa: E402
from app.auth_service import ServicePrincipal  # noqa: E402
from app.errors import BrainClientError  # noqa: E402


def test_service_403():
    try:
        gate_brain_apply(ServicePrincipal())
        assert False
    except BrainClientError as exc:
        assert exc.status_code == 403
        assert exc.error_reason == "human_oauth_required"
