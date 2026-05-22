"""Unit tests for edu_news_refresh helpers (no Drive I/O)."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

_CRON = Path(__file__).resolve().parents[1] / "cron"
if str(_CRON) not in sys.path:
    sys.path.insert(0, str(_CRON))

import edu_news_refresh as mod  # noqa: E402


def test_parse_hotovo_date_iso_and_cz():
    assert mod._parse_hotovo_date("_(2026-05-20)_") == date(2026, 5, 20)
    assert mod._parse_hotovo_date("_(20. 5. 2026)_") == date(2026, 5, 20)
    assert mod._parse_hotovo_date("přesunuto do HOTOVO 20. 5. 2026") == date(2026, 5, 20)


def test_parse_hotovo_date_missing_returns_none():
    assert mod._parse_hotovo_date("bez data v bloku") is None


def test_effective_hotovo_cutoff_respects_cycle():
    today = date(2026, 5, 22)
    state = {"cycleStartedAt": "2026-05-22T10:00:00+02:00"}
    assert mod._effective_hotovo_cutoff(today, state) == date(2026, 5, 22)


def test_progress_baseline_skips_unchanged():
    tasks = [
        {
            "id": "T1",
            "proj": "finance",
            "name": "Overdue faktury",
            "st": "op",
            "p": "ASAP",
            "ice": {"i": 8, "c": 7, "e": 5},
            "ch": [
                {"d": True},
                {"d": True},
                {"d": False},
            ],
        }
    ]
    baseline = mod.build_progress_baseline(tasks)
    assert baseline == {"finance:T1": 2}
    out = mod.collect_progress_candidates(tasks, progress_baseline=baseline)
    assert out == []


def test_progress_baseline_allows_new_steps():
    tasks = [
        {
            "id": "T1",
            "proj": "finance",
            "name": "Overdue faktury",
            "st": "op",
            "p": "ASAP",
            "ice": {"i": 8, "c": 7, "e": 5},
            "ch": [
                {"d": True},
                {"d": True},
                {"d": True},
            ],
        }
    ]
    baseline = {"finance:T1": 2}
    out = mod.collect_progress_candidates(tasks, progress_baseline=baseline)
    assert len(out) == 1
    assert out[0]["key"] == "finance:T1"
