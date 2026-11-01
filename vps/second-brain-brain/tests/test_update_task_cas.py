"""T4/B5 — DriveConflictError → 409 cas_conflict."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from drive_io import DriveConflictError  # noqa: E402

from app.errors import BrainClientError  # noqa: E402
from app.tools import update_task as mod  # noqa: E402


def test_render_frontmatter_patch_replaces_materials_list():
    text = (
        "---\n"
        "id: X1\n"
        "title: T\n"
        "materials:\n"
        '  - "[[Old]]"\n'
        "  - https://old.example/a\n"
        "status: Next\n"
        "---\n\n"
        "# X1 — T\n"
    )
    out = mod.render_frontmatter_patch(
        text,
        {
            "materials": [
                "https://no-work.circle.so/events/digi",
                "https://mail.google.com/mail/#all/abc",
            ]
        },
    )
    assert "[[Old]]" not in out
    assert "https://old.example/a" not in out
    assert '  - "https://no-work.circle.so/events/digi"\n' in out
    assert '  - "https://mail.google.com/mail/#all/abc"\n' in out
    assert out.count("materials:") == 1
    assert "status: Next\n" in out


def test_render_frontmatter_patch_empty_materials_list():
    text = "---\nid: X1\nmaterials:\n  - https://x.test\n---\n\nbody\n"
    out = mod.render_frontmatter_patch(text, {"materials": []})
    assert "materials: []\n" in out
    assert "https://x.test" not in out


def test_normalize_materials_string_and_dedupe():
    from app.tools.materials_yaml import normalize_materials

    assert normalize_materials("https://a.test\n[[Wiki]]\nhttps://a.test\n") == [
        "https://a.test",
        "[[Wiki]]",
    ]
    assert normalize_materials(None) == []


def test_drive_conflict_maps_to_409():
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = "abc"
    vault.read_text.return_value = (
        "---\nid: X1\ntitle: T\n---\n\n# X1 — T\n",
        meta,
    )
    vault.write_text.side_effect = DriveConflictError("oid mismatch")

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *a):
            return False

    with patch.object(mod, "brain_vault", return_value=_CM()):
        with pytest.raises(BrainClientError) as ei:
            mod.update_task(path="02-PROJEKTY/test/tasks/X1.md", patch={"status": "Next"})
    assert ei.value.status_code == 409
    assert ei.value.error_reason == "cas_conflict"
    assert "oid" not in ei.value.as_dict()


def _vault(oid: str, write_error: DriveConflictError | None = None):
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = oid
    vault.read_text.return_value = (
        "---\nid: X1\ntitle: T\n---\n\n# X1 — T\n",
        meta,
    )
    if write_error is not None:
        vault.write_text.side_effect = write_error

    class _CM:
        def __enter__(self):
            return vault

        def __exit__(self, *args):
            return False

    return vault, _CM()


def test_t33_b42_precheck_oid_mismatch_does_not_write():
    vault, cm = _vault("current-oid")
    with patch.object(mod, "brain_vault", return_value=cm):
        for dry_run in (True, False):
            vault.write_text.reset_mock()
            with pytest.raises(BrainClientError) as ei:
                mod.update_task(
                    path="02-PROJEKTY/test/tasks/X1.md",
                    patch={"status": "Next"},
                    expect_oid="stale-oid",
                    dry_run=dry_run,
                )
            assert ei.value.status_code == 409
            body = ei.value.as_dict()
            assert body["error_reason"] == "oid_mismatch"
            assert body["oid"] == "current-oid"
            vault.write_text.assert_not_called()


def test_t33_b43_drive_conflict_oid_follows_expect_oid():
    vault, cm = _vault("abc", DriveConflictError("oid mismatch", oid="newer-oid"))
    with patch.object(mod, "brain_vault", return_value=cm):
        with pytest.raises(BrainClientError) as ei:
            mod.update_task(
                path="02-PROJEKTY/test/tasks/X1.md",
                patch={"status": "Next"},
                expect_oid="abc",
            )
        body = ei.value.as_dict()
        assert ei.value.status_code == 409
        assert body["error_reason"] == "oid_mismatch"
        assert body["oid"] == "newer-oid"

        with pytest.raises(BrainClientError) as plain:
            mod.update_task(
                path="02-PROJEKTY/test/tasks/X1.md",
                patch={"status": "Next"},
            )
        plain_body = plain.value.as_dict()
        assert plain.value.status_code == 409
        assert plain_body["error_reason"] == "cas_conflict"
        assert "oid" not in plain_body
