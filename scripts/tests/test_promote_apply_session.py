"""Promote script refuses the wrong backend and plans distinct task ids."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "vps" / "second-brain-hub" / "lib"))

from promote_open_checkboxes import apply_allowed, main, plan_promotions  # noqa: E402


def _story(body: str, **fm):
    base = {
        "id": "RBU-S7",
        "type": "story",
        "slug": "rb-universe-development",
        "status": "Doing",
        "focus": "2026-W42",
        "deadline": "2026-10-20",
        "parent": "[[RBU-E1 — Epic]]",
    }
    base.update(fm)
    return SimpleNamespace(frontmatter=base, body=body, rel_path="02-PROJEKTY/rb-universe-development/tasks/RBU-S7 — Story.md")


def _git(tmp, *args):
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    subprocess.check_call(["git", *args], cwd=tmp, env=env)


def test_dirty_git_start_does_not_reset_or_write_the_anchor(tmp_path):
    from git_io import GitVault

    _git(tmp_path, "init", "-b", "main")
    (tmp_path / "readme.md").write_text("a\n")
    _git(tmp_path, "add", "readme.md")
    _git(tmp_path, "commit", "-m", "init")
    (tmp_path / "readme.md").write_text("dirty\n")
    vault = GitVault(tmp_path, remote="", push=False, discard_dirty_on_error=True, env={})
    vault.begin_session()
    assert vault.skipped is True
    assert not (tmp_path / "00-System" / "task-promotion-applied.json").exists()
    vault.end_session()
    assert (tmp_path / "readme.md").read_text() == "dirty\n"


def test_exception_in_session_drops_the_uncommitted_file(tmp_path):
    from git_io import GitVault

    _git(tmp_path, "init", "-b", "main")
    (tmp_path / "readme.md").write_text("a\n")
    _git(tmp_path, "add", "readme.md")
    _git(tmp_path, "commit", "-m", "init")
    vault = GitVault(tmp_path, remote="", push=False, discard_dirty_on_error=True, env={})
    try:
        with vault:
            (tmp_path / "readme.md").write_text("changed\n")
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert (tmp_path / "readme.md").read_text() == "a\n"
    log = subprocess.check_output(["git", "log", "--oneline"], cwd=tmp_path, text=True)
    assert "boom" not in log


def test_apply_refuses_drive_and_mac_root():
    assert apply_allowed({}) == "ALLOW_VAULT_APPLY"
    assert main(["--apply"], {}) == 2
    assert main(["--apply"], {"ALLOW_VAULT_APPLY": "1", "VAULT_BACKEND": "drive", "GIT_VAULT_ROOT": "/data/vault"}) == 2
    assert main(["--apply"], {"ALLOW_VAULT_APPLY": "1", "VAULT_BACKEND": "git", "GIT_VAULT_ROOT": "/Users/me/vault"}) == 2
    assert main([], {}, tasks=[]) == 0


def test_two_open_checks_get_two_ids_and_leave_focus_off_the_tasks():
    body = "## Operativní kroky\n- [ ] **RBU-S7-1** První\n- [ ] **RBU-S7-2** Druhý\n- [x] **RBU-S7-3** Hotovo\n"
    plans = plan_promotions([_story(body)], id_for_index=lambda i: f"RBU{10 + i}")
    assert [item["new_id"] for item in plans] == ["RBU-T10", "RBU-T11"]
    assert all(item["focus"] == "" for item in plans)
    assert all(item["deadline"] == "" for item in plans)
    assert "RBU-S7-3" not in [item["checkbox_id"] for item in plans]


def test_single_open_check_takes_focus_and_deadline():
    body = "## Operativní kroky\n- [ ] **RBU-S7-1** Jediný\n"
    epic = SimpleNamespace(
        frontmatter={"id": "RBU-E1", "type": "epic", "slug": "rb-universe-development", "deadline": "2026-10-25"},
        body="",
        rel_path="e.md",
    )
    plans = plan_promotions([epic, _story(body)], id_for_index=lambda i: "RBU12")
    assert plans[0]["focus"] == "2026-W42"
    assert plans[0]["deadline"] == "2026-10-20"
    assert plans[0]["status"] == "Next"


class _Mem:
    def __init__(self, files: dict[str, str]):
        self.files = dict(files)
        self.writes: list[str] = []

    def read_text(self, path: str):
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path], None

    def write_text(self, path: str, text: str, **_kwargs):
        self.files[path] = text
        self.writes.append(path)
        return None


def test_write_plan_creates_the_child_trace_and_anchor_once():
    from promote_open_checkboxes import write_plan

    body = "---\nid: RBU-S7\nstatus: Doing\nfocus: 2026-W42\ndeadline: 2026-10-20\n---\n## Operativní kroky\n- [ ] **RBU-S7-1** Jediný\n"
    story_path = "02-PROJEKTY/rb-universe-development/tasks/RBU-S7 — Story.md"
    vault = _Mem({story_path: body})
    plans = plan_promotions([_story("## Operativní kroky\n- [ ] **RBU-S7-1** Jediný\n")], id_for_index=lambda i: "RBU12")
    first = write_plan(vault, plans, today="2026-10-16")
    assert first["applied_at"] == "2026-10-16"
    child = next(path for path in first["files"] if path.endswith(".md"))
    assert "promoted_from: RBU-S7-1" in vault.files[child]
    assert "type: task" in vault.files[child]
    assert "RBU-S7-1 → [[RBU-T12 — Jediný]]" in vault.files[story_path]
    assert "2026-W42" not in vault.files[story_path]
    second = write_plan(vault, [], today="2026-10-20")
    assert second["applied_at"] == "2026-10-16"
    assert ANCHOR_WRITES(vault) == 1


def ANCHOR_WRITES(vault: _Mem) -> int:
    from promote_open_checkboxes import ANCHOR

    return sum(1 for path in vault.writes if path == ANCHOR)


def test_title_with_colon_is_quoted_and_trace_lands_in_the_log():
    from promote_open_checkboxes import write_plan

    body = "---\nid: RBU-S7\nstatus: Doing\nfocus:\ndeadline:\n---\n## Operativní kroky\n- [ ] **RBU-S7-1** A: B\n  pokračování\n"
    story_path = "02-PROJEKTY/rb-universe-development/tasks/RBU-S7 — Story.md"
    vault = _Mem({story_path: body})
    plans = plan_promotions(
        [_story("## Operativní kroky\n- [ ] **RBU-S7-1** A: B\n  pokračování\n", focus="", deadline="")],
        id_for_index=lambda i: "RBU14",
    )
    write_plan(vault, plans, today="2026-10-16")
    child = next(text for path, text in vault.files.items() if "RBU-T14" in path)
    assert 'title: "A: B"' in child
    assert "pokračování" in child
    assert "- [ ] **RBU-S7-1**" not in vault.files[story_path]
    assert "RBU-S7-1 → [[RBU-T14 — A: B]]" in vault.files[story_path]


def test_slash_in_the_title_stays_one_file():
    from promote_open_checkboxes import write_plan

    title = "Ověřit [Allfred](https://redbuttonedu.allfred.io/projects/detail/?id=187) a [[02-PROJEKTY/finance/x|materiál]]"
    line = f"## Operativní kroky\n- [ ] **F-S1-1** {title}\n"
    story = _story(line, id="F-S1", slug="finance", focus="", deadline="")
    vault = _Mem({story.rel_path: "---\nid: F-S1\nstatus: Next\nfocus:\ndeadline:\n---\n" + line})
    plans = plan_promotions([story], id_for_index=lambda i: "F94")
    write_plan(vault, plans, today="2026-10-16")
    child = next(path for path in vault.files if "F-T94" in path)
    assert "/" not in child.split("tasks/", 1)[1]
    assert "https://redbuttonedu.allfred.io/projects/detail/?id=187" in vault.files[child]
    stem = child.rsplit("/", 1)[1].removesuffix(".md")
    assert f"F-S1-1 → [[{stem}]]" in vault.files[story.rel_path]


def test_dry_run_shows_a_date_blocked_by_the_epic(capsys):
    body = "## Operativní kroky\n- [ ] **RBU-S7-1** Jediný\n"
    epic = SimpleNamespace(
        frontmatter={"id": "RBU-E1", "type": "epic", "slug": "rb-universe-development", "deadline": "2026-10-10"},
        body="",
        rel_path="e.md",
    )
    story = _story(body, deadline="2026-10-20")
    assert main([], {}, tasks=[epic, story]) == 0
    row = json.loads(capsys.readouterr().out)["plans"][0]
    assert row["blocked_by_epic"] is True
    assert row["story_deadline"] == "2026-10-20"
    assert row["epic_id"] == "RBU-E1"
    assert row["epic_deadline"] == "2026-10-10"
    assert row["deadline"] == ""


def test_dry_run_lists_focus_and_writes_nothing(capsys):
    body = "## Operativní kroky\n- [ ] **RBU-S7-1** První\n- [ ] **RBU-S7-2** Druhý\n"
    assert main([], {}, tasks=[_story(body)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["written"] is False
    assert payload["count"] == 2
    assert all(row["clear_story_focus"] for row in payload["plans"])
    assert all(row["focus"] == "" for row in payload["plans"])


def test_apply_deletes_base_files():
    from promote_open_checkboxes import write_plan

    class _Vault(_Mem):
        def list_dir(self, path, pattern="*", recursive=False):
            suffix = ".md" if str(pattern).endswith(".md") else ".base"
            return [
                SimpleNamespace(rel_path=rel)
                for rel in self.files
                if rel.startswith(path) and rel.endswith(suffix)
            ]

        def delete(self, path):
            self.files.pop(path, None)
            self.writes.append("deleted:" + path)

    story_path = "02-PROJEKTY/rb-universe-development/tasks/RBU-S7 — Story.md"
    hub_path = "02-PROJEKTY/RB Universe development.md"
    vault = _Vault(
        {
            story_path: "---\nid: RBU-S7\nfocus:\n---\n![[All-tasks-hierarchy.base#EpicStories]]\n## Poznámky / log\n",
            hub_path: "# Hub\n\n![[All-tasks.base#ProjectKanban]]\n",
            "00-System/Bases/All-tasks.base": "views: []\n",
        }
    )
    write_plan(vault, [], today="2026-10-16")
    assert "00-System/Bases/All-tasks.base" not in vault.files
    assert ".base" not in vault.files[story_path]
    assert ".base" not in vault.files[hub_path]


def test_single_check_later_than_epic_keeps_the_date_on_the_story():
    body = "## Operativní kroky\n- [ ] **RBU-S7-1** Pozdě\n"
    epic = SimpleNamespace(
        frontmatter={"id": "RBU-E1", "type": "epic", "slug": "rb-universe-development", "deadline": "2026-10-10"},
        body="",
        rel_path="e.md",
    )
    plans = plan_promotions([epic, _story(body)], id_for_index=lambda i: "RBU13")
    assert plans[0]["deadline"] == ""
    assert plans[0]["move_dates"] is False
