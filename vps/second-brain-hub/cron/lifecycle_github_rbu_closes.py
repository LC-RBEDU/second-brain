#!/usr/bin/env python3
"""Apply ``Closes RBU*`` from GitHub (branch ``dev``) onto vault RBU tasks.

Reads commits (and optionally merged PRs) since the last processed SHA,
parses Closes/Fixes/Resolves refs, and CAS-updates matching task files under
``02-PROJEKTY/rb-universe-development/tasks/``.

Env:
  VAULT_DRIVE_ID          — required
  GITHUB_TOKEN            — required (repo read)
  RBU_GITHUB_REPO         — default RedButtonEDU/RB-Universe
  RBU_GITHUB_BRANCH       — default dev
  RBU_GITHUB_INCLUDE_PRS  — ``1`` to also scan merged PR title/body (default 1)

State: ``00-System/github-rbu-closes-state.json`` (last sha + timestamp).
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveVault, credentials_from_env  # noqa: E402
from github_rbu_closes import (  # noqa: E402
    DEFAULT_BRANCH,
    DEFAULT_REPO,
    apply_close_action,
    extract_actions_from_text,
    fetch_merged_pr_bodies,
    fetch_new_commit_messages,
    index_rbu_tasks,
    load_state,
    save_state,
)
from task_io import iter_active_tasks  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def main() -> None:
    root_id = (os.environ.get("VAULT_DRIVE_ID") or "").strip()
    if not root_id:
        raise RuntimeError("VAULT_DRIVE_ID env not set")
    token = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not token:
        print("lifecycle_github_rbu_closes: GITHUB_TOKEN not set — skip")
        return

    repo = (os.environ.get("RBU_GITHUB_REPO") or DEFAULT_REPO).strip()
    branch = (os.environ.get("RBU_GITHUB_BRANCH") or DEFAULT_BRANCH).strip()
    include_prs = (os.environ.get("RBU_GITHUB_INCLUDE_PRS") or "1").strip() not in {
        "0",
        "false",
        "no",
    }

    creds, _ = credentials_from_env()
    vault = DriveVault(root_id, credentials=creds)
    today = datetime.now(TZ).date().isoformat()
    state = load_state(vault)
    since_sha = state.get("last_sha")

    commits = fetch_new_commit_messages(
        token=token, repo=repo, branch=branch, since_sha=since_sha
    )
    events: list[dict[str, str]] = list(commits)
    if include_prs:
        since_iso = state.get("last_pr_merged_at")
        try:
            events.extend(
                fetch_merged_pr_bodies(
                    token=token, repo=repo, base=branch, since_iso=since_iso
                )
            )
        except Exception as e:
            print(f"  ! PR scan skipped: {e}")

    # Newest-first from API; process oldest-first so state advances correctly
    events_chrono = list(reversed(events))

    actions = []
    for ev in events_chrono:
        actions.extend(
            extract_actions_from_text(
                ev.get("message") or "",
                sha=ev.get("sha"),
                source=ev.get("source") or ev.get("sha"),
            )
        )

    by_id = index_rbu_tasks(list(iter_active_tasks(vault)))
    counts = {
        "applied": 0,
        "skipped": 0,
        "conflict": 0,
        "not_found": 0,
        "epic_blocked": 0,
        "noop": 0,
    }

    seen_refs: set[str] = set()
    for action in actions:
        dedupe = f"{action.ref}@{action.sha}"
        if dedupe in seen_refs:
            continue
        seen_refs.add(dedupe)
        task = by_id.get(action.task_id)
        if not task:
            counts["not_found"] += 1
            print(f"  ? {action.ref} — no active RBU task {action.task_id}")
            continue
        # Re-read for CAS freshness
        try:
            text, meta = vault.read_text(task.rel_path)
            from task_io import parse_task_text

            task = parse_task_text(text, rel_path=task.rel_path, meta=meta)
            by_id[action.task_id] = task
        except Exception as e:
            counts["conflict"] += 1
            print(f"  ! re-read failed {action.task_id}: {e}")
            continue

        result, detail = apply_close_action(vault, task, action, today_str=today)
        counts[result] = counts.get(result, 0) + 1
        print(f"  {result}: {detail}")
        if result == "applied":
            # Refresh index entry after write
            try:
                text, meta = vault.read_text(task.rel_path)
                from task_io import parse_task_text

                by_id[action.task_id] = parse_task_text(
                    text, rel_path=task.rel_path, meta=meta
                )
            except Exception:
                pass

    new_state = dict(state)
    if commits:
        # commits list is newest-first
        new_state["last_sha"] = commits[0]["sha"]
    new_state["last_run"] = datetime.now(TZ).isoformat(timespec="seconds")
    new_state["repo"] = repo
    new_state["branch"] = branch
    try:
        save_state(vault, new_state)
    except Exception as e:
        print(f"  ! state save failed: {e}")

    print(
        "lifecycle_github_rbu_closes: "
        f"events={len(events)} actions={len(actions)} "
        + " ".join(f"{k}={v}" for k, v in counts.items())
    )


if __name__ == "__main__":
    main()
