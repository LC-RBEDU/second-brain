"""create_task — ceiling + write + tombstone under mutate session (R6 / B4 / B31)."""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from context_tombstone import delete_context_tombstone  # noqa: E402
from task_id_allocate import next_id, with_level  # noqa: E402

from app.errors import BrainClientError  # noqa: E402
from app.fm_contract import strip_aliases_for_new_write  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402

_SAFE_TITLE = re.compile(r"[^\w\s\-—]+", re.UNICODE)


def _slugify_title(title: str) -> str:
    t = _SAFE_TITLE.sub("", title).strip()
    t = re.sub(r"\s+", "-", t)
    return t[:80] or "task"


def _hub_filename(vault: Any, slug: str) -> str:
    """Best-effort hub display name from 02-PROJEKTY/*.md frontmatter slug match."""
    try:
        metas = vault.list_dir("02-PROJEKTY", pattern="*.md", recursive=False)
    except Exception:
        return slug
    for meta in metas:
        rel = getattr(meta, "rel_path", "")
        name = getattr(meta, "name", "")
        if not rel or "/" in name:
            continue
        try:
            text, _ = vault.read_text(rel)
        except Exception:
            continue
        if f"slug: {slug}" in text or f'slug: "{slug}"' in text:
            return Path(name).stem
    return slug


def _render_task(
    *,
    task_id: str,
    title: str,
    slug: str,
    hub: str,
    level: str,
    status: str,
    detail: str,
) -> str:
    today = date.today().isoformat()
    type_map = {"epic": "epic", "story": "story", "task": "task"}
    work_type = type_map.get(level, "story")
    fm = {
        "id": task_id,
        "type": work_type,
        "title": title,
        "project": f"[[{hub}]]",
        "slug": slug,
        "status": status,
        "parent": "",
        "focus": "",
        "agent": "none",
        "ice_i": 5,
        "ice_c": 5,
        "ice_e": 5,
        "deadline": "",
        "review_deadline": "",
        "waitUntil": "",
        "created": today,
        "updated": today,
        "materials": [],
        "source": "brain-api",
        "company_priorities": [],
        "blocked_by": [],
    }
    fm = strip_aliases_for_new_write(fm)
    # YAML by hand — avoid dumping empty aliases
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: []")
        elif v == "" and k in ("parent", "focus", "deadline", "review_deadline", "waitUntil"):
            lines.append(f"{k}:")
        elif isinstance(v, str) and (":" in v or v.startswith("[[")):
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {task_id} — {title}")
    lines.append("")
    lines.append(f"**Z:** brain-api")
    lines.append(f"**Detail:** {detail or '—'}")
    lines.append("")
    lines.append("## Operativní kroky")
    lines.append(f"- [ ] **{task_id}-1** …")
    lines.append("")
    lines.append("## Poznámky / log")
    lines.append(f"- {today}: Založeno přes Brain API.")
    lines.append("")
    return "\n".join(lines)


def create_task(
    *,
    slug: str,
    title: str,
    detail: str = "",
    level: str = "story",
    status: str = "Next",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    title = (title or "").strip()
    slug = (slug or "").strip()
    if not title or not slug:
        raise BrainClientError(message="slug and title required", status_code=400)
    if level not in ("epic", "story", "task"):
        raise BrainClientError(message="level must be epic|story|task", status_code=400)

    with brain_vault(mode="mutate", env=env) as vault:
        delete_context_tombstone(vault)
        bare, where = next_id(vault, slug)
        task_id = with_level(bare, level) if level else bare
        # Hierarchy projects use letter; flat may use bare — prefer with_level when asked.
        hub = _hub_filename(vault, slug)
        rel_dir = f"02-PROJEKTY/{slug}/tasks"
        vault.mkdir_p(rel_dir)
        fname = f"{task_id} — {title}.md"
        rel = f"{rel_dir}/{fname}"
        if vault.exists(rel):
            raise BrainClientError(
                message=f"task file exists: {rel}",
                status_code=409,
                error_reason="task_exists",
            )
        body = _render_task(
            task_id=task_id,
            title=title,
            slug=slug,
            hub=hub,
            level=level,
            status=status,
            detail=detail,
        )
        vault.write_text(rel, body)
        return {
            "id": task_id,
            "path": rel,
            "ceiling_source": where,
            "title": title,
            "slug": slug,
        }
