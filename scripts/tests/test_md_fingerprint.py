"""T6/T7 — CLI md_fingerprint capture/compare (A33)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / "ŠABLONY/skills/grammar-nazi/scripts/md_fingerprint.py"
FIXTURES = CLI.parent / "fixtures"
VALID = FIXTURES / "valid-full.md"
BROKEN = FIXTURES / "broken-highlights.md"
TASKS_NONE = FIXTURES / "valid-tasks-none.md"
SHARED = FIXTURES / "valid-shared-no-hl.md"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )


def test_capture_valid_full_exit_0(tmp_path: Path) -> None:
    out = tmp_path / "fp.json"
    r = _run("capture", "--md", str(VALID), "--out", str(out))
    assert r.returncode == 0, r.stderr
    fp = json.loads(out.read_text(encoding="utf-8"))
    assert fp["highlights_count"] == 3
    assert fp["has_highlights_block"] is True
    assert fp["variant"] == "full"
    assert "finance/rozpocet-h2" in fp["cards"]
    assert fp["cards"]["finance/rozpocet-h2"]["tasks_count"] == 1
    assert fp["cards"]["finance/rozpocet-h2"]["co_zaznelo_count"] == 2
    assert fp["table_rows"] == 1
    assert fp["name_aliases"].get("Domčo") == "Dominik Test"
    assert fp["cards"]["finance/rozpocet-h2"]["owner"] == "Lukáš Cypra"


def test_capture_tasks_none_count_zero(tmp_path: Path) -> None:
    out = tmp_path / "fp.json"
    r = _run("capture", "--md", str(TASKS_NONE), "--out", str(out))
    assert r.returncode == 0, r.stderr
    fp = json.loads(out.read_text(encoding="utf-8"))
    assert fp["cards"]["ops/status-sync"]["tasks_count"] == 0


def test_capture_broken_highlights_exit_2(tmp_path: Path) -> None:
    out = tmp_path / "fp.json"
    r = _run("capture", "--md", str(BROKEN), "--out", str(out))
    assert r.returncode == 2
    assert not out.exists()


def test_capture_shared_without_highlights_ok(tmp_path: Path) -> None:
    out = tmp_path / "fp.json"
    r = _run("capture", "--md", str(SHARED), "--out", str(out))
    assert r.returncode == 0, r.stderr
    fp = json.loads(out.read_text(encoding="utf-8"))
    assert fp["variant"] == "shared"
    assert fp["has_highlights_block"] is False


def test_compare_identical_exit_0(tmp_path: Path) -> None:
    before = tmp_path / "fp.json"
    assert _run("capture", "--md", str(VALID), "--out", str(before)).returncode == 0
    r = _run("compare", "--before", str(before), "--md", str(VALID))
    assert r.returncode == 0, r.stderr


def test_compare_wording_change_same_structure_exit_0(tmp_path: Path) -> None:
    """B17 — fingerprint nehashuje wording bulletů."""
    before = tmp_path / "fp.json"
    assert _run("capture", "--md", str(VALID), "--out", str(before)).returncode == 0
    text = VALID.read_text(encoding="utf-8")
    text = text.replace(
        "Domluvili jsme strop 100 tisíc Kč.",
        "Domluvili jsme strop sto tisíc Kč.",
    )
    mutated = tmp_path / "mut.md"
    mutated.write_text(text, encoding="utf-8")
    r = _run("compare", "--before", str(before), "--md", str(mutated))
    assert r.returncode == 0, r.stderr


def test_compare_cardinality_co_zaznelo_exit_1(tmp_path: Path) -> None:
    before = tmp_path / "fp.json"
    assert _run("capture", "--md", str(VALID), "--out", str(before)).returncode == 0
    text = VALID.read_text(encoding="utf-8")
    # drop one Co zaznělo bullet
    text = text.replace("- Termín je konec října.\n", "")
    mutated = tmp_path / "mut.md"
    mutated.write_text(text, encoding="utf-8")
    r = _run("compare", "--before", str(before), "--md", str(mutated))
    assert r.returncode == 1
    assert "co_zaznelo_count" in r.stderr


def test_compare_owner_change_exit_1(tmp_path: Path) -> None:
    before = tmp_path / "fp.json"
    assert _run("capture", "--md", str(VALID), "--out", str(before)).returncode == 0
    text = VALID.read_text(encoding="utf-8")
    text = text.replace(
        "- **owner:** Lukáš Cypra",
        "- **owner:** Dominik Test",
        1,
    )
    mutated = tmp_path / "mut.md"
    mutated.write_text(text, encoding="utf-8")
    r = _run("compare", "--before", str(before), "--md", str(mutated))
    assert r.returncode == 1
    assert "owner" in r.stderr


def test_compare_after_invalid_highlights_exit_2(tmp_path: Path) -> None:
    before = tmp_path / "fp.json"
    assert _run("capture", "--md", str(VALID), "--out", str(before)).returncode == 0
    r = _run("compare", "--before", str(before), "--md", str(BROKEN))
    assert r.returncode == 2


def test_compare_shared_no_hl_stable(tmp_path: Path) -> None:
    before = tmp_path / "fp.json"
    assert _run("capture", "--md", str(SHARED), "--out", str(before)).returncode == 0
    text = SHARED.read_text(encoding="utf-8").replace("Krátký bod.", "Krátký bod upraven.")
    mutated = tmp_path / "mut.md"
    mutated.write_text(text, encoding="utf-8")
    r = _run("compare", "--before", str(before), "--md", str(mutated))
    assert r.returncode == 0, r.stderr
