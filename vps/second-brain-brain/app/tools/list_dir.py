"""list_dir — allowlisted vault listing (R4)."""
from __future__ import annotations

from typing import Any

from app.errors import BrainClientError
from app.tools.read_file import _allowed
from app.vault_deps import brain_vault


def list_dir(
    rel_path: str,
    *,
    pattern: str | None = None,
    recursive: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not _allowed(rel_path) and rel_path not in ("", "."):
        # allow listing roots that are prefixes
        if not any(
            rel_path.rstrip("/") + "/" == p or p.startswith(rel_path.rstrip("/") + "/")
            for p in (
                "00-System/",
                "01-INBOX/",
                "02-PROJEKTY/",
                "03-AREAS/",
                "05-RESOURCES/",
                "07-ARCHIV/",
            )
        ):
            raise BrainClientError(
                message=f"path not allowlisted: {rel_path!r}",
                status_code=403,
                error_reason="path_denied",
            )
    with brain_vault(mode="read", env=env) as vault:
        metas = vault.list_dir(
            rel_path or "",
            pattern=pattern,
            recursive=recursive,
            include_folders=True,
        )
        return {
            "path": rel_path,
            "entries": [
                {
                    "name": getattr(m, "name", ""),
                    "rel_path": getattr(m, "rel_path", ""),
                    "is_folder": bool(getattr(m, "is_folder", False)),
                }
                for m in metas
            ],
        }
