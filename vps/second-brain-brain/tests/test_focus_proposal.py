"""propose_focus writes nothing. apply_focus writes once. A second apply is 404."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.batch_store import clear_for_tests  # noqa: E402
from app.errors import BrainClientError  # noqa: E402
from app.tools import focus_proposal as mod  # noqa: E402
from app.tools import set_focus as focus_mod  # noqa: E402
from focus import current_focus_week  # noqa: E402

TODAY = date(2026, 10, 12)
WEEK = current_focus_week(TODAY)
PATH = "02-PROJEKTY/second-brain/tasks/SB-S17 — Test.md"


class _CM:
    def __init__(self, vault):
        self.vault = vault

    def __enter__(self):
        return self.vault

    def __exit__(self, *a):
        return False


def _task_md() -> str:
    return (
        "---\nid: SB-S17\ntype: story\ntitle: Test\n"
        "slug: second-brain\nstatus: Next\nfocus:\nupdated: 2026-10-01\n---\n\n# t\n"
    )


def _vault() -> MagicMock:
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = "oid1"
    vault.read_text.return_value = (_task_md(), meta)
    meta2 = MagicMock()
    meta2.oid = "oid2"
    vault.write_text.return_value = meta2
    return vault


def test_propose_does_not_write_and_second_apply_is_missing():
    clear_for_tests()
    proposed = mod.propose_focus(task_path=PATH, focus_week=WEEK, principal="dev")
    assert proposed["written"] is False
    vault = _vault()
    with patch.object(focus_mod, "_prague_today", lambda env=None: TODAY):
        with patch.object(focus_mod, "brain_vault", return_value=_CM(vault)):
            with patch.object(focus_mod, "iter_active_tasks", return_value=iter([])):
                with patch.object(focus_mod, "delete_context_tombstone"):
                    with patch.object(focus_mod, "_paused_slugs_from_vault", return_value=set()):
                        out = mod.apply_focus(proposal_id=proposed["proposal_id"], principal="dev")
    assert out["focus"] == WEEK
    vault.write_text.assert_called_once()
    with pytest.raises(BrainClientError) as ei:
        mod.apply_focus(proposal_id=proposed["proposal_id"], principal="dev")
    assert ei.value.status_code == 404
    clear_for_tests()
