"""read_file allowlist deny."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.errors import BrainClientError  # noqa: E402
from app.tools.read_file import read_file  # noqa: E402


def test_path_denied():
    with pytest.raises(BrainClientError) as ei:
        read_file("../etc/passwd")
    assert ei.value.status_code == 403
