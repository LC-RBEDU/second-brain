"""Režimy zápisu Cowork / Grok Bot (T1–T12)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lib"))

from agent_write_guard import (  # noqa: E402
    ALL_REASONS,
    Request,
    append_agent_bus,
    classify_surface,
    decide,
    format_bus_block,
)

TODAY = "2026-10-04"
BUS = f"OBSIDIAN/00-System/Agent_Bus/{TODAY}.md"
OLD_BUS = "OBSIDIAN/00-System/Agent_Bus/2026-10-03.md"
DAILY = "01-INBOX/daily/note.md"
TASK = "02-PROJEKTY/finance/tasks/F1 — Poznámka.md"
HELD = "---\nstatus: Next\n---\nřádek\n"
HELD_DONE = "---\nstatus: Done\n---\nřádek\n"


def _req(**kwargs) -> Request:
    base = dict(today=TODAY, has_folder=True, actor="Cowork", guide_readable=True)
    base.update(kwargs)
    return Request(**base)


def _block(actor: str = "Cowork", topic: str = "bus") -> str:
    return format_bus_block("18:00", actor, topic, "text")


def test_t1_disk_cowork_append_keeps_old_blocks():
    old = _block("Cursor", "starší") + _block("Grok", "druhý")
    block = _block("Cowork", "nový")
    decision = decide(
        _req(op="append_bus", path=BUS, target_read="ok", existing=old, reread=old, block=block)
    )
    assert decision.reason == "allow_append_bus"
    assert decision.text.startswith(old)
    assert decision.text.rstrip("\n").endswith(block.rstrip("\n"))
    assert append_agent_bus(old, block).startswith(old)


def test_t1_create_task_denied_and_absent_bus_allowed():
    denied = decide(_req(op="create", path=TASK, target_read="absent"))
    assert denied.reason == "deny_new_task"
    other = decide(_req(op="create", path="05-RESOURCES/poznamka.md", target_read="absent"))
    assert other.reason == "deny_create"
    created = decide(_req(op="append_bus", path=BUS, target_read="absent", block=_block()))
    assert created.reason == "allow_append_bus"
    assert created.text.startswith("## 18:00 — Cowork")


def test_t1_bus_edges():
    old = _block()
    foreign = decide(
        _req(op="append_bus", path=BUS, existing=old, reread=old + "x", block=_block("Grok", "jiné"))
    )
    assert foreign.reason == "deny_foreign_block"
    duplicate = decide(_req(op="append_bus", path=BUS, existing=old, reread=old, block=old))
    assert duplicate.reason == "deny_duplicate_block"
    old_day = decide(_req(op="append_bus", path=OLD_BUS, target_read="absent", block=_block()))
    assert old_day.reason == "deny_old_bus_day"
    eternal = decide(
        _req(op="append_bus", path="OBSIDIAN/00-System/Agent_Bus.md", target_read="absent", block=_block())
    )
    assert eternal.reason == "deny_old_bus_day"
    bad = decide(_req(op="append_bus", path=BUS, target_read="absent", block="jen text\n"))
    assert bad.reason == "deny_bus_heading"


def test_t2_grok_append_and_workspace():
    old = _block("Cursor", "a")
    block = _block("Grok", "b")
    ok = decide(
        _req(
            op="append_bus",
            actor="Grok",
            path=BUS,
            existing=old,
            reread=old,
            block=block,
        )
    )
    assert ok.reason == "allow_append_bus"
    assert "Grok" in ok.text
    denied = decide(_req(op="append_bus", path="/workspace/vault.md", target_read="absent", block=block))
    assert denied.reason == "deny_workspace"


def test_t3_placeholder_is_not_remote_and_other_daily_still_allowed():
    failed = decide(
        _req(op="overwrite", path=TASK, target_read="placeholder", held=HELD, reread=HELD, proposed=HELD)
    )
    assert failed.reason == "deny_read_failed"
    assert failed.claimed_remote is False
    assert failed.text is None
    daily = decide(_req(op="create", path=DAILY, target_read="absent"))
    assert daily.reason == "allow_daily_create"


def test_t4_unreadable_guide_and_cowork_phone():
    disk_overwrite = decide(
        _req(op="overwrite", guide_readable=False, path=TASK, held=HELD, reread=HELD, proposed=HELD)
    )
    assert disk_overwrite.reason == "deny_existing_md"
    assert disk_overwrite.claimed_remote is False
    disk_daily = decide(_req(op="create", guide_readable=False, path=DAILY, target_read="absent"))
    assert disk_daily.reason == "allow_daily_create"
    assert disk_daily.claimed_remote is False
    phone_line = HELD.replace("Next", "Doing")
    phone = decide(
        _req(
            op="overwrite",
            actor="Cowork",
            has_folder=False,
            path=TASK,
            held=HELD,
            reread=HELD,
            proposed=phone_line,
        )
    )
    assert phone.reason == "deny_existing_md"
    phone_daily = decide(_req(op="create", has_folder=False, path=DAILY, target_read="absent"))
    assert phone_daily.reason == "allow_daily_create"
    phone_bus = decide(
        _req(op="append_bus", has_folder=False, path=BUS, target_read="absent", block=_block())
    )
    assert phone_bus.reason == "deny_agent_bus_remote"
    phone_focus = decide(
        _req(
            op="set_focus",
            has_folder=False,
            user_said_focus=True,
            focus_count=4,
            held=HELD,
            reread=HELD,
            path=TASK,
        )
    )
    assert phone_focus.reason == "deny_focus_cowork_phone"
    closed_desktop = decide(
        _req(
            op="create",
            is_schedule=True,
            has_folder=True,
            desktop_open=False,
            path=DAILY,
            target_read="absent",
        )
    )
    assert closed_desktop.reason == "allow_daily_create"
    assert classify_surface("Cowork", True, True, False) == "cowork_phone"


def test_t5_phone_one_line_and_disk_prefix():
    changed = HELD.replace("Next", "Doing")
    phone_ok = decide(
        _req(
            op="overwrite",
            actor="Grok",
            has_folder=False,
            path=TASK,
            held=HELD,
            reread=HELD,
            proposed=changed,
        )
    )
    assert phone_ok.reason == "allow_overwrite"
    two = HELD.replace("Next", "Doing").replace("řádek", "jiný")
    assert decide(
        _req(
            op="overwrite",
            actor="Grok",
            has_folder=False,
            path=TASK,
            held=HELD,
            reread=HELD,
            proposed=two,
        )
    ).reason == "deny_phone_not_one_line"
    shorter = "status: Next\nřádek\n"
    assert decide(
        _req(
            op="overwrite",
            actor="Grok",
            has_folder=False,
            path=TASK,
            held=HELD,
            reread=HELD,
            proposed=shorter,
        )
    ).reason == "deny_phone_not_one_line"
    prefix = decide(
        _req(op="overwrite", path=TASK, held=HELD, reread=HELD, proposed="---\nstatus: Next\n")
    )
    assert prefix.reason == "deny_prefix_cut"
    assert prefix.text is None
    disk_line = decide(_req(op="overwrite", path=TASK, held=HELD, reread=HELD, proposed=changed))
    assert disk_line.reason == "allow_overwrite"
    stale = decide(
        _req(op="overwrite", path=TASK, held=HELD_DONE, reread=HELD, proposed=HELD)
    )
    assert stale.reason == "deny_stale_reread"
    assert stale.text is None
    daily_after = decide(_req(op="create", path=DAILY, target_read="absent"))
    assert daily_after.reason == "allow_daily_create"
    live_prefix = decide(
        _req(op="overwrite", path=TASK, held=HELD, reread="---\nstatus: Next\n", proposed=HELD)
    )
    assert live_prefix.reason == "restore_original"
    assert live_prefix.text == HELD
    incomplete = decide(
        _req(op="overwrite", path=TASK, held=HELD, reread="kousek jiného textu", proposed="kousek jiného textu")
    )
    assert incomplete.reason == "deny_stale_reread"
    assert decide(
        _req(op="overwrite", path=TASK, origin_restore_failed=True, held=HELD, reread=HELD, proposed=changed)
    ).reason == "deny_task_after_failed_restore"
    assert decide(
        _req(op="append_bus", actor="Grok", has_folder=False, path=BUS, target_read="absent", block=_block("Grok"))
    ).reason == "deny_agent_bus_remote"
    middle = HELD + "druhý\n"
    cut_middle = middle.replace("řádek\n", "")
    assert decide(
        _req(op="overwrite", path=TASK, held=middle, reread=middle, proposed=cut_middle)
    ).reason == "allow_overwrite"
    boxes = decide(
        _req(
            op="overwrite",
            path=TASK,
            held=HELD,
            reread=HELD,
            proposed=changed,
            set_done_because_checkboxes=True,
        )
    )
    assert boxes.reason == "deny_status_done_from_boxes"
    stav = decide(
        _req(
            op="overwrite",
            path=TASK,
            held=HELD,
            reread=HELD,
            proposed=changed,
            touches_stav_auto=True,
        )
    )
    assert stav.reason == "deny_stav_auto"
    schedule_grok = decide(
        _req(
            op="overwrite",
            actor="Grok",
            is_schedule=True,
            has_folder=True,
            desktop_open=False,
            path=TASK,
            held=HELD,
            reread=HELD,
            proposed=changed,
        )
    )
    assert schedule_grok.reason == "allow_overwrite"


def test_t6_morning_and_open_desktop_schedule_write_nothing():
    morning = _req(op="create", is_schedule=True, has_folder=True, desktop_open=True, path=DAILY, target_read="absent")
    assert decide(morning).reason == "deny_morning_write"
    bus = _req(
        op="append_bus",
        is_schedule=True,
        has_folder=True,
        desktop_open=True,
        path=BUS,
        target_read="absent",
        block=_block(),
    )
    assert decide(bus).reason == "deny_morning_write"
    script = _req(
        op="run_script",
        is_schedule=True,
        has_folder=True,
        desktop_open=True,
        script="build_agent_context.py",
        after_task_write=True,
    )
    assert decide(script).reason == "deny_morning_build_context"
    slack = _req(
        op="run_script",
        is_schedule=True,
        has_folder=True,
        desktop_open=True,
        script="slack_send_message.py",
        user_said_send=True,
    )
    assert decide(slack).reason == "deny_slack"
    assert classify_surface("Cowork", True, True, True) == "morning_schedule"


def test_t7_scripts_and_slack():
    assert decide(_req(op="run_script", script="next_task_id.py")).reason == "deny_script"
    assert decide(
        _req(op="run_script", script="build_agent_context.py", after_task_write=True)
    ).reason == "allow_script"
    assert decide(_req(op="run_script", script="build_agent_context.py")).reason == "deny_script"
    assert decide(
        _req(op="run_script", has_folder=False, script="build_agent_context.py", after_task_write=True)
    ).reason == "deny_script"
    assert decide(
        _req(op="run_script", script="schedule_reminder.py", preview_shown=True)
    ).reason == "allow_script"
    assert decide(_req(op="run_script", script="schedule_reminder.py")).reason == "deny_script"
    for name in ("archive_inbox_item.py", "sync_lide_people.py", "extract_material_text.py", "git", "vps/cron/x.py"):
        assert decide(_req(op="run_script", script=name)).reason == "deny_script"
    assert decide(
        _req(op="run_script", script="slack_send_message.py", user_said_send=True)
    ).reason == "allow_slack_send"
    assert decide(_req(op="run_script", script="slack_send_message.py")).reason == "deny_slack"
    assert decide(
        _req(op="run_script", actor="Grok", script="slack_send_message.py", user_said_send=True)
    ).reason == "deny_slack"
    assert decide(_req(op="create", path=DAILY, target_read="absent")).reason == "allow_daily_create"


def test_t8_archive_and_recurring():
    assert decide(_req(op="move_archive", path="07-ARCHIV/tasks-done/finance/F1.md")).reason == "deny_archive_move"
    assert decide(
        _req(op="overwrite", path="07-ARCHIV/tasks-done/finance/F1.md", held=HELD, reread=HELD, proposed=HELD)
    ).reason == "deny_archive_move"
    assert decide(
        _req(op="overwrite", recurring=True, leaves_tasks=True, path=TASK, held=HELD, reread=HELD, proposed=HELD)
    ).reason == "deny_recurring_move"
    assert decide(
        _req(op="overwrite", recurring=True, path=TASK, held=HELD, reread=HELD, proposed=HELD.replace("Next", "Doing"))
    ).reason == "allow_overwrite"
    stale = decide(
        _req(op="overwrite", recurring=True, path=TASK, held=HELD_DONE, reread=HELD, proposed=HELD_DONE)
    )
    assert stale.reason == "deny_stale_reread"
    assert stale.text is None


def test_t9_focus_cap():
    assert decide(_req(op="set_focus", path=TASK, held=HELD, reread=HELD)).reason == "deny_focus_without_ask"
    full = decide(
        _req(op="set_focus", path=TASK, held=HELD, reread=HELD, user_said_focus=True, focus_count=5)
    )
    assert full.reason == "deny_focus_over_5"
    room = decide(
        _req(op="set_focus", path=TASK, held=HELD, reread=HELD, user_said_focus=True, focus_count=4)
    )
    assert room.reason == "allow_focus"
    again = decide(
        _req(
            op="set_focus",
            path=TASK,
            held=HELD,
            reread=HELD,
            user_said_focus=True,
            focus_count=5,
            already_in_focus=True,
        )
    )
    assert again.reason == "allow_focus"
    morning = decide(
        _req(
            op="set_focus",
            is_schedule=True,
            desktop_open=True,
            user_said_focus=True,
            focus_count=0,
            path=TASK,
            held=HELD,
            reread=HELD,
        )
    )
    assert morning.reason == "deny_morning_write"
    phone_ok = decide(
        _req(
            op="set_focus",
            actor="Grok",
            has_folder=False,
            user_said_focus=True,
            focus_count=4,
            path=TASK,
            held=HELD,
            reread=HELD,
        )
    )
    assert phone_ok.reason == "allow_focus"
    phone_stale = decide(
        _req(
            op="set_focus",
            actor="Grok",
            has_folder=False,
            user_said_focus=True,
            focus_count=4,
            path=TASK,
            held=HELD_DONE,
            reread=HELD,
        )
    )
    assert phone_stale.reason == "deny_stale_reread"
    boxes = decide(
        _req(
            op="set_focus",
            actor="Grok",
            has_folder=False,
            user_said_focus=True,
            focus_count=4,
            path=TASK,
            held=HELD,
            reread=HELD,
            set_done_because_checkboxes=True,
        )
    )
    assert boxes.reason == "deny_status_done_from_boxes"


def test_t10_guide_codes_when_vault_present():
    vault = REPO / "OBSIDIAN"
    if not vault.is_dir():
        pytest.skip("vault není na tomhle stroji")
    guide = vault / "00-System" / "agent-guide-mimo-cursor.md"
    assert guide.is_file(), "návod ve vaultu chybí"
    text = guide.read_text(encoding="utf-8")
    for reason in ALL_REASONS:
        assert reason in text
    assert "C0C3E0JFNA0" not in text
    assert "next_task_id.py" not in text


def test_t11_morning_prompt_disables_skill_side_effects():
    prompt = (REPO / "ŠABLONY" / "cowork-morning-brief.md").read_text(encoding="utf-8")
    assert "agenda-co-ted" in prompt
    assert "24h" in prompt
    assert "uklid" in prompt
    assert "build_agent_context.py" in prompt
    assert "Do not run build_agent_context.py" in prompt
    assert "Do not move" in prompt
    assert "refresh with `python3 scripts/build_agent_context.py`" not in prompt


def test_t12_cowork_instructions_point_at_guide():
    text = (REPO / "cowork-instructions.md").read_text(encoding="utf-8")
    assert "OBSIDIAN/00-System/agent-guide-mimo-cursor.md" in text
    assert "01-INBOX/daily/" in text
    assert "platí návod" in text
