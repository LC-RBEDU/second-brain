"""Git working-copy vault I/O (GitVault) for second-brain-hub cron jobs.

Path API mirrors DriveVault. CAS uses git blob SHA (`expect_oid`); session
lifecycle: flock → optional fetch → optional dirty-skip → ops → optional
commit_if_dirty → optional push. Read sessions turn the optional steps off.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping

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


class VaultSessionSkipped(DriveVaultError):
    """Session skipped (dirty WT / flock) — mutate refused (no silent success)."""

    def __init__(self, message: str = "", *, skip_reason: str | None = None) -> None:
        super().__init__(message or "vault session skipped (dirty WT or flock)")
        self.skip_reason = skip_reason


class GitPushError(DriveVaultError):
    """ff-only push failed (optionally after reset to @{upstream})."""

    def __init__(self, message: str = "", *, error_reason: str = "vault_push_reset_ok") -> None:
        super().__init__(message or "git push ff-only failed")
        self.error_reason = error_reason


class GitEnqueueError(DriveVaultError):
    """Durable push-queue enqueue failed after local commit (Keep tip)."""

    def __init__(
        self,
        message: str = "",
        *,
        error_reason: str = "vault_push_enqueue_failed",
    ) -> None:
        super().__init__(message or "push queue enqueue failed")
        self.error_reason = error_reason


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


_OCTAL_ESCAPE_RE = re.compile(r"\\[0-7]{3}")
_CHANGED_PREFIXES = ("02-PROJEKTY/", "07-ARCHIV/tasks-done/")


def git_blob_oid(data: bytes, object_format: str) -> str:
    """Git blob id of ``data``. Same bytes as ``git hash-object``."""
    payload = f"blob {len(data)}\0".encode("ascii") + data
    if object_format == "sha256":
        return hashlib.sha256(payload).hexdigest()
    return hashlib.sha1(payload).hexdigest()


def _parse_log_name_only_z(stdout: str) -> set[str]:
    """Paths from ``git log -z --name-only``.

    ``-z`` separates commits, not paths. A commit chunk is split on LF only
    (not ``splitlines`` — U+2028 stays inside a name). One trailing CR is a
    CRLF. Quoted or octal-escaped lines are dropped. The raw chunk is never
    passed to ``_norm_rel``.
    """
    found: set[str] = set()
    for chunk in stdout.split("\0"):
        if not chunk:
            continue
        for line in chunk.split("\n"):
            if line.endswith("\r"):
                line = line[:-1]
            if not line:
                continue
            if '"' in line or _OCTAL_ESCAPE_RE.search(line):
                continue
            try:
                rel = _norm_rel(line)
            except ValueError:
                continue
            if rel.startswith(_CHANGED_PREFIXES):
                found.add(rel)
    return found


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
        strict_push: bool = False,
        discard_dirty_on_error: bool = False,
        fetch_on_begin: bool = True,
        check_dirty_on_begin: bool = True,
        commit_on_end: bool = True,
        push_on_end: bool | None = None,
        on_push_fail: Literal["reset", "keep_tip"] = "keep_tip",
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
        self.strict_push = strict_push
        self.discard_dirty_on_error = discard_dirty_on_error
        self.fetch_on_begin = fetch_on_begin
        self.check_dirty_on_begin = check_dirty_on_begin
        self.commit_on_end = commit_on_end
        # A25: push_on_end ≠ push_enabled. None → sync push when push_enabled.
        self.push_on_end = True if push_on_end is None else bool(push_on_end)
        self.on_push_fail: Literal["reset", "keep_tip"] = (
            on_push_fail if on_push_fail in ("reset", "keep_tip") else "keep_tip"
        )

        self._session_active = False
        self.skipped = False
        self.skip_reason: str | None = None
        self._lock_fh = None
        self._git_cmds: list[list[str]] = []  # test spy
        self._object_format_name: str | None = None
        self.last_push_job_id: str | None = None

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
        self.skip_reason = None
        self._session_active = True
        if not self._acquire_lock():
            log.warning(
                "git_io: flock busy on %s within %.1fs — skipping session",
                self._lock_path(),
                self.flock_timeout,
            )
            self.skipped = True
            self.skip_reason = "vault_flock_busy"
            return
        if self.fetch_on_begin:
            try:
                self._git(["fetch", "origin"], check=False)
            except Exception as exc:  # noqa: BLE001
                log.warning("git_io: fetch failed: %s", exc)
        if self.check_dirty_on_begin and self._is_dirty():
            log.warning(
                "git_io: working tree dirty at session start under %s — "
                "skip+log only (no reset)",
                self.root,
            )
            self.skipped = True
            self.skip_reason = "vault_dirty_start"

    def end_session(self, *, exc_type=None) -> None:
        if not self._session_active:
            return
        try:
            if self.skipped or self.dry_run or exc_type is not None or not self.commit_on_end:
                return
            committed = self.commit_if_dirty()
            if not (committed and self.push_enabled):
                return
            if self.push_on_end:
                self._push_ff_only()
            else:
                # A26: enqueue while flock still held (before unlock in finally).
                self._enqueue_push_job(source="end_session")
        finally:
            if (
                self.discard_dirty_on_error
                and exc_type is not None
                and not self.skipped
                and self._lock_fh is not None
            ):
                try:
                    self._git(["reset", "--hard", "HEAD"], check=False)
                    # Untracked files survive reset --hard and poison the next mutate.
                    self._git(["clean", "-fd"], check=False)
                except Exception as exc:  # noqa: BLE001
                    log.error("git_io: discard_dirty_on_error reset failed: %s", exc)
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

    def _object_format(self) -> str:
        """``sha1`` or ``sha256``, once per instance. Default sha1."""
        if self._object_format_name:
            return self._object_format_name
        fmt = "sha1"
        proc = self._git(["rev-parse", "--show-object-format"], check=False)
        if proc.returncode == 0:
            raw = (proc.stdout or "").strip().lower()
            if raw in {"sha1", "sha256"}:
                fmt = raw
        self._object_format_name = fmt
        return fmt

    def _blob_oid_for_path(self, path: Path) -> str | None:
        if not path.is_file():
            return None
        return git_blob_oid(path.read_bytes(), self._object_format())

    def _blob_oid_for_bytes(self, data: bytes) -> str:
        return git_blob_oid(data, self._object_format())

    def head_sha(self) -> str | None:
        proc = self._git(["rev-parse", "HEAD"], check=False)
        if proc.returncode != 0:
            return None
        sha = (proc.stdout or "").strip()
        return sha or None

    def changed_paths_since(self, since_iso: str) -> set[str]:
        """Vault paths committed after ``since_iso`` under projects and archive.

        Goes through ``_git`` so the argv lands in ``_git_cmds``. ``-z`` splits
        commits; path lines are parsed by ``_parse_log_name_only_z``.
        """
        proc = self._git(
            [
                "-c",
                "core.quotepath=false",
                "log",
                "-z",
                f"--since={since_iso}",
                "--name-only",
                "--pretty=format:",
                "--",
                "02-PROJEKTY",
                "07-ARCHIV/tasks-done",
            ],
            check=True,
        )
        return _parse_log_name_only_z(proc.stdout or "")

    def _meta_for_path(self, rel_path: str, *, compute_oid: bool = True) -> FileMeta:
        rel = _norm_rel(rel_path)
        path = self._abspath(rel)
        if not path.exists():
            raise DriveNotFoundError(f"Path not found: {rel!r}")
        is_dir = path.is_dir()
        parent_rel = ""
        if rel:
            segs = _split_rel(rel)
            parent_rel = "/".join(segs[:-1])
        # list_dir: skip hash-object (P10); CAS paths pass compute_oid=True
        oid = None if is_dir or not compute_oid else self._blob_oid_for_path(path)
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

    def _require_mutate(self) -> None:
        if self.skipped:
            reason = self.skip_reason or "vault_dirty_start"
            raise VaultSessionSkipped(
                f"git vault session skipped ({reason}) — refusing mutate",
                skip_reason=reason,
            )

    def is_tip_ahead(self) -> bool:
        """True when HEAD has commits not in @{upstream} (or compare fails)."""
        proc = self._git(
            ["rev-list", "--count", "@{upstream}..HEAD"],
            check=False,
        )
        if proc.returncode != 0:
            return True
        try:
            return int((proc.stdout or "0").strip() or "0") > 0
        except ValueError:
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
                    f"{rel!r} oid mismatch: current={current!r} expect={expect_oid!r}",
                    oid=current,
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

    def is_tracked(self, rel_path: str) -> bool:
        rel = _norm_rel(rel_path)
        if not rel:
            return False
        result = self._git(["ls-files", "--error-unmatch", "--", rel], check=False)
        return result.returncode == 0

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
                        results.append(self._meta_for_path(child_rel, compute_oid=False))
                else:
                    if _matches_pattern(entry.name, needle):
                        results.append(self._meta_for_path(child_rel, compute_oid=False))

        walk(base, base_rel)
        results.sort(key=lambda m: m.rel_path)
        return results

    def read_text(self, rel_path: str, *, encoding: str = "utf-8") -> tuple[str, FileMeta]:
        rel = _norm_rel(rel_path)
        path = self._abspath(rel)
        if not path.exists():
            raise DriveNotFoundError(f"Path not found: {rel!r}")
        if path.is_dir():
            raise DriveVaultError(f"Cannot read folder as text: {rel_path!r}")
        data = path.read_bytes()
        parent_rel = ""
        if rel:
            parent_rel = "/".join(_split_rel(rel)[:-1])
        oid = self._blob_oid_for_bytes(data)
        meta = FileMeta(
            id=rel or oid or "",
            name=path.name if rel else self.root.name,
            mime_type=_guess_mime(path, is_dir=False),
            modified_time=_utc_mtime(path),
            size=len(data),
            parent_id=parent_rel or None,
            rel_path=rel,
            oid=oid,
        )
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

        self._require_mutate()

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
        self._require_mutate()
        path = self._abspath(rel)
        if path.exists() and not path.is_dir():
            raise DriveVaultError(f"mkdir_p: {rel!r} exists and is not a folder")
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    mkdir = mkdir_p

    def move(
        self,
        src_rel: str,
        dst_rel: str,
        *,
        expect_oid: str | None = None,
        expect_mtime: datetime | None = None,
    ) -> FileMeta:
        src_n = _norm_rel(src_rel)
        dst_n = _norm_rel(dst_rel)
        if not dst_n:
            raise ValueError("dst_rel cannot be empty")
        src = self._abspath(src_n)
        dst = self._abspath(dst_n)
        if not src.exists():
            raise DriveNotFoundError(f"Path not found: {src_n!r}")
        self._check_cas(src_n, src, expect_oid=expect_oid, expect_mtime=expect_mtime)
        if self.dry_run:
            log.info("git_io: would-move %s -> %s", src_n, dst_n)
            return self._meta_for_path(src_n)
        self._require_mutate()
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise DriveVaultError(f"move: destination exists: {dst_n!r}")
        shutil.move(str(src), str(dst))
        return self._meta_for_path(dst_n)

    def delete(
        self,
        rel_path: str,
        *,
        permanent: bool = False,
        expect_oid: str | None = None,
        expect_mtime: datetime | None = None,
    ) -> None:
        _ = permanent  # git has no trash; always remove from working tree
        rel = _norm_rel(rel_path)
        path = self._abspath(rel)
        if not path.exists():
            raise DriveNotFoundError(f"Path not found: {rel!r}")
        self._check_cas(rel, path, expect_oid=expect_oid, expect_mtime=expect_mtime)
        if self.dry_run:
            log.info("git_io: would-delete %s", rel)
            return
        self._require_mutate()
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
        msg = (
            message
            or getattr(self, "commit_message", None)
            or f"hub: vault update {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )
        self._git(["commit", "-m", msg], check=True)
        return True

    def _enqueue_push_job(self, *, source: str = "brain", attempts: int = 0) -> str:
        """Durable enqueue under flock. Raises GitEnqueueError on I/O failure."""
        from push_queue import enqueue

        try:
            job_id = enqueue(self.root, attempts=attempts, source=source)
        except OSError as exc:
            raise GitEnqueueError(
                f"push queue enqueue failed: {exc}",
                error_reason="vault_push_enqueue_failed",
            ) from exc
        self.last_push_job_id = job_id
        log.info("git_io: enqueued push job %s (source=%s)", job_id, source)
        return job_id

    def push_tip_ff_only(self) -> None:
        """Push current tip ff-only (worker path). No commit gate (A41 / R23)."""
        if self.dry_run or not self.push_enabled:
            return
        self._push_ff_only()

    def _push_ff_only(self) -> None:
        if self.dry_run or not self.push_enabled:
            return
        # Debian bookworm git (2.39.x) has no `git push --ff-only` flag;
        # `push.ff=only` rejects non-ff updates equivalently (B6).
        proc = self._git(
            ["-c", "push.ff=only", "push", "origin", self.branch],
            check=False,
        )
        if proc.returncode == 0:
            return
        if self.on_push_fail == "keep_tip":
            log.error(
                "git_io: push ff-only rejected (rc=%s); Keep tip "
                "(no reset --hard @{upstream})",
                proc.returncode,
            )
            if self.strict_push:
                raise GitPushError(
                    "git push ff-only failed; tip kept ahead of @{upstream}",
                    error_reason="vault_push_keep_tip",
                )
            return
        log.error(
            "git_io: push ff-only rejected (rc=%s); resetting hard to @{upstream}",
            proc.returncode,
        )
        # B6: reset --hard @{upstream} ONLY after failed ff-only push (reset mode)
        reset = self._git(["reset", "--hard", "@{upstream}"], check=False)
        if not self.strict_push:
            return
        if reset.returncode == 0 and not self._is_dirty() and not self.is_tip_ahead():
            raise GitPushError(
                "git push ff-only failed; reset to @{upstream} OK",
                error_reason="vault_push_reset_ok",
            )
        raise GitPushError(
            "git push ff-only failed; reset to @{upstream} failed or tip still ahead",
            error_reason="vault_push_reset_failed",
        )
