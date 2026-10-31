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
        "vault_push_keep_tip",
        "vault_push_enqueue_failed",
        "vault_push_pending_failed",
        "vault_tip_ahead",
        "vault_push_disabled",
        "vault_paused",
    } <= ERROR_REASONS


def test_t29_defer_unset_sync_push_on_end():
    """T29 / B32: BRAIN_DEFER_PUSH unset ≡ 0 → mutate sync (push_on_end=True)."""
    vault = MagicMock()
    vault.skipped = False
    vault.push_enabled = True
    vault.is_tip_ahead.return_value = False
    captured: dict = {}

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    def _open(**kwargs):
        captured.update(kwargs)
        return _CM()

    with patch("app.vault_deps.open_vault", side_effect=_open):
        with brain_vault(mode="mutate", env={"GIT_VAULT_PUSH": "1"}):
            pass
    assert captured.get("push_on_end") is True
    assert captured.get("on_push_fail") == "keep_tip"


def test_defer_on_sets_push_on_end_false():
    """A20′: BRAIN_DEFER_PUSH=1 → push_on_end=False (enqueue path)."""
    vault = MagicMock()
    vault.skipped = False
    vault.push_enabled = True
    vault.is_tip_ahead.return_value = False
    captured: dict = {}

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    def _open(**kwargs):
        captured.update(kwargs)
        return _CM()

    with patch("app.vault_deps.open_vault", side_effect=_open):
        with brain_vault(
            mode="mutate",
            env={"GIT_VAULT_PUSH": "1", "BRAIN_DEFER_PUSH": "1"},
        ):
            pass
    assert captured.get("push_on_end") is False


def test_t28_git_enqueue_error_maps_503():
    """T28: GitEnqueueError on session end → vault_push_enqueue_failed 503."""
    from git_io import GitEnqueueError

    vault = MagicMock()
    vault.skipped = False
    vault.push_enabled = True
    vault.is_tip_ahead.return_value = False

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            raise GitEnqueueError(
                "disk full", error_reason="vault_push_enqueue_failed"
            )

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with pytest.raises(BrainVaultError) as ei:
            with brain_vault(
                mode="mutate",
                env={"GIT_VAULT_PUSH": "1", "BRAIN_DEFER_PUSH": "1"},
            ):
                pass
    assert ei.value.error_reason == "vault_push_enqueue_failed"
    assert ei.value.status_code == 503


def test_defer_tip_ahead_allow_healthy_cover(tmp_path: Path):
    """Allow chain: defer=1 + tip ahead + healthy pending → mutate OK."""
    vault = MagicMock()
    vault.skipped = False
    vault.push_enabled = True
    vault.is_tip_ahead.return_value = True
    vault.root = tmp_path

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with patch("push_queue.has_exhausted_failure", return_value=False):
            with patch("push_queue.has_healthy_cover", return_value=True):
                with brain_vault(
                    mode="mutate",
                    env={
                        "GIT_VAULT_PUSH": "1",
                        "BRAIN_DEFER_PUSH": "1",
                        "GIT_VAULT_ROOT": str(tmp_path),
                    },
                ) as v:
                    assert v is vault


def test_defer_tip_ahead_exhausted_fails(tmp_path: Path):
    """Hard gate: defer=1 + exhausted fail → vault_push_pending_failed."""
    vault = MagicMock()
    vault.skipped = False
    vault.push_enabled = True
    vault.is_tip_ahead.return_value = True
    vault.root = tmp_path

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with patch("push_queue.has_exhausted_failure", return_value=True):
            with pytest.raises(BrainVaultError) as ei:
                with brain_vault(
                    mode="mutate",
                    env={"GIT_VAULT_PUSH": "1", "BRAIN_DEFER_PUSH": "1"},
                ):
                    pass
    assert ei.value.error_reason == "vault_push_pending_failed"


def test_defer_orphan_tip_enqueues_cover(tmp_path: Path):
    """Orphan tip (no healthy cover) → enqueue orphan_cover; mutate OK."""
    vault = MagicMock()
    vault.skipped = False
    vault.push_enabled = True
    vault.is_tip_ahead.return_value = True
    vault.root = tmp_path
    enq: dict = {}

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    def _enqueue(root, *, attempts=0, source="brain"):
        enq["root"] = root
        enq["attempts"] = attempts
        enq["source"] = source
        return "job-orphan"

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with patch("push_queue.has_exhausted_failure", return_value=False):
            with patch("push_queue.has_healthy_cover", return_value=False):
                with patch("push_queue.enqueue", side_effect=_enqueue):
                    with brain_vault(
                        mode="mutate",
                        env={
                            "GIT_VAULT_PUSH": "1",
                            "BRAIN_DEFER_PUSH": "1",
                            "GIT_VAULT_ROOT": str(tmp_path),
                        },
                    ) as v:
                        assert v is vault
    assert enq.get("source") == "orphan_cover"
    assert enq.get("attempts") == 0


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


def test_brain_vault_paused_on_mutate():
    class _Paused:
        skipped = False
        push_enabled = True

        def is_tip_ahead(self):
            return False

    vault = _Paused()
    # Simulate factory wrapper name
    vault.__class__ = type("_PausedVault", (_Paused,), {})

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch("app.vault_deps.open_vault", return_value=_CM()):
        with pytest.raises(BrainVaultError) as ei:
            with brain_vault(
                mode="mutate",
                env={"GIT_VAULT_PUSH": "1", "VAULT_WRITERS_PAUSED": "1"},
            ):
                pass
    assert ei.value.error_reason == "vault_paused"


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
