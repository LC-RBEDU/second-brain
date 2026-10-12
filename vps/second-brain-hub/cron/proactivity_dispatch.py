#!/usr/bin/env python3
"""F3/F4 proactivity — morning/due CTA; evening L1 digest → digests/ + Saturnin."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from drive_io import DriveConflictError  # noqa: E402
from evening_l1_digest import (  # noqa: E402
    DIGEST_DIR,
    build_match_from_brain,
    deliver_to_saturnin,
    digest_rel_path,
    fetch_l1_brain,
    parse_deliver,
    patch_deliver_frontmatter,
    render_digest_md,
    writers_paused,
)
from push_dispatch import as_dict, dispatch_proactivity  # noqa: E402
from vault_factory import open_vault  # noqa: E402

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))


def _trigger_for(now: datetime, explicit: str | None) -> str:
    if explicit:
        return explicit
    h = now.hour
    if h <= 9:
        return "morning"
    if h >= 17:
        return "evening"
    return "due"


def _run_morning_due(trigger: str, *, dry_run: bool) -> None:
    slack_n = 0
    with open_vault() as vault:
        try:
            metas = vault.list_dir("01-INBOX/slack", pattern="*.md", recursive=True)
            slack_n = len(list(metas))
        except Exception:
            slack_n = 0

    preview = {
        "trigger": trigger,
        "slack_dump_count": slack_n,
        "message": "jdi do live triáže",
        "propose": False,
        "batch_id": None,
    }
    print(f"proactivity_dispatch: trigger={trigger} preview={preview} dry_run={dry_run}")
    msg = f"{trigger}: jdi do live triáže (Slack live — :eyes: / :gear:)"
    result = dispatch_proactivity(msg, dry_run=dry_run)
    print(f"  deliver={as_dict(result)}")
    if dry_run:
        print("  [dry] 0 OS push, 0 Slack send, 0 chat deliver, 0 propose")


def _run_evening(*, dry_run: bool, force: bool, brain_url: str) -> None:
    if writers_paused():
        print("proactivity_dispatch: evening VAULT_WRITERS_PAUSED=1 — 0 write, 0 Grok")
        return

    now = datetime.now(TZ)
    day = now.date().isoformat()
    rel = digest_rel_path(day)
    print(
        f"proactivity_dispatch: trigger=evening day={day} rel={rel} "
        f"dry_run={dry_run} force={force}"
    )

    exists = False
    deliver: str | None = None
    body = ""
    meta = None
    with open_vault() as vault:
        if getattr(vault, "skipped", False):
            print(
                f"proactivity_dispatch: evening vault skipped "
                f"({getattr(vault, 'skip_reason', None)}) — 0 write, 0 Grok"
            )
            return
        if vault.exists(rel):
            exists = True
            body, meta = vault.read_text(rel)
            deliver = parse_deliver(body)

    if exists and deliver == "OK" and not force:
        print("proactivity_dispatch: evening already_exists deliver=OK — skip")
        return

    if exists and deliver != "OK" and not force:
        # Saturnin-only retry (B2b / B4b)
        if dry_run:
            print(
                "proactivity_dispatch: evening [dry] Saturnin-only path — "
                "0 Brain, 0 write, 0 Grok, 0 CAS"
            )
            return
        ok, detail = deliver_to_saturnin(body, day=day, dry_run=False)
        status = "OK" if ok else "FAIL"
        print(f"  saturnin_only deliver={status} detail={detail}")
        with open_vault() as vault:
            if getattr(vault, "skipped", False):
                print("  ! vault skipped on deliver patch")
                return
            # re-read for fresh CAS meta
            _, fresh = vault.read_text(rel)
            patched = patch_deliver_frontmatter(
                vault, rel, status=status, detail=detail, meta=fresh
            )
            if not patched:
                print(
                    "  ! CAS conflict on deliver patch — leave FM unchanged, exit 0",
                    file=sys.stderr,
                )
        return

    # first run or --force → rebuild
    payload, total_err = fetch_l1_brain(brain_url=brain_url or None)
    if total_err:
        print(f"  brain total_degrade={total_err}")
    elif payload and payload.get("error_reason"):
        print(f"  brain partial={payload.get('error_reason')}")

    md = ""
    with open_vault() as vault:
        if getattr(vault, "skipped", False):
            print("  ! vault skipped on match — 0 write, 0 Grok")
            return
        match = build_match_from_brain(vault, payload, total_error=total_err)
        md = render_digest_md(
            day=day,
            match=match,
            generated_at=now.isoformat(timespec="seconds"),
        )
        print(
            f"  match candidates={match.candidate_count} "
            f"matched_tasks={len(match.matched)} unmatched={len(match.unmatched)}"
        )
        if dry_run:
            print(
                "proactivity_dispatch: evening [dry] rebuild preview — "
                "0 write, 0 Grok, 0 propose"
            )
            print(f"  [dry] would write {rel} chars={len(md)}")
            return
        vault.mkdir_p(DIGEST_DIR)
        try:
            vault.write_text(rel, md)
        except DriveConflictError as exc:
            print(
                f"  ! CAS conflict on digest write — abort Grok, exit 0 ({exc})",
                file=sys.stderr,
            )
            return

    ok, detail = deliver_to_saturnin(md, day=day, dry_run=False)
    status = "OK" if ok else "FAIL"
    print(f"  saturnin deliver={status} detail={detail}")
    with open_vault() as vault:
        if getattr(vault, "skipped", False):
            print("  ! vault skipped on deliver patch (MD already written)")
            return
        _, fresh = vault.read_text(rel)
        patched = patch_deliver_frontmatter(
            vault, rel, status=status, detail=detail, meta=fresh
        )
        if not patched:
            print(
                "  ! CAS conflict on deliver patch — leave FM unchanged, exit 0",
                file=sys.stderr,
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--trigger",
        choices=("morning", "due", "evening"),
        default=None,
        help="Force trigger slot (default: by clock)",
    )
    parser.add_argument(
        "--brain-url",
        default=os.environ.get("BRAIN_PUBLIC_URL", ""),
        help="Brain base URL (default BRAIN_PUBLIC_URL)",
    )
    args = parser.parse_args()
    now = datetime.now(TZ)
    trigger = _trigger_for(now, args.trigger)

    if trigger == "evening":
        _run_evening(dry_run=args.dry_run, force=args.force, brain_url=args.brain_url)
        return

    # --force ignored for morning/due
    _run_morning_due(trigger, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
