"""Parse GitHub Closes refs and apply them to RBU vault tasks.

Primary signal: commit message / PR title+body containing
``Closes RBU62-1`` (checkbox) or ``Closes RBU62`` (story Done when no open steps).

Only slug ``rb-universe-development`` / prefix ``RBU`` is mutated.
Epics are never closed by this path.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from hierarchy import (
    TYPE_EPIC,
    is_epic,
    mark_checkbox_done,
    normalise_work_type,
    parse_closes_refs,
    split_subtask_ref,
)
from task_io import (
    all_checkboxes_done,
    open_checkbox_count,
    parse_task_text,
    serialize_task,
    update_task,
)

DEFAULT_REPO = "RedButtonEDU/RB-Universe"
DEFAULT_BRANCH = "dev"
STATE_REL = "00-System/github-rbu-closes-state.json"
RBU_SLUG = "rb-universe-development"


@dataclass
class CloseAction:
    ref: str
    kind: str  # "subtask" | "story"
    task_id: str
    subtask_num: str | None = None
    sha: str | None = None
    source: str | None = None


def classify_ref(ref: str) -> CloseAction:
    split = split_subtask_ref(ref)
    if split:
        tid, num = split
        return CloseAction(ref=ref, kind="subtask", task_id=tid, subtask_num=num)
    return CloseAction(ref=ref, kind="story", task_id=ref)


def extract_actions_from_text(text: str, *, sha: str | None = None, source: str | None = None) -> list[CloseAction]:
    actions = []
    for ref in parse_closes_refs(text or ""):
        if not ref.upper().startswith("RBU"):
            continue
        action = classify_ref(ref)
        action.sha = sha
        action.source = source
        actions.append(action)
    return actions


def _gh_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "second-brain-hub-rbu-closes",
    }


def github_get(url: str, token: str) -> Any:
    req = urllib.request.Request(url, headers=_gh_headers(token))
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def fetch_new_commit_messages(
    *,
    token: str,
    repo: str,
    branch: str,
    since_sha: str | None,
    limit: int = 50,
) -> list[dict[str, str]]:
    """Return newest commits on branch (sha, message), stopping after since_sha.

    GitHub ``commits?sha=branch`` returns newest first. We collect until we hit
    ``since_sha`` (exclusive) or ``limit``.
    """
    q = urllib.parse.urlencode({"sha": branch, "per_page": min(limit, 100)})
    url = f"https://api.github.com/repos/{repo}/commits?{q}"
    try:
        data = github_get(url, token)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:500]
        raise RuntimeError(f"GitHub commits failed {e.code}: {body}") from e

    out: list[dict[str, str]] = []
    for item in data:
        sha = item.get("sha") or ""
        if since_sha and sha == since_sha:
            break
        msg = ((item.get("commit") or {}).get("message")) or ""
        out.append({"sha": sha, "message": msg})
        if len(out) >= limit:
            break
    return out


def fetch_merged_pr_bodies(
    *,
    token: str,
    repo: str,
    base: str,
    since_iso: str | None = None,
    limit: int = 30,
) -> list[dict[str, str]]:
    """Merged PRs into base branch (newest first)."""
    q = urllib.parse.urlencode(
        {
            "state": "closed",
            "base": base,
            "sort": "updated",
            "direction": "desc",
            "per_page": min(limit, 100),
        }
    )
    url = f"https://api.github.com/repos/{repo}/pulls?{q}"
    try:
        data = github_get(url, token)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:500]
        raise RuntimeError(f"GitHub pulls failed {e.code}: {body}") from e

    out: list[dict[str, str]] = []
    for pr in data:
        if not pr.get("merged_at"):
            continue
        if since_iso and str(pr.get("merged_at")) < since_iso:
            continue
        title = pr.get("title") or ""
        body = pr.get("body") or ""
        sha = ((pr.get("merge_commit_sha")) or "")
        out.append(
            {
                "sha": sha,
                "message": f"{title}\n\n{body}",
                "source": f"PR#{pr.get('number')}",
            }
        )
        if len(out) >= limit:
            break
    return out


def index_rbu_tasks(tasks: list[Any]) -> dict[str, Any]:
    """Map task id → ParsedTask-like for RBU slug only."""
    by_id: dict[str, Any] = {}
    for t in tasks:
        fm = getattr(t, "frontmatter", None) or (t if isinstance(t, dict) else {})
        slug = str(fm.get("slug") or getattr(t, "slug", "") or "")
        if slug != RBU_SLUG:
            continue
        tid = str(fm.get("id") or getattr(t, "task_id", "") or "")
        if tid:
            by_id[tid] = t
    return by_id


def apply_close_action(
    vault,
    task,
    action: CloseAction,
    *,
    today_str: str,
) -> tuple[str, str]:
    """Apply one CloseAction. Returns (result, detail).

    result ∈ applied | skipped | conflict | not_found | epic_blocked | noop
    """
    if is_epic(task) or normalise_work_type(task.frontmatter.get("type")) == TYPE_EPIC:
        return "epic_blocked", f"{action.ref}: epic cannot be closed via GitHub"

    src = action.source or action.sha or "github"
    if action.kind == "subtask":
        assert action.subtask_num is not None
        new_body, changed = mark_checkbox_done(task.body, action.task_id, action.subtask_num)
        if not changed:
            # Already checked or missing
            if all_checkboxes_done(task.body) and not task.is_terminal:
                # Still try story auto-done below
                pass
            else:
                return "noop", f"{action.ref}: checkbox missing or already [x]"
        else:
            log = (
                f"- {today_str}: `{action.ref}` [x] — auto from GitHub "
                f"({src}). [lifecycle_github_rbu_closes]\n"
            )
            # Re-parse body into task for update
            task.body = new_body
            # If all done after flip → Done
            new_status = None
            if all_checkboxes_done(new_body):
                new_status = "Done"
                log += (
                    f"- {today_str}: Done — auto (všechny operativní kroky [x] "
                    f"po GitHub Closes). [lifecycle_github_rbu_closes]\n"
                )
            ok = update_task(
                vault,
                task,
                new_status=new_status,
                today_str=today_str,
                body_append=log,
            )
            return ("applied" if ok else "conflict"), action.ref

    # Story-level Closes
    if open_checkbox_count(task.body) > 0:
        return (
            "skipped",
            f"{action.ref}: open checkboxes remain — not marking story Done",
        )
    if task.is_terminal:
        return "noop", f"{action.ref}: already terminal"
    log = (
        f"- {today_str}: Done — auto from GitHub Closes {action.ref} "
        f"({src}). [lifecycle_github_rbu_closes]\n"
    )
    ok = update_task(
        vault,
        task,
        new_status="Done",
        today_str=today_str,
        body_append=log,
    )
    return ("applied" if ok else "conflict"), action.ref


def load_state(vault) -> dict[str, Any]:
    try:
        text, _ = vault.read_text(STATE_REL)
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(vault, state: dict[str, Any]) -> None:
    text = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    # No CAS — single writer cron owns this file
    vault.write_text(STATE_REL, text, expect_mtime=None)
