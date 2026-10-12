"""Rozhodnutí, jestli Cowork nebo Grok Bot smí zápis do vaultu.

Modul nic nezapisuje a nečte disk. Datum a texty dodá volající.
Allow je až poslední krok dané operace.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

ACTORS = ("Cursor", "Cowork", "Grok")
HM_RE = re.compile(r"^\d{2}:\d{2}$")
# Mirror hub lib/focus.py (CLI path has no hub PYTHONPATH).
FOCUS_TASK_LIMIT = 10
FOCUS_EPIC_LIMIT = 5

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
    "deny_stale_reread",
    "deny_no_frontmatter",
    "restore_original",
    "deny_task_after_failed_restore",
    "allow_daily_create",
    "deny_existing_md",
    "deny_new_task",
    "deny_create",
    "deny_focus_remote",
    "allow_focus",
    "deny_focus_without_ask",
    "deny_focus_task_limit",
    "deny_focus_epic_limit",
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
    today: str = ""
    existing: str = ""
    reread: str = ""
    held: str = ""
    proposed: str = ""
    block: str = ""
    user_said_focus: bool = False
    already_in_focus: bool = False
    focus_count: int = 0
    focus_epic_count: int = 0
    # Target would take a task/story slot (default) vs epic slot after set_focus.
    would_consume_focus_slot: bool = True
    would_consume_epic_focus_slot: bool = False
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


def classify_surface(actor: str, is_schedule: bool, has_folder: bool, desktop_open: bool = False) -> str:
    """Režim podle toho, co jde, ne podle zařízení.

    has_folder = čtení SECOND_BRAIN/ přes připojenou složku prošlo.
    desktop_open se už nevyhodnocuje (zůstává kvůli kompatibilitě volání).
    """
    phone = "grok_phone" if actor == "Grok" else "cowork_phone"
    if not has_folder:
        return phone
    if is_schedule:
        return "morning_schedule"
    return "disk_grok" if actor == "Grok" else "disk_cowork"


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
    if proposed == "":
        return original != ""
    if original.rstrip("\n") == proposed.rstrip("\n"):
        return False
    return original.startswith(proposed)


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
    norm = "/" + _norm_path(path).lstrip("/")
    for prefix in ("/workspace", "/home/claude", "/mnt/user-data"):
        if norm == prefix or norm.startswith(prefix + "/"):
            return True
    return False


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


def prague_today() -> str:
    return datetime.now(ZoneInfo("Europe/Prague")).date().isoformat()


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
    if not req.today:
        req.today = prague_today()
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
    if remote:
        return _deny("deny_focus_remote", claimed_remote=True)
    if not req.user_said_focus:
        return _deny("deny_focus_without_ask")
    if not req.already_in_focus:
        if req.would_consume_focus_slot and req.focus_count >= FOCUS_TASK_LIMIT:
            return _deny("deny_focus_task_limit")
        if req.would_consume_epic_focus_slot and req.focus_epic_count >= FOCUS_EPIC_LIMIT:
            return _deny("deny_focus_epic_limit")
    if req.set_done_because_checkboxes:
        return _deny("deny_status_done_from_boxes")
    if req.touches_stav_auto:
        return _deny("deny_stav_auto")
    if req.target_read in ("failed", "placeholder"):
        return _deny("deny_read_failed", claimed_remote=False)
    if not req.guide_readable:
        return _deny("deny_existing_md", claimed_remote=False)
    if surface.startswith("disk"):
        if req.reread != req.held:
            if req.reread != "" and is_prefix_cut(req.held, req.reread):
                return Decision("restore", "restore_original", req.held)
            return _deny("deny_stale_reread")
        return Decision("apply", "allow_focus")
    return _deny("deny_focus_without_ask")


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
    if remote:
        return _deny("deny_existing_md", claimed_remote=True)
    if not req.guide_readable:
        return _deny("deny_existing_md", claimed_remote=False)
    if req.reread != req.held:
        if req.reread != "" and is_prefix_cut(req.held, req.reread):
            return Decision("restore", "restore_original", req.held)
        return _deny("deny_stale_reread")
    if is_prefix_cut(req.held, req.proposed):
        return _deny("deny_prefix_cut")
    if req.set_done_because_checkboxes:
        return _deny("deny_status_done_from_boxes")
    if req.touches_stav_auto:
        return _deny("deny_stav_auto")
    if not closed_frontmatter(req.held):
        return _deny("deny_no_frontmatter")
    return Decision("apply", "allow_overwrite", req.proposed)


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
