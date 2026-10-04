"""Rozhodnutí, jestli Cowork nebo Grok Bot smí zápis do vaultu.

Modul nic nezapisuje a nečte disk. Datum a texty dodá volající.
Allow je až poslední krok dané operace.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ACTORS = ("Cursor", "Cowork", "Grok")
HM_RE = re.compile(r"^\d{2}:\d{2}$")

ALL_REASONS = (
    "allow_append_bus",
    "deny_foreign_block",
    "deny_duplicate_block",
    "deny_old_bus_day",
    "deny_bus_heading",
    "deny_workspace",
    "deny_read_failed",
    "deny_agent_bus_remote",
    "deny_morning_write",
    "allow_overwrite",
    "deny_prefix_cut",
    "deny_phone_not_one_line",
    "deny_stale_reread",
    "restore_original",
    "deny_task_after_failed_restore",
    "allow_daily_create",
    "deny_existing_md",
    "deny_new_task",
    "deny_create",
    "deny_focus_cowork_phone",
    "allow_focus",
    "deny_focus_without_ask",
    "deny_focus_over_5",
    "deny_morning_build_context",
    "allow_script",
    "deny_script",
    "allow_slack_send",
    "deny_slack",
    "deny_archive_move",
    "deny_recurring_move",
    "deny_status_done_from_boxes",
    "deny_stav_auto",
)


@dataclass
class Decision:
    outcome: str
    reason: str
    text: str | None = None
    claimed_remote: bool = False


@dataclass
class Request:
    op: str
    actor: str = "Cowork"
    is_schedule: bool = False
    has_folder: bool = False
    desktop_open: bool = False
    surface: str = ""
    target_read: str = "ok"
    guide_readable: bool = True
    path: str = ""
    today: str = "2026-10-04"
    existing: str = ""
    reread: str = ""
    held: str = ""
    proposed: str = ""
    block: str = ""
    user_said_focus: bool = False
    already_in_focus: bool = False
    focus_count: int = 0
    user_said_send: bool = False
    preview_shown: bool = False
    after_task_write: bool = False
    script: str = ""
    set_done_because_checkboxes: bool = False
    touches_stav_auto: bool = False
    recurring: bool = False
    leaves_tasks: bool = False
    origin_restore_failed: bool = False
    extra: dict = field(default_factory=dict)


def classify_surface(actor: str, is_schedule: bool, has_folder: bool, desktop_open: bool) -> str:
    phone = "grok_phone" if actor == "Grok" else "cowork_phone"
    if is_schedule and has_folder and desktop_open:
        return "morning_schedule"
    if is_schedule and not has_folder:
        return phone
    if is_schedule and has_folder and not desktop_open:
        return phone
    if not is_schedule and has_folder:
        return "disk_grok" if actor == "Grok" else "disk_cowork"
    return phone


def closed_frontmatter(text: str) -> bool:
    stripped = text.lstrip("\ufeff").lstrip()
    if not stripped.startswith("---\n"):
        return False
    return "\n---" in stripped[4:]


def _norm_end(text: str) -> str:
    if text == "" or text.endswith("\n"):
        return text
    return text + "\n"


def is_prefix_cut(original: str, proposed: str) -> bool:
    original_n = _norm_end(original)
    proposed_n = _norm_end(proposed)
    return proposed_n != original_n and proposed_n != "" and original_n.startswith(proposed_n)


def is_single_line_replace(original: str, proposed: str) -> bool:
    old = original.splitlines()
    new = proposed.splitlines()
    if len(old) != len(new) or not old:
        return False
    return sum(1 for left, right in zip(old, new) if left != right) == 1


def format_bus_block(hm: str, actor: str, topic: str, body: str = "") -> str:
    if actor not in ACTORS or not HM_RE.match(hm):
        raise ValueError("bad bus heading")
    text = f"## {hm} — {actor}\ntéma: {topic}\n"
    if body:
        text += body.rstrip("\n") + "\n"
    return text


def append_agent_bus(existing: str, block: str) -> str:
    if existing == "":
        out = block
    else:
        sep = "" if existing.endswith("\n") else "\n"
        out = existing + sep + block
    if not out.endswith("\n"):
        out += "\n"
    if not out.startswith(existing):
        raise RuntimeError("append must keep the existing prefix")
    return out


def preserves_prefix(before: str, after: str) -> bool:
    return after.startswith(before)


def _norm_path(path: str) -> str:
    return path.replace("\\", "/")


def _is_workspace(path: str) -> bool:
    norm = _norm_path(path)
    return norm == "/workspace" or norm.startswith("/workspace/") or "/workspace/" in f"/{norm.strip('/')}/"


def _is_today_bus(path: str, today: str) -> bool:
    return _norm_path(path).endswith(f"00-System/Agent_Bus/{today}.md")


def _is_bus_path(path: str) -> bool:
    norm = _norm_path(path)
    return "Agent_Bus/" in norm or norm.endswith("Agent_Bus.md") or norm.endswith("/Agent_Bus")


def _is_daily(path: str) -> bool:
    norm = _norm_path(path)
    return "/01-INBOX/daily/" in f"/{norm}" or norm.startswith("01-INBOX/daily/")


def _is_tasks(path: str) -> bool:
    norm = _norm_path(path)
    return "02-PROJEKTY/" in norm and "/tasks/" in norm


def _is_archive(path: str) -> bool:
    norm = _norm_path(path)
    return norm.startswith("07-ARCHIV/") or "/07-ARCHIV/" in norm


def _deny(reason: str, claimed_remote: bool = False, text: str | None = None) -> Decision:
    return Decision("deny", reason, text, claimed_remote)


def _surface(req: Request) -> str:
    if req.surface:
        return req.surface
    return classify_surface(req.actor, req.is_schedule, req.has_folder, req.desktop_open)


def _valid_block(block: str) -> bool:
    if not block.startswith("## "):
        return False
    first, _, rest = block.partition("\n")
    if " — " not in first:
        return False
    actor = first.split(" — ", 1)[1].strip()
    if actor not in ACTORS:
        return False
    hm = first[3:].split(" — ", 1)[0].strip()
    if not HM_RE.match(hm):
        return False
    return rest.startswith("téma:")


def decide(req: Request) -> Decision:
    if req.origin_restore_failed and req.op == "overwrite":
        return _deny("deny_task_after_failed_restore")
    if _is_workspace(req.path):
        return _deny("deny_workspace")
    if req.op == "move_archive" or _is_archive(req.path):
        return _deny("deny_archive_move")
    if req.recurring and req.leaves_tasks:
        return _deny("deny_recurring_move")
    if req.op == "set_focus":
        return _decide_focus(req)
    if req.op in ("create", "append_bus"):
        return _decide_create(req)
    if req.op == "overwrite":
        return _decide_overwrite(req)
    if req.op == "run_script":
        return _decide_script(req)
    return _deny("deny_create")


def _decide_focus(req: Request) -> Decision:
    surface = _surface(req)
    remote = surface.endswith("phone")
    if surface == "morning_schedule":
        return _deny("deny_morning_write")
    if surface == "cowork_phone":
        return _deny("deny_focus_cowork_phone", claimed_remote=True)
    if not req.user_said_focus:
        return _deny("deny_focus_without_ask", claimed_remote=remote)
    if not req.already_in_focus and req.focus_count >= 5:
        return _deny("deny_focus_over_5", claimed_remote=remote)
    if req.set_done_because_checkboxes:
        return _deny("deny_status_done_from_boxes", claimed_remote=remote)
    if req.touches_stav_auto:
        return _deny("deny_stav_auto", claimed_remote=remote)
    if surface == "grok_phone":
        if req.reread == req.held and closed_frontmatter(req.held):
            return Decision("apply", "allow_focus", claimed_remote=True)
        return _deny("deny_stale_reread", claimed_remote=True)
    if surface.startswith("disk"):
        if req.reread != req.held:
            if is_prefix_cut(req.held, req.reread):
                return Decision("restore", "restore_original", req.held)
            return _deny("deny_stale_reread")
        return Decision("apply", "allow_focus")
    return _deny("deny_focus_without_ask", claimed_remote=remote)


def _decide_create(req: Request) -> Decision:
    surface = _surface(req)
    remote = surface.endswith("phone")
    if surface == "morning_schedule":
        return _deny("deny_morning_write")

    bus_op = req.op == "append_bus" or _is_today_bus(req.path, req.today) or _is_bus_path(req.path)
    if bus_op:
        if not surface.startswith("disk"):
            return _deny("deny_agent_bus_remote", claimed_remote=remote)
        if not req.guide_readable:
            return _deny("deny_existing_md", claimed_remote=False)
        if req.target_read in ("failed", "placeholder"):
            return _deny("deny_read_failed", claimed_remote=False)
        if not _is_today_bus(req.path, req.today):
            return _deny("deny_old_bus_day")
        if req.target_read == "ok" and req.reread != req.existing:
            return _deny("deny_foreign_block")
        if not _valid_block(req.block):
            return _deny("deny_bus_heading")
        existing = "" if req.target_read == "absent" else req.existing
        if req.target_read == "ok" and existing.rstrip("\n").endswith(req.block.rstrip("\n")):
            return _deny("deny_duplicate_block")
        if req.target_read not in ("ok", "absent"):
            return _deny("deny_read_failed", claimed_remote=False)
        return Decision("apply", "allow_append_bus", append_agent_bus(existing, req.block))

    if not req.guide_readable:
        if req.target_read == "absent" and _is_daily(req.path):
            return Decision("apply", "allow_daily_create", claimed_remote=False)
        return _deny("deny_existing_md", claimed_remote=False)
    if _is_tasks(req.path):
        return _deny("deny_new_task", claimed_remote=remote)
    if _is_daily(req.path) and req.target_read == "absent":
        return Decision("apply", "allow_daily_create", claimed_remote=remote)
    if _is_daily(req.path):
        return _deny("deny_existing_md", claimed_remote=remote)
    return _deny("deny_create", claimed_remote=remote)


def _decide_overwrite(req: Request) -> Decision:
    surface = _surface(req)
    remote = surface.endswith("phone")
    if surface == "morning_schedule":
        return _deny("deny_morning_write")
    if req.target_read in ("failed", "placeholder"):
        return _deny("deny_read_failed", claimed_remote=False)
    if surface == "cowork_phone":
        return _deny("deny_existing_md", claimed_remote=True)
    if not req.guide_readable:
        return _deny("deny_existing_md", claimed_remote=False)
    if req.reread != req.held:
        if surface.startswith("disk") and is_prefix_cut(req.held, req.reread):
            return Decision("restore", "restore_original", req.held)
        return _deny("deny_stale_reread", claimed_remote=remote)
    if is_prefix_cut(req.held, req.proposed):
        return _deny("deny_prefix_cut", claimed_remote=remote)
    if req.set_done_because_checkboxes:
        return _deny("deny_status_done_from_boxes", claimed_remote=remote)
    if req.touches_stav_auto:
        return _deny("deny_stav_auto", claimed_remote=remote)
    if surface == "grok_phone":
        if closed_frontmatter(req.held) and is_single_line_replace(req.held, req.proposed):
            return Decision("apply", "allow_overwrite", req.proposed, claimed_remote=True)
        return _deny("deny_phone_not_one_line", claimed_remote=True)
    if surface.startswith("disk") and closed_frontmatter(req.held):
        return Decision("apply", "allow_overwrite", req.proposed)
    if surface.startswith("disk"):
        return _deny("deny_stale_reread")
    return _deny("deny_existing_md", claimed_remote=remote)


def _script_name(script: str) -> str:
    return script.replace("\\", "/").rsplit("/", 1)[-1]


def _decide_script(req: Request) -> Decision:
    surface = _surface(req)
    remote = surface.endswith("phone")
    name = _script_name(req.script)
    if surface == "morning_schedule":
        if name == "build_agent_context.py":
            return _deny("deny_morning_build_context")
        if name == "slack_send_message.py":
            return _deny("deny_slack")
        return _deny("deny_morning_write")
    if name == "slack_send_message.py":
        if req.actor == "Cowork" and req.user_said_send and surface != "morning_schedule":
            return Decision("apply", "allow_slack_send", claimed_remote=remote)
        return _deny("deny_slack", claimed_remote=remote)
    banned = {
        "next_task_id.py",
        "archive_inbox_item.py",
        "sync_lide_people.py",
        "extract_material_text.py",
    }
    if name in banned or name == "git" or "deploy" in name or "/vps/" in req.script.replace("\\", "/"):
        return _deny("deny_script", claimed_remote=remote)
    if not surface.startswith("disk"):
        return _deny("deny_script", claimed_remote=remote)
    if name == "build_agent_context.py" and req.after_task_write:
        return Decision("apply", "allow_script")
    if name == "schedule_reminder.py" and req.preview_shown:
        return Decision("apply", "allow_script")
    return _deny("deny_script", claimed_remote=remote)
