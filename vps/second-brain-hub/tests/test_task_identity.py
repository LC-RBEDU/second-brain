"""Tests for task identity checks — duplicate IDs and filename drift."""
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from task_identity import (  # noqa: E402
    check_task_identity,
    expected_stem,
    find_duplicate_ids,
    find_filename_drift,
    sanitize_title,
    strip_wikilinks,
)


@dataclass
class T:
    id: str
    title: str
    rel_path: str


def task(tid, title, folder="02-PROJEKTY/finance/tasks", stem=None):
    stem = stem if stem is not None else expected_stem(tid, title)
    return T(tid, title, f"{folder}/{stem}.md")


# ---------------------------------------------------------------------------
# sanitize_title — filesystem-hostile characters
# ---------------------------------------------------------------------------


def test_sanitize_replaces_path_and_drive_hostile_chars():
    assert sanitize_title("Ninjabot: projít smlouvy / služby") == "Ninjabot projít smlouvy - služby"
    assert sanitize_title("1:1 s Martinem") == "1 1 s Martinem"


def test_sanitize_keeps_diacritics_and_emoji():
    assert sanitize_title("Nahrát EDU news ♻️ weekly") == "Nahrát EDU news ♻️ weekly"


def test_expected_stem_falls_back_to_bare_id():
    """A title made only of stripped characters must not yield ` — .md`."""
    assert expected_stem("OPS2", "??") == "OPS2"


# ---------------------------------------------------------------------------
# duplicate IDs
# ---------------------------------------------------------------------------


def test_two_tasks_one_id_is_flagged():
    issues = find_duplicate_ids([
        task("F36", "Plán režijních nákladů"),
        task("F36", "Opravit fakturační workflow"),
    ])
    assert [i.kind for i in issues] == ["duplicate_id"]
    assert issues[0].task_id == "F36"


def test_distinct_ids_are_fine():
    assert find_duplicate_ids([task("F36", "A"), task("F37", "B")]) == []


def test_rotated_ritual_instances_share_an_id_legitimately():
    """Every archived run of a ritual carries the same ID — that is the point.

    Six OPS2 rotations once got 'repaired' onto one filename and overwrote each
    other, so this guard is load-bearing, not cosmetic.
    """
    arch = "07-ARCHIV/tasks-done/operations"
    issues = find_duplicate_ids([
        T("OPS2", "Nahrát EDU news", f"{arch}/OPS2-2026-06-01.md"),
        T("OPS2", "Nahrát EDU news", f"{arch}/OPS2-2026-06-04.md"),
        T("OPS2", "Nahrát EDU news", f"{arch}/OPS2-2026-06-12.md"),
    ])
    assert issues == []


def test_ritual_still_collides_with_a_real_second_task():
    """Rotations are exempt; a genuinely different task claiming the ID is not."""
    arch = "07-ARCHIV/tasks-done/operations"
    issues = find_duplicate_ids([
        T("OPS2", "Nahrát EDU news", f"{arch}/OPS2-2026-06-01.md"),
        T("OPS2", "Nahrát EDU news", f"{arch}/OPS2-2026-06-04.md"),
        task("OPS2", "Něco úplně jiného", folder="02-PROJEKTY/operations/tasks"),
    ])
    assert len(issues) == 1


# ---------------------------------------------------------------------------
# filename drift
# ---------------------------------------------------------------------------


def test_filename_matching_title_is_clean():
    assert find_filename_drift([task("S16", "Anti-Švarc — struktura témat a DoD do offsite")]) == []


def test_dropped_em_dash_is_drift():
    """The exact break that left [[S16 — Anti-Švarc — struktura…]] dangling."""
    issues = find_filename_drift([
        task("S16", "Anti-Švarc — struktura témat a DoD do offsite",
             stem="S16 — Anti-Švarc struktura témat a DoD do offsite"),
    ])
    assert len(issues) == 1 and issues[0].kind == "filename_drift"


def test_sanitized_characters_are_not_drift():
    """`:` becomes a space in the filename by design — that is not a mismatch."""
    assert find_filename_drift([task("PD6", "Ninjabot: projít smlouvy / služby")]) == []


def test_rotation_filename_is_not_drift():
    assert find_filename_drift([
        T("OS1", "Vystavit fakturu (Lukáš → RB)", "07-ARCHIV/tasks-done/osobni/OS1-2026-07-13.md"),
    ]) == []


def test_task_without_title_is_skipped():
    assert find_filename_drift([T("F1", "", "02-PROJEKTY/finance/tasks/F1.md")]) == []


# ---------------------------------------------------------------------------
# H1 comparison helper
# ---------------------------------------------------------------------------


def test_strip_wikilinks_prefers_the_displayed_alias():
    assert strip_wikilinks("pohledy [[Jan Mašek|Honza]] + [[Luboš Malý]]") == "pohledy Honza + Luboš Malý"


# ---------------------------------------------------------------------------
# combined entry point
# ---------------------------------------------------------------------------


def test_check_returns_serialisable_dicts():
    out = check_task_identity([task("F36", "A"), task("F36", "B")])
    assert out and out[0]["kind"] == "duplicate_id"
    assert out[0]["id"] == "F36" and isinstance(out[0]["paths"], list)
