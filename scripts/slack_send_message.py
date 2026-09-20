#!/usr/bin/env python3
"""Send a Slack message as Lukáš, with optional file attachments.

Reads a user token (xoxp-) from $SLACK_USER_TOKEN or ~/.config/second-brain/slack.env.
Does not touch the login keychain or Slack desktop cookies. Never prints the token.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_FILE = Path.home() / ".config" / "second-brain" / "slack.env"


def _die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def load_token() -> str:
    token = (os.environ.get("SLACK_USER_TOKEN") or "").strip()
    if not token and TOKEN_FILE.exists():
        for line in TOKEN_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "SLACK_USER_TOKEN":
                token = value.strip().strip("'\"")
                break
    if not token:
        _die(
            "Chybí SLACK_USER_TOKEN. User OAuth Token (xoxp-) patří do "
            f"{TOKEN_FILE} — ne do chatu a ne do login keychain.",
            2,
        )
    if token.startswith("xoxb-"):
        _die("Tohle je bot token (xoxb-). Na zprávu jako Lukáš je user token (xoxp-).", 2)
    return token


def api(token: str, method: str, payload: dict) -> dict:
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        _die(f"Slack {method} HTTP {exc.code}")
    except urllib.error.URLError as exc:
        _die(f"Slack {method} síť: {exc.reason}")
    if not body.get("ok"):
        _die(f"Slack {method}: {body.get('error') or 'unknown_error'}")
    return body


def resolve_channel(token: str, channel: str | None, emails: list[str]) -> str:
    if channel:
        return channel
    if not emails:
        _die("Zadej --channel nebo --emails.")
    ids = []
    for email in emails:
        body = api(token, "users.lookupByEmail", {"email": email})
        user = body.get("user") or {}
        user_id = user.get("id")
        if not user_id:
            _die(f"Slack nenašel {email}")
        name = user.get("real_name") or user.get("name") or email
        print(f"recipient {name} {email}")
        ids.append(user_id)
    opened = api(token, "conversations.open", {"users": ",".join(ids)})
    channel_id = (opened.get("channel") or {}).get("id")
    if not channel_id:
        _die("conversations.open nevrátil kanál")
    return channel_id


def upload_files(token: str, channel: str, paths: list[Path], text: str) -> None:
    staged = []
    for path in paths:
        data = path.read_bytes()
        up = api(
            token,
            "files.getUploadURLExternal",
            {"filename": path.name, "length": str(len(data))},
        )
        req = urllib.request.Request(up["upload_url"], data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp.read()
        except urllib.error.HTTPError as exc:
            _die(f"upload {path.name} HTTP {exc.code}")
        staged.append({"id": up["file_id"], "title": path.name})
        print(f"staged {path.name}")
    payload = {
        "files": json.dumps(staged),
        "channel_id": channel,
        "initial_comment": text,
    }
    done = api(token, "files.completeUploadExternal", payload)
    for item in done.get("files") or []:
        link = item.get("permalink")
        if link:
            print(f"permalink {link}")


def post_text(token: str, channel: str, text: str) -> None:
    body = api(token, "chat.postMessage", {"channel": channel, "text": text, "unfurl_links": "false"})
    print(f"ts {body.get('ts')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pošli Slack zprávu jako Lukáš (user token).")
    parser.add_argument("--channel", help="Channel ID (C… / G… / D…). Jinak DM z --emails.")
    parser.add_argument("--emails", help="Čárkou oddělené e-maily účastníků, bez odesílatele.")
    parser.add_argument("--text", help="Text zprávy.")
    parser.add_argument("--text-file", type=Path, help="Soubor s textem zprávy.")
    parser.add_argument("--file", action="append", type=Path, default=[], help="Příloha, lze víckrát.")
    parser.add_argument("--dry-run", action="store_true", help="Jen auth + adresáti, nic neposílat.")
    args = parser.parse_args()

    text = args.text or ""
    if args.text_file:
        text = args.text_file.read_text()
    text = text.strip("\n")
    if not text:
        _die("Chybí text (--text nebo --text-file).")
    for path in args.file:
        if not path.is_file():
            _die(f"Příloha neexistuje: {path}")

    token = load_token()
    auth = api(token, "auth.test", {})
    print(f"from {auth.get('user')} team {auth.get('team')}")
    emails = [item.strip() for item in (args.emails or "").split(",") if item.strip()]
    channel = resolve_channel(token, args.channel, emails)
    print(f"channel {channel}")
    if args.dry_run:
        print("dry-run")
        return
    if args.file:
        upload_files(token, channel, args.file, text)
    else:
        post_text(token, channel, text)
    print("sent_ok")


if __name__ == "__main__":
    main()
