from __future__ import annotations

from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from dashboard_bff.app import ALLOWED_EMAIL, COOKIE, HttpxBrain, create_app, sign_session

SECRET = "test-secret"
Y_PATH = "02-PROJEKTY/finance/tasks/Y.md"
ARCHIVE = "07-ARCHIV/tasks-done/finance/X.md"


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeBrain:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.queue: list[FakeResponse] = []
        self.export_tasks: list[dict[str, str]] = []

    def call(self, method: str, path: str, *, json_body: dict | None = None, params: dict | None = None) -> FakeResponse:
        self.calls.append({"method": method, "path": path, "json": json_body, "params": params})
        if path == "/v1/tasks/export":
            return FakeResponse(200, {"tasks": self.export_tasks, "count": len(self.export_tasks)})
        if not self.queue:
            return FakeResponse(200, {"ok": True})
        return self.queue.pop(0)


def client(brain: FakeBrain | None = None, *, limit: int = 40) -> tuple[TestClient, FakeBrain]:
    brain = brain or FakeBrain()
    app = create_app(brain, secret=SECRET, batch_limit=limit)
    return TestClient(app), brain


def auth(email: str = ALLOWED_EMAIL) -> dict[str, str]:
    return {COOKIE: sign_session(email, SECRET)}


def test_b17_cookie_email_and_focus_strip():
    api, brain = client()
    assert api.get("/api/export").status_code == 401
    foreign = api.get("/api/export", cookies=auth("other@example.com"))
    assert foreign.status_code == 403
    assert foreign.json()["error_reason"] == "forbidden"
    response = api.patch(
        "/api/tasks",
        cookies=auth(),
        json={"path": Y_PATH, "patch": {"title": "Nový", "focus": "2026-W43", "updated": "2026-10-01"}, "expect_oid": "a"},
    )
    assert response.status_code == 200
    sent = brain.calls[-1]
    assert sent["method"] == "PATCH"
    assert sent["path"] == "/v1/tasks"
    assert sent["json"]["patch"] == {"title": "Nový"}


def test_export_asks_for_open_tasks_only():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"tasks": [], "count": 0})

    brain = HttpxBrain(
        "http://brain.test",
        "service-token",
        transport=httpx.MockTransport(handler),
    )
    api = TestClient(create_app(brain, secret=SECRET))
    response = api.get("/api/export", cookies=auth())
    assert response.status_code == 200
    assert "include_closed_days=0" in seen["url"]
    assert "since=" not in seen["url"]
    assert seen["auth"] == "Bearer service-token"


def test_b30_one_task_is_patch_and_two_are_bulk():
    api, brain = client()
    api.patch(
        "/api/tasks",
        cookies=auth(),
        json={"path": Y_PATH, "patch": {"status": "Next"}, "expect_oid": "a"},
    )
    assert brain.calls[-1]["method"] == "PATCH"
    brain.calls.clear()
    api.post(
        "/api/cleanup",
        cookies=auth(),
        json={
            "items": [
                {"id": "F-T1", "path": Y_PATH, "title": "Jedna", "patch": {"status": "Done"}, "expect_oid": "a"},
                {"id": "F-T2", "path": "02-PROJEKTY/finance/tasks/Z.md", "title": "Dva", "patch": {"status": "Done"}, "expect_oid": "b"},
            ]
        },
    )
    assert brain.calls[0]["method"] == "POST"
    assert brain.calls[0]["path"] == "/v1/tasks/bulk"
    assert [item["id"] for item in brain.calls[0]["json"]["updates"]] == ["F-T1", "F-T2"]


def test_b57_archive_never_calls_brain_and_done_patch_is_status_only():
    api, brain = client()
    for method, url, payload in (
        ("PATCH", "/api/tasks", {"path": ARCHIVE, "patch": {"status": "Done"}}),
        ("POST", "/api/cleanup", {"items": [{"id": "X", "path": ARCHIVE, "patch": {"status": "Done"}}]}),
        ("POST", "/api/focus/propose", {"task_path": ARCHIVE, "focus_week": "2026-W43"}),
    ):
        response = api.request(method, url, cookies=auth(), json=payload)
        assert response.status_code == 400
        assert response.json()["error_reason"] == "archive_readonly"
    assert brain.calls == []
    done = api.patch(
        "/api/tasks",
        cookies=auth(),
        json={"path": Y_PATH, "patch": {"status": "Done", "focus": "2026-W43"}, "expect_oid": "y"},
    )
    assert done.status_code == 200
    assert brain.calls[-1]["json"]["patch"] == {"status": "Done"}


@pytest.mark.parametrize("status", [409, 404, 500])
def test_b18_stops_after_the_first_failure(status: int):
    brain = FakeBrain()
    brain.queue = [
        FakeResponse(200, {"ok": True}),
        FakeResponse(
            status,
            {
                "error_reason": "oid_mismatch" if status == 409 else "not_found",
                "detail": {
                    "failures": [
                        {"id": "B1", "path": Y_PATH, "oid": "oid-new"},
                        {"id": "B2", "path": Y_PATH, "oid": "oid-b2"},
                    ]
                }
                if status == 409
                else {},
            },
        ),
    ]
    brain.export_tasks = [
        {"id": "B1"},
        {"id": "B2"},
        {"id": "C1"},
        {"id": "C2"},
    ]
    api, brain = client(brain, limit=2)
    items = [
        {"id": task_id, "path": f"02-PROJEKTY/finance/tasks/{task_id}.md", "title": task_id, "patch": {"status": "Done"}, "expect_oid": "old"}
        for task_id in ("A1", "A2", "B1", "B2", "C1", "C2")
    ]
    response = api.post("/api/cleanup", cookies=auth(), json={"items": items})
    body = response.json()
    writes = [call for call in brain.calls if call["path"] != "/v1/tasks/export"]
    assert len(writes) == 2
    assert body["written"] == {"count": 2, "ids": ["A1", "A2"]}
    assert "cards" not in body
    assert set(body["written"]) == {"count", "ids"}
    assert body["saved"] == []
    assert body["failed"] == ["B1", "B2"]
    assert body["pending"] == ["C1", "C2"]
    assert body["dialog"] is None
    assert body["preview_open"] is True
    if status == 409:
        assert body["expect_oid"] == {"B1": "oid-new", "B2": "oid-b2"}
    else:
        assert body["expect_oid"] == {}


def test_family_stays_in_one_batch():
    api, brain = client(limit=1)
    api.post(
        "/api/cleanup",
        cookies=auth(),
        json={
            "items": [
                {"id": "F-S1", "path": Y_PATH, "title": "Story", "patch": {"status": "Cancelled"}, "expect_oid": "a"},
                {"id": "F-T1", "parent": "F-S1", "path": "02-PROJEKTY/finance/tasks/T.md", "title": "Dítě", "patch": {"status": "Cancelled"}, "expect_oid": "b"},
            ]
        },
    )
    writes = [call for call in brain.calls if call["path"] == "/v1/tasks/bulk"]
    assert len(writes) == 1
    assert [item["id"] for item in writes[0]["json"]["updates"]] == ["F-S1", "F-T1"]


def test_b52_deadline_conflict_is_not_retried():
    brain = FakeBrain()
    brain.queue = [FakeResponse(409, {"error_reason": "deadline_order", "detail": {"child": "F-T1"}})]
    api, brain = client(brain)
    response = api.patch(
        "/api/tasks",
        cookies=auth(),
        json={"path": Y_PATH, "patch": {"deadline": "2026-10-01"}, "expect_oid": "a"},
    )
    assert response.status_code == 409
    assert response.json()["error_reason"] == "deadline_order"
    assert response.json()["detail"] == {"child": "F-T1"}
    assert response.json()["dialog"] is None
    assert len(brain.calls) == 1


def test_b56_open_child_keeps_the_selection_and_skips_the_oid_dialog():
    brain = FakeBrain()
    brain.queue = [
        FakeResponse(
            400,
            {"error_reason": "open_child_under_closed_parent", "detail": {"parent_id": "F-E1", "child_ids": ["F-T1"]}},
        )
    ]
    brain.export_tasks = [{"id": "F-E1"}, {"id": "F-S1"}, {"id": "F-S2"}]
    api, brain = client(brain)
    one = api.post(
        "/api/cleanup",
        cookies=auth(),
        json={
            "items": [
                {"id": "F-E1", "path": Y_PATH, "title": "Epic", "patch": {"status": "Done"}, "expect_oid": "a"},
                {"id": "F-S1", "parent": "F-E1", "path": "02-PROJEKTY/finance/tasks/S.md", "title": "Story", "patch": {"status": "Done"}, "expect_oid": "b"},
            ]
        },
    )
    body = one.json()
    assert body["dialog"] is None
    assert body["selection"] == ["F-E1", "F-S1"]
    assert body["lines"] == ["F-E1 — Epic", "F-T1 — F-T1"]
    assert body["preview_open"] is True
    assert len([call for call in brain.calls if call["path"] != "/v1/tasks/export"]) == 1

    brain.queue = [
        FakeResponse(
            400,
            {
                "error_reason": "open_child_under_closed_parent",
                "detail": {
                    "failures": [
                        {"parent_id": "F-E1", "child_ids": ["F-T1"]},
                        {"parent_id": "F-S2", "child_ids": ["F-T2"]},
                    ]
                },
            },
        )
    ]
    two = api.post(
        "/api/cleanup",
        cookies=auth(),
        json={
            "items": [
                {"id": "F-E1", "path": Y_PATH, "title": "Epic", "patch": {"status": "Cancelled"}, "expect_oid": "a"},
                {"id": "F-S2", "path": "02-PROJEKTY/finance/tasks/S2.md", "title": "Jiná", "patch": {"status": "Cancelled"}, "expect_oid": "c"},
            ]
        },
    )
    assert two.json()["lines"] == ["F-E1 — Epic", "F-T1 — F-T1", "F-S2 — Jiná", "F-T2 — F-T2"]
    assert "parent_id" not in two.json()


def test_b19_propose_does_not_write_or_offer_force_save():
    api, brain = client()
    brain.queue = [FakeResponse(200, {"proposal_id": "p1", "written": False})]
    response = api.post(
        "/api/focus/propose",
        cookies=auth(),
        json={"task_path": Y_PATH, "focus_week": "2026-W43", "expect_oid": "a"},
    )
    assert response.status_code == 200
    assert response.json()["written"] is False
    assert response.json()["force_save"] is False
    assert response.json()["dialog"] is None
    assert brain.calls[0]["path"] == "/v1/focus/propose"
    assert all(call["path"] != "/v1/set_focus" for call in brain.calls)


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (403, "focus_story_has_open_child"),
        (403, "focus_task_limit_exceeded"),
        (403, "focus_epic_limit_exceeded"),
        (409, "cas_conflict"),
    ],
)
def test_b28_focus_errors_pass_through(status: int, reason: str):
    brain = FakeBrain()
    brain.queue = [FakeResponse(status, {"error_reason": reason})]
    api, _brain = client(brain)
    response = api.post("/api/focus/apply", cookies=auth(), json={"proposal_id": "p1"})
    assert response.status_code == status
    assert response.json()["error_reason"] == reason
    assert response.json()["dialog"] is None
    assert response.json()["force_save"] is False


def test_healthz_is_open():
    api, _brain = client()
    assert api.get("/healthz").json() == {"status": "ok"}


def test_over_cap_does_not_call_brain():
    api, brain = client()
    items = [
        {"id": f"F-T{index}", "path": Y_PATH, "title": "T", "patch": {"status": "Done"}, "expect_oid": "a"}
        for index in range(81)
    ]
    response = api.post("/api/cleanup", cookies=auth(), json={"items": items})
    assert response.status_code == 400
    assert response.json()["error_reason"] == "batch_too_large"
    assert brain.calls == []
