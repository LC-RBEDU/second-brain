"""Request-scoped brain_vault — central tip/PUSH/PAUSED/skip gate (A60–A64)."""
from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Literal, Mapping

# Coolify image: /app/lib/; local: ../second-brain-hub/lib/
for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[2] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from git_io import GitEnqueueError, GitPushError  # noqa: E402
from vault_factory import VaultPausedError, open_vault  # noqa: E402

from app.errors import BrainClientError, BrainVaultError, vault_error  # noqa: E402

VaultMode = Literal["read", "mutate", "rebuild"]

# A62: retry 1–2× only vault_flock_busy (initial + up to 2 retries).
_FLOCK_MAX_ATTEMPTS = 3
_FLOCK_RETRY_SLEEP_S = 0.15


def _env_flag(env: Mapping[str, str], key: str) -> bool:
    """2-arg flag (A52″). unset / \"\" → False. No ``default=`` (≠ git_io._env_flag)."""
    raw = (env.get(key) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def defer_push_enabled(env: Mapping[str, str]) -> bool:
    """BRAIN_DEFER_PUSH truthy → async enqueue (F3c). Default off (unset≡0)."""
    return _env_flag(env, "BRAIN_DEFER_PUSH")


def _is_paused_wrapper(vault: Any) -> bool:
    return type(vault).__name__ == "_PausedVault"


def _push_enabled(vault: Any, env: Mapping[str, str]) -> bool:
    if hasattr(vault, "push_enabled"):
        return bool(vault.push_enabled)
    inner = getattr(vault, "_inner", None)
    if inner is not None and hasattr(inner, "push_enabled"):
        return bool(inner.push_enabled)
    return _env_flag(env, "GIT_VAULT_PUSH")


def _tip_ahead(vault: Any) -> bool:
    fn = getattr(vault, "is_tip_ahead", None)
    if callable(fn):
        return bool(fn())
    inner = getattr(vault, "_inner", None)
    if inner is not None:
        fn = getattr(inner, "is_tip_ahead", None)
        if callable(fn):
            return bool(fn())
    return False


def _vault_root(vault: Any, env: Mapping[str, str]) -> Path:
    root = getattr(vault, "root", None)
    if root is not None:
        return Path(root)
    inner = getattr(vault, "_inner", None)
    if inner is not None and getattr(inner, "root", None) is not None:
        return Path(inner.root)
    return Path(env.get("GIT_VAULT_ROOT") or "/data/vault")


def _gate_tip_for_writers(
    vault: Any, *, env: Mapping[str, str], defer: bool
) -> None:
    """Tip-gate: defer=0 → any tip-ahead 503; defer=1 → Allow chain / hard fail."""
    if not _tip_ahead(vault):
        return
    if not defer:
        raise vault_error("vault_tip_ahead")
    # Defer=1: Allow chain when healthy pending; hard gate on exhausted fail / orphan.
    try:
        from push_queue import (  # noqa: WPS433
            enqueue,
            has_exhausted_failure,
            has_healthy_cover,
        )
    except ImportError:
        raise vault_error("vault_tip_ahead") from None

    root = _vault_root(vault, env)
    if has_exhausted_failure(root):
        raise vault_error("vault_push_pending_failed")
    if has_healthy_cover(root):
        return  # Allow chain (R18)
    # Orphan tip: ensure cover job (attempts=0) so worker can recover (A29″ hub-like).
    try:
        enqueue(root, attempts=0, source="orphan_cover")
    except OSError as exc:
        raise vault_error(
            "vault_push_enqueue_failed",
            f"orphan tip cover enqueue failed: {exc}",
        ) from exc


def _gate_after_open(
    vault: Any, *, mode: VaultMode, env: Mapping[str, str], defer: bool
) -> None:
    """A60 steps (1)–(4). Raises BrainVaultError → 503."""
    if bool(getattr(vault, "skipped", False)):
        reason = getattr(vault, "skip_reason", None)
        if not reason:
            # A56 — never invent vault_dirty_start from bare skipped
            raise BrainClientError(
                message="vault.skipped without skip_reason — misconfigured session (A56)",
                status_code=500,
                error_reason="misconfigured_session",
            )
        raise vault_error(str(reason))

    if mode in ("mutate", "rebuild"):
        if _is_paused_wrapper(vault) or _env_flag(env, "VAULT_WRITERS_PAUSED"):
            raise vault_error("vault_paused")
        if not _push_enabled(vault, env):
            raise vault_error("vault_push_disabled")
        _gate_tip_for_writers(vault, env=env, defer=defer)


def _session_flags(
    mode: VaultMode, check_dirty: bool, *, defer: bool
) -> dict[str, Any]:
    """Read never fetches, commits, or resets. Mutate and rebuild always do.

    A20′: ``push_on_end=False`` only when BRAIN_DEFER_PUSH is active.
    """
    if mode == "read":
        return {
            "fetch_on_begin": False,
            "check_dirty_on_begin": check_dirty,
            "commit_on_end": False,
            "discard_dirty_on_error": False,
            "push_on_end": True,
            "on_push_fail": "keep_tip",
        }
    return {
        "fetch_on_begin": True,
        "check_dirty_on_begin": True,
        "commit_on_end": True,
        "discard_dirty_on_error": True,
        "push_on_end": not defer,
        "on_push_fail": "keep_tip",
    }


def _open_and_gate(
    *, mode: VaultMode, env: Mapping[str, str], check_dirty: bool, defer: bool
) -> tuple[Any, Any]:
    """Enter open_vault + A60 gate. On flock_busy may raise for retry."""
    cm = open_vault(
        env=env,
        strict_push=True,
        **_session_flags(mode, check_dirty, defer=defer),
    )
    vault = cm.__enter__()
    try:
        _gate_after_open(vault, mode=mode, env=env, defer=defer)
    except (BrainVaultError, BrainClientError):
        cm.__exit__(None, None, None)
        raise
    return cm, vault


def _map_git_exit_error(exc: BaseException) -> None:
    if isinstance(exc, (GitPushError, GitEnqueueError)):
        raise vault_error(
            getattr(exc, "error_reason", None) or "vault_push_reset_ok",
            str(exc) or None,
        ) from exc


@contextmanager
def brain_vault(
    *,
    mode: VaultMode,
    env: Mapping[str, str] | None = None,
    check_dirty: bool = True,
) -> Iterator[Any]:
    """Open vault with Brain flags; apply A60 gate; map GitPush/Enqueue → 503.

    Tools/rest MUST use this — never bare ``open_vault`` (A64).
    ``check_dirty`` applies only to ``mode="read"``. Mutate and rebuild always
    fetch, check dirty, commit. With ``BRAIN_DEFER_PUSH=1`` they enqueue instead
    of sync push (Keep tip).
    """
    if mode not in ("read", "mutate", "rebuild"):
        raise ValueError(f"mode must be read|mutate|rebuild, got {mode!r}")
    env_map: Mapping[str, str] = env if env is not None else os.environ
    defer = defer_push_enabled(env_map)

    cm: Any = None
    vault: Any = None
    for attempt in range(_FLOCK_MAX_ATTEMPTS):
        try:
            cm, vault = _open_and_gate(
                mode=mode, env=env_map, check_dirty=check_dirty, defer=defer
            )
            break
        except BrainVaultError as exc:
            if (
                exc.error_reason == "vault_flock_busy"
                and attempt + 1 < _FLOCK_MAX_ATTEMPTS
            ):
                time.sleep(_FLOCK_RETRY_SLEEP_S)
                continue
            raise
    else:
        raise vault_error("vault_flock_busy")

    assert cm is not None and vault is not None
    try:
        yield vault
    except VaultPausedError as exc:
        cm.__exit__(type(exc), exc, exc.__traceback__)
        raise vault_error("vault_paused", str(exc)) from exc
    except BaseException as exc:
        suppress = cm.__exit__(type(exc), exc, exc.__traceback__)
        _map_git_exit_error(exc)
        if not suppress:
            raise
    else:
        try:
            cm.__exit__(None, None, None)
        except (GitPushError, GitEnqueueError) as exc:
            _map_git_exit_error(exc)
