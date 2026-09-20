"""Google Drive vault I/O for the second-brain-hub cron jobs.

Supports two authentication modes (auto-detected via env in
`credentials_from_env`):

* **OAuth user delegation** (preferred): full read+write to the user's own
  Drive without storage-quota issues. Requires a one-time consent flow
  via `scripts/oauth_setup.py`. Env: `GOOGLE_DRIVE_OAUTH_JSON`.
* **Service Account** (fallback): works for read-only access on shared
  folders, but cannot create new files in a user-owned Drive due to
  quota constraints. Acceptable for limited use cases. Env:
  `GOOGLE_DRIVE_SA_JSON` (+ optional `GOOGLE_DRIVE_IMPERSONATE`).

DriveVault wraps the Drive API v3 with a path-based interface (mirroring
the layout of the OBSIDIAN vault). It provides:

* read / write text and JSON files
* directory listing with optional pattern filter and recursion
* mkdir -p semantics
* atomic move via addParents / removeParents
* trash / permanent delete
* mtime-based compare-and-swap (CAS) on write_text / write_json to detect
  conflicting writes (e.g. user editing the same file in Obsidian while
  the cron job runs)
* exponential backoff retry on transient HTTP errors

Designed to replace `pathlib.Path` usage in the cron scripts so that the
container can run completely stateless against Google Drive as the single
source of truth.

Typical usage:

    info = parse_service_account_json(os.environ["GOOGLE_DRIVE_SA_JSON"])
    vault = DriveVault(os.environ["VAULT_DRIVE_ID"], info)

    text, meta = vault.read_text("02-PROJEKTY/Finance.md")
    new_text = transform(text)
    try:
        vault.write_text(
            "02-PROJEKTY/Finance.md",
            new_text,
            expect_mtime=meta.modified_time,
        )
    except DriveConflictError:
        logger.warning("Finance.md changed externally, will retry next run")
"""
from __future__ import annotations

import fnmatch
import io
import json
import logging
import os
import random
import socket
import ssl
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, TypeVar

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
FOLDER_MIME = "application/vnd.google-apps.folder"


def credentials_from_oauth(info: dict):
    """Build google.oauth2.credentials.Credentials from a merged OAuth JSON.

    `info` must contain: client_id, client_secret, refresh_token, token_uri.
    Scope is fixed to Drive full read+write.
    """
    required = ("client_id", "client_secret", "refresh_token", "token_uri")
    missing = [k for k in required if not info.get(k)]
    if missing:
        raise ValueError(f"OAuth credentials missing keys: {missing}")
    return OAuthCredentials(
        token=None,  # acquired on first request via refresh_token
        refresh_token=info["refresh_token"],
        token_uri=info["token_uri"],
        client_id=info["client_id"],
        client_secret=info["client_secret"],
        scopes=info.get("scopes") or [DRIVE_SCOPE],
    )


def credentials_from_service_account(info: dict, *, subject: str | None = None):
    """Build SA credentials, optionally impersonating a Workspace user via DWD."""
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=[DRIVE_SCOPE]
    )
    if subject:
        creds = creds.with_subject(subject)
    return creds


def credentials_from_env(env: dict | None = None):
    """Auto-detect credentials from env, preferring OAuth over SA.

    Env variables (checked in order):
      GOOGLE_DRIVE_OAUTH_JSON   — merged OAuth JSON (preferred when present)
      GOOGLE_DRIVE_SA_JSON      — SA JSON; optional GOOGLE_DRIVE_IMPERSONATE for DWD
      GOOGLE_SERVICE_ACCOUNT_JSON  — fallback SA JSON
    """
    env = env if env is not None else os.environ
    oauth_raw = (env.get("GOOGLE_DRIVE_OAUTH_JSON") or "").strip()
    if oauth_raw:
        return credentials_from_oauth(json.loads(oauth_raw)), "oauth"
    sa_raw = (env.get("GOOGLE_DRIVE_SA_JSON") or env.get("GOOGLE_SERVICE_ACCOUNT_JSON") or "").strip()
    if sa_raw:
        from google_sa_json import parse_service_account_json  # local import to avoid circular
        info = parse_service_account_json(sa_raw)
        subject = (env.get("GOOGLE_DRIVE_IMPERSONATE") or "").strip() or None
        return credentials_from_service_account(info, subject=subject), "sa"
    raise RuntimeError(
        "No Drive credentials in env. Set GOOGLE_DRIVE_OAUTH_JSON (preferred) "
        "or GOOGLE_DRIVE_SA_JSON (+ optional GOOGLE_DRIVE_IMPERSONATE)."
    )

T = TypeVar("T")

log = logging.getLogger("drive_io")


class DriveVaultError(Exception):
    """Base error for DriveVault operations."""


class DriveNotFoundError(DriveVaultError):
    """Path does not resolve to any Drive file."""


class DriveConflictError(DriveVaultError):
    """CAS mismatch: file modified externally since `expect_mtime`."""


@dataclass(frozen=True)
class FileMeta:
    """Stable metadata view of a Drive file as exposed to callers."""

    id: str
    name: str
    mime_type: str
    modified_time: datetime  # tz-aware UTC
    size: int | None  # None for native Google docs / folders
    parent_id: str | None  # one parent (vault layout is single-parent tree)
    rel_path: str  # path inside vault, e.g. "02-PROJEKTY/Finance.md"

    @property
    def is_folder(self) -> bool:
        return self.mime_type == FOLDER_MIME


def _parse_iso8601(raw: str) -> datetime:
    """Drive returns RFC 3339 like '2026-05-21T11:51:54.209Z'."""
    if not raw:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    # `fromisoformat` in py3.11+ accepts trailing 'Z'; be defensive for older.
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _norm_rel(rel: str) -> str:
    """Normalize a vault-relative path: strip leading/trailing slashes."""
    if rel is None:
        raise ValueError("rel_path is required")
    rel = rel.replace("\\", "/").strip("/")
    if "//" in rel:
        raise ValueError(f"Empty path segment in: {rel!r}")
    return rel


def _split_rel(rel: str) -> list[str]:
    rel = _norm_rel(rel)
    if not rel:
        return []
    return rel.split("/")


def _glob_to_substr(pattern: str | None) -> str | None:
    """Normalize a client-side filename filter to lowercase.

    Drive query language doesn't support globbing, so the directory is fetched
    and filtered locally by `_matches_pattern`.
    """
    if not pattern:
        return None
    return pattern.strip().lower() or None


def _matches_pattern(name: str, needle: str | None) -> bool:
    """Match a filename against a glob, or a substring when there is no wildcard.

    Patterns with a wildcard go through fnmatch, so an interior '*' works:
    'LL-*.md' used to be reduced to the literal substring 'll-*.md', which
    matches no real filename and made whole directories look empty without
    raising anything. Wildcard-free patterns keep the substring behaviour that
    callers pass prefixes like 'waiting-' for.
    """
    if needle is None:
        return True
    low = name.lower()
    if any(ch in needle for ch in "*?["):
        return fnmatch.fnmatchcase(low, needle)
    return needle in low


_RETRYABLE_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, HttpError):
        status = getattr(exc.resp, "status", None)
        try:
            status_int = int(status) if status is not None else None
        except (TypeError, ValueError):
            status_int = None
        return status_int in _RETRYABLE_HTTP_STATUSES
    if isinstance(exc, (socket.timeout, socket.gaierror, ssl.SSLError, ConnectionError, TimeoutError)):
        return True
    return False


def _retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
    rng: Callable[[], float] = random.random,
) -> T:
    """Run `fn`, retrying on transient HTTP / network errors with backoff."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — we re-raise non-retryable
            if attempt >= max_attempts or not _is_retryable(exc):
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = delay * 0.2 * rng()
            log.warning(
                "drive_io: retry %d/%d after %.1fs due to %s: %s",
                attempt,
                max_attempts,
                delay + jitter,
                type(exc).__name__,
                exc,
            )
            sleep(delay + jitter)


class _LRU(OrderedDict):
    def __init__(self, maxsize: int = 512):
        super().__init__()
        self._maxsize = maxsize

    def __setitem__(self, key, value):  # type: ignore[override]
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self._maxsize:
            self.popitem(last=False)

    def __getitem__(self, key):  # type: ignore[override]
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value


_META_FIELDS = "id,name,mimeType,modifiedTime,size,parents"
_LIST_FIELDS = f"nextPageToken, files({_META_FIELDS})"


class DriveVault:
    """Path-based facade over Google Drive API v3 for a single root folder."""

    def __init__(
        self,
        root_folder_id: str,
        sa_info: dict | None = None,
        *,
        credentials=None,
        service=None,
        cache_size: int = 512,
    ) -> None:
        """Construct a vault facade.

        Args:
          root_folder_id: Drive folder ID at the vault root.
          sa_info: Service-Account JSON dict (legacy convenience). Mutually
                   exclusive with `credentials`.
          credentials: Pre-built google-auth credentials object (preferred;
                       use `credentials_from_env()` or
                       `credentials_from_oauth()` to build).
          service: Pre-built Drive service (for tests).
          cache_size: LRU path-to-meta cache size.
        """
        if not root_folder_id:
            raise ValueError("root_folder_id is required")
        self._root_id = root_folder_id
        if service is not None:
            self._svc = service
        else:
            if credentials is None:
                if sa_info is None:
                    raise ValueError(
                        "Provide either `credentials` or `sa_info` (or `service`)"
                    )
                credentials = service_account.Credentials.from_service_account_info(
                    sa_info, scopes=[DRIVE_SCOPE]
                )
            self._svc = build("drive", "v3", credentials=credentials, cache_discovery=False)
        self._meta_cache: _LRU = _LRU(cache_size)

    # ------------------------------------------------------------------ helpers

    def _meta_from_api(self, payload: dict, rel_path: str) -> FileMeta:
        parents = payload.get("parents") or []
        parent_id = parents[0] if parents else None
        size_raw = payload.get("size")
        size = int(size_raw) if size_raw is not None else None
        return FileMeta(
            id=payload["id"],
            name=payload["name"],
            mime_type=payload.get("mimeType", ""),
            modified_time=_parse_iso8601(payload.get("modifiedTime", "")),
            size=size,
            parent_id=parent_id,
            rel_path=_norm_rel(rel_path),
        )

    def _root_meta(self) -> FileMeta:
        cached = self._meta_cache.get("")
        if cached:
            return cached
        payload = _retry(
            lambda: self._svc.files()
            .get(fileId=self._root_id, fields=_META_FIELDS, supportsAllDrives=True)
            .execute()
        )
        meta = self._meta_from_api(payload, "")
        self._meta_cache[""] = meta
        return meta

    def _lookup_child(self, parent_id: str, name: str) -> dict | None:
        # Drive query: escape single quotes
        esc = name.replace("\\", "\\\\").replace("'", "\\'")
        q = f"'{parent_id}' in parents and name = '{esc}' and trashed = false"

        def call():
            return (
                self._svc.files()
                .list(
                    q=q,
                    fields=_LIST_FIELDS,
                    pageSize=2,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )

        resp = _retry(call)
        files = resp.get("files") or []
        if not files:
            return None
        # Drive allows duplicate names within a folder; prefer non-trashed first
        return files[0]

    def _resolve(self, rel_path: str) -> FileMeta:
        rel = _norm_rel(rel_path)
        if not rel:
            return self._root_meta()
        if rel in self._meta_cache:
            return self._meta_cache[rel]
        segments = _split_rel(rel)
        # Walk from root, caching every intermediate prefix.
        parent_id = self._root_id
        accumulated: list[str] = []
        last_meta: FileMeta | None = None
        for seg in segments:
            accumulated.append(seg)
            prefix = "/".join(accumulated)
            if prefix in self._meta_cache:
                last_meta = self._meta_cache[prefix]
                parent_id = last_meta.id
                continue
            child = self._lookup_child(parent_id, seg)
            if child is None:
                raise DriveNotFoundError(f"Path not found: {prefix!r}")
            meta = self._meta_from_api(child, prefix)
            self._meta_cache[prefix] = meta
            parent_id = meta.id
            last_meta = meta
        assert last_meta is not None
        return last_meta

    def _list_all(self, query: str) -> list[dict]:
        out: list[dict] = []
        page = None
        while True:
            def call(page_token=page):
                return (
                    self._svc.files()
                    .list(
                        q=query,
                        fields=_LIST_FIELDS,
                        pageSize=1000,
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True,
                        pageToken=page_token or "",
                    )
                    .execute()
                )

            resp = _retry(call)
            out.extend(resp.get("files") or [])
            page = resp.get("nextPageToken")
            if not page:
                break
        return out

    # ------------------------------------------------------------------ public

    @property
    def root_id(self) -> str:
        return self._root_id

    def exists(self, rel_path: str) -> bool:
        try:
            self._resolve(rel_path)
            return True
        except DriveNotFoundError:
            return False

    def stat(self, rel_path: str) -> FileMeta:
        return self._resolve(rel_path)

    def list_dir(
        self,
        rel_path: str,
        *,
        pattern: str | None = None,
        recursive: bool = False,
        include_folders: bool = False,
    ) -> list[FileMeta]:
        folder = self._resolve(rel_path) if _norm_rel(rel_path) else self._root_meta()
        if folder.mime_type != FOLDER_MIME:
            raise DriveVaultError(f"Not a folder: {rel_path!r}")
        needle = _glob_to_substr(pattern)
        base_rel = _norm_rel(rel_path)
        results: list[FileMeta] = []
        stack: list[tuple[str, str]] = [(folder.id, base_rel)]
        while stack:
            cur_id, cur_rel = stack.pop()
            children = self._list_all(f"'{cur_id}' in parents and trashed = false")
            for child in children:
                child_rel = f"{cur_rel}/{child['name']}" if cur_rel else child["name"]
                meta = self._meta_from_api(child, child_rel)
                self._meta_cache[child_rel] = meta
                if meta.is_folder:
                    if recursive:
                        stack.append((meta.id, child_rel))
                    if include_folders and _matches_pattern(meta.name, needle):
                        results.append(meta)
                else:
                    if _matches_pattern(meta.name, needle):
                        results.append(meta)
        results.sort(key=lambda m: m.rel_path)
        return results

    def read_text(self, rel_path: str, *, encoding: str = "utf-8") -> tuple[str, FileMeta]:
        meta = self._resolve(rel_path)
        if meta.is_folder:
            raise DriveVaultError(f"Cannot read folder as text: {rel_path!r}")

        def call():
            request = self._svc.files().get_media(fileId=meta.id, supportsAllDrives=True)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return buf.getvalue()

        data = _retry(call)
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
        mime_type: str = "text/markdown",
        encoding: str = "utf-8",
    ) -> FileMeta:
        return self.write_bytes(
            rel_path,
            text.encode(encoding),
            expect_mtime=expect_mtime,
            mime_type=mime_type,
        )

    def write_bytes(
        self,
        rel_path: str,
        data: bytes,
        *,
        expect_mtime: datetime | None = None,
        mime_type: str = "application/octet-stream",
    ) -> FileMeta:
        rel = _norm_rel(rel_path)
        if not rel:
            raise ValueError("rel_path cannot be empty")
        segments = _split_rel(rel)
        name = segments[-1]
        parent_rel = "/".join(segments[:-1])
        parent_id = self.mkdir_p(parent_rel) if parent_rel else self._root_id

        existing: FileMeta | None
        try:
            existing = self._resolve(rel)
        except DriveNotFoundError:
            existing = None

        if expect_mtime is not None:
            if existing is None:
                raise DriveConflictError(
                    f"CAS expected existing file at {rel!r}, but file does not exist"
                )
            fresh = self._meta_from_api(
                _retry(
                    lambda: self._svc.files()
                    .get(
                        fileId=existing.id,
                        fields=_META_FIELDS,
                        supportsAllDrives=True,
                    )
                    .execute()
                ),
                rel,
            )
            if fresh.modified_time > expect_mtime:
                raise DriveConflictError(
                    f"{rel!r} modified externally at {fresh.modified_time.isoformat()}"
                    f" (expected <= {expect_mtime.isoformat()})"
                )
            existing = fresh
            self._meta_cache[rel] = fresh

        body = io.BytesIO(data)
        media = MediaIoBaseUpload(body, mimetype=mime_type, resumable=False)

        if existing is None:
            metadata = {"name": name, "parents": [parent_id], "mimeType": mime_type}

            def create():
                return (
                    self._svc.files()
                    .create(
                        body=metadata,
                        media_body=media,
                        fields=_META_FIELDS,
                        supportsAllDrives=True,
                    )
                    .execute()
                )

            payload = _retry(create)
        else:
            def update():
                return (
                    self._svc.files()
                    .update(
                        fileId=existing.id,
                        media_body=media,
                        fields=_META_FIELDS,
                        supportsAllDrives=True,
                    )
                    .execute()
                )

            payload = _retry(update)

        meta = self._meta_from_api(payload, rel)
        self._meta_cache[rel] = meta
        return meta

    def write_json(
        self,
        rel_path: str,
        obj: Any,
        *,
        expect_mtime: datetime | None = None,
        indent: int | None = 2,
    ) -> FileMeta:
        text = json.dumps(obj, ensure_ascii=False, indent=indent)
        return self.write_text(
            rel_path,
            text,
            expect_mtime=expect_mtime,
            mime_type="application/json",
        )

    def mkdir_p(self, rel_path: str) -> str:
        rel = _norm_rel(rel_path)
        if not rel:
            return self._root_id
        segments = _split_rel(rel)
        parent_id = self._root_id
        accumulated: list[str] = []
        for seg in segments:
            accumulated.append(seg)
            prefix = "/".join(accumulated)
            if prefix in self._meta_cache:
                meta = self._meta_cache[prefix]
                if not meta.is_folder:
                    raise DriveVaultError(
                        f"mkdir_p: {prefix!r} exists and is not a folder"
                    )
                parent_id = meta.id
                continue
            child = self._lookup_child(parent_id, seg)
            if child is None:
                metadata = {
                    "name": seg,
                    "mimeType": FOLDER_MIME,
                    "parents": [parent_id],
                }

                def create():
                    return (
                        self._svc.files()
                        .create(
                            body=metadata,
                            fields=_META_FIELDS,
                            supportsAllDrives=True,
                        )
                        .execute()
                    )

                child = _retry(create)
            elif child.get("mimeType") != FOLDER_MIME:
                raise DriveVaultError(
                    f"mkdir_p: {prefix!r} exists and is not a folder"
                )
            meta = self._meta_from_api(child, prefix)
            self._meta_cache[prefix] = meta
            parent_id = meta.id
        return parent_id

    def move(self, src_rel: str, dst_rel: str) -> FileMeta:
        src = self._resolve(src_rel)
        dst_rel_n = _norm_rel(dst_rel)
        if not dst_rel_n:
            raise ValueError("dst_rel cannot be empty")
        segments = _split_rel(dst_rel_n)
        new_name = segments[-1]
        new_parent_rel = "/".join(segments[:-1])
        new_parent_id = (
            self.mkdir_p(new_parent_rel) if new_parent_rel else self._root_id
        )
        body: dict = {}
        if new_name != src.name:
            body["name"] = new_name
        remove_parents = src.parent_id or ""

        def update():
            return (
                self._svc.files()
                .update(
                    fileId=src.id,
                    body=body or None,
                    addParents=new_parent_id,
                    removeParents=remove_parents,
                    fields=_META_FIELDS,
                    supportsAllDrives=True,
                )
                .execute()
            )

        payload = _retry(update)
        # Invalidate old path
        self._meta_cache.pop(src.rel_path, None)
        meta = self._meta_from_api(payload, dst_rel_n)
        self._meta_cache[dst_rel_n] = meta
        return meta

    def delete(self, rel_path: str, *, permanent: bool = False) -> None:
        meta = self._resolve(rel_path)
        if permanent:
            def call():
                return (
                    self._svc.files()
                    .delete(fileId=meta.id, supportsAllDrives=True)
                    .execute()
                )
        else:
            def call():
                return (
                    self._svc.files()
                    .update(
                        fileId=meta.id,
                        body={"trashed": True},
                        fields="id",
                        supportsAllDrives=True,
                    )
                    .execute()
                )

        _retry(call)
        self._meta_cache.pop(meta.rel_path, None)

    # ------------------------------------------------------------------ debug

    def cache_keys(self) -> Iterable[str]:
        return tuple(self._meta_cache.keys())
