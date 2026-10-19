"""Brain export_tasks — T7, T8, T14, T17–T19, T25, T26."""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("BRAIN_ALLOW_NO_PUSH", "1")
os.environ.setdefault("BRAIN_SERVICE_TOKEN", "test-service-token")

from app.mcp_app import build_mcp  # noqa: E402
from app.tools import export_tasks as export_mod  # noqa: E402
from app.tools import find_tasks as find_mod  # noqa: E402
from app.tools import update_task as update_mod  # noqa: E402
from drive_io import DriveNotFoundError, DriveVaultError  # noqa: E402


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
            if is_dir:
                if include_folders:
                    out.append(_Meta(rel, True))
                continue
            if pattern == "*.md" and not name.endswith(".md"):
                continue
            out.append(_Meta(rel, False))
        return out


class _CM:
    def __init__(self, vault):
        self.vault = vault

    def __enter__(self):
        return self.vault

    def __exit__(self, *args):
        return False


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    return root


def _env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_VAULT_ROOT"] = str(root)
    env["GIT_VAULT_REMOTE"] = ""
    env["VAULT_BACKEND"] = "git"
    env["BRAIN_ALLOW_NO_PUSH"] = "1"
    env["GIT_VAULT_PUSH"] = "0"
    env["BRAIN_SERVICE_TOKEN"] = "test-service-token"
    env.pop("VAULT_WRITERS_PAUSED", None)
    return env


def _task(task_id: str, title: str, *, status: str | None = "Next", parent: str = "", deadline: str = "") -> str:
    status_line = f"status: {status}\n" if status is not None else ""
    parent_line = f"parent: {parent}\n" if parent else ""
    deadline_line = f"deadline: {deadline}\n" if deadline else ""
    return (
        f"---\nid: {task_id}\ntitle: {title}\ntype: task\nslug: alpha\n"
        f"{status_line}{parent_line}{deadline_line}---\n"
    )


def test_t7_find_tasks_fields_match_for_non_terminal(monkeypatch):
    vault = MemVault()
    vault.add(
        "02-PROJEKTY/alpha/tasks/E1 — Prazdny.md",
        _task("E1", "Prazdny", status=None, parent='"[[IAD-E4 — Security & Performance]]"'),
    )
    vault.add(
        "02-PROJEKTY/alpha/tasks/N1 — Dalsi.md",
        _task("N1", "Dalsi", status="Next", deadline="2026-11-01"),
    )
    vault.add("02-PROJEKTY/alpha/tasks/D1 — Hotovo.md", _task("D1", "Hotovo", status="Done"))
    vault.add("02-PROJEKTY/alpha/tasks/C1 — Zruseno.md", _task("C1", "Zruseno", status="Cancelled"))

    def _open(*, mode, env=None, check_dirty=True):
        assert mode == "read"
        del env, check_dirty
        return _CM(vault)

    monkeypatch.setattr(find_mod, "brain_vault", _open)
    monkeypatch.setattr(export_mod, "brain_vault", _open)
    found = find_mod.find_tasks()["tasks"]
    exported = {row["id"]: row for row in export_mod.export_tasks()["tasks"]}
    assert {row["id"] for row in found} == {"E1", "N1", "D1", "C1"}
    for row in found:
        if row["status"] in {"Done", "Cancelled"}:
            assert row["id"] not in exported
            continue
        exp = exported[row["id"]]
        assert exp["status"] == row["status"]
        assert exp["parent"] == row["parent"]
        assert exp["deadline"] == row["deadline"]
    assert exported["E1"]["status"] == ""
    assert exported["E1"]["parent"] == "IAD-E4"


def test_t8_dry_run_expect_oid_is_not_409(tmp_path: Path):
    root = _repo(tmp_path)
    tasks = root / "02-PROJEKTY" / "alpha" / "tasks"
    tasks.mkdir(parents=True)
    live = tasks / "X1 — Nadpis.md"
    broken = tasks / "Y1 — Rozbite.md"
    live.write_text(_task("X1", "Nadpis"), encoding="utf-8")
    broken.write_text("---\nid: [broken\n---\nbody\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "tasks")
    env = _env(root)
    out = export_mod.export_tasks(env=env)
    rows = {row["path"]: row for row in out["tasks"]}
    live_row = rows["02-PROJEKTY/alpha/tasks/X1 — Nadpis.md"]
    bad_row = rows["02-PROJEKTY/alpha/tasks/Y1 — Rozbite.md"]

    def hashed(path: Path) -> str:
        proc = subprocess.run(
            ["git", "hash-object", str(path)],
            capture_output=True,
            check=True,
            text=True,
        )
        return proc.stdout.strip()

    assert live_row["oid"] == hashed(live)
    assert bad_row["oid"] == hashed(broken)
    ok = update_mod.update_task(
        path=live_row["path"],
        patch={"status": "Doing"},
        expect_oid=live_row["oid"],
        dry_run=True,
        env=env,
    )
    assert ok["dry_run"] is True
    bad = update_mod.update_task(
        path=bad_row["path"],
        patch={"status": "Doing"},
        expect_oid=bad_row["oid"],
        dry_run=True,
        env=env,
    )
    assert bad["dry_run"] is True


def test_t14_mcp_structured_content(tmp_path: Path, monkeypatch):
    root = _repo(tmp_path)
    for key, value in _env(root).items():
        monkeypatch.setenv(key, value)
    mcp = build_mcp()
    result = asyncio.run(mcp.call_tool("export_tasks", {}))
    assert result.is_error is False
    payload = result.structured_content
    assert isinstance(payload, dict)
    assert "tasks" in payload
    assert payload["count"] == len(payload["tasks"])
    assert "result" not in payload
    assert not isinstance(payload.get("tasks"), str)


def test_t17_read_mode_does_not_rebuild_context(monkeypatch):
    tool_src = Path(export_mod.__file__).read_text(encoding="utf-8")
    lib_src = (_HUB / "task_export.py").read_text(encoding="utf-8")
    assert "get_context" not in tool_src
    assert "get_context" not in lib_src
    assert "build_and_write_context_bundle" not in tool_src
    assert "build_and_write_context_bundle" not in lib_src

    def boom(*_args, **_kwargs):
        raise AssertionError("context rebuild")

    import agent_context_build
    import app.tools.get_context as get_context_mod

    monkeypatch.setattr(agent_context_build, "build_and_write_context_bundle", boom)
    monkeypatch.setattr(get_context_mod, "get_context", boom)
    seen: dict[str, str] = {}

    def _open(*, mode, env=None, check_dirty=True):
        del env, check_dirty
        seen["mode"] = mode
        return _CM(MemVault())

    monkeypatch.setattr(export_mod, "brain_vault", _open)
    out = export_mod.export_tasks()
    assert seen["mode"] == "read"
    assert out["count"] == len(out["tasks"])
    assert "open_count" not in out


def test_t18_rest_auth_and_t19_validation(tmp_path: Path, monkeypatch):
    from app.main import app

    root = _repo(tmp_path)
    for key, value in _env(root).items():
        monkeypatch.setenv(key, value)
    client = TestClient(app)
    anonymous = client.get("/v1/tasks/export")
    assert anonymous.status_code == 401
    authed = client.get(
        "/v1/tasks/export",
        headers={"Authorization": "Bearer test-service-token"},
    )
    assert authed.status_code == 200
    body = authed.json()
    assert body["count"] == len(body["tasks"])
    assert "open_count" not in body

    fields = client.get(
        "/v1/tasks/export",
        params={"fields": "nope"},
        headers={"Authorization": "Bearer test-service-token"},
    )
    assert fields.status_code == 400
    assert fields.json()["error_reason"] == "invalid_fields"
    negative = client.get(
        "/v1/tasks/export",
        params={"include_closed_days": -1},
        headers={"Authorization": "Bearer test-service-token"},
    )
    assert negative.status_code == 400
    assert negative.json()["error_reason"] == "invalid_include_closed_days"
    since = client.get(
        "/v1/tasks/export",
        params={"since": "not-a-date"},
        headers={"Authorization": "Bearer test-service-token"},
    )
    assert since.status_code == 400
    assert since.json()["error_reason"] == "invalid_since"


def _repo_with_origin(tmp_path: Path) -> Path:
    root = _repo(tmp_path)
    bare = tmp_path / "origin.git"
    _git(tmp_path, "clone", "--bare", str(root), str(bare))
    _git(root, "remote", "add", "origin", str(bare))
    _git(root, "fetch", "origin")
    _git(root, "branch", "--set-upstream-to=origin/main", "main")
    return root


def _git_ops(cmds: list[list[str]]) -> list[str]:
    ops: list[str] = []
    for cmd in cmds:
        args = cmd[1:]
        if args[:1] == ["-c"]:
            args = args[2:]
        if args:
            ops.append(args[0])
    return ops


def _spy_vaults(monkeypatch, held: list) -> None:
    import app.vault_deps as vault_deps

    real = vault_deps.open_vault

    def _open(**kwargs):
        vault = real(**kwargs)
        held.append(vault)
        return vault

    monkeypatch.setattr(vault_deps, "open_vault", _open)


def test_t25_read_skips_fetch_and_commit_mutate_rebuild_keep_them(tmp_path: Path, monkeypatch):
    root = _repo_with_origin(tmp_path)
    env = _env(root)
    env["GIT_VAULT_PUSH"] = "1"
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    _git(root, "fetch", "origin")
    assert _git(root, "rev-parse", "HEAD").stdout.strip() == head

    held: list = []
    _spy_vaults(monkeypatch, held)
    from app.vault_deps import brain_vault

    with brain_vault(mode="read", env=env) as vault:
        assert vault.head_sha() == head
    read_ops = _git_ops(held[-1]._git_cmds)
    for forbidden in ("fetch", "add", "commit", "push"):
        assert forbidden not in read_ops
    assert _git(root, "rev-parse", "HEAD").stdout.strip() == head

    out = export_mod.export_tasks(env=env)
    assert out["vault_head"] == head
    assert out["count"] == len(out["tasks"])
    assert "open_count" not in out
    export_ops = _git_ops(held[-1]._git_cmds)
    for forbidden in ("fetch", "status", "add", "commit", "push"):
        assert forbidden not in export_ops
    assert _git(root, "rev-parse", "HEAD").stdout.strip() == head

    with brain_vault(mode="mutate", env=env) as vault:
        vault.write_text("02-PROJEKTY/mutate.md", "mutate\n")
    mutate_ops = _git_ops(held[-1]._git_cmds)
    for required in ("fetch", "add", "commit"):
        assert required in mutate_ops
    assert (root / "02-PROJEKTY" / "mutate.md").read_text(encoding="utf-8") == "mutate\n"
    assert _git(root, "rev-parse", "HEAD").stdout.strip() != head

    with brain_vault(mode="rebuild", env=env) as vault:
        vault.write_text("02-PROJEKTY/rebuild.md", "rebuild\n")
    rebuild_ops = _git_ops(held[-1]._git_cmds)
    for required in ("fetch", "add", "commit"):
        assert required in rebuild_ops
    assert (root / "02-PROJEKTY" / "rebuild.md").read_text(encoding="utf-8") == "rebuild\n"


def test_t26_dirty_export_stays_200_other_read_is_503(tmp_path: Path, monkeypatch):
    root = _repo_with_origin(tmp_path)
    env = _env(root)
    env["GIT_VAULT_PUSH"] = "1"
    tasks = root / "02-PROJEKTY" / "alpha" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "Z9 — Spinavy.md").write_text(
        "---\nid: Z9\ntitle: Spinavy unikat\nstatus: Next\ntype: task\nslug: alpha\n---\n",
        encoding="utf-8",
    )
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    held: list = []
    _spy_vaults(monkeypatch, held)

    out = export_mod.export_tasks(env=env)
    assert out["count"] == len(out["tasks"]) == 1
    assert out["tasks"][0]["id"] == "Z9"
    assert out["tasks"][0]["title"] == "Spinavy unikat"
    assert _git(root, "rev-parse", "HEAD").stdout.strip() == head
    ops = _git_ops(held[-1]._git_cmds)
    for forbidden in ("fetch", "status", "add", "commit", "push"):
        assert forbidden not in ops

    from app.errors import BrainVaultError

    with pytest.raises(BrainVaultError) as other_read:
        find_mod.find_tasks(env=env)
    assert other_read.value.error_reason == "vault_dirty_start"
    assert other_read.value.status_code == 503

    from app.vault_deps import brain_vault

    marker = root / "02-PROJEKTY" / "mutate-should-not.md"
    with pytest.raises(BrainVaultError) as mutate:
        with brain_vault(mode="mutate", env=env) as vault:
            vault.write_text("02-PROJEKTY/mutate-should-not.md", "nope\n")
    assert mutate.value.error_reason == "vault_dirty_start"
    assert not marker.exists()
    assert _git(root, "rev-parse", "HEAD").stdout.strip() == head


def test_t26_invalid_since_does_not_reset_tracked_bytes(tmp_path: Path, monkeypatch):
    root = _repo_with_origin(tmp_path)
    env = _env(root)
    env["GIT_VAULT_PUSH"] = "1"
    rel = "02-PROJEKTY/alpha/tracked.md"
    path = root / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(b"committed-head\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "track")
    dirty = b"worktree-dirty-bytes\n"
    path.write_bytes(dirty)
    before = path.read_bytes()
    head_bytes = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=str(root),
        check=True,
        capture_output=True,
    ).stdout
    assert before == dirty
    assert before != head_bytes

    held: list = []
    _spy_vaults(monkeypatch, held)
    from app.errors import BrainClientError

    with pytest.raises(BrainClientError) as ei:
        export_mod.export_tasks(since="not-a-date", env=env)
    assert ei.value.status_code == 400
    assert ei.value.error_reason == "invalid_since"
    assert path.read_bytes() == before
    assert path.read_bytes() != head_bytes
    assert path.is_file()
    assert not any("reset" in cmd and "--hard" in cmd for cmd in held[-1]._git_cmds)
