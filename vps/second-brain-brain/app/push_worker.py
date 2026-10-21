"""Brain lifespan worker: drain durable push queue via push_tip_ff_only (A41–A42)."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

log = logging.getLogger("push_worker")

# Coolify: /app/lib/; local hub lib
for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[2] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break


def _poll_s() -> float:
    """Poll interval; clamp to [0.5, 5] so env cannot exceed B25 budget."""
    raw = (os.environ.get("BRAIN_PUSH_POLL_S") or "5").strip()
    try:
        return min(5.0, max(0.5, float(raw)))
    except ValueError:
        return 5.0


def _defer_on() -> bool:
    return (os.environ.get("BRAIN_DEFER_PUSH") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _vault_root() -> Path:
    return Path(os.environ.get("GIT_VAULT_ROOT") or "/data/vault")


def process_one_job() -> bool:
    """Process at most one pending job. Returns True if work was attempted."""
    from push_queue import (  # noqa: WPS433
        MAX_ATTEMPTS,
        STATUS_FAILED,
        STATUS_PENDING,
        STATUS_RUNNING,
        clear_synced,
        load_queue,
        next_pending,
        update_job,
    )
    from vault_factory import open_vault

    root = _vault_root()
    job = next_pending(root)
    if job is None:
        # Tip already sync → clear any leftover failed cover
        with open_vault(
            env=os.environ,
            strict_push=False,
            commit_on_end=False,
            fetch_on_begin=False,
            check_dirty_on_begin=False,
            on_push_fail="keep_tip",
        ) as vault:
            if not vault.is_tip_ahead():
                data = load_queue(root)
                if data.get("jobs"):
                    clear_synced(root)
        return False

    job_id = str(job["id"])
    attempts = int(job.get("attempts") or 0)
    update_job(root, job_id, status=STATUS_RUNNING)

    try:
        with open_vault(
            env=os.environ,
            strict_push=True,
            commit_on_end=False,
            fetch_on_begin=False,
            check_dirty_on_begin=False,
            push_on_end=True,
            on_push_fail="keep_tip",
        ) as vault:
            if not vault.is_tip_ahead():
                clear_synced(root)
                return True
            vault.push_enabled = True
            vault.push_tip_ff_only()
            if not vault.is_tip_ahead():
                clear_synced(root)
            else:
                # keep_tip without raise (strict off path) — treat as fail attempt
                raise RuntimeError("push returned but tip still ahead")
    except Exception as exc:  # noqa: BLE001
        attempts += 1
        err = str(exc)[:500]
        log.warning(
            "push_worker: job %s attempt %s/%s failed: %s",
            job_id,
            attempts,
            MAX_ATTEMPTS,
            err,
        )
        if attempts >= MAX_ATTEMPTS:
            update_job(
                root,
                job_id,
                status=STATUS_FAILED,
                attempts=attempts,
                last_error=err,
            )
        else:
            update_job(
                root,
                job_id,
                status=STATUS_PENDING,
                attempts=attempts,
                last_error=err,
            )
        return True
    return True


async def push_worker_loop(stop: asyncio.Event) -> None:
    """Poll ≤ BRAIN_PUSH_POLL_S (default 5). No-op when BRAIN_DEFER_PUSH off."""
    while not stop.is_set():
        if _defer_on():
            try:
                await asyncio.to_thread(process_one_job)
            except Exception as exc:  # noqa: BLE001
                log.exception("push_worker: loop error: %s", exc)
        try:
            await asyncio.wait_for(stop.wait(), timeout=_poll_s())
        except asyncio.TimeoutError:
            continue


def wake_push_worker(app: Any) -> None:
    """Optional HTTP wake: nudge event so loop runs sooner (bonus, not required)."""
    ev = getattr(app.state, "push_wake", None)
    if isinstance(ev, asyncio.Event):
        ev.set()
