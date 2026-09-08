"""Unit tests for lib/drive_io.DriveVault.

Tests do not hit the real Google Drive API. Instead, they install a fake
implementation of `googleapiclient.discovery.build("drive", "v3", ...)` that
mimics the small slice of behaviour we exercise:

* files.get(fileId=, fields=)
* files.list(q=, fields=, pageSize=, pageToken=)
* files.create(body=, media_body=)
* files.update(fileId=, body=, media_body=, addParents=, removeParents=)
* files.delete(fileId=)
* files.get_media(fileId=)  with MediaIoBaseDownload

The fake stores everything in an in-memory tree. A small `FakeHttpError`
helper lets individual tests trigger retryable / non-retryable failures.
"""
from __future__ import annotations

import io
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

_LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(_LIB_DIR))

from googleapiclient.errors import HttpError  # noqa: E402

import drive_io  # noqa: E402
from drive_io import (  # noqa: E402
    DriveConflictError,
    DriveNotFoundError,
    DriveVault,
    DriveVaultError,
    FileMeta,
    FOLDER_MIME,
    _parse_iso8601,
)


# --------------------------------------------------------------------- helpers


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class _FakeResp:
    def __init__(self, status: int):
        self.status = status
        self.reason = "fake"

    def __getitem__(self, key):
        return {"status": str(self.status), "content-type": "application/json"}[key]


def make_http_error(status: int, msg: str = "fake error") -> HttpError:
    resp = _FakeResp(status)
    content = json.dumps({"error": {"code": status, "message": msg}}).encode()
    return HttpError(resp, content)


class FakeFile:
    """One node in the fake Drive tree (file or folder)."""

    _ids = iter(range(1000, 1_000_000))

    def __init__(
        self,
        name: str,
        mime_type: str,
        parents: list[str],
        *,
        body: bytes = b"",
        modified_time: datetime | None = None,
    ):
        self.id = f"f{next(FakeFile._ids)}"
        self.name = name
        self.mime_type = mime_type
        self.parents = list(parents)
        self.body = body
        self.modified_time = modified_time or datetime.now(timezone.utc)
        self.trashed = False

    def to_meta(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "mimeType": self.mime_type,
            "modifiedTime": _iso(self.modified_time),
            "parents": list(self.parents),
        }
        if self.mime_type != FOLDER_MIME:
            out["size"] = str(len(self.body))
        return out


class _FilesEndpoint:
    """Mimics the subset of svc.files() we use."""

    def __init__(self, drive: "FakeDrive"):
        self.drive = drive

    def get(self, fileId, fields=None, supportsAllDrives=False):
        return _Call(lambda: self.drive._get(fileId))

    def get_media(self, fileId, supportsAllDrives=False):
        # Returned object is passed to MediaIoBaseDownload; we expose a `.uri`
        # so the downloader can decide if it's done. MediaIoBaseDownload only
        # calls `request.http.request(request.uri)` — too low-level to mock.
        # Easier: return a sentinel that our patched downloader can read.
        return _MediaSentinel(self.drive, fileId)

    def list(
        self,
        q=None,
        fields=None,
        pageSize=None,
        pageToken=None,
        supportsAllDrives=False,
        includeItemsFromAllDrives=False,
    ):
        return _Call(lambda: self.drive._list(q, pageSize, pageToken))

    def create(
        self,
        body=None,
        media_body=None,
        fields=None,
        supportsAllDrives=False,
    ):
        return _Call(lambda: self.drive._create(body, media_body))

    def update(
        self,
        fileId=None,
        body=None,
        media_body=None,
        addParents=None,
        removeParents=None,
        fields=None,
        supportsAllDrives=False,
    ):
        return _Call(
            lambda: self.drive._update(
                fileId, body, media_body, addParents, removeParents
            )
        )

    def delete(self, fileId=None, supportsAllDrives=False):
        return _Call(lambda: self.drive._delete(fileId))


class _Call:
    def __init__(self, fn):
        self._fn = fn

    def execute(self):
        return self._fn()


class _MediaSentinel:
    def __init__(self, drive: "FakeDrive", file_id: str):
        self.drive = drive
        self.file_id = file_id


class FakeDrive:
    """In-memory Drive with a root folder + arbitrary children."""

    def __init__(self):
        self.files: dict[str, FakeFile] = {}
        root = FakeFile("ROOT", FOLDER_MIME, parents=[])
        root.id = "root_id"
        self.files[root.id] = root
        self.root_id = root.id
        self._fail_queue: list[Exception] = []

    # --------- public test helpers
    def add_folder(self, name: str, parent_id: str | None = None) -> FakeFile:
        parent = parent_id or self.root_id
        f = FakeFile(name, FOLDER_MIME, parents=[parent])
        self.files[f.id] = f
        return f

    def add_file(
        self,
        name: str,
        parent_id: str | None,
        body: str | bytes = b"",
        modified_time: datetime | None = None,
        mime_type: str = "text/markdown",
    ) -> FakeFile:
        parent = parent_id or self.root_id
        data = body.encode("utf-8") if isinstance(body, str) else body
        f = FakeFile(
            name, mime_type, parents=[parent], body=data, modified_time=modified_time
        )
        self.files[f.id] = f
        return f

    def queue_failure(self, exc: Exception, *, count: int = 1) -> None:
        self._fail_queue.extend([exc] * count)

    # --------- API fake
    def _maybe_fail(self):
        if self._fail_queue:
            raise self._fail_queue.pop(0)

    def _get(self, file_id):
        self._maybe_fail()
        f = self.files.get(file_id)
        if not f or f.trashed:
            raise make_http_error(404, "not found")
        return f.to_meta()

    def _list(self, q, page_size, page_token):
        self._maybe_fail()
        # Parse query: supports "'parent_id' in parents", "name = 'X'",
        # "trashed = false".
        import re as _re

        parent_match = _re.search(r"'([^']+)' in parents", q or "")
        parent_id = parent_match.group(1) if parent_match else None
        name_match = _re.search(r"name = '((?:[^'\\]|\\.)*)'", q or "")
        name = None
        if name_match:
            name = name_match.group(1).replace("\\'", "'").replace("\\\\", "\\")

        results = []
        for f in self.files.values():
            if f.trashed:
                continue
            if parent_id and parent_id not in f.parents:
                continue
            if name is not None and f.name != name:
                continue
            results.append(f)

        results.sort(key=lambda f: f.name.lower())

        # paginate
        size = int(page_size or 100)
        start = 0
        if page_token:
            start = int(page_token)
        chunk = results[start : start + size]
        out: dict[str, Any] = {"files": [r.to_meta() for r in chunk]}
        if start + size < len(results):
            out["nextPageToken"] = str(start + size)
        return out

    def _read_media_bytes(self, file_id: str) -> bytes:
        self._maybe_fail()
        f = self.files.get(file_id)
        if not f or f.trashed:
            raise make_http_error(404, "not found")
        return f.body

    def _create(self, body, media_body):
        self._maybe_fail()
        parents = body.get("parents") or [self.root_id]
        mime = body.get("mimeType") or "application/octet-stream"
        name = body["name"]
        data = b""
        if media_body is not None:
            data = _consume_upload(media_body)
        f = FakeFile(name, mime, parents=parents, body=data)
        self.files[f.id] = f
        return f.to_meta()

    def _update(self, file_id, body, media_body, add_parents, remove_parents):
        self._maybe_fail()
        f = self.files.get(file_id)
        if not f:
            raise make_http_error(404, "not found")
        if body:
            if "name" in body:
                f.name = body["name"]
            if body.get("trashed") is True:
                f.trashed = True
        if media_body is not None:
            f.body = _consume_upload(media_body)
        if remove_parents:
            for p in str(remove_parents).split(","):
                if p in f.parents:
                    f.parents.remove(p)
        if add_parents:
            for p in str(add_parents).split(","):
                if p not in f.parents:
                    f.parents.append(p)
        f.modified_time = datetime.now(timezone.utc)
        return f.to_meta()

    def _delete(self, file_id):
        self._maybe_fail()
        if file_id in self.files:
            del self.files[file_id]
        return {}


def _consume_upload(media_body) -> bytes:
    # MediaIoBaseUpload exposes _fd (BytesIO) — easiest to read.
    fd = getattr(media_body, "_fd", None)
    if fd is None:
        # Fallback: try .getbytes(0, size)
        size = media_body.size()
        return media_body.getbytes(0, size)
    fd.seek(0)
    return fd.read()


class FakeService:
    def __init__(self, drive: FakeDrive):
        self._drive = drive

    def files(self):
        return _FilesEndpoint(self._drive)


# Patch MediaIoBaseDownload to use our sentinel.
@pytest.fixture(autouse=True)
def _patch_downloader(monkeypatch):
    class _FakeDownloader:
        def __init__(self, buf: io.BytesIO, sentinel: _MediaSentinel):
            self._buf = buf
            self._sentinel = sentinel
            self._done = False

        def next_chunk(self):
            if self._done:
                return None, True
            data = self._sentinel.drive._read_media_bytes(self._sentinel.file_id)
            self._buf.write(data)
            self._done = True
            return None, True

    monkeypatch.setattr(drive_io, "MediaIoBaseDownload", _FakeDownloader)


@pytest.fixture
def fake_drive():
    return FakeDrive()


@pytest.fixture
def vault(fake_drive):
    svc = FakeService(fake_drive)
    return DriveVault(fake_drive.root_id, sa_info={}, service=svc)


# ----------------------------------------------------------------------- tests


def test_parse_iso8601_z_suffix():
    dt = _parse_iso8601("2026-05-21T11:51:54.209Z")
    assert dt.tzinfo is not None
    assert dt.year == 2026 and dt.month == 5 and dt.day == 21


def test_resolve_root(vault):
    meta = vault.stat("")
    assert meta.is_folder
    assert meta.rel_path == ""


def test_resolve_nested(fake_drive, vault):
    proj = fake_drive.add_folder("02-PROJEKTY")
    fake_drive.add_file("Finance.md", proj.id, body="hello")
    meta = vault.stat("02-PROJEKTY/Finance.md")
    assert meta.name == "Finance.md"
    assert meta.rel_path == "02-PROJEKTY/Finance.md"
    assert not meta.is_folder


def test_resolve_missing_raises(vault):
    with pytest.raises(DriveNotFoundError):
        vault.stat("nope/missing.md")


def test_exists(fake_drive, vault):
    fake_drive.add_folder("00-System")
    assert vault.exists("00-System") is True
    assert vault.exists("nope") is False


def test_read_text(fake_drive, vault):
    proj = fake_drive.add_folder("02-PROJEKTY")
    fake_drive.add_file("Finance.md", proj.id, body="# Téma\n\ncontent")
    text, meta = vault.read_text("02-PROJEKTY/Finance.md")
    assert text == "# Téma\n\ncontent"
    assert meta.name == "Finance.md"
    assert meta.size == len("# Téma\n\ncontent".encode())


def test_read_json(fake_drive, vault):
    sysd = fake_drive.add_folder("00-System")
    fake_drive.add_file("config.json", sysd.id, body=json.dumps({"a": 1}))
    obj, _meta = vault.read_json("00-System/config.json")
    assert obj == {"a": 1}


def test_list_dir_filter_md(fake_drive, vault):
    proj = fake_drive.add_folder("02-PROJEKTY")
    fake_drive.add_file("Finance.md", proj.id)
    fake_drive.add_file("Operations.md", proj.id)
    fake_drive.add_file("notes.txt", proj.id)
    md = vault.list_dir("02-PROJEKTY", pattern="*.md")
    assert [m.name for m in md] == ["Finance.md", "Operations.md"]


def test_list_dir_pagination(fake_drive, vault, monkeypatch):
    # Force tiny page size to trigger pagination.
    proj = fake_drive.add_folder("02-PROJEKTY")
    for i in range(5):
        fake_drive.add_file(f"f{i}.md", proj.id)
    original_list = drive_io.DriveVault._list_all

    def small_list(self, query):
        # call into the fake with small pages by reaching service directly
        out = []
        page = None
        while True:
            resp = self._svc.files().list(
                q=query, fields="x", pageSize=2, pageToken=page or ""
            ).execute()
            out.extend(resp.get("files") or [])
            page = resp.get("nextPageToken")
            if not page:
                break
        return out

    monkeypatch.setattr(drive_io.DriveVault, "_list_all", small_list)
    files = vault.list_dir("02-PROJEKTY", pattern="*.md")
    assert len(files) == 5


def test_list_dir_recursive_include_folders(fake_drive, vault):
    a = fake_drive.add_folder("A")
    b = fake_drive.add_folder("B", parent_id=a.id)
    fake_drive.add_file("x.md", a.id)
    fake_drive.add_file("y.md", b.id)
    flat = vault.list_dir("A")
    assert {m.name for m in flat} == {"B", "x.md"} or {m.name for m in flat} == {"x.md"}
    rec = vault.list_dir("A", recursive=True, include_folders=True)
    names = {m.rel_path for m in rec}
    assert names == {"A/B", "A/x.md", "A/B/y.md"}


def test_list_dir_on_file_raises(fake_drive, vault):
    fake_drive.add_file("README.md", None)
    with pytest.raises(DriveVaultError):
        vault.list_dir("README.md")


def test_write_text_creates_file(fake_drive, vault):
    fake_drive.add_folder("00-System")
    meta = vault.write_text("00-System/hello.md", "world")
    assert meta.name == "hello.md"
    text, _ = vault.read_text("00-System/hello.md")
    assert text == "world"


def test_write_text_updates_existing(fake_drive, vault):
    sysd = fake_drive.add_folder("00-System")
    fake_drive.add_file("hello.md", sysd.id, body="old")
    meta = vault.write_text("00-System/hello.md", "new content")
    text, _ = vault.read_text("00-System/hello.md")
    assert text == "new content"
    assert meta.name == "hello.md"


def test_write_text_cas_passes_when_unchanged(fake_drive, vault):
    sysd = fake_drive.add_folder("00-System")
    older = datetime.now(timezone.utc) - timedelta(minutes=5)
    fake_drive.add_file("hub.md", sysd.id, body="orig", modified_time=older)
    _text, meta = vault.read_text("00-System/hub.md")
    vault.write_text(
        "00-System/hub.md", "rewritten", expect_mtime=meta.modified_time
    )
    text, _ = vault.read_text("00-System/hub.md")
    assert text == "rewritten"


def test_write_text_cas_fails_when_externally_modified(fake_drive, vault):
    sysd = fake_drive.add_folder("00-System")
    older = datetime.now(timezone.utc) - timedelta(minutes=10)
    f = fake_drive.add_file("hub.md", sysd.id, body="orig", modified_time=older)
    _text, meta = vault.read_text("00-System/hub.md")
    # External edit bumps mtime forward
    f.modified_time = datetime.now(timezone.utc)
    f.body = b"external edit"
    with pytest.raises(DriveConflictError):
        vault.write_text(
            "00-System/hub.md", "should not land", expect_mtime=meta.modified_time
        )
    text, _ = vault.read_text("00-System/hub.md")
    assert text == "external edit"


def test_write_json_roundtrip(fake_drive, vault):
    fake_drive.add_folder("00-System")
    obj = {"a": [1, 2, 3], "b": {"x": "y"}}
    vault.write_json("00-System/data.json", obj)
    loaded, _ = vault.read_json("00-System/data.json")
    assert loaded == obj


def test_mkdir_p_creates_chain(fake_drive, vault):
    fid = vault.mkdir_p("07-ARCHIV/inbox-processed/2026/05/slack")
    assert fid
    assert vault.exists("07-ARCHIV/inbox-processed/2026/05/slack")
    # Idempotent
    again = vault.mkdir_p("07-ARCHIV/inbox-processed/2026/05/slack")
    assert again == fid


def test_mkdir_p_conflict_with_file(fake_drive, vault):
    fake_drive.add_file("README.md", None)
    with pytest.raises(DriveVaultError):
        vault.mkdir_p("README.md")


def test_write_text_creates_missing_parent_folders(fake_drive, vault):
    vault.write_text("a/b/c.md", "hello")
    assert vault.exists("a/b/c.md")


def test_move_changes_parent(fake_drive, vault):
    inbox = fake_drive.add_folder("01-INBOX")
    slack = fake_drive.add_folder("slack", parent_id=inbox.id)
    fake_drive.add_file("note.md", slack.id, body="hi")
    moved = vault.move(
        "01-INBOX/slack/note.md", "07-ARCHIV/inbox-processed/2026/05/note.md"
    )
    assert moved.rel_path == "07-ARCHIV/inbox-processed/2026/05/note.md"
    assert vault.exists("07-ARCHIV/inbox-processed/2026/05/note.md")
    assert not vault.exists("01-INBOX/slack/note.md")


def test_move_rename(fake_drive, vault):
    fake_drive.add_folder("foo")
    fake_drive.add_file("a.md", None, body="x")
    moved = vault.move("a.md", "foo/b.md")
    assert moved.name == "b.md"
    assert vault.exists("foo/b.md")
    assert not vault.exists("a.md")


def test_delete_trashed(fake_drive, vault):
    fake_drive.add_file("trash.md", None, body="x")
    vault.delete("trash.md")
    assert not vault.exists("trash.md")


def test_retry_on_429_then_success(fake_drive, vault, monkeypatch):
    fake_drive.add_folder("00-System")
    fake_drive.queue_failure(make_http_error(429, "rate"), count=2)
    monkeypatch.setattr(drive_io.time, "sleep", lambda _s: None)
    meta = vault.write_text("00-System/x.md", "ok")
    assert meta.name == "x.md"


def test_retry_exhausted_raises(fake_drive, vault, monkeypatch):
    fake_drive.add_folder("00-System")
    fake_drive.queue_failure(make_http_error(503, "down"), count=10)
    monkeypatch.setattr(drive_io.time, "sleep", lambda _s: None)
    with pytest.raises(HttpError):
        vault.write_text("00-System/x.md", "ok")


def test_non_retryable_error_propagates(fake_drive, vault):
    fake_drive.add_folder("00-System")
    fake_drive.queue_failure(make_http_error(403, "forbidden"))
    with pytest.raises(HttpError):
        vault.write_text("00-System/x.md", "no")


def test_path_normalization():
    from drive_io import _norm_rel, _split_rel

    assert _norm_rel("a/b/") == "a/b"
    assert _norm_rel("/a/b") == "a/b"
    assert _norm_rel("") == ""
    with pytest.raises(ValueError):
        _norm_rel("a//b")
    assert _split_rel("/a/b/") == ["a", "b"]
    assert _split_rel("") == []


def test_filemeta_isfolder():
    m = FileMeta(
        id="x", name="f", mime_type=FOLDER_MIME, modified_time=datetime.now(timezone.utc),
        size=None, parent_id=None, rel_path="f",
    )
    assert m.is_folder is True


def test_matches_pattern_handles_interior_wildcard():
    """'LL-*.md' used to collapse to a literal substring and match nothing."""
    from drive_io import _glob_to_substr, _matches_pattern

    needle = _glob_to_substr("LL-*.md")
    assert _matches_pattern("LL-2026-09-08-neco.md", needle) is True
    assert _matches_pattern("Icon", needle) is False
    assert _matches_pattern("2026-09-08-jiny.md", needle) is False

    ops2 = _glob_to_substr("OPS2-*.md")
    assert _matches_pattern("OPS2-2026-W36.md", ops2) is True

    # beze změny: krajní hvězdička i pattern bez wildcardu
    assert _matches_pattern("hub.md", _glob_to_substr("*.md")) is True
    assert _matches_pattern("hub.md.bak", _glob_to_substr("*.md")) is False
    assert _matches_pattern("x-batch.json", _glob_to_substr("*-batch.json")) is True
    assert _matches_pattern("waiting-42.json", _glob_to_substr("waiting-")) is True
    assert _matches_pattern("cokoliv.md", None) is True
