"""T6 / B8–B10 — GET /v1/context/light warm + service 403 + stale 503."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ["BRAIN_ALLOW_NO_PUSH"] = "1"
os.environ["BRAIN_SERVICE_TOKEN"] = "test-service-token"

from app.errors import BrainVaultError  # noqa: E402
from app.main import app  # noqa: E402
from app.tools import get_context_light as light_mod  # noqa: E402


def test_service_token_403_on_light():
    client = TestClient(app)
    r = client.get(
        "/v1/context/light",
        headers={"Authorization": "Bearer test-service-token"},
    )
    assert r.status_code == 403
    assert r.json().get("error_reason") == "human_oauth_required"


def test_warm_light_ok():
    import json

    light = {"generated_at": "x", "top_priority_today": [{"id": "X1"}]}

    fake = MagicMock()
    fake.read_json.side_effect = lambda rel: (light, MagicMock())

    class Ctx:
        def __enter__(self):
            return fake

        def __exit__(self, *a):
            return None

    with (
        patch.object(light_mod, "brain_vault", return_value=Ctx()),
        patch.object(light_mod, "needs_rebuild", return_value=False),
    ):
        out = light_mod.get_context_light(env={})
    assert out["mode"] == "warm"
    assert out["context"]["top_priority_today"][0]["id"] == "X1"
    # B8 / P1 — response body light ≤256 KB
    assert len(json.dumps(out["context"], ensure_ascii=False).encode("utf-8")) <= 256 * 1024


def test_stale_trio_503():
    fake = MagicMock()
    fake.read_json.side_effect = lambda rel: ({"generated_at": "2020-01-01T00:00:00Z"}, MagicMock())

    class Ctx:
        def __enter__(self):
            return fake

        def __exit__(self, *a):
            return None

    with patch.object(light_mod, "brain_vault", return_value=Ctx()):
        with pytest.raises(BrainVaultError) as exc:
            light_mod.get_context_light(env={})
    assert exc.value.error_reason == "context_light_stale"
    assert exc.value.status_code == 503
