"""T7d — shared partial client-apply report format (B33 helper)."""
from __future__ import annotations

import sys
from pathlib import Path

_BRAIN = Path(__file__).resolve().parents[1]
if str(_BRAIN) not in sys.path:
    sys.path.insert(0, str(_BRAIN))

from app.partial_apply_report import is_all_ok, normalize_report  # noqa: E402


def test_normalize_succeeded_and_failed():
    report = normalize_report(
        succeeded=["a", {"id": "b"}],
        failed=[{"id": "c", "error_reason": "boom"}, {"id": "d", "error": "x"}],
    )
    assert report["succeeded"] == ["a", "b"]
    assert report["failed"] == [
        {"id": "c", "error_reason": "boom"},
        {"id": "d", "error_reason": "x"},
    ]
    assert is_all_ok(report) is False


def test_all_ok_when_no_failures():
    report = normalize_report(succeeded=["a"], failed=[])
    assert is_all_ok(report) is True
