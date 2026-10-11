"""capture_daily — write 01-INBOX/daily/ note (R6)."""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.errors import BrainClientError
from app.vault_deps import brain_vault

DAILY_DIR = "01-INBOX/daily"
_SAFE = re.compile(r"[^\w\s\-—]+", re.UNICODE)


def capture_daily(
    text: str,
    *,
    title: str | None = None,
    env: dict | None = None,
) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise BrainClientError(message="text required", status_code=400)
    env = env if env is not None else dict(os.environ)
    tz = ZoneInfo(env.get("TZ") or "Europe/Prague")
    now = datetime.now(tz)
    slug = _SAFE.sub("", (title or text[:40])).strip()
    slug = re.sub(r"\s+", "-", slug)[:50] or "note"
    fname = f"{now.strftime('%Y-%m-%d-%H%M%S')}-{slug}.md"
    rel = f"{DAILY_DIR}/{fname}"
    body = (
        f"# {title or slug}\n\n"
        f"**Z:** brain-api capture_daily\n"
        f"**Kdy:** {now.isoformat(timespec='seconds')}\n\n"
        f"{text}\n"
    )
    with brain_vault(mode="mutate", env=env) as vault:
        vault.mkdir_p(DAILY_DIR)
        vault.write_text(rel, body)
    return {"ok": True, "path": rel}
