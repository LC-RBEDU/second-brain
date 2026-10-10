"""T2 grep: cron/scripts must not construct DriveVault directly (C1–C23)."""
from __future__ import annotations

import re
from pathlib import Path

HUB = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"DriveVault\s*\(")


def test_no_direct_drivevault_in_cron_or_hub_scripts():
    offenders: list[str] = []
    for base in (HUB / "cron", HUB / "scripts"):
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                if PATTERN.search(line) and not line.lstrip().startswith("#"):
                    offenders.append(f"{path.relative_to(HUB)}:{i}: {line.strip()}")
    assert not offenders, "Direct DriveVault( in call-sites:\n" + "\n".join(offenders)


def test_cron_imports_open_vault():
    """Spot-check critical writers use vault_factory."""
    must = [
        "cron/build_agent_context.py",
        "cron/inbox_inventory.py",
        "cron/slack_poll.py",
        "cron/reminders_dispatch.py",
    ]
    for rel in must:
        text = (HUB / rel).read_text(encoding="utf-8")
        assert "open_vault" in text, f"{rel} missing open_vault"
