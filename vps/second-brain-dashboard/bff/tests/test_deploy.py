from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from dashboard_bff.app import create_app
from dashboard_bff.oauth import callback_url
from tests.test_bff import SECRET, FakeBrain

ROOT = Path(__file__).resolve().parents[2]


def test_callback_url_strips_slash():
    assert callback_url("https://dash.example/") == "https://dash.example/oauth/callback"


def test_authorize_uses_the_dashboard_redirect(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("DASHBOARD_PUBLIC_URL", "https://dash.example/")
    client = TestClient(create_app(FakeBrain(), secret=SECRET))
    response = client.get("/oauth/authorize", follow_redirects=False)
    assert response.status_code == 302
    assert "redirect_uri=https%3A%2F%2Fdash.example%2Foauth%2Fcallback" in response.headers["location"]
    assert response.cookies.get("sb_dashboard_oauth_state")


def test_image_does_not_mount_the_vault():
    dockerfile = (ROOT / "Dockerfile").read_text()
    setup = (ROOT / "deploy" / "setup-coolify.sh").read_text()
    assert "/data/vault" not in dockerfile
    assert "INSERT INTO local_persistent_volumes" not in setup
    assert "/oauth/callback" in setup
    assert "GOOGLE_CLIENT_ID" in setup
    assert "second-brain-dashboard" in setup


def test_dockerfile_copies_web_public_for_logo():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "second-brain-dashboard/web/public" in dockerfile
    assert (ROOT / "web" / "public" / "logo.svg").is_file()
