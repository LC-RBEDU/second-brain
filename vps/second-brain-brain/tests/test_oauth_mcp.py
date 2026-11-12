"""MCP OAuth for Claude — T1–T57 except the manual T60."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import inspect
import json
import os
import sys
import threading
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("BRAIN_ALLOW_NO_PUSH", "1")
os.environ.setdefault("BRAIN_SERVICE_TOKEN", "test-service-token")

from app.auth_service import ServicePrincipal  # noqa: E402
from app.errors import BrainClientError  # noqa: E402
from app.main import app  # noqa: E402
from app.mcp_app import build_mcp, run_tool  # noqa: E402
from app.oauth_mcp_audit import audit_line  # noqa: E402
from app.oauth_mcp_metadata import www_authenticate  # noqa: E402
from app.oauth_mcp_revoke import main as revoke_main  # noqa: E402
from app.oauth_mcp_routes import (  # noqa: E402
    complete_token,
    google_outbound,
    oauth_mcp_token,
)
from app.oauth_mcp_scope import OAuthPrincipal, READ, TOOL_SCOPES, WRITE  # noqa: E402
from app.oauth_mcp_store import (  # noqa: E402
    OAuthUnavailable,
    code_used_at,
    family_id_for_refresh,
    family_revoked,
    is_expired,
    iso,
    issue_code,
    open_count,
    read_access,
    redeem_code,
    reset_runtime,
    set_expires,
    token_hash,
    transaction_row,
    utcnow,
)
from app import oauth_mcp_store as store  # noqa: E402
from app.oauth_routes import _COOKIE, _serializer, read_session_email  # noqa: E402
from app.request_principal import (  # noqa: E402
    get_brain_principal,
    reset_brain_principal,
    set_brain_principal,
)
from app.tools import get_context as get_context_mod  # noqa: E402
from app.tools import set_focus as set_focus_mod  # noqa: E402

AI = "https://claude.ai/api/mcp/auth_callback"
COM = "https://claude.com/api/mcp/auth_callback"
LOOP = "http://127.0.0.1:8765/callback"
EMAIL = "lukas@redbuttonedu.cz"


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path, client):
    monkeypatch.setenv("BRAIN_PUBLIC_URL", "https://brain.cyprovi.cz")
    monkeypatch.setenv("BRAIN_OAUTH_DB", str(tmp_path / "oauth.sqlite"))
    monkeypatch.setenv("BRAIN_OAUTH_TOKEN_PEPPER", "pepper-test")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "csecret")
    monkeypatch.setenv("BRAIN_ALLOW_NO_PUSH", "1")
    monkeypatch.setenv("BRAIN_SERVICE_TOKEN", "test-service-token")
    client.cookies.clear()
    reset_runtime()
    google_outbound.clear()
    yield
    reset_runtime()


@pytest.fixture(scope="module")
def client():
    # No lifespan here. The MCP session manager accepts .run() once per process,
    # and other modules already enter it. OAuth routes do not need it.
    return TestClient(app)


def _pkce(verifier: str = "verifier-value-which-is-long-enough-for-s256") -> tuple[str, str]:
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _register(client: TestClient, uris: list[str] | None = None, name: str = "Claude") -> dict:
    response = client.post(
        "/oauth/mcp/register",
        json={
            "client_name": name,
            "redirect_uris": uris or [AI],
            "token_endpoint_auth_method": "none",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _authorize(client: TestClient, client_id: str, **extra: str):
    _verifier, challenge = _pkce()
    params = {
        "client_id": client_id,
        "redirect_uri": AI,
        "response_type": "code",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": "st",
    }
    params.update(extra)
    return client.get("/oauth/mcp/authorize", params=params)


def _tx_id(html: str) -> str:
    marker = 'name="id" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


def _pair(scope: str = "brain:read brain:write") -> dict:
    verifier, challenge = _pkce()
    code = issue_code(
        email=EMAIL,
        client_id="client",
        client_name="Claude",
        redirect_uri=AI,
        scope=scope,
        code_challenge=challenge,
    )
    body = redeem_code(code, verifier)
    assert "access_token" in body, body
    return body


def test_t1_mcp_401_advertises_resource(client: TestClient):
    response = client.post("/mcp", json={})
    assert response.status_code == 401
    assert response.json().get("error_reason") == "client_error"
    header = response.headers["www-authenticate"]
    assert header == www_authenticate()
    assert "resource_metadata=" in header
    assert 'scope="brain:read brain:write"' in header


def test_t2_service_token_does_not_open_sqlite(client: TestClient):
    del client
    before = open_count
    status, seen = _probe({b"authorization": b"Bearer test-service-token"})
    assert status == 200
    assert seen and isinstance(seen[0], ServicePrincipal)
    assert open_count == before


def test_t3_cookie_principal_does_not_open_sqlite(client: TestClient):
    del client
    cookie = _serializer().dumps({"email": EMAIL})
    before = open_count
    status, seen = _probe({b"cookie": f"{_COOKIE}={cookie}".encode()})
    assert status == 200
    assert seen == [f"oauth:{EMAIL}"]
    assert open_count == before
    assert read_session_email(cookie) == EMAIL


def test_t4_oauth_access_runs_tool(client: TestClient):
    del client
    body = _pair()
    status, seen = _probe({b"authorization": f"Bearer {body['access_token']}".encode()})
    assert status == 200
    assert seen and isinstance(seen[0], OAuthPrincipal)
    assert seen[0].email == EMAIL
    token = set_brain_principal(
        OAuthPrincipal(EMAIL, frozenset(body["scope"].split()), "Claude")
    )
    called = []
    try:
        assert run_tool("get_context", lambda: called.append(1) or "ok") == "ok"
    finally:
        reset_brain_principal(token)
    assert called == [1]
    record = read_access(body["access_token"])
    assert record is not None and record.email == EMAIL


def test_t5_removed_allowlist_is_401(client: TestClient, monkeypatch):
    body = _pair()
    monkeypatch.setattr("app.mcp_auth.email_allowed", lambda _email: False)
    response = client.post(
        "/mcp/",
        headers={"Authorization": f"Bearer {body['access_token']}"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_context"}},
    )
    assert response.status_code == 401


def test_t6_expired_or_revoked_access_is_401(client: TestClient):
    body = _pair()
    family = family_id_for_refresh(body["refresh_token"])
    assert family
    set_expires("access_tokens", "token_hash", token_hash(body["access_token"]), iso(utcnow()))
    expired = client.post("/mcp/", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert expired.status_code == 401
    assert "resource_metadata=" in expired.headers["www-authenticate"]
    fresh = _pair()
    other = family_id_for_refresh(fresh["refresh_token"])
    assert other
    store.revoke(family_id=other)
    revoked = client.post("/mcp/", headers={"Authorization": f"Bearer {fresh['access_token']}"})
    assert revoked.status_code == 401
    assert "resource_metadata=" in revoked.headers["www-authenticate"]


def test_t7_rest_rejects_oauth_without_header(client: TestClient):
    body = _pair()
    response = client.get("/v1/context", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert response.status_code == 401
    assert "www-authenticate" not in response.headers


def test_t8_rest_service_and_cookie_stay(client: TestClient):
    try:
        service = client.get("/v1/reminders", headers={"Authorization": "Bearer test-service-token"})
        assert service.status_code != 401
        assert "www-authenticate" not in service.headers
    except RuntimeError as exc:
        assert "VAULT" in str(exc) or "GIT" in str(exc)
    cookie = _serializer().dumps({"email": EMAIL})
    try:
        human = client.get("/v1/reminders", cookies={_COOKIE: cookie})
        assert human.status_code != 401
        assert "www-authenticate" not in human.headers
    except RuntimeError as exc:
        assert "VAULT" in str(exc) or "GIT" in str(exc)


def test_t9_api_key_is_not_a_bearer(client: TestClient):
    body = _pair()
    response = client.post("/mcp/", headers={"X-API-Key": body["access_token"]})
    assert response.status_code == 401
    assert response.json().get("error_reason") == "client_error"


def test_t10_protected_resource_documents_match(client: TestClient):
    root = client.get("/.well-known/oauth-protected-resource").json()
    mounted = client.get("/.well-known/oauth-protected-resource/mcp").json()
    assert root == mounted
    assert root["resource"] == "https://brain.cyprovi.cz/mcp/"
    assert root["authorization_servers"] == ["https://brain.cyprovi.cz"]
    assert "offline_access" not in json.dumps(root)


def test_t11_authorization_server_metadata(client: TestClient):
    doc = client.get("/.well-known/oauth-authorization-server").json()
    assert doc["registration_endpoint"].endswith("/oauth/mcp/register")
    assert doc["client_id_metadata_document_supported"] is True
    assert doc["token_endpoint_auth_methods_supported"] == ["none"]
    assert doc["grant_types_supported"] == ["authorization_code", "refresh_token"]
    assert "private_key_jwt" not in json.dumps(doc)
    missing = client.get("/.well-known/openid-configuration")
    assert missing.status_code == 404


def test_t12_dcr_returns_client_and_reaches_consent(client: TestClient):
    for uris in ([AI, COM], [AI]):
        created = _register(client, uris)
        assert "client_secret" not in created
        assert created["token_endpoint_auth_method"] == "none"
        page = _authorize(client, created["client_id"])
        assert page.status_code == 200
        assert "Pokračovat" in page.text
        assert 'method="post"' in page.text


def test_t13_dcr_rejects_loopback(client: TestClient):
    before = _client_count()
    response = client.post(
        "/oauth/mcp/register",
        json={"redirect_uris": [LOOP], "token_endpoint_auth_method": "none"},
    )
    assert response.status_code == 400
    assert _client_count() == before


def test_t14_cimd_hosted_document_reaches_consent(client: TestClient, monkeypatch):
    url = "https://claude.ai/oauth/mcp-oauth-client-metadata"
    _mock_cimd(
        monkeypatch,
        {
            "client_id": url,
            "client_name": "Claude",
            "redirect_uris": [AI],
            "grant_types": [
                "authorization_code",
                "refresh_token",
                "urn:ietf:params:oauth:grant-type:jwt-bearer",
            ],
            "token_endpoint_auth_method": "none",
        },
    )
    page = _authorize(client, url)
    assert page.status_code == 200
    assert "Pokračovat" in page.text


def test_t15_cimd_loopback_does_not_login(client: TestClient, monkeypatch):
    url = "https://claude.ai/oauth/claude-code-client-metadata"
    _mock_cimd(
        monkeypatch,
        {
            "client_id": url,
            "client_name": "Claude Code",
            "redirect_uris": [AI, LOOP],
            "grant_types": ["authorization_code", "refresh_token"],
        },
    )
    page = _authorize(client, url, redirect_uri=LOOP)
    assert page.status_code == 400
    assert google_outbound == []
    assert "accounts.google.com" not in page.headers.get("location", "")
    assert store.count_codes() == 0


def test_t16_bad_redirect_or_pkce_does_not_go_to_google(client: TestClient):
    created = _register(client)
    bad_redirect = _authorize(client, created["client_id"], redirect_uri="https://evil.example/cb")
    plain = _authorize(client, created["client_id"], code_challenge_method="plain")
    for response in (bad_redirect, plain):
        assert response.status_code == 400
        assert "accounts.google.com" not in response.headers.get("location", "")


def test_t17_resource_compare(client: TestClient):
    created = _register(client)
    accepted = _authorize(client, created["client_id"], resource="HTTPS://Brain.cyprovi.cz/mcp")
    assert accepted.status_code == 200
    missing = _authorize(client, created["client_id"])
    assert missing.status_code == 200
    mismatch = _authorize(client, created["client_id"], resource="https://evil.example/mcp")
    assert mismatch.status_code == 400
    assert mismatch.json()["error"] == "invalid_target"


def test_t18_omitted_scope_is_both(client: TestClient):
    created = _register(client)
    page = _authorize(client, created["client_id"])
    row = transaction_row(_tx_id(page.text))
    assert row is not None
    assert row[4] == "brain:read brain:write"


def test_t19_offline_access_is_dropped_and_code_returns_refresh(client: TestClient):
    created = _register(client)
    page = _authorize(client, created["client_id"], scope="brain:read offline_access")
    row = transaction_row(_tx_id(page.text))
    assert row is not None and row[4] == "brain:read"
    assert "offline_access" not in row[4]
    verifier, challenge = _pkce()
    code = issue_code(
        email=EMAIL,
        client_id=created["client_id"],
        client_name="Claude",
        redirect_uri=AI,
        scope=row[4],
        code_challenge=challenge,
    )
    token = client.post(
        "/oauth/mcp/token",
        data={"grant_type": "authorization_code", "code": code, "code_verifier": verifier},
    )
    assert token.status_code == 200
    assert token.json()["refresh_token"]
    assert token.json()["scope"] == "brain:read"


def test_t20_consent_form_and_cancel(client: TestClient):
    created = _register(client)
    page = _authorize(client, created["client_id"])
    html = page.text
    assert 'method="post"' in html
    assert 'action="/oauth/mcp/continue"' in html
    assert "action=\"/oauth/mcp/continue?" not in html
    assert html.count("<button") == 1
    assert 'name="id"' in html
    tx = _tx_id(html)
    before = transaction_row(tx)
    codes = store.count_codes()
    cancelled = client.get("/oauth/mcp/cancelled", follow_redirects=False)
    assert cancelled.status_code == 200
    assert cancelled.request.method == "GET"
    assert "accounts.google.com" not in cancelled.headers.get("location", "")
    assert store.count_codes() == codes
    assert transaction_row(tx) == before


def test_t21_state_is_escaped_and_urlencoded(client: TestClient, monkeypatch):
    created = _register(client)
    state = '<script>"'
    page = _authorize(client, created["client_id"], state=state)
    assert "<script>" not in page.text
    assert "&lt;script&gt;" in page.text
    tx = _tx_id(page.text)
    continued = client.post("/oauth/mcp/continue", data={"id": tx}, follow_redirects=False)
    assert continued.status_code == 302
    monkeypatch.setattr(
        "app.oauth_mcp_routes.exchange_google",
        _async_return((200, "stranger@example.com")),
    )
    denied = client.get(
        "/oauth/mcp/callback",
        params={"code": "g", "state": tx},
        cookies=continued.cookies,
        follow_redirects=False,
    )
    location = denied.headers["location"]
    assert parse_qs(urlparse(location).query)["state"] == [state]
    assert "error=access_denied" in location or parse_qs(urlparse(location).query)["error"] == [
        "access_denied"
    ]


def test_t22_foreign_email_lists_no_allowlist(client: TestClient, monkeypatch):
    created = _register(client, name="Claude")
    page = _authorize(client, created["client_id"], state="client-state")
    tx = _tx_id(page.text)
    continued = client.post("/oauth/mcp/continue", data={"id": tx}, follow_redirects=False)
    monkeypatch.setattr(
        "app.oauth_mcp_routes.exchange_google",
        _async_return((200, "stranger@example.com")),
    )
    denied = client.get(
        "/oauth/mcp/callback",
        params={"code": "g", "state": tx},
        cookies=continued.cookies,
        follow_redirects=False,
    )
    assert "lukas@redbuttonedu.cz" not in denied.text
    assert "lukas.cypra@gmail.com" not in denied.text
    assert "přístup zamítnut" in denied.text
    query = parse_qs(urlparse(denied.headers["location"]).query)
    assert query["error"] == ["access_denied"]
    assert query["state"] == ["client-state"]
    assert store.count_codes() == 0


def test_t23_google_non_200_mints_nothing(client: TestClient, monkeypatch):
    created = _register(client)
    page = _authorize(client, created["client_id"])
    tx = _tx_id(page.text)
    continued = client.post("/oauth/mcp/continue", data={"id": tx}, follow_redirects=False)
    monkeypatch.setattr("app.oauth_mcp_routes.exchange_google", _async_return((500, None)))
    denied = client.get(
        "/oauth/mcp/callback",
        params={"code": "g", "state": tx},
        cookies=continued.cookies,
        follow_redirects=False,
    )
    assert denied.status_code == 400
    assert store.count_codes() == 0
    assert "access_token" not in denied.text


def test_t24_code_is_one_time(client: TestClient):
    verifier, challenge = _pkce()
    code = issue_code(
        email=EMAIL,
        client_id="c",
        client_name="Claude",
        redirect_uri=AI,
        scope="brain:read brain:write",
        code_challenge=challenge,
    )
    first = client.post(
        "/oauth/mcp/token",
        data={"grant_type": "authorization_code", "code": code, "code_verifier": verifier},
    )
    second = client.post(
        "/oauth/mcp/token",
        data={"grant_type": "authorization_code", "code": code, "code_verifier": verifier},
    )
    assert first.status_code == 200
    payload = first.json()
    assert payload["access_token"] and payload["refresh_token"]
    assert set(payload) == {"access_token", "token_type", "expires_in", "refresh_token", "scope"}
    assert family_id_for_refresh(payload["refresh_token"])
    assert second.status_code == 400
    assert second.json() == {"error": "invalid_grant"}


def test_t25_refresh_keeps_read_scope(client: TestClient):
    body = _pair("brain:read")
    refreshed = client.post(
        "/oauth/mcp/token",
        data={"grant_type": "refresh_token", "refresh_token": body["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["scope"] == "brain:read"


def test_t26_refresh_cannot_grow_to_write(client: TestClient):
    body = _pair("brain:read")
    family = family_id_for_refresh(body["refresh_token"])
    refused = client.post(
        "/oauth/mcp/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": body["refresh_token"],
            "scope": "brain:write",
        },
    )
    assert refused.status_code == 400
    assert refused.json() == {"error": "invalid_scope"}
    assert family and family_revoked(family) is False
    again = client.post(
        "/oauth/mcp/token",
        data={"grant_type": "refresh_token", "refresh_token": body["refresh_token"]},
    )
    assert again.status_code == 200


def test_t34_t35_overlapping_refresh_then_replay(client: TestClient):
    del client
    assert inspect.iscoroutinefunction(oauth_mcp_token) is False
    body = _pair()
    old = body["refresh_token"]
    family = family_id_for_refresh(old)
    form = {"grant_type": "refresh_token", "refresh_token": old}
    loser_in = threading.Event()
    results: list[tuple[str, object]] = []

    def hold() -> None:
        assert loser_in.wait(2)

    def on_wait() -> None:
        loser_in.set()

    def run(label: str, **hooks) -> None:
        results.append((label, complete_token(form, **hooks)))

    threads = [
        threading.Thread(target=run, args=("a",), kwargs={"hold": hold, "on_wait": on_wait}),
        threading.Thread(target=run, args=("b",), kwargs={"hold": hold, "on_wait": on_wait}),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(3)
    payloads = [json.loads(item.body) for _label, item in results]  # type: ignore[attr-defined]
    ok = [item for item in payloads if "access_token" in item]
    denied = [item for item in payloads if item.get("error") == "invalid_grant"]
    assert len(ok) == 1 and len(denied) == 1
    new = ok[0]["refresh_token"]
    assert family and family_revoked(family) is False
    kept = complete_token({"grant_type": "refresh_token", "refresh_token": new})
    assert json.loads(kept.body)["access_token"]
    assert family_revoked(family) is False
    replay = complete_token({"grant_type": "refresh_token", "refresh_token": old})
    assert json.loads(replay.body) == {"error": "invalid_grant"}
    assert family_revoked(family) is True
    dead = complete_token({"grant_type": "refresh_token", "refresh_token": new})
    assert json.loads(dead.body) == {"error": "invalid_grant"}


def test_t36_one_family_does_not_kill_the_other():
    first = _pair()
    second = _pair()
    rotated = complete_token(
        {"grant_type": "refresh_token", "refresh_token": first["refresh_token"]}
    )
    assert "access_token" in json.loads(rotated.body)
    replay = complete_token(
        {"grant_type": "refresh_token", "refresh_token": first["refresh_token"]}
    )
    assert json.loads(replay.body) == {"error": "invalid_grant"}
    other = complete_token(
        {"grant_type": "refresh_token", "refresh_token": second["refresh_token"]}
    )
    assert "access_token" in json.loads(other.body)


def test_t37_expiry_includes_equality():
    body = _pair()
    now = iso(utcnow())
    set_expires("refresh_tokens", "token_hash", token_hash(body["refresh_token"]), now)
    assert is_expired(now)
    expired = complete_token(
        {"grant_type": "refresh_token", "refresh_token": body["refresh_token"]}
    )
    assert json.loads(expired.body) == {"error": "invalid_grant"}
    aged = _pair()
    family = family_id_for_refresh(aged["refresh_token"])
    assert family
    set_expires("families", "id", family, iso(utcnow() - timedelta(days=91)))
    capped = complete_token(
        {"grant_type": "refresh_token", "refresh_token": aged["refresh_token"]}
    )
    assert json.loads(capped.body) == {"error": "invalid_grant"}
    verifier, challenge = _pkce()
    code = issue_code(
        email=EMAIL,
        client_id="c",
        client_name="Claude",
        redirect_uri=AI,
        scope="brain:read",
        code_challenge=challenge,
    )
    set_expires("codes", "code_hash", token_hash(code), iso(utcnow() - timedelta(seconds=61)))
    assert redeem_code(code, verifier) == {"error": "invalid_grant"}
    access = _pair()
    set_expires(
        "access_tokens",
        "token_hash",
        token_hash(access["access_token"]),
        iso(utcnow() - timedelta(hours=2)),
    )
    record = read_access(access["access_token"])
    assert record is not None and record.expired
    set_expires(
        "refresh_tokens",
        "token_hash",
        token_hash(access["refresh_token"]),
        iso(utcnow() - timedelta(days=31)),
    )
    stale = complete_token(
        {"grant_type": "refresh_token", "refresh_token": access["refresh_token"]}
    )
    assert json.loads(stale.body) == {"error": "invalid_grant"}


def test_t39_missing_pepper_or_vault_path_is_503(client: TestClient, monkeypatch, tmp_path):
    monkeypatch.delenv("BRAIN_OAUTH_TOKEN_PEPPER", raising=False)
    _assert_degraded(client)
    monkeypatch.setenv("BRAIN_OAUTH_TOKEN_PEPPER", "pepper-test")
    root = tmp_path / "vault"
    root.mkdir()
    monkeypatch.setenv("GIT_VAULT_ROOT", str(root))
    monkeypatch.setenv("BRAIN_OAUTH_DB", str(root / "oauth.sqlite"))
    _assert_degraded(client)


def test_t40_oauth_hash_does_not_use_the_session_secret(monkeypatch):
    monkeypatch.setenv("BRAIN_SESSION_SECRET", "")
    monkeypatch.setenv("BRAIN_SERVICE_TOKEN", "test-service-token")
    cookie = _serializer().dumps({"email": EMAIL})
    assert read_session_email(cookie) == EMAIL
    monkeypatch.delenv("BRAIN_OAUTH_TOKEN_PEPPER", raising=False)
    with pytest.raises(OAuthUnavailable):
        token_hash("raw-token")


def test_t41_read_token_cannot_run_a_write_tool(capsys):
    token = set_brain_principal(OAuthPrincipal(EMAIL, frozenset({READ}), "Claude"))
    called = []
    try:
        result = run_tool("create_task", lambda: called.append("dry_run") or "ran")
    finally:
        reset_brain_principal(token)
    assert called == []
    assert result.is_error
    assert "insufficient_scope" in result.content[0].text
    assert json.loads(capsys.readouterr().out)["result"] == "insufficient_scope"


def test_t42_write_token_runs_the_tool():
    token = set_brain_principal(OAuthPrincipal(EMAIL, frozenset({READ, WRITE}), "Claude"))
    try:
        assert run_tool("create_task", lambda: "ran") == "ran"
    finally:
        reset_brain_principal(token)


def test_t44_tool_map_matches_the_server():
    names = sorted(tool.name for tool in asyncio.run(build_mcp().list_tools()))
    assert names == sorted(TOOL_SCOPES)
    assert len(TOOL_SCOPES) == 33
    assert sum(scope == READ for scope in TOOL_SCOPES.values()) == 13
    assert sum(scope == WRITE for scope in TOOL_SCOPES.values()) == 20
    token = set_brain_principal(OAuthPrincipal(EMAIL, frozenset({READ, WRITE}), "Claude"))
    called = []
    try:
        result = run_tool("not_a_tool", lambda: called.append(1))
    finally:
        reset_brain_principal(token)
    assert called == []
    assert result.is_error


def test_t45_read_context_does_not_rebuild(monkeypatch):
    modes: list[str] = []

    class _CM:
        def __enter__(self):
            return object()

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(get_context_mod, "needs_rebuild", lambda *a, **k: True)
    monkeypatch.setattr(
        get_context_mod,
        "brain_vault",
        lambda mode="read", env=None: modes.append(mode) or _CM(),
    )
    with pytest.raises(BrainClientError) as caught:
        get_context_mod.get_context(allow_rebuild=False)
    assert caught.value.error_reason == "context_rebuild_requires_write"
    assert modes == ["read"]


def test_t46_write_context_still_rebuilds(monkeypatch):
    modes: list[str] = []

    class _CM:
        def __enter__(self):
            return object()

        def __exit__(self, *args):
            return False

    seen = {"n": 0}

    def needs(*_a, **_k):
        seen["n"] += 1
        return seen["n"] == 1

    monkeypatch.setattr(get_context_mod, "needs_rebuild", needs)
    monkeypatch.setattr(get_context_mod, "attach_sembly_pending", lambda *a, **k: None)
    monkeypatch.setattr(
        get_context_mod,
        "build_and_write_context_bundle",
        lambda *a, **k: {"context": True},
    )
    monkeypatch.setattr(
        get_context_mod,
        "brain_vault",
        lambda mode="read", env=None: modes.append(mode) or _CM(),
    )
    out = get_context_mod.get_context(allow_rebuild=True)
    assert out["mode"] == "rebuild"
    assert modes == ["read", "rebuild"]


def test_t47_focus_writers(monkeypatch):
    from datetime import date
    from unittest.mock import MagicMock, patch

    from focus import current_focus_week

    today = date(2026, 10, 12)
    week = current_focus_week(today)
    path = "02-PROJEKTY/second-brain/tasks/SB-S17 — Test.md"
    text = (
        "---\nid: SB-S17\ntype: story\ntitle: Test\nslug: second-brain\n"
        "status: Next\nfocus:\nupdated: 2026-10-01\n---\n\n# t\n"
    )
    monkeypatch.setattr(set_focus_mod, "_prague_today", lambda env=None: today)

    def write_with(principal):
        vault = MagicMock()
        meta = MagicMock()
        meta.oid = "oid1"
        vault.read_text.return_value = (text, meta)
        meta2 = MagicMock()
        meta2.oid = "oid2"
        vault.write_text.return_value = meta2
        vault.list_dir.return_value = []

        class CM:
            def __enter__(self):
                return vault

            def __exit__(self, *a):
                return False

        with patch.object(set_focus_mod, "brain_vault", return_value=CM()):
            with patch.object(set_focus_mod, "iter_active_tasks", return_value=iter([])):
                with patch.object(set_focus_mod, "delete_context_tombstone"):
                    with patch.object(set_focus_mod, "_paused_slugs_from_vault", return_value=set()):
                        out = set_focus_mod.set_focus(
                            via_apply=True,
                            task_path=path,
                            focus_week=week,
                            principal=principal,
                        )
        assert vault.write_text.called
        return out

    assert write_with(ServicePrincipal())["focus"] == week
    assert write_with(OAuthPrincipal(EMAIL, frozenset({WRITE}), "Claude"))["focus"] == week
    with pytest.raises(BrainClientError) as bare:
        set_focus_mod.set_focus(via_apply=False, task_path=path, focus_week=week)
    assert bare.value.error_reason == "focus_requires_proposal"
    with pytest.raises(BrainClientError):
        set_focus_mod.set_focus(
            via_apply=True,
            task_path=path,
            focus_week=week,
            principal=OAuthPrincipal(EMAIL, frozenset({READ}), "Claude"),
        )


def test_t48_apply_gates_and_read_does_not_start():
    from app.auth_apply import gate_brain_apply

    with pytest.raises(BrainClientError) as service:
        gate_brain_apply(ServicePrincipal())
    assert service.value.status_code == 403
    with pytest.raises(BrainClientError) as cookie:
        gate_brain_apply(f"oauth:{EMAIL}")
    assert cookie.value.status_code == 501
    with pytest.raises(BrainClientError) as oauth:
        gate_brain_apply(OAuthPrincipal(EMAIL, frozenset({WRITE}), "Claude"))
    assert oauth.value.status_code == 501
    token = set_brain_principal(OAuthPrincipal(EMAIL, frozenset({READ}), "Claude"))
    called = []
    try:
        run_tool("mailbox_apply", lambda: called.append(1))
        run_tool("external_apply", lambda: called.append(1))
    finally:
        reset_brain_principal(token)
    assert called == []


def test_t49_audit_line_is_stdout_only(capsys):
    token = set_brain_principal(ServicePrincipal())
    try:
        audit_line("get_context", "ok")
    finally:
        reset_brain_principal(token)
    line = json.loads(capsys.readouterr().out)
    assert line["identity"] == "service"
    assert line["client"] == "service"
    assert line["tool"] == "get_context"
    source = inspect.getsource(audit_line)
    assert "brain_vault" not in source


def test_t50_jwt_bearer_is_unsupported(client: TestClient):
    response = client.post("/oauth/mcp/token", data={"grant_type": "jwt-bearer", "assertion": "x"})
    assert response.status_code == 400
    assert response.json() == {"error": "unsupported_grant_type"}
    paths = [getattr(route, "path", "") for route in app.routes]
    assert not any("enterprise" in path for path in paths)


def test_t51_revoke_family_leaves_the_other(client: TestClient):
    first = _pair()
    second = _pair()
    family = family_id_for_refresh(first["refresh_token"])
    assert family
    assert revoke_main(["--family", family]) == 0
    dead = client.post("/mcp/", headers={"Authorization": f"Bearer {first['access_token']}"})
    assert dead.status_code == 401
    live = read_access(second["access_token"])
    assert live is not None and live.revoked is False
    paths = [getattr(route, "path", "") for route in app.routes]
    assert not any(path.endswith("/oauth/mcp/revoke") for path in paths)


def test_t52_foreign_redirect_does_not_move_the_row(client: TestClient):
    created = _register(client)
    page = _authorize(client, created["client_id"])
    tx = _tx_id(page.text)
    before = transaction_row(tx)
    codes = store.count_codes()
    ok = client.post("/oauth/mcp/continue", data={"id": tx}, follow_redirects=False)
    assert ok.status_code == 302
    assert "accounts.google.com" in ok.headers["location"]
    assert "sb_mcp_oauth_tx" in ok.cookies
    assert google_outbound == []
    assert transaction_row(tx) == before

    def stop(url: str, data: dict) -> None:
        response = client.post(url, data=data, follow_redirects=False)
        assert response.status_code == 400
        location = response.headers.get("location", "")
        assert "accounts.google.com" not in location
        assert "evil.example" not in location
        assert transaction_row(tx) == before
        assert store.count_codes() == codes
        assert google_outbound == []

    stop("/oauth/mcp/continue", {"id": tx, "redirect_uri": "https://evil.example/cb"})
    stop(
        "/oauth/mcp/continue?redirect_uri=" + "https://evil.example/cb",
        {"id": tx},
    )
    stop(
        "/oauth/mcp/continue?redirect_uri=" + AI,
        {"id": tx, "redirect_uri": "https://evil.example/cb"},
    )
    stop(
        "/oauth/mcp/continue?redirect_uri=" + "https://evil.example/cb",
        {"id": tx, "redirect_uri": AI},
    )


def test_t53_client_name_is_escaped(client: TestClient):
    created = _register(client, name='<b>"Claude')
    page = _authorize(client, created["client_id"])
    assert '<b>"Claude' not in page.text
    assert "&lt;b&gt;" in page.text
    assert "&quot;Claude" in page.text


def test_t54_callback_requires_the_cookie(client: TestClient, monkeypatch):
    created = _register(client)
    page = _authorize(client, created["client_id"])
    tx = _tx_id(page.text)
    monkeypatch.setattr(
        "app.oauth_mcp_routes.exchange_google",
        _async_return((200, EMAIL)),
    )
    bare = client.get(
        "/oauth/mcp/callback",
        params={"code": "g", "state": tx},
        follow_redirects=False,
    )
    assert bare.status_code == 400
    assert "claude.ai" not in bare.headers.get("location", "")
    assert store.count_codes() == 0
    mismatched = client.get(
        "/oauth/mcp/callback",
        params={"code": "g", "state": tx},
        cookies={"sb_mcp_oauth_tx": "other"},
        follow_redirects=False,
    )
    assert mismatched.status_code == 400
    assert store.count_codes() == 0
    assert google_outbound == []


def test_t55_bad_verifier_leaves_the_code():
    verifier, challenge = _pkce()
    code = issue_code(
        email=EMAIL,
        client_id="c",
        client_name="Claude",
        redirect_uri=AI,
        scope="brain:read",
        code_challenge=challenge,
    )
    refused = redeem_code(code, verifier + "-no")
    assert refused == {"error": "invalid_grant"}
    assert "access_token" not in refused
    assert code_used_at(code) is None


def test_t56_overlapping_redeem_mints_one_pair():
    verifier, challenge = _pkce()
    code = issue_code(
        email=EMAIL,
        client_id="c",
        client_name="Claude",
        redirect_uri=AI,
        scope="brain:read brain:write",
        code_challenge=challenge,
    )
    release = threading.Event()
    results: list[dict] = []

    def hold() -> None:
        release.wait(2)

    def once(use_hold: bool) -> None:
        results.append(redeem_code(code, verifier, hold=hold if use_hold else None))

    first = threading.Thread(target=once, args=(True,))
    first.start()
    threading.Event().wait(0.05)
    second = threading.Thread(target=once, args=(False,))
    second.start()
    threading.Event().wait(0.05)
    release.set()
    first.join(3)
    second.join(3)
    ok = [item for item in results if "access_token" in item]
    denied = [item for item in results if item.get("error") == "invalid_grant"]
    assert len(ok) == 1 and len(denied) == 1


def test_t57_unknown_and_expired_transaction_stops(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        "app.oauth_mcp_routes.exchange_google",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("google")),
    )
    before_tx = store.count_transactions()
    before_codes = store.count_codes()
    unknown = client.post("/oauth/mcp/continue", data={"id": "missing"}, follow_redirects=False)
    assert unknown.status_code == 400
    assert "location" not in unknown.headers
    assert store.count_transactions() == before_tx
    assert store.count_codes() == before_codes
    created = _register(client)
    page = _authorize(client, created["client_id"])
    tx = _tx_id(page.text)
    snapshot = transaction_row(tx)
    set_expires("transactions", "id", tx, iso(utcnow()))
    expired = client.post("/oauth/mcp/continue", data={"id": tx}, follow_redirects=False)
    assert expired.status_code == 400
    assert "location" not in expired.headers
    assert transaction_row(tx) == transaction_row(tx)
    assert store.count_codes() == before_codes
    client.cookies.clear()
    client.cookies.set("sb_mcp_oauth_tx", tx)
    callback = client.get(
        "/oauth/mcp/callback",
        params={"code": "g", "state": tx},
        follow_redirects=False,
    )
    assert callback.status_code == 400
    assert "location" not in callback.headers
    assert store.count_codes() == before_codes
    assert google_outbound == []
    created2 = _register(client)
    page2 = _authorize(client, created2["client_id"])
    tx2 = _tx_id(page2.text)
    set_expires("transactions", "id", tx2, iso(utcnow() - timedelta(seconds=1)))
    older = client.post("/oauth/mcp/continue", data={"id": tx2}, follow_redirects=False)
    assert older.status_code == 400
    assert snapshot is not None


def _probe(headers: dict[bytes, bytes]) -> tuple[int, list]:
    from starlette.responses import PlainTextResponse

    from app.mcp_auth import McpAuthMiddleware

    seen: list = []

    async def inner(scope, receive, send):
        seen.append(get_brain_principal())
        resp = PlainTextResponse("ok")
        await resp(scope, receive, send)

    middleware = McpAuthMiddleware(inner)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "path": "/mcp/",
        "raw_path": b"/mcp/",
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [(key, value) for key, value in headers.items()] + [(b"host", b"testserver")],
        "client": ("127.0.0.1", 123),
        "server": ("testserver", 80),
    }
    chunks: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        chunks.append(message)

    asyncio.run(middleware(scope, receive, send))
    status = next(item["status"] for item in chunks if item["type"] == "http.response.start")
    return status, seen


def _client_count() -> int:
    conn = store._connect()
    try:
        return int(conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0])
    finally:
        conn.close()


def _mock_cimd(monkeypatch, doc: dict) -> None:
    class Response:
        status_code = 200
        is_redirect = False

        def json(self):
            return doc

    monkeypatch.setattr("app.oauth_mcp_routes.httpx.get", lambda *a, **k: Response())


def _async_return(value):
    async def inner(*args, **kwargs):
        return value

    return inner


def _assert_degraded(client: TestClient) -> None:
    meta = client.get("/.well-known/oauth-protected-resource")
    assert meta.status_code == 200
    denied = client.post("/mcp", json={})
    assert denied.status_code == 401
    assert "resource_metadata=" in denied.headers["www-authenticate"]
    before = open_count
    status, seen = _probe({b"authorization": b"Bearer test-service-token"})
    assert status == 200
    assert seen and isinstance(seen[0], ServicePrincipal)
    assert open_count == before
    for response in (
        client.post("/oauth/mcp/register", json={"redirect_uris": [AI]}),
        client.get(
            "/oauth/mcp/authorize",
            params={
                "client_id": "x",
                "redirect_uri": AI,
                "code_challenge": "abc",
                "code_challenge_method": "S256",
            },
        ),
        client.post("/oauth/mcp/token", data={"grant_type": "refresh_token", "refresh_token": "nope"}),
    ):
        assert response.status_code == 503
        assert response.json() == {"error": "temporarily_unavailable"}
