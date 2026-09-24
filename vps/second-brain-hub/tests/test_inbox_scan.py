"""Unit tests for lib/inbox_scan.iter_inbox_items."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import inbox_scan as mod  # noqa: E402


@dataclass
class _Meta:
    name: str
    rel_path: str


class _FakeVault:
    def __init__(self, files: dict[str, str]):
        self.files = files

    def list_dir(self, rel: str, pattern: str = "*", recursive: bool = False):
        out = []
        prefix = rel.rstrip("/") + "/"
        for path in self.files:
            if not path.startswith(prefix):
                continue
            if pattern == "*.md" and not path.endswith(".md"):
                continue
            name = path.rsplit("/", 1)[-1]
            out.append(_Meta(name=name, rel_path=path))
        return out

    def read_text(self, rel: str):
        if rel not in self.files:
            from drive_io import DriveNotFoundError

            raise DriveNotFoundError(rel)
        return self.files[rel], None


def test_iter_skips_readme_and_zpracovano():
    vault = _FakeVault(
        {
            "01-INBOX/slack/README.md": "# ignore\n",
            "01-INBOX/slack/keep-me.md": "# Keep\n\nbody\n",
            "01-INBOX/email/done.md": "**ZPRACOVÁNO**\n\nalready done\n",
            "01-INBOX/daily/note.md": "# Daily\n",
        }
    )
    items = mod.iter_inbox_items(vault)
    rels = sorted(r for r, _ in items)
    assert rels == [
        "01-INBOX/daily/note.md",
        "01-INBOX/slack/keep-me.md",
    ]


def test_iter_missing_subdir_ok():
    vault = _FakeVault({"01-INBOX/slack/a.md": "# A\n"})
    items = mod.iter_inbox_items(vault)
    assert len(items) == 1
    assert items[0][0] == "01-INBOX/slack/a.md"


def test_inbox_subdirs_constant():
    assert "slack" in mod.INBOX_SUBDIRS
    assert "email" in mod.INBOX_SUBDIRS
