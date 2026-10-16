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
    evaluate_deadline_order,
    node_from_frontmatter,
)
from drive_io import DriveConflictError  # noqa: E402
from task_io import parse_task_text  # noqa: E402

from app.errors import BrainClientError
from app.policy import FOCUS_PROPOSAL_MESSAGE, deny_focus_write, deny_stav_auto_write
from app.vault_deps import brain_vault

_FM_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)


def _yaml_value(key: str, val: Any) -> str:
    if val is None or val == "":
        return f"{key}:\n"
    if isinstance(val, str) and (":" in val or val.startswith("[[")):
        return f'{key}: "{val}"\n'
    return f"{key}: {val}\n"


def render_frontmatter_patch(text: str, patch: dict[str, Any]) -> str:
    matched = _FM_RE.match(text)
    if not matched:
        raise BrainClientError(message="no frontmatter", status_code=400, error_reason="no_frontmatter")
    fm_raw, body = matched.group(1), matched.group(2)
    lines = fm_raw.splitlines(keepends=True)
    keys_done: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        if ":" in line and not line.strip().startswith("#"):
            key = line.split(":", 1)[0].strip()
            if key in patch:
                new_lines.append(_yaml_value(key, patch[key]))
                keys_done.add(key)
                continue
        new_lines.append(line if line.endswith("\n") else line + "\n")
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
                    error_reason="cas_conflict",
                )
            m = _FM_RE.match(text)
            if not m:
                raise BrainClientError(message="no frontmatter", status_code=400)
            if "deadline" in patch:
                parts = path.split("/")
                slug = parts[1] if len(parts) > 2 and parts[0] == "02-PROJEKTY" else ""
                parsed = parse_task_text(text, rel_path=path, meta=meta)
                nodes = _deadline_nodes(vault, slug) if slug else []
                current_id = str(parsed.frontmatter.get("id") or "")
                if current_id and not any(node.id == current_id for node in nodes):
                    nodes.append(node_from_frontmatter(parsed.frontmatter))
                raw_deadline = patch.get("deadline")
                proposed = None if raw_deadline in (None, "") else str(raw_deadline)
                order = evaluate_deadline_order(
                    nodes,
                    {current_id: proposed} if current_id else {},
                    allow_parent_shift=allow_parent_shift,
                )
                if not order.get("ok", False):
                    raise BrainClientError(
                        message="deadline_order",
                        status_code=409,
                        error_reason="deadline_order",
                        detail=order,
                    )
            new_text = render_frontmatter_patch(text, patch)
            if dry_run:
                return {
                    "path": path,
                    "dry_run": True,
                    "patched": sorted(patch.keys()),
                    "oid": oid,
                }
            kwargs: dict[str, Any] = {}
            if expect_oid is not None:
                kwargs["expect_oid"] = expect_oid
            meta2 = vault.write_text(path, new_text, **kwargs)
        except DriveConflictError as exc:
            raise BrainClientError(
                message=str(exc),
                status_code=409,
                error_reason="cas_conflict",
            ) from exc
        return {
            "path": path,
            "oid": getattr(meta2, "oid", None),
            "patched": sorted(patch.keys()),
        }
