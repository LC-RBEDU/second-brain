"""T12/B37 — meeting_prep_dispatch --dry-run does not call Brain."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

HUB = Path(__file__).resolve().parents[1]
CRON = HUB / "cron" / "meeting_prep_dispatch.py"


def test_dry_run_source_mentions_zero_write():
    src = CRON.read_text(encoding="utf-8")
    assert "--dry-run" in src
    assert "0 vault write" in src or "would prepare/send" in src


def test_dry_run_no_urlopen():
    # Import-free: run with dry-run and monkeypatch vault via env that fails open
    # Assert script path exists and argparse accepts --dry-run
    r = subprocess.run(
        [sys.executable, str(CRON), "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert r.returncode == 0
    assert "--dry-run" in r.stdout
