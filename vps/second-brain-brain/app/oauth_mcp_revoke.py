"""Revoke a Claude OAuth family. No HTTP route."""
from __future__ import annotations

import argparse
import sys

from app.oauth_mcp_store import OAuthUnavailable, revoke


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.oauth_mcp_revoke")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email")
    group.add_argument("--family")
    args = parser.parse_args(argv)
    try:
        count = revoke(email=args.email, family_id=args.family)
    except OAuthUnavailable as exc:
        print(f"oauth unavailable: {exc}", file=sys.stderr)
        return 1
    print(count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
