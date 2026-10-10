"""T4/B5 — DriveConflictError → 409 cas_conflict."""
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

from drive_io import DriveConflictError  # noqa: E402

from app.errors import BrainClientError  # noqa: E402
from app.tools import update_task as mod  # noqa: E402


def test_drive_conflict_maps_to_409():
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = "abc"
    vault.read_text.return_value = (
        "---\nid: X1\ntitle: T\n---\n\n# X1 — T\n",
        meta,
    )
    vault.write_text.side_effect = DriveConflictError("oid mismatch")

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch.object(mod, "brain_vault", return_value=_CM()):
        with pytest.raises(BrainClientError) as ei:
            mod.update_task(path="02-PROJEKTY/test/tasks/X1.md", patch={"status": "Next"})
    assert ei.value.status_code == 409
    assert ei.value.error_reason == "cas_conflict"
