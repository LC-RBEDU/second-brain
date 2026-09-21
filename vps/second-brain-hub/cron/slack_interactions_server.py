#!/usr/bin/env python3
"""HTTP target for the Slack Odpověz button. Cron stays the main process."""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from slack_client import SlackAPIError, post_message  # noqa: E402
from slack_interactions import parse_interaction, reply_from_action, verify_slack_signature  # noqa: E402


def _ack(handler: BaseHTTPRequestHandler, code: int, body: bytes = b"") -> None:
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    if body:
        handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write("slack_interactions: " + (fmt % args) + "\n")

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/slack/interactions":
            _ack(self, 404, b"{}")
            return
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length)
        secret = (os.environ.get("SLACK_SIGNING_SECRET") or "").strip()
        ok = verify_slack_signature(
            secret,
            self.headers.get("X-Slack-Request-Timestamp") or "",
            body,
            self.headers.get("X-Slack-Signature") or "",
        )
        if not ok:
            _ack(self, 401, b"{}")
            return
        try:
            payload = parse_interaction(body)
        except json.JSONDecodeError:
            _ack(self, 400, b"{}")
            return
        if payload.get("type") == "url_verification":
            challenge = json.dumps({"challenge": payload.get("challenge", "")}).encode()
            _ack(self, 200, challenge)
            return
        reply = reply_from_action(payload)
        if reply is None:
            _ack(self, 200, b"{}")
            return
        channel, thread_ts, text = reply
        token = (os.environ.get("SLACK_USER_TOKEN") or "").strip()
        if not token:
            _ack(self, 500, b"{}")
            return
        # Ack Slack before the post so the button does not time out.
        _ack(self, 200, b"{}")
        try:
            post_message(token, channel, text, thread_ts=thread_ts)
        except SlackAPIError as exc:
            print(f"slack_interactions: post failed: {exc}")
            return
        response_url = str(payload.get("response_url") or "")
        if response_url:
            _replace_card(response_url)


def _replace_card(response_url: str) -> None:
    import urllib.request

    data = json.dumps(
        {"replace_original": True, "text": "Odesláno."}
    ).encode("utf-8")
    req = urllib.request.Request(
        response_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as exc:  # noqa: BLE001
        print(f"slack_interactions: card update failed: {exc}")


def main() -> None:
    port = int(os.environ.get("SLACK_INTERACTIONS_PORT") or "8080")
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"slack_interactions: listening :{port}/slack/interactions")
    server.serve_forever()


if __name__ == "__main__":
    main()
