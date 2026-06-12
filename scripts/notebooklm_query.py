#!/usr/bin/env python3
"""Thin CLI wrapper for notebooklm-py (Google NotebookLM).

Requires: pip install "notebooklm-py[browser]" && notebooklm login

Usage:
  python3 scripts/notebooklm_query.py list
  python3 scripts/notebooklm_query.py ask "<notebook title or id>" "question"
  python3 scripts/notebooklm_query.py sources "<notebook>"
"""
from __future__ import annotations

import argparse
import asyncio
import sys


def _fail(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    print("Hint: pip install \"notebooklm-py[browser]\" && notebooklm login", file=sys.stderr)
    sys.exit(code)


async def _client():
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        _fail("notebooklm-py not installed")
    try:
        return NotebookLMClient.from_storage()
    except Exception as e:
        _fail(f"NotebookLM auth failed ({e}). Run: notebooklm login")


async def cmd_list(_args) -> int:
    try:
        async with await _client() as client:
            notebooks = await client.notebooks.list()
            for nb in notebooks:
                print(f"{nb.id}\t{nb.title}")
    except ValueError as e:
        _fail(str(e))
    return 0


async def _find_notebook(client, needle: str):
    notebooks = await client.notebooks.list()
    needle_l = needle.lower()
    for nb in notebooks:
        if nb.id == needle or needle_l in (nb.title or "").lower():
            return nb
    return None


async def cmd_ask(args) -> int:
    try:
        async with await _client() as client:
            nb = await _find_notebook(client, args.notebook)
            if not nb:
                _fail(f"notebook not found: {args.notebook}")
            result = await client.chat.ask(nb.id, args.question)
            print(result.answer)
    except ValueError as e:
        _fail(str(e))
    return 0


async def cmd_sources(args) -> int:
    try:
        async with await _client() as client:
            nb = await _find_notebook(client, args.notebook)
            if not nb:
                _fail(f"notebook not found: {args.notebook}")
            sources = await client.sources.list(nb.id)
            for s in sources:
                print(f"- {getattr(s, 'title', s)}")
    except ValueError as e:
        _fail(str(e))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="NotebookLM query helper")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="List notebooks")
    ask = sub.add_parser("ask", help="Ask notebook a question")
    ask.add_argument("notebook")
    ask.add_argument("question")
    src = sub.add_parser("sources", help="List sources in notebook")
    src.add_argument("notebook")
    args = p.parse_args()
    if args.cmd == "list":
        return asyncio.run(cmd_list(args))
    if args.cmd == "ask":
        return asyncio.run(cmd_ask(args))
    if args.cmd == "sources":
        return asyncio.run(cmd_sources(args))
    return 1


if __name__ == "__main__":
    sys.exit(main())
