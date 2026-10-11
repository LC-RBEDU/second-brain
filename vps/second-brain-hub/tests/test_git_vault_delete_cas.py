"""B30 — GitVault.delete accepts expect_oid CAS."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB / "lib"))

from git_io import GitVault  # noqa: E402


def test_delete_signature_has_expect_oid():
    sig = inspect.signature(GitVault.delete)
    assert "expect_oid" in sig.parameters
