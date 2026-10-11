"""T14 — slack_poll discover includes :eyes:."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB / "lib"))

# Load slack_poll with stubbed heavy deps if needed
spec = importlib.util.spec_from_file_location(
    "slack_poll", HUB / "cron" / "slack_poll.py"
)
# Simpler: just read source
src = (HUB / "cron" / "slack_poll.py").read_text(encoding="utf-8")
assert "hasmy::eyes:" in src
assert "hasmy::gear:" in src
