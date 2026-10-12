"""set_focus — allow oauth/service, limit, clear, CAS (plan B#)."""
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

from app.auth_service import ServicePrincipal  # noqa: E402
from app.errors import BrainClientError  # noqa: E402
from app.policy import allow_focus_write, deny_focus_write  # noqa: E402
from app.request_principal import (  # noqa: E402
    get_brain_principal,
    reset_brain_principal,
    set_brain_principal,
)
from app.tools import set_focus as mod  # noqa: E402
from app.tools import update_task as update_mod  # noqa: E402
from drive_io import DriveConflictError, DriveNotFoundError  # noqa: E402
from focus import current_focus_week  # noqa: E402
from today_priority import count_focus_slots, would_consume_focus_slot  # noqa: E402

TODAY = date(2026, 10, 12)
WEEK = current_focus_week(TODAY)
PATH = "02-PROJEKTY/second-brain/tasks/SB-S17 — Test.md"


def _task_md(*, focus: str = "", status: str = "Next", typ: str = "story", slug: str = "second-brain"):
    return (
        f"---\nid: SB-S17\ntype: {typ}\ntitle: Test\n"
        f"slug: {slug}\nstatus: {status}\nfocus: {focus}\nupdated: 2026-10-01\n---\n\n# t\n"
    )


class _CM:
    def __init__(self, vault):
        self.vault = vault

    def __enter__(self):
        return self.vault

    def __exit__(self, *a):
        return False


def _vault(text: str, *, write_ok: bool = True):
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = "oid1"
    meta.rel_path = PATH
    meta.name = "SB-S17 — Test.md"
    vault.read_text.return_value = (text, meta)
    if write_ok:
        meta2 = MagicMock()
        meta2.oid = "oid2"
        vault.write_text.return_value = meta2
    vault.list_dir.return_value = []
    return vault


def test_allow_focus_write_principals():
    assert allow_focus_write("oauth:x@y.cz").allowed
    assert allow_focus_write(ServicePrincipal()).allowed
    assert allow_focus_write("dev").allowed
    assert allow_focus_write(None).allowed is False
    assert deny_focus_write().allowed is False


def test_b1_oauth_sets_focus(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    vault = _vault(_task_md())
    # iter_active_tasks yields nothing → others=0
    with patch.object(mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(mod, "iter_active_tasks", return_value=iter([])):
            with patch.object(mod, "delete_context_tombstone"):
                with patch.object(mod, "_paused_slugs_from_vault", return_value=set()):
                    out = mod.set_focus(
                        task_path=PATH,
                        focus_week=WEEK,
                        principal="oauth:lukas@redbuttonedu.cz",
                    )
    assert out["focus"] == WEEK
    assert out["cleared"] is False
    assert out["already_in_focus"] is False
    vault.write_text.assert_called_once()


def test_b2_service_principal(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    vault = _vault(_task_md())
    with patch.object(mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(mod, "iter_active_tasks", return_value=iter([])):
            with patch.object(mod, "delete_context_tombstone"):
                with patch.object(mod, "_paused_slugs_from_vault", return_value=set()):
                    out = mod.set_focus(
                        task_path=PATH,
                        focus_week=WEEK,
                        principal=ServicePrincipal(),
                    )
    assert out["focus"] == WEEK


def test_b4_clear(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    vault = _vault(_task_md(focus=WEEK))
    with patch.object(mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(mod, "iter_active_tasks", return_value=iter([])):
            with patch.object(mod, "delete_context_tombstone"):
                with patch.object(mod, "_paused_slugs_from_vault", return_value=set()):
                    out = mod.set_focus(
                        task_path=PATH,
                        focus_week="",
                        principal="dev",
                    )
    assert out["cleared"] is True
    assert out["focus"] is None


def test_b6_limit_exceeded(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    vault = _vault(_task_md())
    # Fake 5 other eligible via count_focus_slots patch
    with patch.object(mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(mod, "iter_active_tasks", return_value=iter([])):
            with patch.object(mod, "delete_context_tombstone"):
                with patch.object(mod, "_paused_slugs_from_vault", return_value=set()):
                    with patch.object(mod, "count_focus_slots", return_value=5):
                        with pytest.raises(BrainClientError) as ei:
                            mod.set_focus(
                                task_path=PATH,
                                focus_week=WEEK,
                                principal="dev",
                            )
    assert ei.value.status_code == 403
    assert ei.value.error_reason == "focus_limit_exceeded"


def test_b16_waiting_allows_when_full(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    vault = _vault(_task_md(status="Waiting"))
    with patch.object(mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(mod, "iter_active_tasks", return_value=iter([])):
            with patch.object(mod, "delete_context_tombstone"):
                with patch.object(mod, "_paused_slugs_from_vault", return_value=set()):
                    with patch.object(mod, "count_focus_slots", return_value=5):
                        out = mod.set_focus(
                            task_path=PATH,
                            focus_week=WEEK,
                            principal="dev",
                        )
    assert out["focus"] == WEEK


def test_b7_non_current_week(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    with pytest.raises(BrainClientError) as ei:
        mod.set_focus(
            task_path=PATH,
            focus_week="2020-W01",
            principal="dev",
        )
    assert ei.value.status_code == 400


def test_b8_cas_conflict(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    vault = _vault(_task_md())
    vault.write_text.side_effect = DriveConflictError("oid mismatch")
    with patch.object(mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(mod, "iter_active_tasks", return_value=iter([])):
            with patch.object(mod, "delete_context_tombstone"):
                with patch.object(mod, "_paused_slugs_from_vault", return_value=set()):
                    with pytest.raises(BrainClientError) as ei:
                        mod.set_focus(
                            task_path=PATH,
                            focus_week=WEEK,
                            expect_oid="oid1",
                            principal="dev",
                        )
    assert ei.value.status_code == 409


def test_b9_update_task_focus_denied():
    with pytest.raises(BrainClientError) as ei:
        update_mod.update_task(
            path=PATH,
            patch={"focus": WEEK},
        )
    assert ei.value.status_code == 403
    assert "set_focus" in ei.value.message


def test_b19_not_found(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    vault = MagicMock()
    vault.read_text.side_effect = DriveNotFoundError("gone")
    with patch.object(mod, "brain_vault", return_value=_CM(vault)):
        with patch.object(mod, "delete_context_tombstone"):
            with pytest.raises(BrainClientError) as ei:
                mod.set_focus(task_path=PATH, focus_week=WEEK, principal="dev")
    assert ei.value.status_code == 404


def test_t12_contextvar_principal(monkeypatch):
    monkeypatch.setattr(mod, "_prague_today", lambda env=None: TODAY)
    vault = _vault(_task_md())
    tok = set_brain_principal(ServicePrincipal())
    try:
        assert get_brain_principal() is not None
        with patch.object(mod, "brain_vault", return_value=_CM(vault)):
            with patch.object(mod, "iter_active_tasks", return_value=iter([])):
                with patch.object(mod, "delete_context_tombstone"):
                    with patch.object(mod, "_paused_slugs_from_vault", return_value=set()):
                        out = mod.set_focus(task_path=PATH, focus_week=WEEK)
        assert out["focus"] == WEEK
    finally:
        reset_brain_principal(tok)


def test_count_focus_slots_a4():
    tasks = [
        {"id": "1", "slug": "a", "status": "Next", "type": "story", "focus": WEEK},
        {"id": "2", "slug": "a", "status": "Waiting", "type": "story", "focus": WEEK},
        {"id": "3", "slug": "a", "status": "Next", "type": "epic", "focus": WEEK},
        {"id": "4", "slug": "paused", "status": "Next", "type": "story", "focus": WEEK},
    ]
    assert count_focus_slots(tasks, TODAY, paused_slugs={"paused"}) == 1
    assert would_consume_focus_slot(tasks[0], set()) is True
    assert would_consume_focus_slot(tasks[1], set()) is False
