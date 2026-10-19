"""export_tasks snapshot — T1–T6, T9–T13, T15–T16, T20–T23, T28–T32."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

_LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(_LIB_DIR))

from drive_io import DriveNotFoundError, DriveVaultError  # noqa: E402
from focus import TERMINAL_STATUSES, current_focus_week  # noqa: E402
from git_io import GitVault  # noqa: E402
from promoted_alias import prague_today  # noqa: E402
from task_export import export_tasks  # noqa: E402


def _git(cwd: Path, *args: str, date: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    bare = tmp_path / "origin.git"
    _git(tmp_path, "clone", "--bare", str(root), str(bare))
    _git(root, "remote", "add", "origin", str(bare))
    _git(root, "fetch", "origin")
    _git(root, "branch", "--set-upstream-to=origin/main", "main")
    return root


def _shape(out: dict) -> None:
    assert out["count"] == len(out["tasks"])
    assert "open_count" not in out


def _md(
    task_id: str,
    title: str,
    *,
    status: str | None = "Next",
    work_type: str = "task",
    parent: str | None = None,
    slug: str = "alpha",
    updated: str = "2026-10-01",
    extra: str = "",
    body: str = "\n",
) -> str:
    lines = [
        "---",
        f"id: {task_id}",
        f"title: {title}",
        f"type: {work_type}",
        f"slug: {slug}",
        f"updated: {updated}",
    ]
    if status is not None:
        lines.append(f"status: {status}")
    if parent is not None:
        lines.append(f"parent: {parent}")
    if extra:
        lines.append(extra.rstrip("\n"))
    lines.append("---")
    return "\n".join(lines) + "\n" + body


class _Meta:
    def __init__(self, rel: str, is_folder: bool = False, oid: str | None = None):
        self.rel_path = rel
        self.name = rel.rstrip("/").split("/")[-1] if rel else ""
        self.is_folder = is_folder
        self.oid = oid


class MemVault:
    def __init__(self):
        self.files: dict[str, str] = {}

    def add(self, path: str, text: str) -> None:
        self.files[path] = text

    def read_text(self, path: str):
        if path not in self.files:
            raise DriveNotFoundError(path)
        return self.files[path], _Meta(path, oid="mem")

    def list_dir(self, path, pattern=None, recursive=False, include_folders=False):
        del recursive
        path = (path or "").strip("/")
        prefix = f"{path}/" if path else ""
        if path:
            exists = any(rel == path or rel.startswith(prefix) for rel in self.files)
            if not exists:
                raise DriveNotFoundError(path)
            if path in self.files and not any(rel.startswith(prefix) for rel in self.files):
                raise DriveVaultError(f"Not a folder: {path}")
        children: dict[str, tuple[bool, str]] = {}
        for rel in self.files:
            if prefix and not rel.startswith(prefix):
                continue
            rest = rel[len(prefix):] if prefix else rel
            if not rest:
                continue
            parts = rest.split("/")
            name = parts[0]
            is_dir = len(parts) > 1
            child_rel = f"{prefix}{name}" if prefix else name
            prev = children.get(name)
            if prev is None or is_dir:
                children[name] = (is_dir, child_rel)
        out = []
        for name, (is_dir, rel) in sorted(children.items()):
            if pattern == "*.md" and not name.endswith(".md"):
                if not (is_dir and include_folders):
                    continue
                if not is_dir:
                    continue
            if is_dir:
                if include_folders:
                    out.append(_Meta(rel, True))
            elif pattern in (None, "*.md") or (pattern == "*.md" and name.endswith(".md")):
                if pattern == "*.md" and not name.endswith(".md"):
                    continue
                out.append(_Meta(rel, False))
        return out


def _by_id(out: dict) -> dict[str, dict]:
    return {row["id"]: row for row in out["tasks"]}


def test_t1_empty_vault_and_missing_task_folders(git_repo: Path):
    vault = GitVault(git_repo, dry_run=True, push=False)
    with vault:
        empty = export_tasks(vault)
    _shape(empty)
    assert empty["tasks"] == []
    assert empty["projects"] == []
    assert empty["count"] == 0

    mem = MemVault()
    mem.add("02-PROJEKTY/Strategy.md", "# Strategy\n")
    mem.add("02-PROJEKTY/vibe/materials/note.md", "note\n")
    mem.add(
        "02-PROJEKTY/alpha/tasks/A1 — Otevreny.md",
        _md("A1", "Otevreny", slug="alpha"),
    )
    mem.add("07-ARCHIV/tasks-done/loose.md", "not a slug folder\n")
    out = export_tasks(mem, include_closed_days=7, projects_csv="alpha,missing-archive")
    _shape(out)
    assert out["count"] == 1
    assert out["tasks"][0]["id"] == "A1"
    assert out["tasks"][0]["project"] == "alpha"


def test_t2_active_done_is_not_a_cap():
    mem = MemVault()
    for n in range(51):
        mem.add(
            f"02-PROJEKTY/alpha/tasks/N{n} — Open.md",
            _md(f"N{n}", "Open"),
        )
    mem.add(
        "02-PROJEKTY/alpha/tasks/D1 — Hotovo.md",
        _md("D1", "Hotovo", status="Done"),
    )
    out = export_tasks(mem)
    _shape(out)
    assert out["count"] == 51
    assert "D1" not in _by_id(out)


def test_t3_task_without_parent():
    mem = MemVault()
    mem.add(
        "02-PROJEKTY/alpha/tasks/T3 — Bez parenta.md",
        _md("T3", "Bez parenta", status="Next", work_type="task"),
    )
    out = export_tasks(mem)
    row = out["tasks"][0]
    assert row["parent"] is None
    assert "parent_required" not in row["parse_errors"]


def test_t4_parent_wikilink_and_bare_id():
    mem = MemVault()
    mem.add(
        "02-PROJEKTY/alpha/tasks/IAD-E4 — Security.md",
        _md("IAD-E4", "Security", work_type="epic"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/S1 — Wikilink.md",
        _md("S1", "Wikilink", work_type="story", parent='"[[IAD-E4 — Security & Performance]]"'),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/S2 — Bare.md",
        _md("S2", "Bare", work_type="story", parent="IAD-E4"),
    )
    out = export_tasks(mem)
    rows = _by_id(out)
    assert rows["S1"]["parent"] == "IAD-E4"
    assert rows["S2"]["parent"] == "IAD-E4"


def test_t5_archive_window():
    today = prague_today().isoformat()
    mem = MemVault()
    mem.add(
        "07-ARCHIV/tasks-done/alpha/R1 — Nedavno.md",
        _md("R1", "Nedavno", status="Done", updated=today),
    )
    mem.add(
        "07-ARCHIV/tasks-done/alpha/O1 — Stare.md",
        _md("O1", "Stare", status="Done", updated="2020-01-01"),
    )
    closed = export_tasks(mem, include_closed_days=0)
    _shape(closed)
    assert closed["tasks"] == []
    opened = export_tasks(mem, include_closed_days=7)
    _shape(opened)
    assert _by_id(opened).keys() == {"R1"}


def test_t6_open_count_matches_definition_without_context():
    mem = MemVault()
    mem.add(
        "02-PROJEKTY/Beta.md",
        "---\ntype: project\nslug: beta\nstatus: paused\n---\n# Beta\n",
    )
    specs = [
        ("alpha", "E1", "Prazdny", None),
        ("alpha", "N1", "Dalsi", "Next"),
        ("alpha", "A1", "Asap", "ASAP"),
        ("alpha", "D1", "Hotovo", "Done"),
        ("alpha", "C1", "Zruseno", "Cancelled"),
        ("beta", "P1", "Pauza", "Next"),
        ("alpha", "K1", "Dite", "Next"),
    ]
    for slug, task_id, title, status in specs:
        parent = "D1" if task_id == "K1" else None
        mem.add(
            f"02-PROJEKTY/{slug}/tasks/{task_id} — {title}.md",
            _md(task_id, title, status=status, slug=slug, parent=parent),
        )
    defined = 0
    for _slug, _task_id, _title, status in specs:
        if str(status or "Next") not in TERMINAL_STATUSES:
            defined += 1
    out = export_tasks(mem, include_closed_days=30, since="2000-01-01")
    _shape(out)
    assert out["count"] == defined
    ids = set(_by_id(out))
    assert "D1" not in ids
    assert "C1" not in ids
    assert "P1" in ids
    assert "parent_not_found" not in _by_id(out)["K1"]["parse_errors"]
    again = export_tasks(mem, include_closed_days=0)
    assert "D1" not in _by_id(again)
    assert "C1" not in _by_id(again)


def test_t9_broken_frontmatter_stays_and_oid_matches(git_repo: Path):
    tasks = git_repo / "02-PROJEKTY" / "alpha" / "tasks"
    tasks.mkdir(parents=True)
    missing = tasks / "M1 — Bez.md"
    broken = tasks / "Y1 — Yaml.md"
    missing.write_text("# bez frontmatteru\n", encoding="utf-8")
    broken.write_text("---\nid: [broken\n---\nbody\n", encoding="utf-8")
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-m", "tasks")

    def hashed(path: Path) -> str:
        proc = subprocess.run(
            ["git", "hash-object", str(path)],
            capture_output=True,
            check=True,
            text=True,
        )
        return proc.stdout.strip()

    vault = GitVault(git_repo, dry_run=True, push=False)
    with vault:
        out = export_tasks(vault)
    _shape(out)
    rows = {row["path"]: row for row in out["tasks"]}
    miss = rows[f"02-PROJEKTY/alpha/tasks/{missing.name}"]
    bad = rows[f"02-PROJEKTY/alpha/tasks/{broken.name}"]
    assert "missing_frontmatter" in miss["parse_errors"]
    assert "yaml_error" in bad["parse_errors"]
    assert miss["oid"] == hashed(missing)
    assert bad["oid"] == hashed(broken)
    assert not any("hash-object" in arg for cmd in vault._git_cmds for arg in cmd)


def test_t10_fields_standard_and_full():
    mem = MemVault()
    mem.add(
        "02-PROJEKTY/alpha/tasks/F1 — Full.md",
        _md(
            "F1",
            "Full",
            extra='materials:\n  - "[[Note]]"\nblocked_by:\n  - X1\ncompany_priorities:\n  - CP1\nsource: manual',
        ),
    )
    standard = export_tasks(mem, fields="standard")
    full = export_tasks(mem, fields="full")
    assert "materials" not in standard["tasks"][0]
    assert "blocked_by" not in standard["tasks"][0]
    assert "company_priorities" not in standard["tasks"][0]
    assert "source" not in standard["tasks"][0]
    row = full["tasks"][0]
    assert row["materials"] == ["[[Note]]"]
    assert row["blocked_by"] == ["X1"]
    assert row["company_priorities"] == ["CP1"]
    assert row["source"] == "manual"


def test_t11_projects_csv_keeps_cross_project_parent():
    mem = MemVault()
    mem.add(
        "02-PROJEKTY/beta/tasks/B-E1 — Epic.md",
        _md("B-E1", "Epic", work_type="epic", slug="beta"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/A-S1 — Story.md",
        _md("A-S1", "Story", work_type="story", slug="alpha", parent="B-E1"),
    )
    mem.add(
        "02-PROJEKTY/beta/tasks/B-S2 — Jina.md",
        _md("B-S2", "Jina", work_type="story", slug="beta", parent="B-E1"),
    )
    out = export_tasks(mem, projects_csv="alpha, alpha,")
    _shape(out)
    assert [row["id"] for row in out["tasks"]] == ["A-S1"]
    assert "parent_not_found" not in out["tasks"][0]["parse_errors"]
    assert out["tasks"][0]["parent"] == "B-E1"


def test_t12_since_sees_body_commit_on_em_dash_path(git_repo: Path):
    tasks = git_repo / "02-PROJEKTY" / "alpha" / "tasks"
    tasks.mkdir(parents=True)
    em_name = "X1 — Nadpis.md"
    old_name = "Y1 — Stary.md"
    em = tasks / em_name
    old = tasks / old_name
    em.write_text(
        "---\nid: X1\ntitle: Nadpis\nstatus: Next\nupdated: 2020-01-01\nslug: alpha\n---\n\nbody v1\n",
        encoding="utf-8",
    )
    old.write_text(
        "---\nid: Y1\ntitle: Stary\nstatus: Next\nupdated: 2020-01-01\nslug: alpha\n---\n\nold\n",
        encoding="utf-8",
    )
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-m", "first", date="2026-10-01T10:00:00+02:00")
    em.write_text(em.read_text(encoding="utf-8").replace("body v1", "body v2"), encoding="utf-8")
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-m", "body", date="2026-10-18T10:00:00+02:00")
    _git(git_repo, "rm", f"02-PROJEKTY/alpha/tasks/{old_name}")
    _git(git_repo, "commit", "-m", "drop old", date="2026-10-19T10:00:00+02:00")

    vault = GitVault(git_repo, dry_run=True, push=False)
    with vault:
        out = export_tasks(vault, since="2026-10-10T00:00:00+02:00")
        with pytest.raises(ValueError, match="invalid_since"):
            export_tasks(vault, since="not-a-date")
    _shape(out)
    assert [row["id"] for row in out["tasks"]] == ["X1"]
    assert out["tasks"][0]["path"] == f"02-PROJEKTY/alpha/tasks/{em_name}"
    assert "deleted" not in out
    assert all(not row["path"].endswith(old_name) for row in out["tasks"])
    joined = [" ".join(cmd) for cmd in vault._git_cmds]
    assert any("-c" in cmd and "core.quotepath=false" in cmd and "-z" in cmd for cmd in joined)


def test_t13_steps_only_in_operational_section():
    body = """- [ ] mimo

## Operativní kroky

- [ ] otevreny
- [x] hotovy

## Poznámky / log

- [ ] taky mimo
"""
    mem = MemVault()
    mem.add(
        "02-PROJEKTY/alpha/tasks/S1 — Kroky.md",
        _md("S1", "Kroky", body=body),
    )
    row = export_tasks(mem)["tasks"][0]
    assert row["steps_total"] == 2
    assert row["steps_done"] == 1


def test_t15_ice_score_stays_null_until_complete():
    mem = MemVault()
    mem.add("02-PROJEKTY/alpha/tasks/I0 — Prazdne.md", _md("I0", "Prazdne"))
    mem.add(
        "02-PROJEKTY/alpha/tasks/I5 — Plne.md",
        _md("I5", "Plne", extra="ice_i: 5\nice_c: 5\nice_e: 5"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/IZ — Nula.md",
        _md("IZ", "Nula", extra="ice_i: 5\nice_c: 5\nice_e: 0"),
    )
    rows = _by_id(export_tasks(mem))
    assert rows["I0"]["ice_i"] is None
    assert rows["I0"]["ice_c"] is None
    assert rows["I0"]["ice_e"] is None
    assert rows["I0"]["priority_score"] is None
    assert "ice_not_int" not in rows["I0"]["parse_errors"]
    assert rows["I5"]["priority_score"] == 5.0
    assert rows["IZ"]["ice_e"] == 0
    assert rows["IZ"]["priority_score"] is None


def test_t16_filename_mismatch_and_rotation():
    mem = MemVault()
    mem.add(
        "02-PROJEKTY/alpha/tasks/ZZ1 — Spatne.md",
        _md("ZZ1", "Spravne"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/OS6-2026-08-05.md",
        _md("OS6", "Ritual"),
    )
    rows = _by_id(export_tasks(mem))
    assert rows["ZZ1"]["filename_title_mismatch"] is True
    assert rows["OS6"]["filename_title_mismatch"] is False
    assert "filename_title_mismatch" not in rows["ZZ1"]["parse_errors"]


def test_t20_parent_rules_stay_on_the_task():
    mem = MemVault()
    mem.add("02-PROJEKTY/alpha/tasks/ST1 — Story.md", _md("ST1", "Story", work_type="story"))
    mem.add("02-PROJEKTY/alpha/tasks/EP1 — Epic.md", _md("EP1", "Epic", work_type="epic"))
    mem.add(
        "02-PROJEKTY/alpha/tasks/TT1 — Pod epicem.md",
        _md("TT1", "Pod epicem", parent="EP1"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/EP2 — S parentem.md",
        _md("EP2", "S parentem", work_type="epic", parent="ST1"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/C1 — Cyklus.md",
        _md("C1", "Cyklus", parent="C2"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/C2 — Zpet.md",
        _md("C2", "Zpet", work_type="story", parent="C1"),
    )
    rows = _by_id(export_tasks(mem))
    assert set(rows) == {"ST1", "EP1", "TT1", "EP2", "C1", "C2"}
    assert "parent_required" in rows["ST1"]["parse_errors"]
    assert "parent_not_story" in rows["TT1"]["parse_errors"]
    assert "epic_has_no_parent" in rows["EP2"]["parse_errors"]
    assert "parent_cycle" in rows["C1"]["parse_errors"]
    assert "parent_cycle" in rows["C2"]["parse_errors"]


def test_t21_duplicate_id_on_two_live_files():
    mem = MemVault()
    mem.add("02-PROJEKTY/alpha/tasks/DUP1 — One.md", _md("DUP1", "One"))
    mem.add("02-PROJEKTY/alpha/tasks/DUP1 — Two.md", _md("DUP1", "Two"))
    rows = export_tasks(mem)["tasks"]
    assert len(rows) == 2
    assert all("duplicate_id" in row["parse_errors"] for row in rows)


def test_t22_envelope_on_git_vault(git_repo: Path):
    vault = GitVault(git_repo, dry_run=True, push=False)
    with vault:
        out = export_tasks(vault)
    _shape(out)
    head = _git(git_repo, "rev-parse", "HEAD").stdout.strip()
    assert out["vault_head"] == head
    assert out["focus_week"] == current_focus_week(prague_today())
    assert out["generated_at"][-6] in "+-"
    assert out["generated_at"][-3] == ":"


def test_t23_six_hundred_files_under_budget(git_repo: Path):
    tasks = git_repo / "02-PROJEKTY" / "bulk" / "tasks"
    tasks.mkdir(parents=True)
    for n in range(600):
        (tasks / f"B{n} — T.md").write_text(
            f"---\nid: B{n}\ntitle: T\nstatus: Next\nslug: bulk\n---\n",
            encoding="utf-8",
        )
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-m", "bulk")
    vault = GitVault(
        git_repo,
        dry_run=False,
        push=True,
        fetch_on_begin=False,
        check_dirty_on_begin=False,
        commit_on_end=False,
    )
    with vault:
        started = time.perf_counter()
        out = export_tasks(vault)
        elapsed = time.perf_counter() - started
    _shape(out)
    assert out["count"] == 600
    assert elapsed < 1.5
    assert not any("hash-object" in arg for cmd in vault._git_cmds for arg in cmd)
    ops = _git_ops(vault._git_cmds)
    for forbidden in ("fetch", "status", "add", "commit", "push"):
        assert forbidden not in ops


def _git_ops(cmds: list[list[str]]) -> list[str]:
    ops: list[str] = []
    for cmd in cmds:
        args = cmd[1:]
        if args[:1] == ["-c"]:
            args = args[2:]
        if args:
            ops.append(args[0])
    return ops


def test_t28_projects_match_collect_projects_four_fields():
    from agent_context_build import collect_projects
    import task_export

    src = Path(task_export.__file__).read_text(encoding="utf-8")
    assert "collect_projects" not in src
    assert "_section_excerpt" not in src
    assert "project_uses_hierarchy" not in src

    mem = MemVault()
    mem.add(
        "02-PROJEKTY/Alpha.md",
        "---\ntype: project\nslug: alpha\nstatus: paused\nhierarchy: true\ntitle: Frontmatter\n---\n"
        "# Alpha z nadpisu\n\n## Scope\n\nDlouhý excerpt, který export nepočítá.\n",
    )
    mem.add(
        "02-PROJEKTY/Beta.md",
        "---\ntype: project\nslug: beta\nhierarchy: \"yes\"\n---\n# Beta\n",
    )
    mem.add(
        "02-PROJEKTY/Universe.md",
        "---\ntype: project\nslug: rb-universe-development\nstatus: active\ntitle: Universe\n---\n"
        "bez hierarchy flagu\n",
    )
    mem.add(
        "02-PROJEKTY/My Hub.md",
        "---\ntype: project\nstatus: active\n---\n# Muj hub\n",
    )
    mem.add(
        "02-PROJEKTY/_draft.md",
        "---\ntype: project\nslug: hidden\nhierarchy: true\n---\n# Hidden\n",
    )
    mem.add(
        "02-PROJEKTY/notes.md",
        "---\ntype: note\nslug: notes\n---\n# Not a hub\n",
    )
    out = export_tasks(mem)
    expected = [
        {
            "slug": str(row["slug"]),
            "title": str(row["title"]),
            "status": str(row["status"] or "active"),
            "hierarchy": bool(row["hierarchy"]),
        }
        for row in collect_projects(mem)
    ]
    assert out["projects"] == sorted(expected, key=lambda row: row["slug"])
    by_slug = {row["slug"]: row for row in out["projects"]}
    assert by_slug["alpha"]["hierarchy"] is True
    assert by_slug["alpha"]["title"] == "Alpha z nadpisu"
    assert by_slug["alpha"]["status"] == "paused"
    assert by_slug["beta"]["hierarchy"] is True
    assert by_slug["beta"]["status"] == "active"
    assert by_slug["rb-universe-development"]["hierarchy"] is True
    assert by_slug["my-hub"]["hierarchy"] is False
    assert by_slug["my-hub"]["title"] == "Muj hub"
    assert "hidden" not in by_slug
    assert "notes" not in by_slug
    assert all("charter_scope" not in row for row in out["projects"])


def test_t29_source_does_not_hardcode_hierarchy_slugs():
    import task_export

    src = Path(task_export.__file__).read_text(encoding="utf-8")
    assert "project_uses_hierarchy" not in src
    for name in ("Finance", "Firemní procesy", "IT AI Data", "RB Universe", "Vibe coding"):
        assert name not in src


def test_t30_filename_alnum_string_not_set_or_prefix():
    from task_export import _alnum, _filename_mismatch
    from task_identity import expected_stem

    mismatches = [
        (
            "AF15 — Nový formát Allfred budgetu — pro delivery",
            "AF15",
            "Nový formát Allfred budgetu — jedna struktura šablony",
        ),
        (
            "AF37 — přehodit planned expenses Our Work→Production",
            "AF37",
            "přehodit planned expenses Our Work→Production Po Dominikově překlopení",
        ),
        (
            "F-S63 — Sledovat: Honza × Luboš — potvrzení net odměny 120k",
            "F-S63",
            "Sledovat: Honza × Luboš — potvrzení net odměny 120k (socko/zdrávko)",
        ),
        (
            "RBU-S99 — Delivery karta projektu — Lucie skill vs Universe (1)",
            "RBU-S99",
            "Delivery karta projektu — Lucie skill vs Universe",
        ),
    ]
    for stem, task_id, title in mismatches:
        assert _filename_mismatch(f"02-PROJEKTY/alpha/tasks/{stem}.md", task_id, title) is True
    fs63_stem, fs63_id, fs63_title = mismatches[2]
    expected = _alnum(expected_stem(fs63_id, fs63_title))
    stem_alnum = _alnum(fs63_stem)
    assert stem_alnum != expected
    assert expected.startswith(stem_alnum)
    assert _alnum("120") != _alnum("012")
    assert _filename_mismatch(
        "02-PROJEKTY/alpha/tasks/N1 — odmena 120.md",
        "N1",
        "odmena 012",
    ) is True
    assert _filename_mismatch(
        "02-PROJEKTY/alpha/tasks/C1 — Navrh -dodavka.md",
        "C1",
        "Navrh/dodavka",
    ) is False
    assert _filename_mismatch(
        "02-PROJEKTY/alpha/tasks/C2 — Hello — world.md",
        "C2",
        "Hello world",
    ) is False
    assert _filename_mismatch(
        "02-PROJEKTY/alpha/tasks/OS6-2026-08-05.md",
        "OS6",
        "Uplne jiny nazev",
    ) is False
    assert _filename_mismatch(
        "02-PROJEKTY/alpha/tasks/ZZ1 — Spatne.md",
        "ZZ1",
        "Spravne",
    ) is True

    mem = MemVault()
    mem.add("02-PROJEKTY/alpha/tasks/ZZ1 — Spatne.md", _md("ZZ1", "Spravne"))
    mem.add("02-PROJEKTY/alpha/tasks/C1 — Navrh -dodavka.md", _md("C1", "Navrh/dodavka"))
    rows = _by_id(export_tasks(mem))
    assert rows["ZZ1"]["filename_title_mismatch"] is True
    assert rows["C1"]["filename_title_mismatch"] is False
    assert "filename_title_mismatch" not in rows["ZZ1"]["parse_errors"]
    assert "filename_title_mismatch" not in rows["C1"]["parse_errors"]


def test_t31_id_type_mismatch_uses_raw_type():
    def _raw(task_id: str, title: str, *, type_line: str | None) -> str:
        type_row = f"type: {type_line}\n" if type_line is not None else ""
        return (
            f"---\nid: {task_id}\ntitle: {title}\n{type_row}"
            "slug: alpha\nstatus: Next\nupdated: 2026-10-01\n---\n"
        )

    mem = MemVault()
    mem.add(
        "02-PROJEKTY/alpha/tasks/S-S33 — Inspirace.md",
        _raw("S-S33", "Inspirace", type_line="task"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/S-S34 — Bez type.md",
        _raw("S-S34", "Bez type", type_line=None),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/S-S35 — Widget.md",
        _raw("S-S35", "Widget", type_line="widget"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/RBU-S99 — Story.md",
        _raw("RBU-S99", "Story", type_line="story"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/AF15 — Task.md",
        _raw("AF15", "Task", type_line="task"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/RBU-E1 — Task.md",
        _raw("RBU-E1", "Task", type_line="task"),
    )
    mem.add(
        "02-PROJEKTY/alpha/tasks/S-S70-1 — Krok.md",
        _raw("S-S70-1", "Krok", type_line="task"),
    )
    before = dict(mem.files)
    rows = _by_id(export_tasks(mem))
    assert mem.files == before
    assert "id_type_mismatch" in rows["S-S33"]["parse_errors"]
    assert rows["S-S33"]["type"] == "task"
    assert "id_type_mismatch" not in rows["S-S34"]["parse_errors"]
    assert "unknown_type" not in rows["S-S34"]["parse_errors"]
    assert rows["S-S34"]["type"] == "task"
    assert rows["S-S35"]["parse_errors"].count("unknown_type") == 1
    assert "id_type_mismatch" not in rows["S-S35"]["parse_errors"]
    assert rows["S-S35"]["type"] == "task"
    assert "id_type_mismatch" not in rows["RBU-S99"]["parse_errors"]
    assert rows["RBU-S99"]["type"] == "story"
    assert "id_type_mismatch" not in rows["AF15"]["parse_errors"]
    assert "id_type_mismatch" in rows["RBU-E1"]["parse_errors"]
    assert rows["RBU-E1"]["type"] == "task"
    assert "id_type_mismatch" not in rows["S-S70-1"]["parse_errors"]
    same_id = MemVault()
    same_id.add(
        "02-PROJEKTY/alpha/tasks/S-S33 — bez type.md",
        _raw("S-S33", "Inspirace", type_line=None),
    )
    bare = _by_id(export_tasks(same_id))["S-S33"]
    assert "id_type_mismatch" not in bare["parse_errors"]
    assert "unknown_type" not in bare["parse_errors"]
    assert bare["type"] == "task"


class _SpyVault(MemVault):
    def __init__(self):
        super().__init__()
        self.reads: list[str] = []
        self.lists: list[str] = []

    def read_text(self, path: str):
        self.reads.append(path)
        return super().read_text(path)

    def list_dir(self, path, pattern=None, recursive=False, include_folders=False):
        self.lists.append(str(path))
        return super().list_dir(
            path,
            pattern=pattern,
            recursive=recursive,
            include_folders=include_folders,
        )


def test_t32_parent_closed_archive_only():
    hung = _SpyVault()
    hung.add(
        "02-PROJEKTY/alpha/tasks/F-T161 — dite.md",
        _md("F-T161", "dite", parent="F-S71", updated="2026-10-19"),
    )
    hung.add(
        "02-PROJEKTY/alpha/tasks/KOS1 — rotace.md",
        _md("KOS1", "rotace", parent="OS6", updated="2026-10-19"),
    )
    hung.add(
        "07-ARCHIV/tasks-done/finance/F-S71 — x.md",
        _md("ZZZ9", "cizi id uvnitr", status="Done", updated="2020-01-01"),
    )
    hung.add(
        "07-ARCHIV/tasks-done/alpha/OS6-2026-08-05.md",
        _md("OS6", "rotace", status="Done", updated="2020-01-01"),
    )
    out = export_tasks(hung, include_closed_days=0, projects_csv="alpha", since="2026-10-01")
    rows = _by_id(out)
    assert set(rows) == {"F-T161", "KOS1"}
    child = rows["F-T161"]["parse_errors"]
    assert "parent_closed" in child
    assert "parent_not_found" not in child
    rotation = rows["KOS1"]["parse_errors"]
    assert "parent_not_found" in rotation
    assert "parent_closed" not in rotation
    assert not any(path.startswith("07-ARCHIV/") for path in hung.reads)

    ghost = _SpyVault()
    ghost.add(
        "02-PROJEKTY/alpha/tasks/G1 — nikde.md",
        _md("G1", "nikde", parent="ZZ9"),
    )
    ghost_rows = _by_id(export_tasks(ghost))
    ghost_err = ghost_rows["G1"]["parse_errors"]
    assert "parent_not_found" in ghost_err
    assert "parent_closed" not in ghost_err

    active = _SpyVault()
    active.add(
        "02-PROJEKTY/alpha/tasks/D1 — Hotovo.md",
        _md("D1", "Hotovo", status="Done"),
    )
    active.add(
        "02-PROJEKTY/alpha/tasks/K1 — Dite.md",
        _md("K1", "Dite", parent="D1"),
    )
    active.add(
        "02-PROJEKTY/alpha/tasks/C9 — Zruseno.md",
        _md("C9", "Zruseno", status="Cancelled"),
    )
    active.add(
        "02-PROJEKTY/alpha/tasks/K9 — Dite.md",
        _md("K9", "Dite", parent="C9"),
    )
    active_rows = _by_id(export_tasks(active))
    assert "D1" not in active_rows
    assert "C9" not in active_rows
    for task_id in ("K1", "K9"):
        errs = active_rows[task_id]["parse_errors"]
        assert "parent_not_found" not in errs
        assert "parent_closed" not in errs
        assert "parent_not_story" in errs
    assert not any(path.startswith("07-ARCHIV") for path in active.lists)

    today = prague_today().isoformat()
    window = _SpyVault()
    window.add(
        "07-ARCHIV/tasks-done/alpha/F-S82 — hotovo.md",
        _md("F-S82", "hotovo", status="Done", work_type="story", updated=today),
    )
    window.add(
        "02-PROJEKTY/alpha/tasks/F-T176 — dite.md",
        _md("F-T176", "dite", parent="F-S82"),
    )
    window.add(
        "07-ARCHIV/tasks-done/alpha/F-S83 — zruseno.md",
        _md("F-S83", "zruseno", status="Cancelled", work_type="story", updated=today),
    )
    window.add(
        "02-PROJEKTY/alpha/tasks/F-T177 — dite.md",
        _md("F-T177", "dite", parent="F-S83"),
    )
    window.add(
        "07-ARCHIV/tasks-done/alpha/F-S84 — next.md",
        _md("F-S84", "next", status="Next", work_type="story", updated=today),
    )
    window.add(
        "02-PROJEKTY/alpha/tasks/F-T178 — dite.md",
        _md("F-T178", "dite", parent="F-S84"),
    )
    window_rows = _by_id(export_tasks(window, include_closed_days=7))
    for task_id in ("F-T176", "F-T177"):
        errs = window_rows[task_id]["parse_errors"]
        assert "parent_closed" in errs
        assert "parent_not_found" not in errs
        assert "parent_not_story" not in errs
    open_parent = window_rows["F-T178"]["parse_errors"]
    assert "parent_closed" not in open_parent
    assert "parent_not_found" not in open_parent
