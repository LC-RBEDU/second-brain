#!/usr/bin/env python3
"""Local safe-write helpers for vault mutations (VC7 backup/CAS-lite)."""
from __future__ import annotations

import hashlib
import shutil
from datetime import datetime
from pathlib import Path


class WriteConflictError(RuntimeError):
    """Raised when on-disk content changed since pre-image."""


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def backup_files(paths: list[Path], vault: Path, ts: str | None = None) -> Path:
    """Copy files to 07-ARCHIV/_backups/<ts>/ preserving relative paths."""
    stamp = ts or datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = vault / "07-ARCHIV" / "_backups" / stamp
    for p in paths:
        if not p.exists():
            continue
        try:
            rel = p.relative_to(vault)
        except ValueError:
            rel = Path(p.name)
        dest = backup_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    return backup_root


def safe_write_text(path: Path, new_content: str, *, expected_hash: str | None = None) -> None:
    """Write with pre-read hash check (content-addressable lite)."""
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if expected_hash is not None and content_hash(current) != expected_hash:
            raise WriteConflictError(f"Conflict writing {path}: content changed")
    else:
        if expected_hash is not None:
            raise WriteConflictError(f"Conflict writing {path}: file appeared")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_content, encoding="utf-8")
    if not new_content.strip() and path.suffix == ".md":
        raise ValueError(f"Refusing empty write to {path}")
    tmp.replace(path)


def atomic_write_text(path: Path, new_content: str) -> None:
    """Temp file + replace (materialization pipeline)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_content, encoding="utf-8")
    tmp.replace(path)
