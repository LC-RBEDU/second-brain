"""T16 smoke — A58 set + brain_vault gates (tip/PUSH/PAUSED/skip)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB_LIB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB_LIB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("BRAIN_ALLOW_NO_PUSH", "1")

from app.errors import ERROR_REASONS, BrainVaultError  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402


def test_a58_error_reason_set():
    assert {
        "vault_dirty_start",
        "vault_flock_busy",
        "vault_push_reset_ok",
        "vault_push_reset_failed",
        "vault_tip_ahead",
        "vault_push_disabled",
        "vault_paused",
    } <= ERROR_REASONS


def test_brain_vault_rejects_tip_ahead_on_mutate():
    vault = MagicMock()
    vault.skipped = False
    vault.skip_reason = None
    vault.push_enabled = True
    vault.is_tip_ahead.return_value = True

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with pytest.raises(BrainVaultError) as ei:
            with brain_vault(mode="mutate", env={"GIT_VAULT_PUSH": "1"}):
                pass
    assert ei.value.error_reason == "vault_tip_ahead"


def test_brain_vault_read_allows_tip_ahead():
    vault = MagicMock()
    vault.skipped = False
    vault.push_enabled = True
    vault.is_tip_ahead.return_value = True

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with brain_vault(mode="read", env={"GIT_VAULT_PUSH": "0"}) as v:
            assert v is vault


def test_brain_vault_push_disabled_on_rebuild():
    vault = MagicMock()
    vault.skipped = False
    vault.push_enabled = False
    vault.is_tip_ahead.return_value = False

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with pytest.raises(BrainVaultError) as ei:
            with brain_vault(mode="rebuild", env={"GIT_VAULT_PUSH": "0"}):
                pass
    assert ei.value.error_reason == "vault_push_disabled"


def test_brain_vault_dirty_start_no_retry():
    vault = MagicMock()
    vault.skipped = True
    vault.skip_reason = "vault_dirty_start"

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    opens = {"n": 0}

    def _open(**_k):
        opens["n"] += 1
        return _CM()

    with patch("app.vault_deps.open_vault", side_effect=_open):
        with pytest.raises(BrainVaultError) as ei:
            with brain_vault(mode="mutate", env={"GIT_VAULT_PUSH": "1"}):
                pass
    assert ei.value.error_reason == "vault_dirty_start"
    assert opens["n"] == 1


def test_brain_vault_flock_busy_retries():
    vault = MagicMock()
    vault.skipped = True
    vault.skip_reason = "vault_flock_busy"

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    opens = {"n": 0}

    def _open(**_k):
        opens["n"] += 1
        return _CM()

    with patch("app.vault_deps.open_vault", side_effect=_open):
        with patch("app.vault_deps.time.sleep"):
            with pytest.raises(BrainVaultError) as ei:
                with brain_vault(mode="read", env={}):
                    pass
    assert ei.value.error_reason == "vault_flock_busy"
    assert opens["n"] == 3
