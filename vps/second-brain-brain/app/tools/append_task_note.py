"""append_task_note — one bullet into an existing task log or steps (CAS)."""
from __future__ import annotations

import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

import yaml  # noqa: E402
from context_tombstone import delete_context_tombstone  # noqa: E402
from drive_io import DriveConflictError, DriveNotFoundError  # noqa: E402
from hierarchy import is_epic  # noqa: E402
from operational_steps import (  # noqa: E402
    _CHECKBOX_RE,
    _SUBTASK_ID_RE,
    is_operational_header,
    sort_operational_steps,
)

from app.errors import BrainClientError  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402

_TASK_PATH_RE = re.compile(r"^02-PROJEKTY/[^/]+/tasks/[^/]+\.md$")
_FM_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)
_CHECKBOX_PREFIX_RE = re.compile(r"^-\s+\[[ xX]\]\s*")
_DASH_PREFIX_RE = re.compile(r"^-\s+")
_DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}:")
_YMD_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LOG_HEADER = "## Poznámky / log"
_TERMINAL = frozenset({"Done", "Cancelled"})


def _prague_today(env: dict[str, str] | None = None) -> date:
    env_map = env if env is not None else os.environ
    tz_name = (env_map.get("TZ") or "Europe/Prague").strip() or "Europe/Prague"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Europe/Prague")
    return datetime.now(tz).date()


def _client(message: str, status: int, reason: str) -> BrainClientError:
    return BrainClientError(message=message, status_code=status, error_reason=reason)


def _collapse_spaces(text: str) -> str:
    return re.sub(r" {2,}", " ", text.strip())


def _strip_leading_subtask(text: str) -> str:
    matched = _SUBTASK_ID_RE.match(text)
    if not matched:
        return text
    rest = text[matched.end() :]
    if rest.startswith(" "):
        rest = rest[1:]
    return rest


def _norm_step_label(raw: str) -> str:
    return _strip_leading_subtask(_collapse_spaces(raw))


def _step_id_from_label(raw: str) -> str | None:
    matched = _SUBTASK_ID_RE.match(raw.strip())
    if not matched:
        return None
    return f"{matched.group('base')}-{matched.group('num')}{matched.group('suffix')}"


def _updated_json(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()[:10]
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        cleaned = value.strip().strip('"').strip("'")
        return cleaned if _YMD_RE.fullmatch(cleaned) else None
    return None


def _body_lines(body: str) -> list[str]:
    if body.endswith("\n"):
        return body.split("\n")[:-1]
    if body == "":
        return []
    return body.split("\n")


def _join_body(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def _is_section_end(line: str) -> bool:
    return line.startswith("## ") or (line.startswith("#") and not line.startswith("###"))


def _find_section(lines: list[str], kind: str) -> tuple[int, int] | None:
    start: int | None = None
    for index, line in enumerate(lines):
        if kind == "step" and is_operational_header(line):
            start = index
            break
        if kind == "log" and line.strip() == _LOG_HEADER:
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if _is_section_end(lines[index]):
            end = index
            break
    return start, end


def _insert_after_last_nonempty(section: list[str], bullet: str) -> list[str]:
    last = -1
    for index, line in enumerate(section):
        if line.strip():
            last = index
    return section[: last + 1] + [bullet] + section[last + 1 :]


def _next_step_number(section: list[str], task_id: str) -> int:
    numbers: list[int] = []
    for line in section:
        box = _CHECKBOX_RE.match(line)
        if not box:
            continue
        ident = _SUBTASK_ID_RE.match(box.group(2).strip())
        if ident and ident.group("base") == task_id:
            numbers.append(int(ident.group("num")))
    return max(numbers) + 1 if numbers else 1


def _patch_updated(fm_raw: str, today: str) -> str:
    lines = fm_raw.splitlines(keepends=True)
    done = False
    new_lines: list[str] = []
    for line in lines:
        if ":" in line and not line.strip().startswith("#"):
            key = line.split(":", 1)[0].strip()
            if key == "updated":
                new_lines.append(f"updated: {today}\n")
                done = True
                continue
        new_lines.append(line if line.endswith("\n") else line + "\n")
    if not done:
        new_lines.append(f"updated: {today}\n")
    return "".join(new_lines)


def _canon_target(target: str) -> str:
    folded = (target or "").strip().casefold()
    if folded in {"log", "note"}:
        return "log"
    if folded == "step":
        return "step"
    raise _client("invalid target", 400, "invalid_target")


def _remainder(text: str, canon: str) -> str:
    remainder = _CHECKBOX_PREFIX_RE.sub("", text, count=1)
    if canon == "log":
        remainder = _DASH_PREFIX_RE.sub("", remainder, count=1)
    remainder = remainder.strip()
    if not remainder:
        raise _client("empty text", 400, "empty_text")
    if len(remainder) > 1000:
        raise _client("text too long", 400, "text_too_long")
    return remainder


def _log_bullet(remainder: str, today: date) -> str:
    if _DATE_PREFIX_RE.match(remainder):
        return f"- {remainder}"
    return f"- {today.isoformat()}: {remainder}"


def append_task_note(
    *,
    path: str,
    text: str,
    target: str,
    expect_oid: str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    cleaned_path = (path or "").strip()
    if not _TASK_PATH_RE.fullmatch(cleaned_path):
        raise _client("invalid task path", 400, "invalid_task_path")
    canon = _canon_target(target)
    raw_text_in = text or ""
    if "\n" in raw_text_in or "\r" in raw_text_in:
        raise _client("text must be a single line", 400, "text_must_be_single_line")
    remainder = _remainder(raw_text_in, canon)

    today = _prague_today(env)
    today_s = today.isoformat()

    with brain_vault(mode="mutate", env=env) as vault:
        try:
            raw_text, meta = vault.read_text(cleaned_path)
        except DriveNotFoundError as exc:
            raise _client("not found", 404, "not_found") from exc
        oid = getattr(meta, "oid", None)
        if expect_oid is not None and oid is not None and str(oid) != str(expect_oid):
            raise _client(
                f"CAS conflict expect_oid={expect_oid!r} got={oid!r}",
                409,
                "cas_conflict",
            )
        matched = _FM_RE.match(raw_text)
        if not matched:
            raise _client("no frontmatter", 400, "no_frontmatter")
        fm_raw, body = matched.group(1), matched.group(2)
        try:
            loaded = yaml.safe_load(fm_raw)
        except yaml.YAMLError as exc:
            raise _client("invalid frontmatter", 400, "invalid_frontmatter") from exc
        if loaded is None:
            fm: dict[str, Any] = {}
        elif not isinstance(loaded, dict):
            raise _client("invalid frontmatter", 400, "invalid_frontmatter")
        else:
            fm = loaded

        status = str(fm.get("status") or "Next")
        epic = is_epic(fm)
        raw_id = fm.get("id")
        task_id = raw_id.strip() if isinstance(raw_id, str) and raw_id.strip() else None

        ident = _SUBTASK_ID_RE.match(remainder)
        if ident and (task_id is None or ident.group("base") != task_id):
            raise _client("text contains a foreign step id", 400, "text_contains_step_id")
        if canon == "step" and task_id is not None and ident and ident.group("base") == task_id:
            remainder = _strip_leading_subtask(remainder).strip()
            if not remainder:
                raise _client("empty text", 400, "empty_text")

        lines = _body_lines(body)
        found = _find_section(lines, canon)
        section = lines[found[0] + 1 : found[1]] if found else []

        if canon == "log":
            bullet = _log_bullet(remainder, today)
            if found:
                for line in section:
                    if line.strip() == bullet:
                        return _present(
                            cleaned_path,
                            canon,
                            oid,
                            line.rstrip(),
                            None,
                            _updated_json(fm.get("updated") if "updated" in fm else None),
                        )
        else:
            wanted = _norm_step_label(remainder)
            if found:
                for line in section:
                    box = _CHECKBOX_RE.match(line)
                    if not box:
                        continue
                    if _norm_step_label(box.group(2)) == wanted:
                        return _present(
                            cleaned_path,
                            canon,
                            oid,
                            line.rstrip(),
                            _step_id_from_label(box.group(2)),
                            _updated_json(fm.get("updated") if "updated" in fm else None),
                        )
            if found is None and epic:
                raise _client("epic has no steps", 400, "epic_has_no_steps")
            if status in _TERMINAL:
                raise _client("task is terminal", 409, "task_terminal")
            if task_id is None:
                raise _client("task id missing", 400, "task_id_missing")
            if any(line.startswith("### ") for line in section):
                raise _client(
                    "step section has subheadings",
                    400,
                    "step_section_has_subheadings",
                )
            number = _next_step_number(section, task_id)
            bullet = f"- [ ] **{task_id}-{number}** {remainder}"

        if found:
            new_section = _insert_after_last_nonempty(section, bullet)
            header, end = found
            lines = lines[: header + 1] + new_section + lines[end:]
        elif canon == "log":
            lines.extend([_LOG_HEADER, bullet])
        else:
            block = ["## Operativní kroky", bullet]
            log_at = next(
                (i for i, line in enumerate(lines) if line.strip() == _LOG_HEADER),
                None,
            )
            if log_at is None:
                lines.extend(block)
            else:
                lines[log_at:log_at] = block

        new_body = _join_body(lines)
        if canon == "step":
            new_body, _changed = sort_operational_steps(new_body)
            if not new_body.endswith("\n"):
                new_body += "\n"
        new_fm = _patch_updated(fm_raw, today_s)
        new_text = "---\n" + new_fm + "---\n" + new_body
        if new_text == raw_text:
            return _present(
                cleaned_path,
                canon,
                oid,
                bullet,
                _step_id_from_label(bullet.split("]", 1)[-1]) if canon == "step" else None,
                _updated_json(fm.get("updated") if "updated" in fm else None),
            )
        delete_context_tombstone(vault)
        kwargs: dict[str, Any] = {}
        if expect_oid is not None:
            kwargs["expect_oid"] = expect_oid
        try:
            meta2 = vault.write_text(cleaned_path, new_text, **kwargs)
        except DriveConflictError as exc:
            raise _client(str(exc), 409, "cas_conflict") from exc
        step_id = None
        if canon == "step":
            step_id = _step_id_from_label(bullet.split("]", 1)[-1])
        return {
            "path": cleaned_path,
            "target": canon,
            "oid": getattr(meta2, "oid", None),
            "already_present": False,
            "inserted_line": bullet,
            "step_id": step_id,
            "updated": today_s,
        }


def _present(
    path: str,
    target: str,
    oid: Any,
    inserted: str,
    step_id: str | None,
    updated: str | None,
) -> dict[str, Any]:
    return {
        "path": path,
        "target": target,
        "oid": oid,
        "already_present": True,
        "inserted_line": inserted,
        "step_id": step_id,
        "updated": updated,
    }
