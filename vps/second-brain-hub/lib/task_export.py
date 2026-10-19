"""Read-only task snapshot for dashboards. Does not rebuild agent-context."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import yaml

from agent_context_build import HUB_TITLE_RE
from drive_io import DriveNotFoundError
from focus import (
    AGENT_VALUES,
    TERMINAL_STATUSES,
    VALID_STATUSES,
    current_focus_week,
    normalise_agent,
    parse_focus,
)
from hierarchy import (
    HIERARCHY_TYPES,
    normalise_work_type,
    parent_chain_cycle,
    parent_type_error,
    parse_parent_id,
)
from operational_steps import is_operational_header
from promoted_alias import PRAGUE, prague_today
from task_identity import ROTATION_RE, _norm, expected_stem
from task_io import ARCHIV_DIR, FRONTMATTER_RE, PROJEKTY_DIR, parse_iso_date, parse_task_text
from task_query import _date10

_CHECKBOX_RE = re.compile(r"^-\s+\[([ xX])\]")
_FIELDS = frozenset({"standard", "full"})
# Level letter is case-insensitive. Subtask ids (S-S70-1) do not fullmatch.
_ID_LEVEL_RE = re.compile(r"^[A-Za-z]+-([EST])\d+[a-z]?$", re.IGNORECASE)
_LEVEL_TO_TYPE = {"E": "epic", "S": "story", "T": "task"}
# ID at the start of an archive filename. OS6-2026-08-05 does not match (hyphen, not space/end).
_ARCHIVE_STEM_RE = re.compile(r"^([A-Za-z]+(?:-[EST])?\d+[a-z]?)(?:\s|$)")


@dataclass
class _Rec:
    path: str
    folder_slug: str
    fm: dict[str, Any]
    body: str
    oid: str | None
    parse_kind: str | None  # missing_frontmatter | yaml_error | None
    archived: bool


def export_tasks(
    vault: Any,
    *,
    include_closed_days: int = 0,
    projects_csv: str = "",
    fields: str = "standard",
    since: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Frontmatter snapshot. ``count == len(tasks)``. No ``open_count``."""
    since_dt = _validate(include_closed_days, fields, since)
    slugs = _parse_projects_csv(projects_csv)
    moment = _prague_now(now)
    today = prague_today(moment)

    active = _read_active(vault)
    archive = (
        _read_archive(vault, slugs, include_closed_days, moment)
        if include_closed_days > 0
        else []
    )
    indexed = active + archive
    id_index = _id_index(indexed)
    duplicate_ids = _duplicate_id_set(indexed)

    changed: set[str] = set()
    if since_dt is not None and isinstance(since, str):
        fn = getattr(vault, "changed_paths_since", None)
        if callable(fn):
            changed = set(fn(since.strip()))

    chosen: list[_Rec] = []
    for rec in active:
        if _bucket_status(rec.fm.get("status")) in TERMINAL_STATUSES:
            continue
        chosen.append(rec)
    chosen.extend(archive)
    # Name scan only when a chosen parent is absent from the index. projects_csv
    # and since do not narrow it. No missing parent → do not list the archive.
    closed_ids: set[str] = (
        _archive_stem_ids(vault) if _chosen_has_missing_parent(chosen, id_index) else set()
    )

    tasks: list[dict[str, Any]] = []
    slug_filter = set(slugs)
    for rec in chosen:
        if slug_filter and rec.folder_slug not in slug_filter:
            continue
        if since_dt is not None and not _matches_since(rec, since_dt, changed):
            continue
        tasks.append(
            _map_task(
                rec,
                fields=fields,
                id_index=id_index,
                duplicate_ids=duplicate_ids,
                closed_ids=closed_ids,
            )
        )
    tasks.sort(key=lambda row: row["path"])

    projects = _projects(vault, slug_filter)
    head = _vault_head(vault)
    return {
        "generated_at": moment.isoformat(timespec="seconds"),
        "vault_head": head,
        "focus_week": current_focus_week(today),
        "count": len(tasks),
        "projects": projects,
        "tasks": tasks,
    }


def _validate(include_closed_days: int, fields: str, since: str | None) -> datetime | None:
    if (
        isinstance(include_closed_days, bool)
        or not isinstance(include_closed_days, int)
        or include_closed_days < 0
    ):
        raise ValueError("invalid_include_closed_days")
    if fields not in _FIELDS:
        raise ValueError("invalid_fields")
    if since is None:
        return None
    if not isinstance(since, str):
        raise ValueError("invalid_since")
    text = since.strip()
    if not text:
        return None
    return _parse_since(text)


def _parse_since(text: str) -> datetime:
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            day = date.fromisoformat(text)
            return datetime(day.year, day.month, day.day, tzinfo=PRAGUE)
        iso = text[:-1] + "+00:00" if text.endswith("Z") else text
        parsed = datetime.fromisoformat(iso)
    except ValueError as exc:
        raise ValueError("invalid_since") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=PRAGUE)
    return parsed


def _parse_projects_csv(raw: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for token in (raw or "").split(","):
        slug = token.strip()
        if not slug or slug in seen:
            continue
        seen.add(slug)
        out.append(slug)
    return out


def _prague_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(PRAGUE)
    if now.tzinfo is None:
        return now.replace(tzinfo=PRAGUE)
    return now.astimezone(PRAGUE)


def _vault_head(vault: Any) -> str | None:
    fn = getattr(vault, "head_sha", None)
    if not callable(fn):
        return None
    sha = fn()
    if not sha:
        return None
    return str(sha)


def _read_active(vault: Any) -> list[_Rec]:
    try:
        entries = vault.list_dir(PROJEKTY_DIR, include_folders=True)
    except DriveNotFoundError:
        return []
    recs: list[_Rec] = []
    for entry in entries:
        if not getattr(entry, "is_folder", False):
            continue
        slug = entry.name
        try:
            files = vault.list_dir(f"{PROJEKTY_DIR}/{slug}/tasks", pattern="*.md")
        except DriveNotFoundError:
            continue
        for meta in files:
            rec = _read_one(vault, meta.rel_path, slug, archived=False)
            if rec is not None:
                recs.append(rec)
    return recs


def _read_archive(
    vault: Any,
    slugs: list[str],
    days: int,
    now: datetime,
) -> list[_Rec]:
    cutoff = prague_today(now) - timedelta(days=days)
    recs: list[_Rec] = []
    if slugs:
        folders = slugs
    else:
        try:
            entries = vault.list_dir(ARCHIV_DIR, include_folders=True)
        except DriveNotFoundError:
            return []
        folders = [entry.name for entry in entries if getattr(entry, "is_folder", False)]
    for slug in folders:
        try:
            files = vault.list_dir(f"{ARCHIV_DIR}/{slug}", pattern="*.md")
        except DriveNotFoundError:
            continue
        for meta in files:
            rec = _read_one(vault, meta.rel_path, slug, archived=True)
            if rec is None:
                continue
            updated = _prague_day(rec.fm.get("updated"))
            if updated is None or updated < cutoff:
                continue
            recs.append(rec)
    return recs


def _read_one(vault: Any, rel_path: str, slug: str, *, archived: bool) -> _Rec | None:
    try:
        text, meta = vault.read_text(rel_path)
    except DriveNotFoundError:
        return None
    kind, fm, body = _split_frontmatter(text)
    oid = getattr(meta, "oid", None)
    return _Rec(
        path=rel_path,
        folder_slug=slug,
        fm=fm,
        body=body,
        oid=str(oid) if oid else None,
        parse_kind=kind,
        archived=archived,
    )


def _split_frontmatter(text: str) -> tuple[str | None, dict[str, Any], str]:
    matched = FRONTMATTER_RE.match(text)
    if not matched:
        return "missing_frontmatter", {}, text
    try:
        loaded = yaml.safe_load(matched.group(1))
    except yaml.YAMLError:
        return "yaml_error", {}, matched.group(2)
    if not isinstance(loaded, dict):
        return "yaml_error", {}, matched.group(2)
    return None, loaded, matched.group(2)


def _id_index(recs: list[_Rec]) -> dict[str, _Rec]:
    """First record wins. Includes active terminals and this call's archive."""
    out: dict[str, _Rec] = {}
    for rec in recs:
        task_id = _text(rec.fm.get("id"))
        if task_id and task_id not in out:
            out[task_id] = rec
    return out


def _duplicate_id_set(recs: list[_Rec]) -> set[str]:
    grouped: dict[str, list[_Rec]] = {}
    for rec in recs:
        task_id = _text(rec.fm.get("id"))
        if task_id:
            grouped.setdefault(task_id, []).append(rec)
    bad: set[str] = set()
    for task_id, group in grouped.items():
        if len(group) < 2:
            continue
        titles = {_norm(_text(rec.fm.get("title"))) for rec in group}
        non_rotation = [rec for rec in group if not ROTATION_RE.match(_stem(rec.path))]
        if len(non_rotation) <= 1 and len(titles) <= 1:
            continue
        bad.add(task_id)
    return bad


def _parent_of_map(index: dict[str, _Rec]) -> dict[str, str | None]:
    return {task_id: parse_parent_id(rec.fm.get("parent")) for task_id, rec in index.items()}


def _matches_since(rec: _Rec, since_dt: datetime, changed: set[str]) -> bool:
    if rec.path in changed:
        return True
    return _updated_in_since(rec.fm.get("updated"), since_dt)


def _updated_in_since(value: Any, since: datetime) -> bool:
    """Date-only ``updated`` covers the whole Prague calendar day."""
    if value is None:
        return False
    if isinstance(value, datetime):
        moment = value if value.tzinfo is not None else value.replace(tzinfo=PRAGUE)
        return moment >= since
    if isinstance(value, date):
        return value >= since.astimezone(PRAGUE).date()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        if "T" in text:
            iso = text[:-1] + "+00:00" if text.endswith("Z") else text
            try:
                moment = datetime.fromisoformat(iso)
            except ValueError:
                return False
            if moment.tzinfo is None:
                moment = moment.replace(tzinfo=PRAGUE)
            return moment >= since
        day = parse_iso_date(text)
        if day is None:
            return False
        return day >= since.astimezone(PRAGUE).date()
    return False


def _prague_day(value: Any) -> date | None:
    if isinstance(value, datetime):
        moment = value if value.tzinfo is not None else value.replace(tzinfo=PRAGUE)
        return moment.astimezone(PRAGUE).date()
    return parse_iso_date(value)


def _project_hierarchy(fm: dict[str, Any]) -> bool:
    return bool(
        fm.get("hierarchy") is True
        or str(fm.get("hierarchy") or "").lower() in {"true", "1", "yes"}
        or (fm.get("slug") or "") == "rb-universe-development"
    )


def _projects(vault: Any, slug_filter: set[str]) -> list[dict[str, Any]]:
    """Charter slug, title, status, hierarchy. No section excerpts, no charter oid."""
    rows: list[dict[str, Any]] = []
    try:
        hubs = vault.list_dir("02-PROJEKTY", pattern="*.md")
    except DriveNotFoundError:
        return rows
    for meta in sorted(hubs, key=lambda item: item.name):
        if meta.name.startswith("_"):
            continue
        try:
            text, _meta = vault.read_text(meta.rel_path)
        except DriveNotFoundError:
            continue
        parsed = parse_task_text(text, rel_path=meta.rel_path)
        fm = parsed.frontmatter
        if (fm.get("type") or "").lower() != "project":
            continue
        body = parsed.body or ""
        slug = fm.get("slug") or meta.name.removesuffix(".md").lower().replace(" ", "-")
        slug = str(slug)
        if slug_filter and slug not in slug_filter:
            continue
        heading = HUB_TITLE_RE.search(body)
        if heading:
            title = heading.group(1).strip()
        else:
            title = fm.get("title") or meta.name.removesuffix(".md")
        rows.append(
            {
                "slug": slug,
                "title": str(title).strip(),
                "status": str(fm.get("status") or "active"),
                "hierarchy": _project_hierarchy(fm),
            }
        )
    rows.sort(key=lambda row: row["slug"])
    return rows


def _chosen_has_missing_parent(chosen: list[_Rec], id_index: dict[str, _Rec]) -> bool:
    for rec in chosen:
        parent, unparsed = _parent_field(rec.fm.get("parent"))
        if unparsed or not parent:
            continue
        if parent not in id_index:
            return True
    return False


def _archive_stem_ids(vault: Any) -> set[str]:
    """IDs from archive filenames. Two levels, like ``_read_archive``. No ``read_text``."""
    found: set[str] = set()
    try:
        entries = vault.list_dir(ARCHIV_DIR, include_folders=True)
    except DriveNotFoundError:
        return found
    for entry in entries:
        if not getattr(entry, "is_folder", False):
            continue
        slug = entry.name
        try:
            files = vault.list_dir(f"{ARCHIV_DIR}/{slug}", pattern="*.md")
        except DriveNotFoundError:
            continue
        for meta in files:
            stem = _stem(getattr(meta, "rel_path", None) or getattr(meta, "name", ""))
            matched = _ARCHIVE_STEM_RE.match(stem)
            if matched:
                found.add(matched.group(1))
    return found


def _map_task(
    rec: _Rec,
    *,
    fields: str,
    id_index: dict[str, _Rec],
    duplicate_ids: set[str],
    closed_ids: set[str],
) -> dict[str, Any]:
    fm = rec.fm
    task_id = _text(fm.get("id"))
    title = _text(fm.get("title"))
    status_out = _status_out(fm.get("status"))
    raw_type = fm.get("type")
    work_type = normalise_work_type(raw_type)
    parent, parent_unparsed = _parent_field(fm.get("parent"))
    focus, focus_unparsed = _focus_field(fm.get("focus"))
    agent, unknown_agent = _agent_field(fm.get("agent"))
    ice_i, ice_c, ice_e, ice_bad = _ice_fields(fm)
    score = _priority_score(ice_i, ice_c, ice_e)
    errors = _parse_errors(
        rec,
        task_id=task_id,
        title=title,
        status_out=status_out,
        work_type=work_type,
        raw_type=raw_type,
        parent=parent,
        parent_unparsed=parent_unparsed,
        id_index=id_index,
        duplicate_ids=duplicate_ids,
        unknown_agent=unknown_agent,
        focus_unparsed=focus_unparsed,
        ice_bad=ice_bad,
        closed_ids=closed_ids,
    )
    steps_total, steps_done = _count_steps(rec.body)
    row: dict[str, Any] = {
        "id": task_id,
        "title": title,
        "type": work_type,
        "status": status_out,
        "parent": parent,
        "project": rec.folder_slug,
        "path": rec.path,
        "oid": rec.oid,
        "deadline": _date10(fm.get("deadline")),
        "review_deadline": _date10(fm.get("review_deadline")),
        "waitUntil": _date10(fm.get("waitUntil")),
        "focus": focus,
        "agent": agent,
        "ice_i": ice_i,
        "ice_c": ice_c,
        "ice_e": ice_e,
        "priority_score": score,
        "is_recurring": bool(fm.get("recurring")),
        "promoted_from": _text(fm.get("promoted_from")) or None,
        "created": _stamp(fm.get("created")),
        "updated": _stamp(fm.get("updated")),
        "steps_total": steps_total,
        "steps_done": steps_done,
        "filename_title_mismatch": _filename_mismatch(rec.path, task_id, title),
        "parse_errors": errors,
    }
    if fields == "full":
        row["materials"] = _str_list(fm.get("materials"))
        row["blocked_by"] = _str_list(fm.get("blocked_by"))
        row["company_priorities"] = _str_list(fm.get("company_priorities"))
        row["source"] = _json_value(fm.get("source"))
    return row


def _parse_errors(
    rec: _Rec,
    *,
    task_id: str,
    title: str,
    status_out: str,
    work_type: str,
    raw_type: Any,
    parent: str | None,
    parent_unparsed: bool,
    id_index: dict[str, _Rec],
    duplicate_ids: set[str],
    unknown_agent: bool,
    focus_unparsed: bool,
    ice_bad: bool,
    closed_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    if rec.parse_kind == "missing_frontmatter":
        errors.append("missing_frontmatter")
    if rec.parse_kind == "yaml_error":
        errors.append("yaml_error")
    if not task_id:
        errors.append("missing_id")
    if not title:
        errors.append("missing_title")
    if status_out and status_out not in VALID_STATUSES:
        errors.append("unknown_status")
    fm_slug = _text(rec.fm.get("slug"))
    if fm_slug and fm_slug != rec.folder_slug:
        errors.append("slug_mismatch")
    parent_missing = False
    if parent_unparsed:
        errors.append("parent_unparsed")
    elif parent and parent in id_index:
        parent_rec = id_index[parent]
        # Active Done/Cancelled (archived False) is not parent_closed.
        # A non-terminal loaded from the archive is not parent_closed either.
        if parent_rec.archived and _bucket_status(parent_rec.fm.get("status")) in TERMINAL_STATUSES:
            errors.append("parent_closed")
    elif parent and parent in closed_ids:
        # Stem hit only. Type is not read, so parent_missing blocks parent_not_found.
        errors.append("parent_closed")
        parent_missing = True
    elif parent:
        errors.append("parent_not_found")
        parent_missing = True
    if not parent_unparsed and not parent_missing:
        parent_type = None
        if parent and parent in id_index:
            parent_type = normalise_work_type(id_index[parent].fm.get("type"))
        reason = parent_type_error(work_type, task_id, parent, parent_type)
        if reason:
            errors.append(reason)
        if (
            parent
            and task_id
            and reason != "parent_cycle"
            and parent_chain_cycle(task_id, parent, _parent_of_map(id_index))
        ):
            errors.append("parent_cycle")
    if task_id and task_id in duplicate_ids:
        errors.append("duplicate_id")
    if _nonempty(raw_type) and str(raw_type).strip().lower() not in HIERARCHY_TYPES:
        errors.append("unknown_type")
    if _id_type_mismatch(task_id, raw_type):
        errors.append("id_type_mismatch")
    if unknown_agent:
        errors.append("unknown_agent")
    if focus_unparsed:
        errors.append("focus_unparsed")
    if ice_bad:
        errors.append("ice_not_int")
    if rec.archived and _bucket_status(rec.fm.get("status")) not in TERMINAL_STATUSES:
        errors.append("archived_not_terminal")
    return errors


def _bucket_status(raw: Any) -> str:
    return str(raw or "Next")


def _status_out(raw: Any) -> str:
    if raw is None:
        return ""
    return str(raw).strip()


def _parent_field(raw: Any) -> tuple[str | None, bool]:
    parent = parse_parent_id(raw)
    if parent is None and _nonempty(raw):
        return None, True
    return parent, False


def _focus_field(raw: Any) -> tuple[str | None, bool]:
    focus = parse_focus(raw)
    if focus is None and _nonempty(raw) and str(raw).strip().lower() not in {"null", "none"}:
        return None, True
    return focus, False


def _agent_field(raw: Any) -> tuple[str, bool]:
    agent = normalise_agent(raw)
    unknown = _nonempty(raw) and str(raw).strip().lower() not in AGENT_VALUES
    return agent, unknown


def _ice_fields(fm: dict[str, Any]) -> tuple[int | None, int | None, int | None, bool]:
    bad = False
    values: list[int | None] = []
    for key in ("ice_i", "ice_c", "ice_e"):
        number, was_bad = _ice_int(fm.get(key))
        bad = bad or was_bad
        values.append(number)
    return values[0], values[1], values[2], bad


def _ice_int(value: Any) -> tuple[int | None, bool]:
    if value is None:
        return None, False
    if isinstance(value, str) and not value.strip():
        return None, False
    if isinstance(value, bool) or not isinstance(value, int):
        return None, True
    return value, False


def _priority_score(ice_i: int | None, ice_c: int | None, ice_e: int | None) -> float | None:
    if ice_i is None or ice_c is None or ice_e is None or ice_e == 0:
        return None
    return round((ice_i * ice_c) / ice_e, 2)


def _count_steps(body: str) -> tuple[int, int]:
    total = 0
    done = 0
    in_section = False
    for line in (body or "").split("\n"):
        if is_operational_header(line):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            in_section = False
            continue
        if not in_section:
            continue
        matched = _CHECKBOX_RE.match(line)
        if not matched:
            continue
        total += 1
        if matched.group(1) in "xX":
            done += 1
    return total, done


def _alnum(text: str) -> str:
    """NFC, then casefold, then letters and digits in order."""
    folded = unicodedata.normalize("NFC", str(text)).casefold()
    return "".join(ch for ch in folded if ch.isalnum())


def _id_type_mismatch(task_id: str, raw_type: Any) -> bool:
    """Raw epic|story|task vs the level letter. Missing/unknown type adds nothing."""
    if not _nonempty(raw_type):
        return False
    raw = str(raw_type).strip().lower()
    if raw not in _LEVEL_TO_TYPE.values():
        return False
    matched = _ID_LEVEL_RE.fullmatch(task_id)
    if not matched:
        return False
    expected = _LEVEL_TO_TYPE[matched.group(1).upper()]
    return expected != raw


def _filename_mismatch(path: str, task_id: str, title: str) -> bool:
    stem = _stem(path)
    if not task_id or not title or ROTATION_RE.match(stem):
        return False
    return _alnum(stem) != _alnum(expected_stem(task_id, title))


def _stem(path: str) -> str:
    return path.rsplit("/", 1)[-1].removesuffix(".md")


def _stamp(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _str_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    return str(value)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict)):
        return True
    return bool(str(value).strip()) and str(value).strip().lower() not in {"null", "none"}
