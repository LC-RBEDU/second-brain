"""Claude MCP OAuth: DCR, CIMD, consent, Google callback, token. Loopback is refused."""
from __future__ import annotations

import html
import json
import time
from typing import Annotated, Any, Callable
from urllib.parse import unquote, urlencode, urlparse

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from app.auth_google import authorize_url, email_allowed, load_oauth_config
from app.oauth_mcp_metadata import public_base
from app.oauth_routes import _cookie_secure
from app import oauth_mcp_store as store

router = APIRouter(tags=["oauth-mcp"])

REDIRECTS = (
    "https://claude.ai/api/mcp/auth_callback",
    "https://claude.com/api/mcp/auth_callback",
)
TX_COOKIE = "sb_mcp_oauth_tx"
SCOPES = ("brain:read", "brain:write")
google_outbound: list[str] = []
_cimd_cache: dict[str, tuple[float, dict[str, Any]]] = {}
CIMD_TTL = 300.0
CIMD_MAX_BYTES = 32_768


def reset_routes() -> None:
    google_outbound.clear()
    _cimd_cache.clear()


def mcp_callback_url() -> str:
    return f"{public_base()}/oauth/mcp/callback"


def _unavailable() -> JSONResponse:
    return JSONResponse({"error": "temporarily_unavailable"}, status_code=503)


def _oauth_error(error: str, status: int = 400) -> JSONResponse:
    return JSONResponse({"error": error}, status_code=status)


def _guard(fn: Callable[[], Response]) -> Response:
    try:
        return fn()
    except store.OAuthUnavailable:
        return _unavailable()


def _scope_list(raw: str | None, *, default_both: bool) -> str | None:
    if raw is None or not str(raw).strip():
        return "brain:read brain:write" if default_both else ""
    parts = [part for part in str(raw).split() if part != "offline_access"]
    if not parts:
        return "brain:read brain:write" if default_both else ""
    if any(part not in SCOPES for part in parts):
        return None
    return " ".join(scope for scope in SCOPES if scope in parts)


def _subset(requested: str, grant: str) -> bool:
    return set(requested.split()) <= set(grant.split())


def _norm_resource(value: str) -> tuple[str, str, str]:
    parsed = urlparse(value.strip())
    return (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"))


def resource_matches(presented: str | None) -> bool:
    if presented is None or not str(presented).strip():
        return True
    from app.oauth_mcp_metadata import resource_url

    return _norm_resource(presented) == _norm_resource(resource_url())


def _decode(value: str | None) -> str | None:
    if value is None:
        return None
    return unquote(value)


def _redirect_decision(stored: str, body: str | None, query: str | None) -> bool:
    if body is None and query is None:
        return True
    if body is not None and query is None:
        return body == stored
    if query is not None and body is None:
        return query == stored
    return body == stored and query == stored and body == query


def _client_name_from(doc: dict[str, Any], fallback: str) -> str:
    name = doc.get("client_name")
    return str(name) if name else fallback


async def exchange_google(code: str, redirect_uri: str) -> tuple[int, str | None]:
    cfg = load_oauth_config()
    google_outbound.append("oauth2.googleapis.com")
    async with httpx.AsyncClient(timeout=20) as client:
        token = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": cfg.client_id,
                "client_secret": cfg.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token.status_code != 200:
            return token.status_code, None
        access = token.json().get("access_token")
        if not access:
            return 400, None
        google_outbound.append("www.googleapis.com")
        info = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access}"},
        )
        if info.status_code != 200:
            return info.status_code, None
        email = str(info.json().get("email") or "").strip().lower()
        return 200, email or None


def fetch_cimd_bytes(url: str) -> bytes | None:
    """Stop reading once the document exceeds the cap. Oversized bytes are not kept."""
    try:
        with httpx.stream("GET", url, timeout=3, follow_redirects=False) as response:
            if response.is_redirect or response.status_code != 200:
                return None
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > CIMD_MAX_BYTES:
                    return None
                chunks.append(chunk)
            return b"".join(chunks)
    except httpx.HTTPError:
        return None


def _load_cimd(url: str) -> dict[str, Any] | None:
    host = (urlparse(url).hostname or "").lower()
    if host not in {"claude.ai", "claude.com"}:
        return None
    cached = _cimd_cache.get(url)
    now = time.monotonic()
    if cached and now - cached[0] < CIMD_TTL:
        return cached[1]
    raw = fetch_cimd_bytes(url)
    if not raw or len(raw) > CIMD_MAX_BYTES:
        return None
    try:
        doc = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(doc, dict) or doc.get("client_id") != url:
        return None
    _cimd_cache[url] = (now, doc)
    return doc


def _resolve_client(client_id: str) -> dict[str, Any] | None:
    if client_id.startswith("https://claude.ai/") or client_id.startswith("https://claude.com/"):
        doc = _load_cimd(client_id)
        if doc is None:
            return None
        uris = doc.get("redirect_uris") or []
        if not isinstance(uris, list):
            return None
        return {
            "client_id": client_id,
            "client_name": _client_name_from(doc, "Claude"),
            "redirect_uris": [str(item) for item in uris],
        }
    row = store.get_client(client_id)
    return row


def _scope_label(scope: str) -> str:
    parts = scope.split()
    labels = []
    if "brain:read" in parts:
        labels.append("čtení")
    if "brain:write" in parts:
        labels.append("zápis")
    return " a ".join(labels) if labels else scope


def _page(*, title: str, lead: str, body: str) -> str:
    """RB EDU card. One consent submit stays the only <button> in the document."""
    return f"""<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='4' fill='%23e9244a'/%3E%3C/svg%3E">
<title>{html.escape(title, quote=True)}</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh; display: grid; place-items: center;
    padding: 24px; background: #f4f4f5; color: #3c3c3d;
    font-family: "Plus Jakarta Sans", Arial, sans-serif;
  }}
  .card {{
    width: min(440px, 100%); background: #fff; border-radius: 16px;
    padding: 32px 28px; box-shadow: 0 12px 40px rgba(60, 60, 61, .08);
  }}
  .mark {{ display: flex; align-items: center; gap: 10px; font-weight: 800; letter-spacing: -.03em; }}
  .dot {{ width: 14px; height: 14px; border-radius: 4px; background: #e9244a; }}
  h1 {{ margin: 22px 0 8px; font-size: 26px; line-height: 1.2; font-weight: 800; letter-spacing: -.03em; }}
  .lead {{ margin: 0 0 22px; color: #5c5c5e; font-size: 15px; line-height: 1.45; }}
  dl {{ margin: 0 0 24px; }}
  .row {{
    display: flex; justify-content: space-between; gap: 16px;
    padding: 12px 0; border-top: 1px solid #ebeced; font-size: 14px;
  }}
  dt {{ color: #5c5c5e; }}
  dd {{ margin: 0; font-weight: 700; text-align: right; }}
  .raw {{ display: block; margin-top: 2px; color: #5c5c5e; font-weight: 500; font-size: 12px; }}
  button {{
    width: 100%; border: 0; background: #e9244a; color: #fff; cursor: pointer;
    font: 700 15px/1 "Plus Jakarta Sans", Arial, sans-serif;
    padding: 14px 18px; border-radius: 12px;
  }}
  button:hover {{ background: #c41e3d; }}
  button:focus-visible {{ outline: 2px solid #3c3c3d; outline-offset: 3px; }}
  .cancel {{ display: block; margin-top: 14px; text-align: center; color: #5c5c5e; font-size: 14px; }}
  .state {{ margin: 22px 0 0; color: #5c5c5e; font-size: 12px; line-height: 1.4; word-break: break-all; }}
  @media (prefers-reduced-motion: reduce) {{ button {{ transition: none; }} }}
</style>
</head>
<body>
<main class="card">
  <div class="mark"><span class="dot"></span>RB EDU</div>
  <h1>{html.escape(title, quote=True)}</h1>
  <p class="lead">{html.escape(lead, quote=True)}</p>
  {body}
</main>
</body>
</html>"""


def _consent_html(*, name: str, scope: str, redirect_uri: str, state: str, tx_id: str) -> str:
    host = urlparse(redirect_uri).hostname or ""
    body = (
        "<dl>"
        f'<div class="row"><dt>Kdo</dt><dd>{html.escape(name, quote=True)}</dd></div>'
        f'<div class="row"><dt>Oprávnění</dt><dd>{html.escape(_scope_label(scope), quote=True)}'
        f'<span class="raw">{html.escape(scope, quote=True)}</span></dd></div>'
        f'<div class="row"><dt>Návrat</dt><dd>{html.escape(host, quote=True)}</dd></div>'
        "</dl>"
        '<form method="post" action="/oauth/mcp/continue">'
        f'<input type="hidden" name="id" value="{html.escape(tx_id, quote=True)}">'
        '<button type="submit">Pokračovat</button>'
        "</form>"
        '<a class="cancel" href="/oauth/mcp/cancelled">Zrušit</a>'
        f'<p class="state">Kód žádosti {html.escape(state, quote=True)}</p>'
    )
    return _page(title="Připojení k Second Brain", lead="Claude žádá o přístup. Pokračování jde na Google.", body=body)


@router.get("/oauth/mcp/cancelled")
def oauth_mcp_cancelled() -> HTMLResponse:
    return HTMLResponse(
        _page(title="Zrušeno", lead="Přihlášení je zrušeno. Klient nedostal přístup.", body="")
    )


@router.post("/oauth/mcp/register")
async def oauth_mcp_register(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return _oauth_error("invalid_request")
    if not isinstance(payload, dict):
        return _oauth_error("invalid_request")

    def run() -> JSONResponse:
        method = payload.get("token_endpoint_auth_method", "none")
        if method != "none":
            return _oauth_error("invalid_client")
        uris = payload.get("redirect_uris")
        if not isinstance(uris, list) or not uris:
            return _oauth_error("invalid_request")
        cleaned = [str(item) for item in uris]
        if any(item not in REDIRECTS for item in cleaned):
            return _oauth_error("invalid_request")
        name = str(payload.get("client_name") or "Claude")
        client_id = store.insert_client(name, cleaned)
        return JSONResponse(
            {"client_id": client_id, "token_endpoint_auth_method": "none"},
            status_code=201,
        )

    return _guard(run)


@router.get("/oauth/mcp/authorize")
def oauth_mcp_authorize(request: Request) -> Response:
    def run() -> Response:
        params = request.query_params
        client_id = params.get("client_id") or ""
        redirect_uri = params.get("redirect_uri") or ""
        state = params.get("state") or ""
        challenge = params.get("code_challenge") or ""
        method = params.get("code_challenge_method") or ""
        if method != "S256" or not challenge:
            return _oauth_error("invalid_request")
        if not resource_matches(params.get("resource")):
            return _oauth_error("invalid_target")
        client = _resolve_client(client_id)
        if client is None:
            return _oauth_error("invalid_client")
        if redirect_uri not in REDIRECTS or redirect_uri not in client["redirect_uris"]:
            return _oauth_error("invalid_request")
        scope = _scope_list(params.get("scope"), default_both=True)
        if scope is None:
            return _oauth_error("invalid_scope")
        tx_id = store.insert_transaction(
            client_id=client_id,
            client_name=client["client_name"],
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=challenge,
            state=state,
            resource=params.get("resource"),
        )
        return HTMLResponse(
            _consent_html(
                name=client["client_name"],
                scope=scope,
                redirect_uri=redirect_uri,
                state=state,
                tx_id=tx_id,
            )
        )

    return _guard(run)


def _stop() -> JSONResponse:
    return JSONResponse({"error": "invalid_request"}, status_code=400)


def _clear_tx_cookie(response: Response) -> None:
    """Match set_cookie, including Secure on HTTPS, or the browser keeps the cookie."""
    response.delete_cookie(
        TX_COOKIE,
        path="/",
        secure=_cookie_secure(public_base()),
        httponly=True,
        samesite="lax",
    )


@router.post("/oauth/mcp/continue")
def oauth_mcp_continue(
    request: Request,
    id: Annotated[str, Form()] = "",
    redirect_uri: Annotated[str | None, Form()] = None,
) -> Response:
    def run() -> Response:
        row = store.transaction_row(id) if id else None
        if row is None or store.is_expired(row[8]):
            return _stop()
        body = _decode(redirect_uri)
        query = _decode(request.query_params.get("redirect_uri"))
        if not _redirect_decision(row[3], body, query):
            return _stop()
        cfg = load_oauth_config()
        if not cfg.client_id or not cfg.public_url:
            return _oauth_error("invalid_request")
        location = authorize_url(
            client_id=cfg.client_id,
            redirect_uri=mcp_callback_url(),
            state=id,
        )
        response = RedirectResponse(location, status_code=302)
        response.set_cookie(
            TX_COOKIE,
            id,
            httponly=True,
            samesite="lax",
            secure=_cookie_secure(cfg.public_url),
            max_age=600,
        )
        return response

    return _guard(run)


@router.get("/oauth/mcp/callback")
async def oauth_mcp_callback(request: Request) -> Response:
    state = request.query_params.get("state") or ""
    cookie = request.cookies.get(TX_COOKIE)
    if not cookie or cookie != state:
        return JSONResponse({"error": "invalid_request"}, status_code=400)
    try:
        row = store.transaction_row(state)
    except store.OAuthUnavailable:
        return _unavailable()
    if row is None or store.is_expired(row[8]):
        return JSONResponse({"error": "invalid_request"}, status_code=400)
    status, email = await exchange_google(request.query_params.get("code") or "", mcp_callback_url())
    if status != 200 or not email:
        return JSONResponse({"error": "invalid_grant"}, status_code=400)
    redirect_uri = row[3]
    client_state = row[6]
    if not email_allowed(email):
        target = redirect_uri + "?" + urlencode({"error": "access_denied", "state": client_state})
        response = HTMLResponse(
            _page(
                title="Přístup zamítnut",
                lead="Tenhle Google účet k Second Brain přístup nemá.",
                body="<p>přístup zamítnut</p>",
            ),
            status_code=302,
        )
        response.headers["location"] = target
        _clear_tx_cookie(response)
        return response
    try:
        raw = store.issue_code(
            email=email,
            client_id=row[1],
            client_name=row[2],
            redirect_uri=redirect_uri,
            scope=row[4],
            code_challenge=row[5],
        )
    except store.OAuthUnavailable:
        return _unavailable()
    target = redirect_uri + "?" + urlencode({"code": raw, "state": client_state})
    response = RedirectResponse(target, status_code=302)
    _clear_tx_cookie(response)
    return response


def complete_token(
    form: dict[str, str | None],
    *,
    hold: Callable[[], None] | None = None,
    on_wait: Callable[[], None] | None = None,
) -> JSONResponse:
    if form.get("client_secret"):
        return _oauth_error("invalid_client")
    grant = form.get("grant_type") or ""
    if not resource_matches(form.get("resource")):
        return _oauth_error("invalid_target")
    if grant == "authorization_code":
        code = form.get("code") or ""
        verifier = form.get("code_verifier") or ""
        if not code or not verifier:
            return _oauth_error("invalid_request")
        body = store.redeem_code(code, verifier, hold=hold)
        if "error" in body:
            return _oauth_error(str(body["error"]))
        return JSONResponse(body)
    if grant == "refresh_token":
        raw = form.get("refresh_token") or ""
        if not raw:
            return _oauth_error("invalid_request")
        presented = form["scope"] if "scope" in form else None
        parsed = _scope_list(presented, default_both=False)
        if parsed is None:
            return _oauth_error("invalid_scope")
        current = store.refresh_grant_scope(raw)
        if current is None:
            return _oauth_error("invalid_grant")
        scope = current if parsed == "" else parsed
        if not _subset(scope, current):
            return _oauth_error("invalid_scope")
        body = store.rotate_refresh(raw, scope, hold=hold, on_wait=on_wait)
        if "error" in body:
            return _oauth_error(str(body["error"]))
        return JSONResponse(body)
    if grant:
        return _oauth_error("unsupported_grant_type")
    return _oauth_error("invalid_request")


@router.post("/oauth/mcp/token")
def oauth_mcp_token(
    grant_type: Annotated[str, Form()] = "",
    code: Annotated[str | None, Form()] = None,
    code_verifier: Annotated[str | None, Form()] = None,
    refresh_token: Annotated[str | None, Form()] = None,
    scope: Annotated[str | None, Form()] = None,
    resource: Annotated[str | None, Form()] = None,
    client_secret: Annotated[str | None, Form()] = None,
) -> JSONResponse:
    form: dict[str, str | None] = {
        "grant_type": grant_type,
        "code": code,
        "code_verifier": code_verifier,
        "refresh_token": refresh_token,
        "resource": resource,
        "client_secret": client_secret,
    }
    if scope is not None:
        form["scope"] = scope
    try:
        return complete_token(form)
    except store.OAuthUnavailable:
        return _unavailable()
