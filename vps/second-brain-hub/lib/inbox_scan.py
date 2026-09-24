"""Scan 01-INBOX for unprocessed .md files (shared by inbox_inventory)."""
from __future__ import annotations

from typing import Protocol

INBOX_SUBDIRS = ("slack", "sembly", "email", "daily", "Clippings")
_HEADER_PROBE_BYTES = 400


class _VaultLike(Protocol):
    def list_dir(self, rel: str, pattern: str = "*", recursive: bool = False): ...
    def read_text(self, rel: str): ...


class _NotFound(Exception):
    """Raised when vault path is missing — callers catch DriveNotFoundError too."""


def iter_inbox_items(vault: _VaultLike) -> list[tuple[str, str]]:
    """Return list of (rel_path, body) for unprocessed INBOX .md files.

    Skipped:
      * README*.md
      * files whose first ~400 bytes contain "ZPRACOVÁNO" marker
    """
    # Local import keeps lib usable without Drive deps at module load for tests
    # that pass a fake vault.
    try:
        from drive_io import DriveNotFoundError  # type: ignore
    except ImportError:  # pragma: no cover
        DriveNotFoundError = _NotFound  # type: ignore

    items: list[tuple[str, str]] = []
    for sub in INBOX_SUBDIRS:
        sub_rel = f"01-INBOX/{sub}"
        try:
            files = vault.list_dir(sub_rel, pattern="*.md", recursive=True)
        except DriveNotFoundError:
            continue
        for meta in files:
            name = getattr(meta, "name", "") or ""
            rel_path = getattr(meta, "rel_path", "") or ""
            if name.startswith("README"):
                continue
            try:
                body, _ = vault.read_text(rel_path)
            except DriveNotFoundError:
                continue
            if "ZPRACOVÁNO" in body[:_HEADER_PROBE_BYTES]:
                continue
            items.append((rel_path, body))
    return items
