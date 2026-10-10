"""get_context freshness — TTL exactly 15 minutes (C2 / R15 / A37)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

# Stale when now - generated_at > 15 minutes exactly (not ≥).
CONTEXT_TTL = timedelta(minutes=15)
DEFAULT_TZ = ZoneInfo("Europe/Prague")


def parse_generated_at(value: Any, *, tz: ZoneInfo | None = None) -> datetime | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    tz = tz or DEFAULT_TZ
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc)


def is_stale(generated_at: datetime | None, *, now: datetime | None = None) -> bool:
    """True when generated_at missing/unparseable or older than TTL (strict >)."""
    if generated_at is None:
        return True
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = now_utc - generated_at.astimezone(timezone.utc)
    return age > CONTEXT_TTL


def needs_rebuild(
    full: dict[str, Any] | None,
    light: dict[str, Any] | None,
    charters: dict[str, Any] | None,
    *,
    now: datetime | None = None,
) -> bool:
    """§3 freshness: missing / bad / stale / side missing / timestamp mismatch."""
    if not full:
        return True
    full_at = parse_generated_at(full.get("generated_at"))
    if is_stale(full_at, now=now):
        return True
    if not light or not charters:
        return True
    light_at = parse_generated_at(light.get("generated_at"))
    charters_at = parse_generated_at(charters.get("generated_at"))
    if light_at is None or charters_at is None:
        return True
    # B3d / A37: all three must share the same generated_at
    if light_at != full_at or charters_at != full_at:
        return True
    return False
