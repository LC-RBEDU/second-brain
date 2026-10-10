"""B3e — needs_rebuild + tip ahead → vault_tip_ahead, no warm stale."""
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

from app.errors import BrainVaultError  # noqa: E402
from app.tools import get_context as mod  # noqa: E402


def test_rebuild_tip_ahead_503():
    # Warm probe: needs_rebuild True (missing files)
    vault_read = MagicMock()
    vault_read.skipped = False
    vault_read.exists.return_value = False

    class _ReadCM:
        def __enter__(self):
            return vault_read

        def __exit__(self, *a):
            return False

    def _brain(*, mode, env=None):
        if mode == "read":
            return _ReadCM()
        raise BrainVaultError(
            error_reason="vault_tip_ahead",
            message="tip ahead",
            status_code=503,
        )

    with patch.object(mod, "brain_vault", side_effect=_brain):
        with patch.object(mod, "_read_json", return_value=None):
            with pytest.raises(BrainVaultError) as ei:
                mod.get_context()
    assert ei.value.error_reason == "vault_tip_ahead"
