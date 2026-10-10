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

from git_io import GitPushError  # noqa: E402
from vault_factory import VaultPausedError, open_vault  # noqa: E402

from app.errors import BrainClientError, BrainVaultError, vault_error  # noqa: E402

VaultMode = Literal["read", "mutate", "rebuild"]

# A62: retry 1–2× only vault_flock_busy (initial + up to 2 retries).
_FLOCK_MAX_ATTEMPTS = 3
_FLOCK_RETRY_SLEEP_S = 0.15


def _env_flag(env: Mapping[str, str], key: str) -> bool:
    raw = (env.get(key) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


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


def _gate_after_open(vault: Any, *, mode: VaultMode, env: Mapping[str, str]) -> None:
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
        if _tip_ahead(vault):
            raise vault_error("vault_tip_ahead")


def _open_and_gate(
    *, mode: VaultMode, env: Mapping[str, str]
) -> tuple[Any, Any]:
    """Enter open_vault + A60 gate. On flock_busy may raise for retry."""
    cm = open_vault(
        env=env,
        strict_push=True,
        discard_dirty_on_error=True,
    )
    vault = cm.__enter__()
    try:
        _gate_after_open(vault, mode=mode, env=env)
    except (BrainVaultError, BrainClientError):
        cm.__exit__(None, None, None)
        raise
    return cm, vault


@contextmanager
def brain_vault(
    *,
    mode: VaultMode,
    env: Mapping[str, str] | None = None,
) -> Iterator[Any]:
    """Open vault with Brain flags; apply A60 gate; map GitPushError → 503.

    Tools/rest MUST use this — never bare ``open_vault`` (A64).
    """
    if mode not in ("read", "mutate", "rebuild"):
        raise ValueError(f"mode must be read|mutate|rebuild, got {mode!r}")
    env_map: Mapping[str, str] = env if env is not None else os.environ

    cm: Any = None
    vault: Any = None
    for attempt in range(_FLOCK_MAX_ATTEMPTS):
        try:
            cm, vault = _open_and_gate(mode=mode, env=env_map)
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
        if isinstance(exc, GitPushError):
            raise vault_error(
                getattr(exc, "error_reason", None) or "vault_push_reset_ok",
                str(exc) or None,
            ) from exc
        if not suppress:
            raise
    else:
        try:
            cm.__exit__(None, None, None)
        except GitPushError as exc:
            raise vault_error(
                getattr(exc, "error_reason", None) or "vault_push_reset_ok",
                str(exc) or None,
            ) from exc
