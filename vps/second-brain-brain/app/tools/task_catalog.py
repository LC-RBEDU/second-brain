"""Load active task files for Brain read tools."""
from __future__ import annotations

import hashlib
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

from promoted_alias import load_applied_at, prague_today  # noqa: E402
from task_io import iter_active_tasks  # noqa: E402

_FM_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL)
_LOG_RE = re.compile(r"^## Poznámky / log\s*$", re.MULTILINE)


def load_tasks(vault: Any) -> list[Any]:
    return list(iter_active_tasks(vault))


def file_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_frontmatter(text: str) -> tuple[str, str]:
    matched = _FM_RE.match(text)
    if not matched:
        return "", text
    return text[: matched.end()], text[matched.end() :]


def log_section(body: str) -> str:
    matched = _LOG_RE.search(body or "")
    if not matched:
        return ""
    rest = body[matched.end() :]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    block = rest[: nxt.start()] if nxt else rest
    return block.strip()


def alias_clock(vault: Any):
    return prague_today(), load_applied_at(vault)
