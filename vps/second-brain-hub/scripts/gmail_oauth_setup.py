#!/usr/bin/env python3
"""One-shot Gmail OAuth for hub drafts (compose scope, not Drive).

Run on the Mac. Sign in as lukas@redbuttonedu.cz. Paste the JSON into Coolify
as GOOGLE_GMAIL_OAUTH_JSON. Do not commit it.

    python3 vps/second-brain-hub/scripts/gmail_oauth_setup.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_CLIENT = Path.home() / ".config" / "mrluc" / "oauth_client.json"
DEFAULT_OUT = Path.home() / ".config" / "mrluc" / "gmail_oauth_creds.json"
COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", type=Path, default=DEFAULT_CLIENT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if not args.client.is_file():
        print(f"ERROR: OAuth client JSON not found at {args.client}", file=sys.stderr)
        return 2
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: pip install google-auth-oauthlib", file=sys.stderr)
        return 2

    client_raw = json.loads(args.client.read_text(encoding="utf-8"))
    inner = client_raw.get("installed") or client_raw.get("web") or client_raw
    print("Opening browser. Sign in as lukas@redbuttonedu.cz. Scope: gmail.compose (drafts, not a separate send step in hub code).")
    flow = InstalledAppFlow.from_client_config({"installed": inner}, scopes=[COMPOSE_SCOPE])
    # Client redirect is http://localhost (not 127.0.0.1) — mismatch fails consent.
    creds = flow.run_local_server(
        host="localhost",
        port=args.port,
        prompt="consent",
        access_type="offline",
        open_browser=True,
    )
    if not creds.refresh_token:
        print("ERROR: no refresh_token. Revoke the app at https://myaccount.google.com/permissions and retry.", file=sys.stderr)
        return 3
    merged = {
        "client_id": inner["client_id"],
        "client_secret": inner["client_secret"],
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "scopes": list(creds.scopes or [COMPOSE_SCOPE]),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(merged), encoding="utf-8")
    os.chmod(args.out, 0o600)
    print(f"Wrote {args.out} (mode 0600).")
    print("Coolify env GOOGLE_GMAIL_OAUTH_JSON = contents of that file. Do not commit it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
