"""Git working-copy vault I/O (GitVault) for second-brain-hub cron jobs.

Path API mirrors DriveVault. CAS uses git blob SHA (`expect_oid`); session
lifecycle: flock → fetch → dirty-skip → ops → commit_if_dirty → optional push.
"""
from __future__ import annotations

import fcntl
import json
import logging
import mimetypes
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from drive_io import (
    FOLDER_MIME,
    DriveConflictError,
    DriveNotFoundError,
    DriveVaultError,
    FileMeta,
    _glob_to_substr,
    _matches_pattern,
    _norm_rel,
    _split_rel,
)

log = logging.getLogger("git_io")

DEFAULT_ROOT = "/data/vault"
DEFAULT_BRANCH = "main"
LOCK_NAME = "second-brain-vault.lock"
FLOCK_TIMEOUT_S = 5.0
DEFAULT_AUTHOR_NAME = "Second Brain Hub"
DEFAULT_AUTHOR_EMAIL = "second-brain-hub@noreply.redbuttonedu.cz"


def _env_flag(env: Mapping[str, str], key: str, default: bool = False) -> bool:
    raw = (env.get(key) or "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _utc_mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _guess_mime(path: Path, *, is_dir: bool) -> str:
    if is_dir:
        return FOLDER_MIME
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


class GitVault:
    """Path-based facade over a local git working copy of the Obsidian vault."""

    def __init__(
        self,
        root: str | Path | None = None,
        *,
        remote: str | None = None,
        branch: str | None = None,
        dry_run: bool | None = None,
        push: bool | None = None,
        author_name: str | None = None,
        author_email: str | None = None,
        env: Mapping[str, str] | None = None,
        flock_timeout: float = FLOCK_TIMEOUT_S,
        require_git: bool = True,
    ) -> None:
        env_map = env if env is not None else os.environ
        self._env = env_map
        self.root = Path(root or env_map.get("GIT_VAULT_ROOT") or DEFAULT_ROOT)
        self.remote = (
            remote
            if remote is not None
            else (env_map.get("GIT_VAULT_REMOTE") or "").strip()
        )
        self.branch = (
            branch
            if branch is not None
            else (env_map.get("GIT_VAULT_BRANCH") or DEFAULT_BRANCH).strip()
            or DEFAULT_BRANCH
        )
        self.dry_run = dry_run if dry_run is not None else _env_flag(env_map, "GIT_VAULT_DRY_RUN")
        self.push_enabled = (
            push if push is not None else _env_flag(env_map, "GIT_VAULT_PUSH")
        )
        self.author_name = (
            author_name
            or (env_map.get("GIT_AUTHOR_NAME") or "").strip()
            or DEFAULT_AUTHOR_NAME
        )
        self.author_email = (
            author_email
            or (env_map.get("GIT_AUTHOR_EMAIL") or "").strip()
            or DEFAULT_AUTHOR_EMAIL
        )
        self.flock_timeout = flock_timeout

        self._session_active = False
        self.skipped = False
        self._lock_fh = None
        self._git_cmds: list[list[str]] = []  # test spy

        if require_git and not (self.root / ".git").is_dir():
            raise RuntimeError(
                f"GIT_VAULT_ROOT {self.root} has no .git directory. "
                "Bootstrap with ensure_clone() outside DRY_RUN (F1-f), "
                "or set an existing working copy."
            )

    # ------------------------------------------------------------------ session

    def __enter__(self) -> "GitVault":
        self.begin_session()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.end_session(exc_type=exc_type)
        return None

    def begin_session(self) -> None:
        if self._session_active:
            return
        self.skipped = False
        self._session_active = True
        if not self._acquire_lock():
            log.warning(
                "git_io: flock busy on %s within %.1fs — skipping session",
                self._lock_path(),
                self.flock_timeout,
            )
            self.skipped = True
            return
        try:
            self._git(["fetch", "origin"], check=False)
        except Exception as exc:  # noqa: BLE001
            log.warning("git_io: fetch failed: %s", exc)
        if self._is_dirty():
            log.warning(
                "git_io: working tree dirty at session start under %s — "
                "skip+log only (no reset)",
                self.root,
            )
            self.skipped = True

    def end_session(self, *, exc_type=None) -> None:
        if not self._session_active:
            return
        try:
            if self.skipped or self.dry_run or exc_type is not None:
                return
            committed = self.commit_if_dirty()
            if committed and self.push_enabled:
                self._push_ff_only()
        finally:
            self._release_lock()
            self._session_active = False

    def ensure_clone(self) -> None:
        """Clone remote into root when .git is missing. Forbidden under DRY_RUN (B25)."""
        if (self.root / ".git").is_dir():
            return
        if self.dry_run:
            raise RuntimeError(
                "GIT_VAULT_DRY_RUN=1 and missing .git — refuse auto-clone (B25)"
            )
        if not self.remote:
            raise RuntimeError("GIT_VAULT_REMOTE required for ensure_clone()")
        self.root.mkdir(parents=True, exist_ok=True)
        if any(self.root.iterdir()):
            raise RuntimeError(
                f"GIT_VAULT_ROOT {self.root} is non-empty without .git; "
                "refusing clone into dirty path"
            )
        self._git(
            ["clone", "--branch", self.branch, self.remote, str(self.root)],
            cwd=self.root.parent,
            check=True,
        )
        self._git(["lfs", "pull"], check=False)

    # ------------------------------------------------------------------ path helpers

    def _abspath(self, rel_path: str) -> Path:
        rel = _norm_rel(rel_path)
        if not rel:
            return self.root
        parts = _split_rel(rel)
        if any(p in (".", "..") for p in parts):
            raise ValueError(f"Invalid path segment in: {rel_path!r}")
        return self.root.joinpath(*parts)

    def _lock_path(self) -> Path:
        return self.root / ".git" / LOCK_NAME

    def _acquire_lock(self) -> bool:
        lock_path = self._lock_path()
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(lock_path, "a+", encoding="utf-8")
        deadline = time.monotonic() + self.flock_timeout
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._lock_fh = fh
                return True
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    fh.close()
                    return False
                time.sleep(0.05)

    def _release_lock(self) -> None:
        fh = self._lock_fh
        self._lock_fh = None
        if fh is None:
            return
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()

    def _git(
        self,
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
        input_bytes: bytes | None = None,
        capture: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        cmd = ["git", *args]
        self._git_cmds.append(cmd)
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = self.author_name
        env["GIT_AUTHOR_EMAIL"] = self.author_email
        env["GIT_COMMITTER_NAME"] = self.author_name
        env["GIT_COMMITTER_EMAIL"] = self.author_email
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or self.root),
            check=check,
            input=input_bytes,
            capture_output=capture,
            env=env,
        )
        # Normalize stdout/stderr to str for callers.
        if capture:
            stdout = proc.stdout.decode() if isinstance(proc.stdout, (bytes, bytearray)) else (proc.stdout or "")
            stderr = proc.stderr.decode() if isinstance(proc.stderr, (bytes, bytearray)) else (proc.stderr or "")
            return subprocess.CompletedProcess(
                proc.args, proc.returncode, stdout, stderr
            )
        return proc  # type: ignore[return-value]

    def _is_dirty(self) -> bool:
        proc = self._git(["status", "--porcelain"], check=True)
        return bool((proc.stdout or "").strip())

    def _blob_oid_for_path(self, path: Path) -> str | None:
        if not path.is_file():
            return None
        proc = self._git(
            ["hash-object", str(path)],
            check=True,
        )
        return (proc.stdout or "").strip() or None

    def _blob_oid_for_bytes(self, data: bytes) -> str:
        proc = self._git(
            ["hash-object", "--stdin"],
            check=True,
            input_bytes=data,
        )
        return (proc.stdout or "").strip()

    def _meta_for_path(self, rel_path: str) -> FileMeta:
        rel = _norm_rel(rel_path)
        path = self._abspath(rel)
        if not path.exists():
            raise DriveNotFoundError(f"Path not found: {rel!r}")
        is_dir = path.is_dir()
        parent = path.parent
        parent_rel = ""
        if rel:
            segs = _split_rel(rel)
            parent_rel = "/".join(segs[:-1])
        oid = None if is_dir else self._blob_oid_for_path(path)
        size = None if is_dir else path.stat().st_size
        return FileMeta(
            id=rel or oid or "",
            name=path.name if rel else self.root.name,
            mime_type=_guess_mime(path, is_dir=is_dir),
            modified_time=_utc_mtime(path) if path.exists() else datetime.fromtimestamp(
                0, tz=timezone.utc
            ),
            size=size,
            parent_id=parent_rel or None,
            rel_path=rel,
            oid=oid,
        )

    def _fake_meta(self, rel_path: str, data: bytes, *, mime_type: str) -> FileMeta:
        rel = _norm_rel(rel_path)
        name = _split_rel(rel)[-1] if rel else ""
        parent_rel = "/".join(_split_rel(rel)[:-1]) if rel else ""
        oid = self._blob_oid_for_bytes(data) if data is not None else None
        return FileMeta(
            id=rel,
            name=name,
            mime_type=mime_type,
            modified_time=datetime.now(timezone.utc),
            size=len(data),
            parent_id=parent_rel or None,
            rel_path=rel,
            oid=oid,
        )

    def _mutate_allowed(self) -> bool:
        if self.skipped:
            log.info("git_io: skipped session — mutate no-op")
            return False
        return True

    def _check_cas(
        self,
        rel: str,
        path: Path,
        *,
        expect_oid: str | None,
        expect_mtime: datetime | None,
    ) -> None:
        if expect_oid is not None:
            if not path.is_file():
                raise DriveConflictError(
                    f"CAS expected existing file at {rel!r}, but file does not exist"
                )
            current = self._blob_oid_for_path(path)
            if current != expect_oid:
                raise DriveConflictError(
                    f"{rel!r} oid mismatch: current={current!r} expect={expect_oid!r}"
                )
            return
        if expect_mtime is not None:
            if not path.exists():
                raise DriveConflictError(
                    f"CAS expected existing file at {rel!r}, but file does not exist"
                )
            current_mtime = _utc_mtime(path)
            if current_mtime > expect_mtime:
                raise DriveConflictError(
                    f"{rel!r} modified externally at {current_mtime.isoformat()}"
                    f" (expected <= {expect_mtime.isoformat()})"
                )

    # ------------------------------------------------------------------ public

    def exists(self, rel_path: str) -> bool:
        return self._abspath(rel_path).exists()

    def stat(self, rel_path: str) -> FileMeta:
        return self._meta_for_path(rel_path)

    def list_dir(
        self,
        rel_path: str,
        *,
        pattern: str | None = None,
        recursive: bool = False,
        include_folders: bool = False,
    ) -> list[FileMeta]:
        base = self._abspath(rel_path)
        if not base.exists():
            raise DriveNotFoundError(f"Path not found: {_norm_rel(rel_path)!r}")
        if not base.is_dir():
            raise DriveVaultError(f"Not a folder: {rel_path!r}")
        needle = _glob_to_substr(pattern)
        base_rel = _norm_rel(rel_path)
        results: list[FileMeta] = []

        def walk(dir_path: Path, dir_rel: str) -> None:
            try:
                entries = sorted(dir_path.iterdir(), key=lambda p: p.name)
            except FileNotFoundError:
                return
            for entry in entries:
                if entry.name == ".git":
                    continue
                child_rel = f"{dir_rel}/{entry.name}" if dir_rel else entry.name
                if entry.is_dir():
                    if recursive:
                        walk(entry, child_rel)
                    if include_folders and _matches_pattern(entry.name, needle):
                        results.append(self._meta_for_path(child_rel))
                else:
                    if _matches_pattern(entry.name, needle):
                        results.append(self._meta_for_path(child_rel))

        walk(base, base_rel)
        results.sort(key=lambda m: m.rel_path)
        return results

    def read_text(self, rel_path: str, *, encoding: str = "utf-8") -> tuple[str, FileMeta]:
        meta = self._meta_for_path(rel_path)
        if meta.is_folder:
            raise DriveVaultError(f"Cannot read folder as text: {rel_path!r}")
        data = self._abspath(rel_path).read_bytes()
        return data.decode(encoding), meta

    def read_json(self, rel_path: str) -> tuple[Any, FileMeta]:
        text, meta = self.read_text(rel_path)
        return json.loads(text), meta

    def write_text(
        self,
        rel_path: str,
        text: str,
        *,
        expect_mtime: datetime | None = None,
        expect_oid: str | None = None,
        mime_type: str = "text/markdown",
        encoding: str = "utf-8",
    ) -> FileMeta:
        return self.write_bytes(
            rel_path,
            text.encode(encoding),
            expect_mtime=expect_mtime,
            expect_oid=expect_oid,
            mime_type=mime_type,
        )

    def write_bytes(
        self,
        rel_path: str,
        data: bytes,
        *,
        expect_mtime: datetime | None = None,
        expect_oid: str | None = None,
        mime_type: str = "application/octet-stream",
    ) -> FileMeta:
        rel = _norm_rel(rel_path)
        if not rel:
            raise ValueError("rel_path cannot be empty")
        path = self._abspath(rel)

        if self.dry_run:
            log.info("git_io: would-write %s (%d bytes)", rel, len(data))
            # CAS still validated against current tree when file exists
            if path.exists():
                self._check_cas(rel, path, expect_oid=expect_oid, expect_mtime=expect_mtime)
            elif expect_oid is not None or expect_mtime is not None:
                raise DriveConflictError(
                    f"CAS expected existing file at {rel!r}, but file does not exist"
                )
            return self._fake_meta(rel, data, mime_type=mime_type)

        if not self._mutate_allowed():
            return self._fake_meta(rel, data, mime_type=mime_type)

        if path.exists():
            self._check_cas(rel, path, expect_oid=expect_oid, expect_mtime=expect_mtime)
        elif expect_oid is not None or expect_mtime is not None:
            raise DriveConflictError(
                f"CAS expected existing file at {rel!r}, but file does not exist"
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self._meta_for_path(rel)

    def write_json(
        self,
        rel_path: str,
        obj: Any,
        *,
        expect_mtime: datetime | None = None,
        expect_oid: str | None = None,
        indent: int | None = 2,
    ) -> FileMeta:
        text = json.dumps(obj, ensure_ascii=False, indent=indent)
        return self.write_text(
            rel_path,
            text,
            expect_mtime=expect_mtime,
            expect_oid=expect_oid,
            mime_type="application/json",
        )

    def mkdir_p(self, rel_path: str) -> str:
        rel = _norm_rel(rel_path)
        if not rel:
            return str(self.root)
        if self.dry_run:
            log.info("git_io: would-mkdir %s", rel)
            return str(self._abspath(rel))
        if not self._mutate_allowed():
            return str(self._abspath(rel))
        path = self._abspath(rel)
        if path.exists() and not path.is_dir():
            raise DriveVaultError(f"mkdir_p: {rel!r} exists and is not a folder")
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    mkdir = mkdir_p

    def move(self, src_rel: str, dst_rel: str) -> FileMeta:
        src_n = _norm_rel(src_rel)
        dst_n = _norm_rel(dst_rel)
        if not dst_n:
            raise ValueError("dst_rel cannot be empty")
        src = self._abspath(src_n)
        dst = self._abspath(dst_n)
        if not src.exists():
            raise DriveNotFoundError(f"Path not found: {src_n!r}")
        if self.dry_run:
            log.info("git_io: would-move %s -> %s", src_n, dst_n)
            return self._meta_for_path(src_n)
        if not self._mutate_allowed():
            return self._meta_for_path(src_n)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise DriveVaultError(f"move: destination exists: {dst_n!r}")
        shutil.move(str(src), str(dst))
        return self._meta_for_path(dst_n)

    def delete(self, rel_path: str, *, permanent: bool = False) -> None:
        _ = permanent  # git has no trash; always remove from working tree
        rel = _norm_rel(rel_path)
        path = self._abspath(rel)
        if not path.exists():
            raise DriveNotFoundError(f"Path not found: {rel!r}")
        if self.dry_run:
            log.info("git_io: would-delete %s", rel)
            return
        if not self._mutate_allowed():
            return
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    # ------------------------------------------------------------------ commit / push

    def commit_if_dirty(self, message: str | None = None) -> bool:
        """Stage all changes and commit only if there is a diff. Returns True if committed."""
        if self.dry_run or self.skipped:
            return False
        self._git(["add", "-A"], check=True)
        diff = self._git(["diff", "--cached", "--quiet"], check=False)
        if diff.returncode == 0:
            return False
        msg = message or f"hub: vault update {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        self._git(["commit", "-m", msg], check=True)
        return True

    def _push_ff_only(self) -> None:
        if self.dry_run or not self.push_enabled:
            return
        proc = self._git(
            ["push", "--ff-only", "origin", self.branch],
            check=False,
        )
        if proc.returncode == 0:
            return
        log.error(
            "git_io: push --ff-only rejected (rc=%s); resetting hard to @{upstream}",
            proc.returncode,
        )
        # B6: reset --hard @{upstream} ONLY after failed ff-only push
        self._git(["reset", "--hard", "@{upstream}"], check=False)
