#!/usr/bin/env python3
"""CLI pro Cowork a Grok Bot. Nic nezapisuje, vypíše rozhodnutí.

Příklad:
  python3 scripts/agent_write_guard.py --op append_bus --actor Cowork \\
    --path OBSIDIAN/00-System/Agent_Bus/2026-10-05.md --target-read absent \\
    --block-file blok.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "lib"))

from agent_write_guard import Request, decide  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Rozhodni, jestli zápis do vaultu smí projít.")
    parser.add_argument("--op", required=True)
    parser.add_argument("--actor", default="Cowork")
    parser.add_argument("--path", default="")
    parser.add_argument("--today", default="", help="YYYY-MM-DD. Prázdné = dnešek Europe/Prague.")
    parser.add_argument("--target-read", default="ok", choices=("ok", "absent", "failed", "placeholder"))
    parser.add_argument("--guide-readable", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--has-folder", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--schedule", action="store_true")
    parser.add_argument(
        "--desktop-open",
        action="store_true",
        help="Nevyhodnocuje se, ponecháno kvůli kompatibilitě.",
    )
    parser.add_argument("--block-file", type=Path)
    parser.add_argument("--existing-file", type=Path)
    parser.add_argument("--reread-file", type=Path)
    parser.add_argument("--held-file", type=Path)
    parser.add_argument("--proposed-file", type=Path)
    parser.add_argument("--script", default="")
    parser.add_argument("--user-said-send", action="store_true")
    parser.add_argument("--user-said-focus", action="store_true")
    parser.add_argument("--already-in-focus", action="store_true")
    parser.add_argument("--focus-count", type=int, default=0)
    parser.add_argument("--focus-epic-count", type=int, default=0)
    parser.add_argument(
        "--would-consume-focus-slot",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--would-consume-epic-focus-slot",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument("--after-task-write", action="store_true")
    parser.add_argument("--preview-shown", action="store_true")
    args = parser.parse_args()

    def read(path: Path | None) -> str:
        if path is None:
            return ""
        return path.read_text(encoding="utf-8")

    decision = decide(
        Request(
            op=args.op,
            actor=args.actor,
            path=args.path,
            today=args.today,
            target_read=args.target_read,
            guide_readable=args.guide_readable,
            has_folder=args.has_folder,
            is_schedule=args.schedule,
            desktop_open=args.desktop_open,
            block=read(args.block_file),
            existing=read(args.existing_file),
            reread=read(args.reread_file) or read(args.existing_file),
            held=read(args.held_file),
            proposed=read(args.proposed_file),
            script=args.script,
            user_said_send=args.user_said_send,
            user_said_focus=args.user_said_focus,
            already_in_focus=args.already_in_focus,
            focus_count=args.focus_count,
            focus_epic_count=args.focus_epic_count,
            would_consume_focus_slot=args.would_consume_focus_slot,
            would_consume_epic_focus_slot=args.would_consume_epic_focus_slot,
            after_task_write=args.after_task_write,
            preview_shown=args.preview_shown,
        )
    )
    json.dump(
        {
            "outcome": decision.outcome,
            "reason": decision.reason,
            "claimed_remote": decision.claimed_remote,
            "text": decision.text,
        },
        sys.stdout,
        ensure_ascii=False,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
