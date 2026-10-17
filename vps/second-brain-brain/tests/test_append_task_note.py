"""append_task_note — section insert, CAS, idempotence (plan T1–T42)."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_BRAIN = Path(__file__).resolve().parents[1]
_HUB = _BRAIN.parent / "second-brain-hub" / "lib"
for p in (_BRAIN, _HUB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ.setdefault("BRAIN_ALLOW_NO_PUSH", "1")
os.environ.setdefault("BRAIN_SERVICE_TOKEN", "test-service-token")

from app.errors import BrainClientError  # noqa: E402
from app.tools import append_task_note as mod  # noqa: E402
from drive_io import DriveConflictError, DriveNotFoundError  # noqa: E402

PATH = "02-PROJEKTY/second-brain/tasks/SB-S17 — Test.md"
TODAY = date(2026, 10, 14)


def _md(
    *,
    body: str,
    status: str = "Next",
    typ: str = "story",
    task_id: str = "SB-S17",
    extra: str = "",
    updated: str = "updated: 2026-10-01\n",
) -> str:
    return (
        f"---\nid: {task_id}\ntype: {typ}\ntitle: Test\nstatus: {status}\n"
        f"focus: 2026-W41\n{updated}{extra}---\n{body}"
    )


class _CM:
    def __init__(self, vault):
        self.vault = vault

    def __enter__(self):
        return self.vault

    def __exit__(self, *args):
        return False


def _vault(text: str, *, oid: str = "oid1"):
    vault = MagicMock()
    meta = MagicMock()
    meta.oid = oid
    vault.read_text.return_value = (text, meta)
    meta2 = MagicMock()
    meta2.oid = "oid2"
    vault.write_text.return_value = meta2
    return vault


def _call(file_text: str | None, **kwargs):
    vault = _vault(file_text or "")
    if file_text is None:
        vault.read_text.side_effect = DriveNotFoundError("missing")
    cm = _CM(vault)
    tomb = MagicMock(return_value=[])
    with (
        patch.object(mod, "_prague_today", return_value=TODAY),
        patch.object(mod, "brain_vault", return_value=cm),
        patch.object(mod, "delete_context_tombstone", tomb),
    ):
        try:
            result = mod.append_task_note(
                path=kwargs.pop("path", PATH),
                text=kwargs.pop("text"),
                target=kwargs.pop("target"),
                expect_oid=kwargs.pop("expect_oid", None),
                env=kwargs.pop("env", None),
            )
        except BrainClientError as exc:
            return exc, vault, tomb
    return result, vault, tomb


def _written(vault) -> str:
    return vault.write_text.call_args[0][1]


def _body(written: str) -> str:
    return written.split("---\n", 2)[-1]


def test_t1_log_before_next_heading_and_steps_stay():
    body = (
        "## Operativní kroky\n"
        "- [x] **SB-S17-2** later\n"
        "- [ ] **SB-S17-1** earlier\n\n"
        "## Poznámky / log\n"
        "- 2026-10-01: old\n\n"
        "## Jiné\n"
        "x\n"
    )
    result, vault, _tomb = _call(_md(body=body), text="foo", target="log")
    assert result["already_present"] is False
    assert result["inserted_line"] == "- 2026-10-14: foo"
    assert result["target"] == "log"
    assert result["step_id"] is None
    assert "BODY" not in result
    written = _body(_written(vault))
    log = written.split("## Poznámky / log\n", 1)[1].split("## Jiné", 1)[0]
    assert log.rstrip().endswith("- 2026-10-14: foo")
    assert "- [x] **SB-S17-2** later\n- [ ] **SB-S17-1** earlier" in written
    dated, vault2, _t = _call(
        _md(body="## Poznámky / log\n"),
        text="2026-10-01: starší",
        target="log",
    )
    assert dated["inserted_line"] == "- 2026-10-01: starší"
    assert "- 2026-10-14: 2026-10-01" not in _written(vault2)


def test_t2_creates_log_section():
    result, vault, _t = _call(_md(body="# t\n"), text="foo", target="log")
    body = _body(_written(vault))
    assert "## Operativní kroky" not in body
    assert body.rstrip().endswith("## Poznámky / log\n- 2026-10-14: foo")
    assert result["already_present"] is False


def test_t3_numbering_and_section_before_log():
    body = (
        "## Operativní kroky\n"
        "- [ ] **SB-S17-1** a\n"
        "- [x] **SB-S17-3b** b\n"
    )
    result, vault, _t = _call(_md(body=body), text="c", target="step")
    assert "- [ ] **SB-S17-4** c" in _written(vault)
    assert result["step_id"] == "SB-S17-4"
    body2 = "# t\n\n\n## Poznámky / log\n- old\n"
    _result, vault2, _t2 = _call(
        _md(body=body2),
        text="new",
        target="step",
    )
    lines = _body(_written(vault2)).splitlines()
    assert lines[0] == "# t"
    assert lines[1] == ""
    assert lines[2] == ""
    assert lines[3] == "## Operativní kroky"
    assert lines[4] == "- [ ] **SB-S17-1** new"
    assert lines[5] == "## Poznámky / log"
    epic, vault3, tomb = _call(
        _md(body="## Poznámky / log\n", typ="epic"),
        text="nope",
        target="step",
    )
    assert isinstance(epic, BrainClientError)
    assert epic.error_reason == "epic_has_no_steps"
    assert vault3.write_text.call_count == 0
    done, vault4, tomb4 = _call(
        _md(body="# t\n", status="Done"),
        text="nope",
        target="step",
    )
    assert done.error_reason == "task_terminal"
    assert vault4.write_text.call_count == 0
    assert tomb4.call_count == 0


def test_t4_sort_open_before_checked():
    body = "## Operativní kroky\n- [x] **SB-S17-1** done\n"
    result, vault, _t = _call(_md(body=body), text="open", target="step")
    written = _written(vault)
    assert isinstance(written, str)
    open_at = written.index("- [ ] **SB-S17-2** open")
    done_at = written.index("- [x] **SB-S17-1** done")
    assert open_at < done_at
    assert "- [x] **SB-S17-1** done" in written
    assert result["step_id"] == "SB-S17-2"


def test_t5_subheading_blocks_new_step():
    body = "## Operativní kroky\n### Skupina\n- [ ] **SB-S17-1** a\n"
    err, vault, tomb = _call(_md(body=body), text="b", target="step")
    assert err.error_reason == "step_section_has_subheadings"
    assert vault.write_text.call_count == 0
    assert tomb.call_count == 0


def test_t6_idempotent_log_updated_is_string_and_next_day_is_new():
    body = "## Poznámky / log\n- 2026-10-14: foo\n"
    result, vault, tomb = _call(_md(body=body), text="foo", target="log")
    assert result["already_present"] is True
    assert result["updated"] == "2026-10-01"
    assert isinstance(result["updated"], str)
    assert vault.write_text.call_count == 0
    assert tomb.call_count == 0
    bad, vault2, _t = _call(
        _md(body=body, updated="updated: not-a-date\n"),
        text="foo",
        target="log",
    )
    assert bad["updated"] is None
    assert vault2.write_text.call_count == 0
    nxt, vault3, tomb3 = _call(
        _md(body="## Poznámky / log\n- 2026-10-13: foo\n"),
        text="foo",
        target="log",
    )
    assert nxt["already_present"] is False
    assert "- 2026-10-14: foo" in _written(vault3)
    assert tomb3.call_count == 1


def test_t7_step_label_whitespace_and_checked():
    body = (
        "## Operativní kroky\n"
        "### Pozn\n"
        "- [X] **SB-S17-1** foo bar\n"
    )
    result, vault, _t = _call(_md(body=body), text="foo  bar", target="step")
    assert result["already_present"] is True
    assert result["step_id"] == "SB-S17-1"
    assert vault.write_text.call_count == 0
    fresh, vault2, _t2 = _call(_md(body=body), text="Foo", target="step")
    assert isinstance(fresh, BrainClientError)
    assert fresh.error_reason == "step_section_has_subheadings"
    other, vault3, _t3 = _call(
        _md(body="## Operativní kroky\n- [ ] a b\n"),
        text="ab",
        target="step",
    )
    assert other["already_present"] is False
    assert vault3.write_text.call_count == 1


def test_t8_rejects_before_vault():
    for kwargs in (
        {"text": "   ", "target": "log"},
        {"text": "- [ ]", "target": "log"},
        {"text": "- ", "target": "log"},
        {"text": "a\nb", "target": "log"},
        {"text": "a\rb", "target": "step"},
        {"text": "x" * 1001, "target": "log"},
    ):
        with patch.object(mod, "brain_vault") as vault_cm:
            with pytest.raises(BrainClientError) as caught:
                mod.append_task_note(path=PATH, **kwargs)
        assert vault_cm.call_count == 0
        assert caught.value.status_code == 400
        assert caught.value.error_reason in {
            "empty_text",
            "text_must_be_single_line",
            "text_too_long",
        }


def test_t9_invalid_path():
    for path in (
        "07-ARCHIV/tasks-done/x/SB-S17.md",
        "02-PROJEKTY/Hub.md",
        "02-PROJEKTY/second-brain/materials/a.md",
        "../02-PROJEKTY/second-brain/tasks/a.md",
        "",
    ):
        with patch.object(mod, "brain_vault") as vault_cm:
            with pytest.raises(BrainClientError) as caught:
                mod.append_task_note(path=path, text="a", target="log")
        assert vault_cm.call_count == 0
        assert caught.value.error_reason == "invalid_task_path"


def test_t10_read_cas():
    err, vault, tomb = _call(_md(body="# t\n"), text="a", target="log", expect_oid="other")
    assert err.error_reason == "cas_conflict"
    assert err.status_code == 409
    assert vault.write_text.call_count == 0
    assert tomb.call_count == 0


def test_t11_write_conflict_calls_write():
    text = _md(body="# t\n")
    vault = _vault(text)
    vault.write_text.side_effect = DriveConflictError("clash")
    with (
        patch.object(mod, "_prague_today", return_value=TODAY),
        patch.object(mod, "brain_vault", return_value=_CM(vault)),
        patch.object(mod, "delete_context_tombstone") as tomb,
    ):
        with pytest.raises(BrainClientError) as caught:
            mod.append_task_note(path=PATH, text="a", target="log")
    assert caught.value.error_reason == "cas_conflict"
    assert vault.write_text.call_count == 1
    assert tomb.call_count == 1


def test_t12_missing_file():
    err, vault, _t = _call(None, text="a", target="log")
    assert err.status_code == 404
    assert err.error_reason == "not_found"
    assert vault.write_text.call_count == 0


def test_t13_no_frontmatter():
    err, _v, _t = _call("# jen nadpis\n", text="a", target="log")
    assert err.error_reason == "no_frontmatter"


def test_t14_missing_id():
    text = "---\ntype: story\nstatus: Next\nupdated: 2026-10-01\n---\n# t\n"
    err, _v, _t = _call(text, text="bar", target="step")
    assert err.error_reason == "task_id_missing"


def test_t15_success_keeps_status_focus_and_skips_cas_kwarg():
    body = "## Stav (auto)\n\nstay\n\n## Poznámky / log\n"
    result, vault, tomb = _call(
        _md(body=body, status="Doing"),
        text="note",
        target="log",
    )
    written = _written(vault)
    assert "status: Doing" in written
    assert "focus: 2026-W41" in written
    assert "updated: 2026-10-14" in written
    assert "## Stav (auto)" in written
    assert "- [x]" not in written.split("## Poznámky / log", 1)[-1]
    assert result["updated"] == "2026-10-14"
    assert isinstance(result["updated"], str)
    kwargs = vault.write_text.call_args.kwargs
    assert "expect_oid" not in kwargs
    assert tomb.call_count == 1
    assert "build_agent_context" not in written


def test_t16_target_alias():
    result, _v, _t = _call(_md(body="# t\n"), text="a", target="Note")
    assert result["target"] == "log"
    step, _v2, _t2 = _call(
        _md(body="## Operativní kroky\n"),
        text="a",
        target="STEP",
    )
    assert step["target"] == "step"
    err, _v3, _t3 = _call(_md(body="# t\n"), text="a", target="notes")
    assert err.error_reason == "invalid_target"


def test_t17_anonymous_post_401():
    from fastapi.testclient import TestClient

    from app.main import app

    with patch.object(mod, "brain_vault") as vault_cm:
        response = TestClient(app).post(
            "/v1/tasks/append",
            json={"path": PATH, "text": "a", "target": "log"},
        )
    assert response.status_code == 401
    assert vault_cm.call_count == 0


def test_t18_call_is_not_focus_policy():
    result, _v, _t = _call(_md(body="# t\n"), text="a", target="log")
    assert result["target"] == "log"
    assert "deny_focus_write" not in Path(mod.__file__).read_text()


def test_t19_mcp_and_rest_share_function():
    from fastapi.testclient import TestClient

    from app.mcp_app import build_mcp
    from app.main import app

    server = build_mcp()
    names = [tool.name for tool in server._tool_manager.list_tools()]
    assert "append_task_note" in names
    sentinel = {
        "path": PATH,
        "target": "log",
        "oid": "o",
        "already_present": False,
        "inserted_line": "- 2026-10-14: a",
        "step_id": None,
        "updated": "2026-10-14",
    }
    with patch(
        "app.tools.append_task_note.append_task_note",
        return_value=sentinel,
    ) as fn:
        response = TestClient(app).post(
            "/v1/tasks/append",
            headers={"Authorization": "Bearer test-service-token"},
            json={"path": PATH, "text": "a", "target": "LOG"},
        )
        assert response.status_code == 200
        assert fn.call_count == 1
        from app.mcp_app import _call as mcp_call
        from app.mcp_app import append_task_note_tool

        mcp_call(
            append_task_note_tool.append_task_note,
            path=PATH,
            text="a",
            target="log",
        )
        assert fn.call_count == 2


def test_t20_update_task_keeps_body_and_hub_append_is_eof():
    from app.tools import update_task as update_mod
    from task_io import ParsedTask, update_task as hub_update

    original = _md(body="BODY\n## Poznámky / log\n- old\n", typ="task", task_id="SB-T17")
    vault = _vault(original)
    with patch.object(update_mod, "brain_vault", return_value=_CM(vault)):
        update_mod.update_task(path=PATH, patch={"status": "Doing"})
    written = _written(vault)
    assert "BODY\n## Poznámky / log\n- old\n" in written
    assert "status: Doing" in written

    hub_vault = MagicMock()
    task = ParsedTask(PATH, {"id": "SB-S17", "status": "Next"}, "BODY\n", None)
    assert hub_update(hub_vault, task, body_append="- tail\n", today_str="2026-10-14")
    hub_written = hub_vault.write_text.call_args[0][1]
    assert hub_written.rstrip().endswith("BODY\n- tail")


def test_t22_epic_rules():
    epic_body = (
        "## Definition of done (epic)\n\n- [ ] hotovo\n\n## Poznámky / log\n\n"
    )
    err, vault, tomb = _call(_md(body=epic_body, typ="epic", task_id="SB-E1"), text="x", target="step")
    assert err.error_reason == "epic_has_no_steps"
    assert vault.write_text.call_count == 0
    assert tomb.call_count == 0
    err2, _v2, _t2 = _call(
        _md(body=epic_body, typ="epic", task_id="SB-E1", status="Done"),
        text="x",
        target="step",
    )
    assert err2.error_reason == "epic_has_no_steps"
    text = (
        "---\nid: SB-E1\nwork_type: epic\ntitle: E\nstatus: Next\nupdated: 2026-10-01\n---\n"
        + epic_body
    )
    err3, _v3, _t3 = _call(text, text="x", target="step")
    assert err3.error_reason == "epic_has_no_steps"
    with_steps = epic_body + "## Operativní kroky\n- [ ] **SB-E1-1** a\n"
    ok, vault4, _t4 = _call(
        _md(body=with_steps, typ="epic", task_id="SB-E1"),
        text="b",
        target="step",
    )
    assert "- [ ] **SB-E1-2** b" in _written(vault4)
    logged, vault5, _t5 = _call(
        _md(body=epic_body, typ="epic", task_id="SB-E1"),
        text="pozn",
        target="log",
    )
    written = _written(vault5)
    assert "- [ ] hotovo" in written
    assert "- 2026-10-14: pozn" in written
    assert logged["target"] == "log"


def test_t23_terminal_log_and_step():
    for status in ("Done", "Cancelled"):
        ok, vault, _t = _call(
            _md(body="## Poznámky / log\n", status=status),
            text="later",
            target="log",
        )
        written = _written(vault)
        assert f"status: {status}" in written
        assert "- 2026-10-14: later" in written
        assert ok["already_present"] is False
        err, vault2, tomb = _call(
            _md(body="## Operativní kroky\n- [ ] **SB-S17-1** a\n", status=status),
            text="b",
            target="step",
        )
        assert err.error_reason == "task_terminal"
        assert vault2.write_text.call_count == 0
        assert tomb.call_count == 0
    same, vault3, tomb3 = _call(
        _md(body="## Operativní kroky\n- [ ] **SB-S17-1** a\n", status="Done"),
        text="a",
        target="step",
    )
    assert same["already_present"] is True
    assert vault3.write_text.call_count == 0
    assert tomb3.call_count == 0
    missing, vault4, _t4 = _call(
        _md(body="# t\n", status="Cancelled"),
        text="z",
        target="step",
    )
    assert missing.error_reason == "task_terminal"
    assert vault4.write_text.call_count == 0


def test_t24_prefixes_and_foreign_id():
    ok, vault, _t = _call(_md(body="# t\n"), text="- [ ] foo", target="log")
    assert ok["inserted_line"] == "- 2026-10-14: foo"
    ok2, _v2, _t2 = _call(_md(body="# t\n"), text="- foo", target="log")
    assert ok2["inserted_line"] == "- 2026-10-14: foo"
    for target in ("log", "step"):
        err, vault3, _t3 = _call(
            _md(body="## Operativní kroky\n"),
            text="- [ ] **RBU-S70-1** foo",
            target=target,
        )
        assert err.error_reason == "text_contains_step_id"
        assert vault3.write_text.call_count == 0
    note, _v4, _t4 = _call(_md(body="# t\n"), text="a", target="Note")
    assert note["target"] == "log"
    step, _v5, _t5 = _call(
        _md(body="## Operativní kroky\n"),
        text="a",
        target="STEP",
    )
    assert step["target"] == "step"


def test_t25_hash_does_not_end_section_subheading_does_not():
    body = (
        "## Operativní kroky\n"
        "- [ ] **SB-S17-1** a\n"
        "# mezi\n"
        "## Poznámky / log\n"
    )
    _ok, vault, _t = _call(_md(body=body), text="b", target="step")
    written = _written(vault)
    assert written.index("- [ ] **SB-S17-2** b") < written.index("# mezi")
    body2 = "## Operativní kroky\n### Skupina\n- [ ] **SB-S17-1** only\n"
    hit, _v2, _t2 = _call(_md(body=body2), text="only", target="step")
    assert hit["already_present"] is True


def test_t26_bad_yaml():
    cases = (
        "---\n- a\n- b\n---\n# t\n",
        "---\nhello\n---\n# t\n",
        "---\n: :\n---\n# t\n",
    )
    for text in cases:
        err, vault, tomb = _call(text, text="a", target="log")
        assert err.error_reason == "invalid_frontmatter"
        assert vault.write_text.call_count == 0
        assert tomb.call_count == 0
    empty = "---\n\n---\n# t\n"
    err2, _v2, _t2 = _call(empty, text="bar", target="step")
    assert err2.error_reason == "task_id_missing"


def test_t27_bold_warning_is_not_a_step_id():
    body = "## Operativní kroky\n- [ ] **Pozor** foo\n"
    hit, vault, _t = _call(_md(body=body), text="**Pozor** foo", target="step")
    assert hit["already_present"] is True
    assert vault.write_text.call_count == 0
    fresh, vault2, _t2 = _call(_md(body=body), text="foo", target="step")
    assert fresh["already_present"] is False
    assert "**SB-S17-1** foo" in _written(vault2)


def test_t28_id_types_and_order():
    for raw_id in ("id: 17\n", "id: true\n", "id:\n  - a\n", "id: {a: 1}\n"):
        text = f"---\n{raw_id}type: story\nstatus: Next\nupdated: 2026-10-01\n---\n## Operativní kroky\n- [ ] foo\n"
        hit, vault, _t = _call(text, text="foo", target="step")
        assert hit["already_present"] is True
        assert vault.write_text.call_count == 0
        err, _v2, _t2 = _call(text, text="bar", target="step")
        assert err.error_reason == "task_id_missing"
        foreign, _v3, _t3 = _call(text, text="**RBU-S70-1** x", target="step")
        assert foreign.error_reason == "text_contains_step_id"


def test_t29_step_id_suffix_and_missing_updated():
    body = "## Operativní kroky\n- [x] **SB-S17-3b** foo  \n"
    text = "---\nid: SB-S17\ntype: story\nstatus: Next\n---\n" + body
    hit, vault, _t = _call(text, text="foo", target="step")
    assert hit["already_present"] is True
    assert hit["step_id"] == "SB-S17-3b"
    assert hit["inserted_line"] == "- [x] **SB-S17-3b** foo"
    assert hit["updated"] is None
    assert vault.write_text.call_count == 0
    fresh, _v2, _t2 = _call(text, text="bar", target="step")
    assert fresh["updated"] == "2026-10-14"
    assert isinstance(fresh["updated"], str)


def test_t30_number_sources():
    body = (
        "## Operativní kroky\n"
        "- [x] **sb-s17-9** other case\n"
        "- [X] **SB-S17-2** counted\n"
        "- [ ] see **SB-S17-8** mid\n"
        "  - [ ] **SB-S17-7** indented\n"
        "## Poznámky / log\n"
        "- **SB-S17-6** in log\n"
    )
    _ok, vault, _t = _call(_md(body=body), text="new", target="step")
    assert "- [ ] **SB-S17-3** new" in _written(vault)
    only_foreign, vault2, _t2 = _call(
        _md(body="## Operativní kroky\n- [ ] **OTHER-1** a\n"),
        text="b",
        target="step",
    )
    assert "- [ ] **SB-S17-1** b" in _written(vault2)
    assert only_foreign["step_id"] == "SB-S17-1"


def test_t31_type_wins_over_work_type():
    text = (
        "---\nid: SB-S17\ntype: story\nwork_type: epic\nstatus: Next\n"
        "updated: 2026-10-01\n---\n## Poznámky / log\n"
    )
    _ok, vault, _t = _call(text, text="a", target="step")
    assert "## Operativní kroky" in _written(vault)
    bare = (
        "---\nid: SB-E1\nwork_type: epic\nstatus: Next\nupdated: 2026-10-01\n---\n# t\n"
    )
    err, _v2, _t2 = _call(bare, text="a", target="step")
    assert err.error_reason == "epic_has_no_steps"


def test_t32_appends_missing_updated_only():
    text = "---\nid: SB-S17\ntype: story\nstatus: Next\n---\n# t\n"
    _ok, vault, _t = _call(text, text="a", target="log")
    written = _written(vault)
    assert "updated: 2026-10-14" in written
    assert "\nstatus:" not in written.split("---\n", 2)[1].replace("status: Next", "", 1)
    fm = written.split("---\n", 2)[1]
    assert "focus:" not in fm


def test_t33_template_comment_then_bullet():
    body = (
        "## Poznámky / log\n"
        "<!--\n"
        "komentář\n"
        "-->\n"
    )
    _ok, vault, _t = _call(_md(body=body), text="po", target="log")
    lines = _body(_written(vault)).splitlines()
    assert lines[lines.index("-->") + 1] == "- 2026-10-14: po"


def test_t34_creates_only_target_section():
    step, vault, _t = _call(_md(body="# t\n"), text="a", target="step")
    body = _body(_written(vault))
    assert "## Poznámky / log" not in body
    assert body.index("## Operativní kroky") + len("## Operativní kroky") < body.index(
        "- [ ] **SB-S17-1** a"
    )
    assert "\n\n- [ ]" not in body.split("## Operativní kroky", 1)[1]
    assert step["target"] == "step"
    log, vault2, _t2 = _call(_md(body="# t\n"), text="a", target="log")
    body2 = _body(_written(vault2))
    assert "## Operativní kroky" not in body2
    assert "\n\n- 2026-10-14" not in body2.split("## Poznámky / log", 1)[1]
    assert log["inserted_line"] == "- 2026-10-14: a"


def test_t35_trailing_blanks_stay_under_bullet():
    body = "## Poznámky / log\n- old\n\n\n## Jiné\n"
    _ok, vault, _t = _call(_md(body=body), text="new", target="log")
    chunk = _body(_written(vault)).split("## Poznámky / log\n", 1)[1].split("## Jiné", 1)[0]
    assert chunk == "- old\n- 2026-10-14: new\n\n\n"
    steps = "## Operativní kroky\n- [x] **SB-S17-1** a\n\n\n## Poznámky / log\n"
    _ok2, vault2, _t2 = _call(_md(body=steps), text="b", target="step")
    chunk2 = _body(_written(vault2)).split("## Operativní kroky\n", 1)[1]
    before_log = chunk2.split("## Poznámky / log", 1)[0]
    assert "- [ ] **SB-S17-2** b" in before_log
    assert before_log.index("- [ ] **SB-S17-2** b") < before_log.index("- [x] **SB-S17-1** a")
    assert before_log.endswith("\n\n\n") 


def test_t36_first_match_wins():
    body = (
        "## Operativní kroky\n"
        "- [x] **SB-S17-4** foo\n"
        "- [ ] **SB-S17-9** foo\n"
    )
    hit, vault, _t = _call(_md(body=body), text="foo", target="step")
    assert hit["already_present"] is True
    assert hit["step_id"] == "SB-S17-4"
    assert vault.write_text.call_count == 0


def test_t37_strips_id_spaces():
    text = '---\nid: " SB-S17 "\ntype: story\nstatus: Next\nupdated: 2026-10-01\n---\n## Operativní kroky\n- [ ] **SB-S17-1** a\n'
    _ok, vault, _t = _call(text, text="**SB-S17-1** b", target="step")
    assert "- [ ] **SB-S17-2** b" in _written(vault)
    err, vault2, _t2 = _call(text, text="**RBU-S70-1** c", target="step")
    assert err.error_reason == "text_contains_step_id"
    assert vault2.write_text.call_count == 0


def test_t38_numeric_max():
    body = "## Operativní kroky\n- [ ] **SB-S17-9** a\n- [ ] **SB-S17-10** b\n"
    _ok, vault, _t = _call(_md(body=body), text="c", target="step")
    written = _written(vault)
    assert "- [ ] **SB-S17-11** c" in written
    assert written.count("**SB-S17-10**") == 1


def test_t39_subprocess_import():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_BRAIN)
    env.pop("PYTHONSAFEPATH", None)
    completed = subprocess.run(
        [sys.executable, "-c", "import app.tools.append_task_note"],
        cwd=_BRAIN,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_t40_write_text_gets_string():
    body = "## Operativní kroky\n- [ ] **SB-S17-1** a\n"
    _ok, vault, _t = _call(_md(body=body), text="b", target="step")
    args = vault.write_text.call_args
    assert isinstance(args[0][1], str)
    assert not isinstance(args[0][1], tuple)


def test_t41_exact_bullet_inside_comment():
    bullet = "- 2026-10-14: hidden"
    body = f"## Poznámky / log\n<!--\n{bullet}\n-->\n"
    hit, vault, _t = _call(_md(body=body), text="hidden", target="log")
    assert hit["already_present"] is True
    assert vault.write_text.call_count == 0
    other, vault2, _t2 = _call(_md(body=body), text="visible", target="log")
    lines = _body(_written(vault2)).splitlines()
    assert lines[lines.index("-->") + 1] == "- 2026-10-14: visible"


def test_t42_eof_blanks_stay():
    body = "## Poznámky / log\n- old\n\n\n"
    _ok, vault, _t = _call(_md(body=body), text="new", target="log")
    written_body = _body(_written(vault))
    assert written_body.endswith("- old\n- 2026-10-14: new\n\n\n")
    assert not written_body.endswith("\n\n\n\n")
