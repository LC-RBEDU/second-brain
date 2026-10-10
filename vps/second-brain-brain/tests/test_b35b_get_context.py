"""T3/B35b — builder raise → BrainVaultError 503, not bare 500."""
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


def test_builder_raise_maps_to_503_brain_vault_error():
    vault_read = MagicMock()
    vault_read.skipped = False

    class _ReadCM:
        def __enter__(self):
            return vault_read

        def __exit__(self, *a):
            return False

    class _RebuildCM:
        def __enter__(self):
            return MagicMock(skipped=False)

        def __exit__(self, *a):
            return False

    def _brain(*, mode, env=None):
        if mode == "read":
            return _ReadCM()
        return _RebuildCM()

    with patch.object(mod, "brain_vault", side_effect=_brain):
        with patch.object(mod, "_read_json", return_value=None):
            with patch.object(
                mod,
                "build_and_write_context_bundle",
                side_effect=RuntimeError("light boom"),
            ):
                with pytest.raises(BrainVaultError) as ei:
                    mod.get_context()
    assert ei.value.status_code == 503
    assert ei.value.error_reason
    assert "light boom" in ei.value.message or "rebuild" in ei.value.message.lower()
