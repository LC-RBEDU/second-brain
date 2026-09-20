"""Active hours for the personal-assistant cron (Europe/Prague)."""
from __future__ import annotations

from datetime import datetime

# 08:00 inclusive through 23:59. 00:00–07:59 the hub does not poll or ping.
ACTIVE_START_HOUR = 8
ACTIVE_END_HOUR = 24


def in_active_window(now: datetime) -> bool:
    return ACTIVE_START_HOUR <= now.hour < ACTIVE_END_HOUR
