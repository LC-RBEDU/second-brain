#!/usr/bin/env python3
"""
Kalendář pro MrLUC dashboard — plný primary Google Calendar (na rozdíl od RB Universe DB,
kde jsou jen schůzky s externími účastníky v Pipedrive).

Credentials (stejné jako RB Universe):
  GOOGLE_SERVICE_ACCOUNT_JSON / GOOGLE_DRIVE_SA_JSON — obsah SA klíče
  GOOGLE_CALENDAR_CREDENTIALS nebo GOOGLE_CALENDAR_JSON — cesta k .json souboru SA

Uživatel (domain-wide delegation):
  CALENDAR_USER_EMAIL (výchozí lukas@redbuttonedu.cz)

Výstup: VAULT/00-System/calendar-events.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from google_sa_json import parse_service_account_json  # noqa: E402

VAULT = Path(
    os.environ.get(
        "VAULT_PATH",
        Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC",
    )
)
OUT = Path(os.environ.get("CALENDAR_EVENTS_JSON", VAULT / "00-System/calendar-events.json"))


def _read_sa_raw() -> str | None:
    for name in ("GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_DRIVE_SA_JSON"):
        raw = (os.environ.get(name) or "").strip()
        if raw:
            return raw
    for name in ("GOOGLE_CALENDAR_CREDENTIALS", "GOOGLE_CALENDAR_JSON"):
        path = (os.environ.get(name) or "").strip()
        if not path:
            continue
        p = Path(path).expanduser()
        if p.is_file():
            return p.read_text(encoding="utf-8")
        if path.startswith("{"):
            return path
    return None


def _user_email() -> str:
    return (os.environ.get("CALENDAR_USER_EMAIL") or "lukas@redbuttonedu.cz").strip().lower()


def _days_ahead() -> int:
    try:
        return max(1, min(14, int(os.environ.get("CALENDAR_DAYS_AHEAD", "2"))))
    except ValueError:
        return 2


def calendar_window() -> tuple[date, date]:
    """Inclusive Prague date range: today .. today + (days_ahead - 1). days_ahead=2 → today + tomorrow."""
    today = datetime.now(PRAGUE).date()
    last = today + timedelta(days=_days_ahead() - 1)
    return today, last


def _event_prague_date(start_raw: str) -> date | None:
    if not start_raw:
        return None
    if len(start_raw) == 10 and start_raw[4] == "-":
        try:
            return date.fromisoformat(start_raw)
        except ValueError:
            return None
    try:
        dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=PRAGUE)
    return dt.astimezone(PRAGUE).date()


def filter_events_to_window(events: list[dict], first: date, last: date) -> list[dict]:
    out: list[dict] = []
    for ev in events:
        d = _event_prague_date((ev.get("start") or ""))
        if d is not None and first <= d <= last:
            out.append(ev)
    return out


def filter_calendar_payload(payload: dict) -> dict:
    """Drop events outside the configured Prague window (safety net for stale cache)."""
    first, last = calendar_window()
    events = filter_events_to_window(payload.get("events") or [], first, last)
    return {
        **payload,
        "events": events,
        "range": {"from": str(first), "to": str(last)},
    }


def load_cached() -> dict | None:
    if not OUT.exists():
        return None
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def fetch_from_google() -> dict:
    raw = _read_sa_raw()
    if not raw:
        raise RuntimeError(
            "Chybí SA credentials — nastav GOOGLE_SERVICE_ACCOUNT_JSON nebo GOOGLE_CALENDAR_CREDENTIALS "
            "(stejný soubor jako v RB Universe / Coolify)"
        )
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as e:
        raise RuntimeError(
            "Nainstaluj google-auth a google-api-python-client (pip install -r requirements.txt)"
        ) from e

    mailbox = _user_email()
    info = parse_service_account_json(raw)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=[CALENDAR_SCOPE]
    ).with_subject(mailbox)
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    today, end_day = calendar_window()
    start_local = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=PRAGUE)
    end_local = datetime(end_day.year, end_day.month, end_day.day, 23, 59, 59, tzinfo=PRAGUE)
    time_min = start_local.astimezone(PRAGUE).isoformat()
    time_max = end_local.astimezone(PRAGUE).isoformat()

    events: list[dict] = []
    page_token = None
    while True:
        resp = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                pageToken=page_token or "",
            )
            .execute()
        )
        for ev in resp.get("items") or []:
            if ev.get("status") == "cancelled":
                continue
            if (ev.get("visibility") or "").lower() == "private":
                continue
            start_raw = (ev.get("start") or {}).get("dateTime") or (ev.get("start") or {}).get("date")
            end_raw = (ev.get("end") or {}).get("dateTime") or (ev.get("end") or {}).get("date")
            if not start_raw:
                continue
            all_day = "date" in (ev.get("start") or {}) and "dateTime" not in (ev.get("start") or {})
            events.append(
                {
                    "id": ev.get("id"),
                    "title": (ev.get("summary") or "").strip() or "(bez názvu)",
                    "start": start_raw,
                    "end": end_raw,
                    "allDay": all_day,
                    "location": (ev.get("location") or "").strip() or None,
                    "htmlLink": ev.get("htmlLink"),
                }
            )
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    events = filter_events_to_window(events, today, end_day)

    return {
        "source": "google_api",
        "user": mailbox,
        "generated": datetime.now(PRAGUE).isoformat(timespec="seconds"),
        "range": {"from": str(today), "to": str(end_day)},
        "events": events,
    }


def refresh(force: bool = False) -> dict:
    if not force and OUT.exists():
        try:
            cached = json.loads(OUT.read_text(encoding="utf-8"))
            gen = cached.get("generated", "")[:10]
            if gen == str(date.today()):
                return filter_calendar_payload(cached)
        except json.JSONDecodeError:
            pass
    try:
        payload = fetch_from_google()
    except Exception as e:
        cached = load_cached()
        if cached:
            cached = filter_calendar_payload(cached)
            cached["source"] = "cache_stale"
            cached["fetchError"] = str(e)
            return cached
        return {
            "source": "none",
            "user": _user_email(),
            "generated": datetime.now(PRAGUE).isoformat(timespec="seconds"),
            "events": [],
            "fetchError": str(e),
        }
    payload = filter_calendar_payload(payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    force = "--force" in sys.argv
    data = refresh(force=force)
    n = len(data.get("events") or [])
    print("calendar", OUT, "events=", n, "source=", data.get("source"))
    if data.get("fetchError"):
        print("warning:", data["fetchError"], file=sys.stderr)


if __name__ == "__main__":
    main()
