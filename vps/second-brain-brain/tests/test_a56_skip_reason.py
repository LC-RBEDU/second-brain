"""A56 — skipped without skip_reason must not become vault_dirty_start."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.errors import BrainClientError  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402


def test_skipped_without_reason_is_misconfig_not_dirty():
    vault = MagicMock()
    vault.skipped = True
    vault.skip_reason = None

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with pytest.raises(BrainClientError) as ei:
            with brain_vault(mode="read", env={}):
                pass
    assert ei.value.status_code == 500
    assert ei.value.error_reason == "misconfigured_session"
    assert "dirty" not in ei.value.error_reason
