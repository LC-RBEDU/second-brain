"""Server-side write policy stubs (F2-d expands deny rules)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""


def deny_focus_write() -> PolicyDecision:
    """B6 — clients must not write focus."""
    return PolicyDecision(False, "focus is human-owned; Brain refuses client writes")


def deny_stav_auto_write() -> PolicyDecision:
    """B7 — ## Stav (auto) is cron-owned."""
    return PolicyDecision(False, "Stav (auto) is hub-cron owned")
