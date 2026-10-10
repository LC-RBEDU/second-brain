"""B1 / B2b — REST auth gate."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ["BRAIN_ALLOW_NO_PUSH"] = "1"
os.environ["BRAIN_SERVICE_TOKEN"] = "test-service-token"

from app.main import app  # noqa: E402


def test_unauthenticated_mutate_401():
    client = TestClient(app)
    # Token configured → anonymous denied
    r = client.post(
        "/v1/tasks",
        json={"slug": "test", "title": "X"},
    )
    assert r.status_code == 401


def test_human_api_key_rejected():
    client = TestClient(app)
    r = client.get("/v1/reminders", headers={"X-API-Key": "human-key"})
    assert r.status_code == 401


def test_service_token_ok_list():
    client = TestClient(app)
    # list opens vault — may 5xx without real WC; auth must pass first
    try:
        r = client.get(
            "/v1/reminders",
            headers={"Authorization": "Bearer test-service-token"},
        )
        assert r.status_code != 401
    except RuntimeError as exc:
        # open_vault may raise before HTTP mapping in TestClient
        assert "VAULT" in str(exc) or "GIT" in str(exc)


def test_f3_stub_501():
    client = TestClient(app)
    r = client.get(
        "/v1/f3/slack_live",
        headers={"Authorization": "Bearer test-service-token"},
    )
    assert r.status_code == 501
