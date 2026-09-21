"""Slack interaction signature and the Odpověz payload."""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import slack_interactions as ix  # noqa: E402


def test_signature_roundtrip():
    secret = "secret"
    timestamp = str(int(time.time()))
    body = b"payload=%7B%7D"
    digest = hmac.new(secret.encode(), b"v0:" + timestamp.encode() + b":" + body, hashlib.sha256).hexdigest()
    assert ix.verify_slack_signature(secret, timestamp, body, f"v0={digest}")
    assert ix.verify_slack_signature(secret, timestamp, body, "v0=nope") is False


def test_reply_from_action_only_lukas():
    payload = {
        "user": {"id": "U014AEZD72S"},
        "actions": [{"action_id": "slack_reply_send", "value": json.dumps({"c": "C1", "t": "1.2"})}],
        "message": {"blocks": [{"block_id": "reply_body", "text": {"text": "Ahoj, pošlu to."}}]},
    }
    assert ix.reply_from_action(payload) == ("C1", "1.2", "Ahoj, pošlu to.")
    payload["user"]["id"] = "UOTHER"
    assert ix.reply_from_action(payload) is None
