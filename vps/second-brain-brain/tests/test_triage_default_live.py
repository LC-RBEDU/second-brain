"""T2 / B3 — get_triage_candidates default L1 = live."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.tools import get_triage_candidates as mod


def test_default_l1_live_and_include_live_true():
    fake_vault = MagicMock()
    fake_vault.exists.return_value = False

    class Ctx:
        def __enter__(self):
            return fake_vault

        def __exit__(self, *a):
            return None

    with (
        patch.object(mod, "brain_vault", return_value=Ctx()),
        patch.object(mod, "list_l1") as list_l1,
        patch("app.tools.slack_live.slack_live_search") as live,
    ):
        list_l1.return_value = MagicMock(error_reason=None, messages=[])
        live.return_value = {"candidates": [], "dumped": False}
        out = mod.get_triage_candidates(env={})
    assert out["default_l1"] == "live"
    assert out["include_live_slack"] is True
    live.assert_called_once()


def test_empty_sources_ok():
    fake_vault = MagicMock()
    fake_vault.exists.return_value = False

    class Ctx:
        def __enter__(self):
            return fake_vault

        def __exit__(self, *a):
            return None

    with (
        patch.object(mod, "brain_vault", return_value=Ctx()),
        patch.object(mod, "list_l1") as list_l1,
        patch("app.tools.slack_live.slack_live_search") as live,
    ):
        list_l1.return_value = MagicMock(error_reason=None, messages=[])
        live.return_value = {"candidates": [], "dumped": False}
        out = mod.get_triage_candidates(env={})
    assert out["sources"]["live_slack"] == []
    assert out["sources"]["slack_dump"] == []
