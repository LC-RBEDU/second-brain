"""update_task — CAS patch of frontmatter fields. Focus goes through propose/apply."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from deadline_order import (  # noqa: E402
    DeadlineNode,
    evaluate_deadline_order,
    node_from_frontmatter,
)
from drive_io import DriveConflictError  # noqa: E402
from hierarchy import parse_parent_id  # noqa: E402
from task_io import iter_active_tasks, parse_task_text  # noqa: E402

from app.errors import BrainClientError
from app.tools.materials_yaml import normalize_materials
from app.tools.open_child import assert_no_open_child
from app.tools.parent_link import check_overlay, needs_forest
from app.policy import FOCUS_PROPOSAL_MESSAGE, deny_focus_write, deny_stav_auto_write
from app.vault_deps import brain_vault

_FM_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)


def _yaml_scalar(val: str) -> str:
    if any(c in val for c in (":", "#", "[", "]", "{", "}", ",", '"', "'")) or val.startswith(
        "[["
    ) or "://" in val or val.startswith(" ") or val.endswith(" "):
        escaped = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return val


def _yaml_value(key: str, val: Any) -> str:
    if val is None or val == "":
        return f"{key}:\n"
    if isinstance(val, list):
        items = [str(item).strip() for item in val if str(item or "").strip()]
        if not items:
            return f"{key}: []\n"
        out = [f"{key}:\n"]
        for item in items:
            out.append(f"  - {_yaml_scalar(item)}\n")
        return "".join(out)
    if isinstance(val, str) and (":" in val or val.startswith("[[") or "://" in val):
        return f"{key}: {_yaml_scalar(val)}\n"
    return f"{key}: {val}\n"


def _is_yaml_key_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("-"):
        return False
    if line[:1] in (" ", "\t"):
        return False
    return ":" in line


def _skip_yaml_value(lines: list[str], start: int) -> int:
    """After replacing a key line at start-1, skip its old multi-line value."""
    i = start
    while i < len(lines):
        raw = lines[i]
        if _is_yaml_key_line(raw):
            break
        if not raw.strip():
            # blank line: keep if next is a new key, else part of block
            if i + 1 < len(lines) and _is_yaml_key_line(lines[i + 1]):
                break
            i += 1
            continue
        if raw.startswith(" ") or raw.startswith("\t") or raw.lstrip().startswith("-"):
            i += 1
            continue
        break
    return i


def render_frontmatter_patch(text: str, patch: dict[str, Any]) -> str:
    matched = _FM_RE.match(text)
    if not matched:
        raise BrainClientError(message="no frontmatter", status_code=400, error_reason="no_frontmatter")
    fm_raw, body = matched.group(1), matched.group(2)
    lines = fm_raw.splitlines(keepends=True)
    keys_done: set[str] = set()
    new_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _is_yaml_key_line(line):
            key = line.split(":", 1)[0].strip()
            if key in patch:
                new_lines.append(_yaml_value(key, patch[key]))
                keys_done.add(key)
                i = _skip_yaml_value(lines, i + 1)
                continue
        new_lines.append(line if line.endswith("\n") else line + "\n")
        i += 1
    for key, val in patch.items():
        if key not in keys_done:
            new_lines.append(_yaml_value(key, val))
    return "---\n" + "".join(new_lines) + "---\n" + body


def _deadline_nodes(vault: Any, slug: str) -> list:
    nodes = []
    try:
        metas = vault.list_dir(f"02-PROJEKTY/{slug}/tasks", pattern="*.md", recursive=True)
    except Exception:
        return nodes
    for meta in metas:
        rel = getattr(meta, "rel_path", "")
        if not rel:
            continue
        try:
            text, file_meta = vault.read_text(rel)
        except Exception:
            continue
        parsed = parse_task_text(text, rel_path=rel, meta=file_meta)
        node = node_from_frontmatter(parsed.frontmatter)
        if node.id:
            nodes.append(node)
    return nodes


def update_task(
    *,
    path: str,
    patch: dict[str, Any],
    expect_oid: str | None = None,
    env: dict[str, str] | None = None,
    allow_parent_shift: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    if not patch:
        raise BrainClientError(message="empty patch", status_code=400)
    if "focus" in patch:
        deny_focus_write()
        raise BrainClientError(
            message=FOCUS_PROPOSAL_MESSAGE,
            status_code=403,
            error_reason="focus_requires_proposal",
        )
    for key in patch:
        if str(key).startswith("stav") or key == "stav_auto":
            d = deny_stav_auto_write()
            raise BrainClientError(
                message=d.reason, status_code=403, error_reason="policy_denied"
            )

    mode = "read" if dry_run else "mutate"
    with brain_vault(mode=mode, env=env) as vault:
        try:
            text, meta = vault.read_text(path)
            oid = getattr(meta, "oid", None)
            if expect_oid is not None and oid is not None and str(oid) != str(expect_oid):
                raise BrainClientError(
                    message=f"CAS conflict expect_oid={expect_oid!r} got={oid!r}",
                    status_code=409,
                    error_reason="oid_mismatch",
                    oid=str(oid),
                )
            m = _FM_RE.match(text)
            if not m:
                raise BrainClientError(message="no frontmatter", status_code=400)
            parsed = parse_task_text(text, rel_path=path, meta=meta)
            current_id = str(parsed.frontmatter.get("id") or "")
            write_patch = {key: value for key, value in patch.items() if key != "updated"}
            if "deadline" in write_patch and write_patch.get("deadline") not in (None, ""):
                write_patch["review_deadline"] = ""
            result_status = str(
                write_patch.get("status") or parsed.frontmatter.get("status") or ""
            )
            if result_status == "Waiting":
                wait = write_patch.get("waitUntil", parsed.frontmatter.get("waitUntil"))
                if wait in (None, ""):
                    raise BrainClientError(
                        message="waiting_no_waituntil",
                        status_code=400,
                        error_reason="waiting_no_waituntil",
                    )
            if result_status in ("Done", "Cancelled") and "status" in write_patch and current_id:
                assert_no_open_child(vault, [(current_id, result_status)])
            if needs_forest(patch) and current_id:
                active = list(iter_active_tasks(vault))
                if not any(str(task.frontmatter.get("id") or "") == current_id for task in active):
                    active.append(parsed)
                normalized = check_overlay(active, [{"id": current_id, "patch": patch}])
                write_patch = normalized[current_id]
                parent_changed = "parent" in patch and parse_parent_id(write_patch.get("parent")) != parse_parent_id(parsed.frontmatter.get("parent"))
                if "deadline" in patch or parent_changed:
                    nodes = [node_from_frontmatter(task.frontmatter) for task in active]
                    if not any(node.id == current_id for node in nodes):
                        nodes.append(node_from_frontmatter(parsed.frontmatter))
                    if parent_changed:
                        new_parent = parse_parent_id(write_patch.get("parent"))
                        nodes = [
                            DeadlineNode(
                                node.id,
                                new_parent if node.id == current_id else node.parent_id,
                                node.status,
                                node.deadline,
                            )
                            for node in nodes
                        ]
                    deadline_patch: dict[str, str | None] = {}
                    if "deadline" in patch:
                        raw_deadline = patch.get("deadline")
                        deadline_patch[current_id] = None if raw_deadline in (None, "") else str(raw_deadline)
                    order = evaluate_deadline_order(
                        nodes,
                        deadline_patch,
                        allow_parent_shift=allow_parent_shift,
                        touched_ids={current_id},
                    )
                    if not order.get("ok", False):
                        raise BrainClientError(
                            message="deadline_order",
                            status_code=409,
                            error_reason="deadline_order",
                            detail=order,
                        )
            write_patch.pop("updated", None)
            if "deadline" in write_patch and write_patch.get("deadline") not in (None, ""):
                write_patch["review_deadline"] = ""
            if "materials" in write_patch:
                write_patch["materials"] = normalize_materials(write_patch.get("materials"))
            new_text = render_frontmatter_patch(text, write_patch)
            if dry_run:
                return {
                    "path": path,
                    "dry_run": True,
                    "patched": sorted(write_patch.keys()),
                    "oid": oid,
                }
            kwargs: dict[str, Any] = {}
            if expect_oid is not None:
                kwargs["expect_oid"] = expect_oid
            meta2 = vault.write_text(path, new_text, **kwargs)
        except DriveConflictError as exc:
            conflict_oid = getattr(exc, "oid", None)
            if expect_oid is not None and conflict_oid is not None:
                raise BrainClientError(
                    message=str(exc),
                    status_code=409,
                    error_reason="oid_mismatch",
                    oid=str(conflict_oid),
                ) from exc
            raise BrainClientError(
                message=str(exc),
                status_code=409,
                error_reason="cas_conflict",
            ) from exc
        return {
            "path": path,
            "oid": getattr(meta2, "oid", None),
            "patched": sorted(write_patch.keys()),
        }
