"""read_file — allowlisted vault read (R4)."""
from __future__ import annotations

from typing import Any

from app.errors import BrainClientError
from app.vault_deps import brain_vault

# Prefix allowlist — expand in F2-d policy if needed.
_ALLOWED_PREFIXES = (
    "00-System/",
    "01-INBOX/",
    "02-PROJEKTY/",
    "03-AREAS/",
    "05-RESOURCES/",
    "07-ARCHIV/",
)


def _allowed(rel: str) -> bool:
    norm = rel.replace("\\", "/").lstrip("./")
    if ".." in norm.split("/"):
        return False
    return any(norm.startswith(p) for p in _ALLOWED_PREFIXES)


def read_file(rel_path: str, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    if not _allowed(rel_path):
        raise BrainClientError(
            message=f"path not allowlisted: {rel_path!r}",
            status_code=403,
            error_reason="path_denied",
        )
    with brain_vault(mode="read", env=env) as vault:
        text, meta = vault.read_text(rel_path)
        return {
            "path": rel_path,
            "text": text,
            "oid": getattr(meta, "oid", None),
            "modified_time": str(getattr(meta, "modified_time", None) or ""),
        }
