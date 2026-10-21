"""Durable async push job registry under ``{GIT_VAULT_ROOT}/.git/`` (A27)."""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Mapping

log = logging.getLogger("push_queue")

QUEUE_FILENAME = "second-brain-push-queue.json"
MAX_ATTEMPTS = 3  # N=3 (A19)

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_FAILED = "failed"
STATUS_DONE = "done"

_HEALTHY = frozenset({STATUS_PENDING, STATUS_RUNNING})


def queue_path(root: str | Path) -> Path:
    return Path(root) / ".git" / QUEUE_FILENAME


def _empty() -> dict[str, Any]:
    return {"jobs": [], "updated_at": time.time()}


def load_queue(root: str | Path) -> dict[str, Any]:
    path = queue_path(root)
    if not path.is_file():
        return _empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("push_queue: corrupt %s (%s) — treating empty", path, exc)
        return _empty()
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        return _empty()
    return data


def save_queue_atomic(root: str | Path, data: Mapping[str, Any]) -> None:
    """Atomic write into ``.git/`` (same filesystem as queue). Raises OSError."""
    git_dir = Path(root) / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)
    path = queue_path(root)
    payload = dict(data)
    payload["updated_at"] = time.time()
    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=".push-queue-", dir=str(git_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(raw)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def has_healthy_cover(root: str | Path) -> bool:
    """True when a pending/running job exists (Allow chain / not orphan)."""
    data = load_queue(root)
    return any(
        isinstance(j, dict) and j.get("status") in _HEALTHY for j in data["jobs"]
    )


def has_exhausted_failure(root: str | Path) -> bool:
    """True when a failed job with attempts >= MAX_ATTEMPTS remains (hard gate)."""
    data = load_queue(root)
    for j in data["jobs"]:
        if not isinstance(j, dict):
            continue
        if j.get("status") != STATUS_FAILED:
            continue
        try:
            attempts = int(j.get("attempts") or 0)
        except (TypeError, ValueError):
            attempts = 0
        if attempts >= MAX_ATTEMPTS:
            return True
    return False


def enqueue(
    root: str | Path,
    *,
    attempts: int = 0,
    source: str = "brain",
) -> str:
    """Append a pending job. Returns job id. Raises OSError on I/O failure."""
    data = load_queue(root)
    job_id = uuid.uuid4().hex
    data["jobs"].append(
        {
            "id": job_id,
            "status": STATUS_PENDING,
            "attempts": int(attempts),
            "source": source,
            "created_at": time.time(),
        }
    )
    save_queue_atomic(root, data)
    return job_id


def next_pending(root: str | Path) -> dict[str, Any] | None:
    data = load_queue(root)
    for j in data["jobs"]:
        if isinstance(j, dict) and j.get("status") == STATUS_PENDING:
            return j
    return None


def update_job(
    root: str | Path,
    job_id: str,
    *,
    status: str | None = None,
    attempts: int | None = None,
    last_error: str | None = None,
) -> None:
    data = load_queue(root)
    found = False
    for j in data["jobs"]:
        if not isinstance(j, dict) or j.get("id") != job_id:
            continue
        found = True
        if status is not None:
            j["status"] = status
        if attempts is not None:
            j["attempts"] = int(attempts)
        if last_error is not None:
            j["last_error"] = last_error
        j["updated_at"] = time.time()
        break
    if not found:
        raise KeyError(job_id)
    # Drop done jobs to keep file small
    data["jobs"] = [
        j
        for j in data["jobs"]
        if not (isinstance(j, dict) and j.get("status") == STATUS_DONE)
    ]
    save_queue_atomic(root, data)


def clear_synced(root: str | Path) -> None:
    """After tip == upstream: drop pending/running/failed cover jobs."""
    data = load_queue(root)
    data["jobs"] = []
    save_queue_atomic(root, data)
