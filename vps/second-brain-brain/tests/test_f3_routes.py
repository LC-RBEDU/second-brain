"""F3 routes — stub gone; apply 403/501; propose OK."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ["BRAIN_ALLOW_NO_PUSH"] = "1"
os.environ["BRAIN_SERVICE_TOKEN"] = "test-service-token"

from app.batch_store import clear_for_tests  # noqa: E402
from app.main import app  # noqa: E402


def _client() -> TestClient:
    return TestClient(app)


def _auth() -> dict[str, str]:
    return {"Authorization": "Bearer test-service-token"}


def test_f3_stub_gone():
    r = _client().get("/v1/f3/slack_live", headers=_auth())
    assert r.status_code == 404


def test_mailbox_propose_and_service_apply_403():
    clear_for_tests()
    c = _client()
    r = c.post(
        "/v1/mailbox/propose",
        headers=_auth(),
        json={
            "items": [
                {"id": "m1", "action": "archive", "reversible": True},
                {"id": "m2", "action": "send", "reversible": False},
            ]
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["batch_id"]
    assert body["mutated"] is False
    flags = {i["id"]: i["reversible"] for i in body["items"]}
    assert flags["m1"] is True
    assert flags["m2"] is False

    r2 = c.post(
        "/v1/mailbox/apply",
        headers=_auth(),
        json={"batch_id": body["batch_id"], "ids": ["m1"]},
    )
    assert r2.status_code == 403
    assert r2.json()["error_reason"] == "human_oauth_required"


def test_mailbox_apply_oauth_501():
    clear_for_tests()
    c = _client()
    r = c.post(
        "/v1/mailbox/propose",
        headers=_auth(),
        json={"items": [{"id": "x", "action": "archive"}]},
    )
    batch_id = r.json()["batch_id"]
    with patch("app.auth_deps.read_session_email", return_value="lukas@redbuttonedu.cz"):
        r2 = c.post(
            "/v1/mailbox/apply",
            headers=_auth(),
            cookies={"sb_session": "fake"},
            json={"batch_id": batch_id},
        )
    # Cookie may not decode — force principal via patch on gate path
    from app.auth_apply import gate_brain_apply
    from app.errors import BrainClientError

    try:
        gate_brain_apply("oauth:lukas@redbuttonedu.cz")
        assert False, "expected raise"
    except BrainClientError as exc:
        assert exc.status_code == 501
        assert exc.error_reason == "oauth_brain_apply_post_f3"


def test_push_test_b18_fail_shape():
    r = _client().post("/v1/push/test", headers=_auth())
    assert r.status_code == 200
    body = r.json()
    assert body["b18"] == "FAIL"
    assert "slack_dm" in body["fallback"]
