"""Vault backend factory: DriveVault | GitVault + writers-paused kill-switch."""
from __future__ import annotations

import os
from typing import Any, Mapping


class VaultPausedError(RuntimeError):
    """Raised when VAULT_WRITERS_PAUSED=1 blocks a mutate operation."""


_MUTATE_METHODS = frozenset(
    {
        "write_text",
        "write_bytes",
        "write_json",
        "mkdir_p",
        "mkdir",
        "move",
        "delete",
    }
)


class _PausedVault:
    """Proxy that rejects mutate methods while forwarding reads / context mgr."""

    def __init__(self, inner: Any) -> None:
        object.__setattr__(self, "_inner", inner)

    def __getattr__(self, name: str) -> Any:
        if name in _MUTATE_METHODS:
            def _blocked(*_a: Any, **_k: Any) -> Any:
                raise VaultPausedError(
                    f"VAULT_WRITERS_PAUSED=1 — refused {name}()"
                )

            return _blocked
        return getattr(self._inner, name)

    def __enter__(self) -> "_PausedVault":
        enter = getattr(self._inner, "__enter__", None)
        if callable(enter):
            enter()
        return self

    def __exit__(self, exc_type, exc, tb) -> Any:
        exit_fn = getattr(self._inner, "__exit__", None)
        if callable(exit_fn):
            return exit_fn(exc_type, exc, tb)
        return None


def _flag(env: Mapping[str, str], key: str) -> bool:
    raw = (env.get(key) or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def open_vault(*, env: Mapping[str, str] | None = None):
    """Return DriveVault or GitVault according to VAULT_BACKEND (default drive).

    Prefer: ``with open_vault() as vault:``.
    When ``VAULT_WRITERS_PAUSED=1``, mutate methods raise ``VaultPausedError``.
    """
    env_map = env if env is not None else os.environ
    backend = (env_map.get("VAULT_BACKEND") or "drive").strip().lower() or "drive"

    if backend == "git":
        from git_io import GitVault

        vault: Any = GitVault(env=env_map)
    elif backend == "drive":
        from drive_io import DriveVault, credentials_from_env

        root_id = (env_map.get("VAULT_DRIVE_ID") or "").strip()
        if not root_id:
            raise RuntimeError("VAULT_DRIVE_ID env not set")
        creds, _ = credentials_from_env(env_map)
        vault = DriveVault(root_id, credentials=creds)
    else:
        raise ValueError(f"Unknown VAULT_BACKEND={backend!r} (expected drive|git)")

    if _flag(env_map, "VAULT_WRITERS_PAUSED"):
        return _PausedVault(vault)
    return vault
