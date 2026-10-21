"""Durable push queue — enqueue / cover / exhausted (A27, T28c)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(_LIB_DIR))

from push_queue import (  # noqa: E402
    MAX_ATTEMPTS,
    STATUS_FAILED,
    STATUS_PENDING,
    enqueue,
    has_exhausted_failure,
    has_healthy_cover,
    load_queue,
    queue_path,
)


@pytest.fixture()
def git_root(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


def test_enqueue_persists_pending(git_root: Path):
    job_id = enqueue(git_root, source="test")
    data = load_queue(git_root)
    assert queue_path(git_root).is_file()
    assert any(j.get("id") == job_id and j.get("status") == STATUS_PENDING for j in data["jobs"])
    assert has_healthy_cover(git_root)
    assert not has_exhausted_failure(git_root)


def test_exhausted_failure_gate(git_root: Path):
    data = {
        "jobs": [
            {
                "id": "j1",
                "status": STATUS_FAILED,
                "attempts": MAX_ATTEMPTS,
                "source": "test",
            }
        ],
        "updated_at": 0,
    }
    queue_path(git_root).write_text(json.dumps(data), encoding="utf-8")
    assert has_exhausted_failure(git_root)
    assert not has_healthy_cover(git_root)


def test_enqueue_raises_oserror_on_readonly(git_root: Path, monkeypatch: pytest.MonkeyPatch):
    def _boom(*_a, **_k):
        raise OSError("read-only")

    monkeypatch.setattr("push_queue.save_queue_atomic", _boom)
    with pytest.raises(OSError):
        enqueue(git_root)
