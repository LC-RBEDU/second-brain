"""SQLite for Claude MCP OAuth. One connection per call. Import does not open the file."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

PEPPER_ENV = "BRAIN_OAUTH_TOKEN_PEPPER"
DB_ENV = "BRAIN_OAUTH_DB"
DEFAULT_DB = "/data/oauth/brain-oauth.sqlite"

ACCESS_TTL = timedelta(hours=1)
REFRESH_TTL = timedelta(days=30)
CODE_TTL = timedelta(seconds=60)
TX_TTL = timedelta(minutes=10)
FAMILY_TTL = timedelta(days=90)

open_count = 0
_registry = threading.Lock()
_refresh_locks: dict[str, threading.Lock] = {}


class OAuthUnavailable(Exception):
    """Pepper missing, path in the vault, or the file cannot be opened."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def is_expired(expires_at: str, now: datetime | None = None) -> bool:
    """expires_at <= now, including equality. Not an age-in-minutes check."""
    current = now or utcnow()
    return parse_time(expires_at) <= current


def db_path() -> Path:
    raw = (os.environ.get(DB_ENV) or DEFAULT_DB).strip() or DEFAULT_DB
    return Path(raw)


def _path_in_vault(path: Path) -> bool:
    try:
        real = path.resolve()
    except OSError:
        real = path
    vault_roots = [Path("/data/vault")]
    git_root = (os.environ.get("GIT_VAULT_ROOT") or "").strip()
    if git_root:
        vault_roots.append(Path(git_root))
    for root in vault_roots:
        try:
            real.relative_to(root.resolve())
        except ValueError:
            continue
        else:
            return True
    text = str(real)
    return text == "/data/vault" or text.startswith("/data/vault/")


def _pepper() -> bytes:
    pepper = (os.environ.get(PEPPER_ENV) or "").strip()
    if not pepper:
        raise OAuthUnavailable("pepper")
    return pepper.encode()


def token_hash(raw: str) -> str:
    return hmac.new(_pepper(), raw.encode(), hashlib.sha256).hexdigest()


def _connect() -> sqlite3.Connection:
    global open_count
    path = db_path()
    if _path_in_vault(path):
        raise OAuthUnavailable("vault")
    if not (os.environ.get(PEPPER_ENV) or "").strip():
        raise OAuthUnavailable("pepper")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, timeout=5)
    except OSError as exc:
        raise OAuthUnavailable("open") from exc
    open_count += 1
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS clients (
            client_id TEXT PRIMARY KEY,
            client_name TEXT NOT NULL,
            redirect_uris TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            client_name TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            scope TEXT NOT NULL,
            code_challenge TEXT NOT NULL,
            state TEXT NOT NULL,
            resource TEXT,
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS codes (
            code_hash TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            family_id TEXT NOT NULL,
            scope TEXT NOT NULL,
            client_id TEXT NOT NULL,
            client_name TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            code_challenge TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used_at TEXT
        );
        CREATE TABLE IF NOT EXISTS families (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            client_id TEXT NOT NULL,
            client_name TEXT NOT NULL,
            scope TEXT NOT NULL,
            created_at TEXT NOT NULL,
            absolute_expires_at TEXT NOT NULL,
            revoked_at TEXT
        );
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token_hash TEXT PRIMARY KEY,
            family_id TEXT NOT NULL,
            status TEXT NOT NULL,
            successor_hash TEXT,
            expires_at TEXT NOT NULL,
            rotated_at TEXT,
            scope TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS access_tokens (
            token_hash TEXT PRIMARY KEY,
            family_id TEXT NOT NULL,
            email TEXT NOT NULL,
            scope TEXT NOT NULL,
            client_id TEXT NOT NULL,
            client_name TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );
        """
    )


def reset_runtime() -> None:
    """Test helper. Does not delete the sqlite file."""
    global open_count
    open_count = 0
    with _registry:
        _refresh_locks.clear()


def _refresh_lock(token_hash_value: str) -> threading.Lock:
    with _registry:
        lock = _refresh_locks.get(token_hash_value)
        if lock is None:
            lock = threading.Lock()
            _refresh_locks[token_hash_value] = lock
        return lock


def insert_client(name: str, redirect_uris: list[str]) -> str:
    import json

    client_id = secrets.token_urlsafe(24)
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "INSERT INTO clients (client_id, client_name, redirect_uris) VALUES (?, ?, ?)",
            (client_id, name, json.dumps(redirect_uris)),
        )
        conn.commit()
    finally:
        conn.close()
    return client_id


def get_client(client_id: str) -> dict[str, Any] | None:
    import json

    conn = _connect()
    try:
        row = conn.execute(
            "SELECT client_id, client_name, redirect_uris FROM clients WHERE client_id = ?",
            (client_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {
        "client_id": row["client_id"],
        "client_name": row["client_name"],
        "redirect_uris": json.loads(row["redirect_uris"]),
    }


def insert_transaction(
    *,
    client_id: str,
    client_name: str,
    redirect_uri: str,
    scope: str,
    code_challenge: str,
    state: str,
    resource: str | None,
) -> str:
    tx_id = secrets.token_urlsafe(24)
    expires = iso(utcnow() + TX_TTL)
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO transactions (
                id, client_id, client_name, redirect_uri, scope, code_challenge,
                state, resource, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tx_id,
                client_id,
                client_name,
                redirect_uri,
                scope,
                code_challenge,
                state,
                resource,
                expires,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return tx_id


def transaction_row(tx_id: str) -> tuple[Any, ...] | None:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return tuple(row)


def count_codes() -> int:
    conn = _connect()
    try:
        return int(conn.execute("SELECT COUNT(*) FROM codes").fetchone()[0])
    finally:
        conn.close()


def count_transactions() -> int:
    conn = _connect()
    try:
        return int(conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0])
    finally:
        conn.close()


@dataclass(frozen=True)
class AccessRecord:
    email: str
    scope: str
    client_name: str
    expired: bool
    revoked: bool


def read_access(raw: str) -> AccessRecord | None:
    try:
        digest = token_hash(raw)
    except OAuthUnavailable:
        raise
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT a.email, a.scope, a.client_name, a.expires_at, f.revoked_at
            FROM access_tokens a
            JOIN families f ON f.id = a.family_id
            WHERE a.token_hash = ?
            """,
            (digest,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return AccessRecord(
        email=row["email"],
        scope=row["scope"],
        client_name=row["client_name"],
        expired=is_expired(row["expires_at"]),
        revoked=bool(row["revoked_at"]),
    )


def issue_code(
    *,
    email: str,
    client_id: str,
    client_name: str,
    redirect_uri: str,
    scope: str,
    code_challenge: str,
) -> str:
    raw = secrets.token_urlsafe(32)
    family_id = secrets.token_urlsafe(18)
    now = utcnow()
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT INTO families (
                id, email, client_id, client_name, scope, created_at, absolute_expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                family_id,
                email,
                client_id,
                client_name,
                scope,
                iso(now),
                iso(now + FAMILY_TTL),
            ),
        )
        conn.execute(
            """
            INSERT INTO codes (
                code_hash, email, family_id, scope, client_id, client_name,
                redirect_uri, code_challenge, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token_hash(raw),
                email,
                family_id,
                scope,
                client_id,
                client_name,
                redirect_uri,
                code_challenge,
                iso(now + CODE_TTL),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return raw


def _insert_pair(
    conn: sqlite3.Connection,
    *,
    family_id: str,
    email: str,
    scope: str,
    client_id: str,
    client_name: str,
    now: datetime,
) -> dict[str, Any]:
    access = secrets.token_urlsafe(32)
    refresh = secrets.token_urlsafe(32)
    conn.execute(
        """
        INSERT INTO access_tokens (
            token_hash, family_id, email, scope, client_id, client_name, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            token_hash(access),
            family_id,
            email,
            scope,
            client_id,
            client_name,
            iso(now + ACCESS_TTL),
        ),
    )
    conn.execute(
        """
        INSERT INTO refresh_tokens (
            token_hash, family_id, status, expires_at, scope
        ) VALUES (?, ?, 'active', ?, ?)
        """,
        (token_hash(refresh), family_id, iso(now + REFRESH_TTL), scope),
    )
    return _token_body(access, refresh, scope)


def _token_body(access: str, refresh: str, scope: str) -> dict[str, Any]:
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": int(ACCESS_TTL.total_seconds()),
        "refresh_token": refresh,
        "scope": scope,
    }


def redeem_code(raw_code: str, verifier: str, *, hold: Callable[[], None] | None = None) -> dict[str, Any]:
    """PKCE and one-time use inside one IMMEDIATE transaction."""
    import base64
    import hashlib as hl

    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM codes WHERE code_hash = ?",
            (token_hash(raw_code),),
        ).fetchone()
        if row is None or row["used_at"] or is_expired(row["expires_at"]):
            conn.rollback()
            return {"error": "invalid_grant"}
        if not hmac.compare_digest(challenge, row["code_challenge"]):
            conn.rollback()
            return {"error": "invalid_grant"}
        if hold is not None:
            hold()
        cur = conn.execute(
            "UPDATE codes SET used_at = ? WHERE code_hash = ? AND used_at IS NULL",
            (iso(utcnow()), row["code_hash"]),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return {"error": "invalid_grant"}
        family = conn.execute(
            "SELECT * FROM families WHERE id = ?",
            (row["family_id"],),
        ).fetchone()
        if family is None or family["revoked_at"] or is_expired(family["absolute_expires_at"]):
            conn.rollback()
            return {"error": "invalid_grant"}
        body = _insert_pair(
            conn,
            family_id=row["family_id"],
            email=row["email"],
            scope=row["scope"],
            client_id=row["client_id"],
            client_name=row["client_name"],
            now=utcnow(),
        )
        conn.commit()
        return body
    finally:
        conn.close()


def code_used_at(raw_code: str) -> str | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT used_at FROM codes WHERE code_hash = ?",
            (token_hash(raw_code),),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return row["used_at"]


def rotate_refresh(
    raw: str,
    scope: str,
    *,
    hold: Callable[[], None] | None = None,
    on_wait: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Sync refresh. waited loser keeps the family; a later replay revokes it."""
    digest = token_hash(raw)
    lock = _refresh_lock(digest)
    waited = not lock.acquire(blocking=False)
    if waited:
        if on_wait is not None:
            on_wait()
        lock.acquire()
    try:
        return _rotate_locked(digest, scope, waited=waited, hold=hold)
    finally:
        lock.release()


def _rotate_locked(
    digest: str,
    scope: str,
    *,
    waited: bool,
    hold: Callable[[], None] | None,
) -> dict[str, Any]:
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM refresh_tokens WHERE token_hash = ?",
            (digest,),
        ).fetchone()
        if row is None:
            conn.rollback()
            return {"error": "invalid_grant"}
        family = conn.execute(
            "SELECT * FROM families WHERE id = ?",
            (row["family_id"],),
        ).fetchone()
        dead = (
            family is None
            or bool(family["revoked_at"])
            or is_expired(family["absolute_expires_at"])
            or is_expired(row["expires_at"])
        )
        if dead:
            conn.rollback()
            return {"error": "invalid_grant"}
        if row["status"] == "active":
            now = utcnow()
            body = _insert_pair(
                conn,
                family_id=row["family_id"],
                email=family["email"],
                scope=scope,
                client_id=family["client_id"],
                client_name=family["client_name"],
                now=now,
            )
            conn.execute(
                """
                UPDATE refresh_tokens
                SET status = 'rotated', successor_hash = ?, rotated_at = ?
                WHERE token_hash = ?
                """,
                (token_hash(body["refresh_token"]), iso(now), digest),
            )
            conn.commit()
            if hold is not None and not waited:
                hold()
            return body
        if waited:
            conn.rollback()
            return {"error": "invalid_grant"}
        conn.execute(
            "UPDATE families SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL",
            (iso(utcnow()), row["family_id"]),
        )
        conn.commit()
        return {"error": "invalid_grant"}
    finally:
        conn.close()


def family_revoked(family_id: str) -> bool:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT revoked_at FROM families WHERE id = ?",
            (family_id,),
        ).fetchone()
    finally:
        conn.close()
    return bool(row and row["revoked_at"])


def refresh_grant_scope(raw: str) -> str | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT scope FROM refresh_tokens WHERE token_hash = ?",
            (token_hash(raw),),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return row["scope"]


def family_id_for_refresh(raw: str) -> str | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT family_id FROM refresh_tokens WHERE token_hash = ?",
            (token_hash(raw),),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return row["family_id"]


def revoke(*, email: str | None = None, family_id: str | None = None) -> int:
    now = iso(utcnow())
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if family_id:
            cur = conn.execute(
                "UPDATE families SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL",
                (now, family_id),
            )
        else:
            cur = conn.execute(
                "UPDATE families SET revoked_at = ? WHERE email = ? AND revoked_at IS NULL",
                (now, (email or "").strip().lower()),
            )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def set_expires(table: str, key_col: str, key: str, expires_at: str) -> None:
    allowed = {
        "transactions": "id",
        "codes": "code_hash",
        "access_tokens": "token_hash",
        "refresh_tokens": "token_hash",
        "families": "id",
    }
    if allowed.get(table) != key_col:
        raise ValueError(table)
    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if table == "families":
            conn.execute(
                f"UPDATE families SET absolute_expires_at = ? WHERE id = ?",
                (expires_at, key),
            )
        else:
            conn.execute(
                f"UPDATE {table} SET expires_at = ? WHERE {key_col} = ?",
                (expires_at, key),
            )
        conn.commit()
    finally:
        conn.close()
