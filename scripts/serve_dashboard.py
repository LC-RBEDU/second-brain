#!/usr/bin/env python3
"""Serve MrLUC/00-System for live dashboard polling (no browser cache)."""
from __future__ import annotations

import argparse
import http.server
import os
from pathlib import Path


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve dashboard from MrLUC/00-System")
    parser.add_argument("--port", type=int, default=int(os.environ.get("DASHBOARD_PORT", "8765")))
    args = parser.parse_args()

    vault = Path(
        os.environ.get(
            "VAULT_PATH",
            Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/MrLUC",
        )
    )
    root = vault / "00-System"
    if not root.is_dir():
        raise SystemExit(f"Missing vault dir: {root}")

    os.chdir(root)
    url = f"http://127.0.0.1:{args.port}/Dashboard.html"
    print(f"Serving {root}")
    print(url)
    http.server.ThreadingHTTPServer(("127.0.0.1", args.port), NoCacheHandler).serve_forever()


if __name__ == "__main__":
    main()
