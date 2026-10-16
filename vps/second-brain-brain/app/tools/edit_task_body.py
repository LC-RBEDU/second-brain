"""edit_task_body — one body line. Frontmatter stays. Write only with confirm."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from context_tombstone import delete_context_tombstone  # noqa: E402
from drive_io import DriveConflictError, DriveNotFoundError  # noqa: E402

from app.errors import BrainClientError
from app.tools.task_catalog import file_hash, split_frontmatter
from app.vault_deps import brain_vault

_TRACE = "→ [["


def _require_provenance(source: str | None, reason: str | None) -> tuple[str, str]:
    src = (source or "").strip()
    why = (reason or "").strip()
    if not src or not why:
        raise BrainClientError(
            message="source and reason are required",
            status_code=400,
            error_reason="missing_provenance",
        )
    return src, why


def _stamp(source: str, reason: str) -> str:
    now = datetime.now(ZoneInfo("Europe/Prague")).strftime("%Y-%m-%d %H:%M")
    return f"- {now} · {source} · {reason}\n"


def _apply_op(lines: list[str], index: int, operation: str, new_text: str) -> list[str]:
    if operation == "delete_line":
        return lines[:index] + lines[index + 1 :]
    if operation == "replace":
        replacement = new_text if new_text.endswith("\n") else new_text + "\n"
        return lines[:index] + [replacement] + lines[index + 1 :]
    if operation == "insert_after":
        inserted = new_text if new_text.endswith("\n") else new_text + "\n"
        return lines[: index + 1] + [inserted] + lines[index + 1 :]
    raise BrainClientError(
        message="operation must be replace, delete_line, or insert_after",
        status_code=400,
        error_reason="bad_operation",
    )


def edit_task_body(
    *,
    path: str,
    operation: str,
    match: str | int,
    new_text: str = "",
    expected_hash: str | None = None,
    expect_oid: str | None = None,
    confirm: bool = False,
    dry_run: bool = False,
    allow_migration_trace: bool = False,
    source: str | None = None,
    reason: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    src, why = _require_provenance(source, reason)
    mode = "read" if dry_run or not confirm else "mutate"
    with brain_vault(mode=mode, env=env) as vault:
        if mode == "mutate":
            delete_context_tombstone(vault)
        try:
            text, meta = vault.read_text(path)
        except DriveNotFoundError as exc:
            raise BrainClientError(message="not_found", status_code=404, error_reason="not_found") from exc
        oid = getattr(meta, "oid", None)
        if expect_oid is not None and oid is not None and str(oid) != str(expect_oid):
            raise BrainClientError(message="cas_conflict", status_code=409, error_reason="cas_conflict")
        digest = file_hash(text)
        if confirm and not dry_run:
            if not expected_hash or expected_hash != digest:
                raise BrainClientError(message="hash_mismatch", status_code=409, error_reason="hash_mismatch")
        header, body = split_frontmatter(text)
        if not header:
            raise BrainClientError(message="no frontmatter", status_code=400, error_reason="no_frontmatter")
        full_lines = text.splitlines(keepends=True)
        body_start = text[: len(header)].count("\n")
        if isinstance(match, int) or (isinstance(match, str) and match.isdigit()):
            number = int(match)
            if number < 1 or number > len(full_lines):
                raise BrainClientError(message="line_out_of_range", status_code=400, error_reason="bad_match")
            index = number - 1
            if index < body_start:
                raise BrainClientError(
                    message="frontmatter is update_task",
                    status_code=400,
                    error_reason="frontmatter_locked",
                )
            indexes = [index]
        else:
            needle = str(match)
            indexes = [
                i
                for i, line in enumerate(full_lines)
                if i >= body_start and line.rstrip("\n") == needle
            ]
        if len(indexes) != 1:
            raise BrainClientError(
                message=f"match_count={len(indexes)}",
                status_code=409,
                error_reason="match_not_unique",
            )
        index = indexes[0]
        if _TRACE in full_lines[index] and not allow_migration_trace:
            raise BrainClientError(
                message="migration trace is locked",
                status_code=409,
                error_reason="migration_trace_locked",
            )
        new_lines = _apply_op(full_lines, index, operation, new_text)
        new_text_full = "".join(new_lines)
        if not new_text_full.endswith("\n"):
            new_text_full += "\n"
        header2, body2 = split_frontmatter(new_text_full)
        log = _stamp(src, why)
        if "## Poznámky / log" in body2:
            body2 = body2.rstrip() + "\n" + log
        else:
            body2 = body2.rstrip() + "\n\n## Poznámky / log\n" + log
        new_text_full = header2 + body2
        if not new_text_full.endswith("\n"):
            new_text_full += "\n"
        diff = {"before_hash": digest, "operation": operation, "line": index + 1}
        if dry_run or not confirm:
            return {"path": path, "dry_run": True, "written": False, "diff": diff, "hash": digest}
        try:
            kwargs: dict[str, Any] = {}
            if expect_oid is not None:
                kwargs["expect_oid"] = expect_oid
            meta2 = vault.write_text(path, new_text_full, **kwargs)
        except DriveConflictError as exc:
            raise BrainClientError(message=str(exc), status_code=409, error_reason="cas_conflict") from exc
        return {
            "path": path,
            "written": True,
            "oid": getattr(meta2, "oid", None),
            "hash": file_hash(new_text_full),
            "diff": diff,
        }
