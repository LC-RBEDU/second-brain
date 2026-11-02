"""finalize_meeting — one commit: meeting note + archive the transcript."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

for _lib in (
    Path("/app/lib"),
    Path(__file__).resolve().parents[3] / "second-brain-hub" / "lib",
):
    if _lib.is_dir() and str(_lib) not in sys.path:
        sys.path.insert(0, str(_lib))
        break

from inbox_archive import attachment_belongs, inbox_archive_rel  # noqa: E402
from task_io import FRONTMATTER_RE  # noqa: E402

from app.errors import BrainClientError  # noqa: E402
from app.vault_deps import brain_vault  # noqa: E402

_SKIP = frozenset({"smoke", "empty", "duplicate", "fragment", "other"})
_KINDS = frozenset({"sembly", "daily"})
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_REQUIRED = (
    "type",
    "material_kind",
    "doc_type",
    "title",
    "meeting_date",
    "participants",
    "variant",
)


def _client(reason: str, message: str, *, status: int = 400, oid: str | None = None, detail: dict | None = None) -> BrainClientError:
    return BrainClientError(
        message=message,
        status_code=status,
        error_reason=reason,
        oid=oid,
        detail=detail,
    )


def _norm_path(raw: str) -> str:
    text = (raw or "").replace("\\", "/").strip()
    if not text or text.startswith("/") or ".." in text.split("/"):
        raise _client("bad_transcript_path", "transcript_path must stay inside 01-INBOX")
    parts = [p for p in text.split("/") if p]
    if len(parts) != 3 or parts[0] != "01-INBOX" or parts[1] not in _KINDS or not parts[2].endswith(".md"):
        if len(parts) >= 2 and parts[0] == "01-INBOX" and parts[1] not in _KINDS:
            raise _client("bad_inbox_kind", "transcript must live in 01-INBOX/sembly or daily")
        raise _client("bad_transcript_path", "transcript_path must be 01-INBOX/sembly|daily/<file>.md")
    if parts[2].startswith("."):
        raise _client("bad_transcript_path", "transcript_path must be a markdown file")
    return "/".join(parts)


def _slugify(title: str) -> str:
    import unicodedata

    text = unicodedata.normalize("NFKD", title)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    text = text[:60].strip("-")
    if not text or not _SLUG_RE.match(text):
        raise _client("bad_slug", "slug could not be derived from title")
    return text


def _check_urls(urls: list[str] | None) -> list[str]:
    if urls is None:
        return []
    if not isinstance(urls, list):
        raise _client("bad_drive_url", "drive_urls must be a list")
    out: list[str] = []
    for item in urls:
        text = str(item or "").strip()
        if not text:
            continue
        if not (text.startswith("http://") or text.startswith("https://")):
            raise _client("bad_drive_url", "drive_urls must be http(s)")
        out.append(text)
    if len(out) > 20:
        raise _client("bad_drive_url", "drive_urls max 20")
    return out


def _split_frontmatter(zapis_md: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(zapis_md)
    if not match:
        raise _client("bad_frontmatter", "zapis_md needs an opening frontmatter fence")
    try:
        loaded = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise _client("bad_frontmatter", f"frontmatter YAML: {exc}") from exc
    if not isinstance(loaded, dict):
        raise _client("bad_frontmatter", "frontmatter must be a mapping")
    return loaded, match.group(2)


def _participants_ok(value: Any) -> bool:
    if isinstance(value, str) and value.strip():
        return True
    if isinstance(value, list) and any(str(item).strip() for item in value):
        return True
    return False


def _compose_zapis(
    zapis_md: str,
    *,
    archive_rel: str,
    drive_urls: list[str],
    meeting_date: str | None,
    slug: str | None,
) -> tuple[str, str, str]:
    fm, body = _split_frontmatter(zapis_md)
    missing = []
    for key in _REQUIRED:
        if key not in fm or fm.get(key) in (None, ""):
            missing.append(key)
    if "participants" not in missing and not _participants_ok(fm.get("participants")):
        missing.append("participants")
    if "variant" not in missing and not str(fm.get("variant") or "").strip():
        missing.append("variant")
    if fm.get("type") not in (None, "", "material") and "type" not in missing:
        missing.append("type")
    if fm.get("type") != "material":
        if "type" not in missing:
            missing.append("type")
    if fm.get("material_kind") != "schuzka" and "material_kind" not in missing:
        missing.append("material_kind")
    if fm.get("doc_type") != "meeting_summary" and "doc_type" not in missing:
        missing.append("doc_type")
    # de-dupe
    missing = list(dict.fromkeys(missing))
    if missing:
        raise _client("missing_fields", "zapis frontmatter is incomplete", detail={"fields": missing})
    raw_date = str(fm.get("meeting_date") or "")[:10]
    if not _DATE_RE.match(raw_date):
        raise _client("bad_frontmatter", "meeting_date must be YYYY-MM-DD")
    if meeting_date and meeting_date != raw_date:
        raise _client("meeting_date_mismatch", "meeting_date does not match frontmatter")
    title = str(fm.get("title") or "").strip()
    use_slug = (slug or "").strip() or _slugify(title)
    if not _SLUG_RE.match(use_slug):
        raise _client("bad_slug", "slug must be kebab-case")
    fm["meeting_date"] = raw_date
    fm["source_transcript"] = archive_rel
    fm["drive_copies"] = drive_urls
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
    text = f"---\n{dumped}---\n{body}"
    zapis_path = f"05-RESOURCES/vystupy/zapisy/{raw_date[:7]}/{raw_date}_{use_slug}_zapis.md"
    return zapis_path, text, raw_date


def _header(archive_body_note: str, transcript: str) -> str:
    return f"**ZPRACOVÁNO**\n{archive_body_note}\n\n{transcript}"


def _archive_header_matches(existing: str, marker: str) -> bool:
    return existing.startswith(f"**ZPRACOVÁNO**\n{marker}\n") or existing.startswith(
        f"**ZPRACOVÁNO**\n{marker}\n\n"
    )


class _Decision:
    def __init__(self) -> None:
        self.zapis_path: str | None = None
        self.archive_path: str = ""
        self.zapis_body: str | None = None
        self.archive_body: str = ""
        self.write_zapis = False
        self.write_archive = False
        self.delete_inbox = False
        self.attachments: list[tuple[str, str]] = []
        self.idempotent = False
        self.warnings: list[str] = []
        self.transcript_oid: str | None = None
        self.zapis_oid: str | None = None
        self.would_write = False


def _read(vault: Any, rel: str) -> tuple[str, Any] | None:
    if not vault.exists(rel):
        return None
    return vault.read_text(rel)


def finalize_meeting(
    *,
    transcript_path: str,
    expect_oid: str | None = None,
    zapis_md: str | None = None,
    meeting_date: str | None = None,
    slug: str | None = None,
    drive_urls: list[str] | None = None,
    skip_reason: str | None = None,
    skip_note: str | None = None,
    dry_run: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = env if env is not None else dict(os.environ)
    rel = _norm_path(transcript_path)
    urls = _check_urls(drive_urls)
    if skip_reason and zapis_md:
        raise _client("bad_request", "pass zapis_md or skip_reason, not both")
    if not skip_reason and not zapis_md:
        raise _client("bad_request", "zapis_md or skip_reason is required")
    if skip_reason and skip_reason not in _SKIP:
        raise _client("bad_skip_reason", "unknown skip_reason")
    if skip_reason == "other" and not str(skip_note or "").strip():
        raise _client("skip_note_required", "skip_reason other needs skip_note")
    try:
        archive_rel = inbox_archive_rel(rel)
    except ValueError as exc:
        raise _client("inbox_date_unparsed", str(exc)) from exc
    kind = archive_rel.split("/")[4]
    if kind not in _KINDS:
        raise _client("bad_inbox_kind", "archive kind must be sembly or daily")

    mode = "read" if dry_run else "mutate"

    def _run(vault: Any) -> _Decision:
        decision = _Decision()
        decision.archive_path = archive_rel
        name = rel.rsplit("/", 1)[-1]
        parent = rel.rsplit("/", 1)[0]
        transcript_hit = _read(vault, rel)
        transcript = transcript_hit[0] if transcript_hit else None
        if transcript_hit is not None:
            meta = transcript_hit[1]
            decision.transcript_oid = getattr(meta, "oid", None)
            if hasattr(vault, "is_tracked") and not vault.is_tracked(rel):
                raise _client("transcript_untracked", "transcript is not tracked")
            if expect_oid and expect_oid != decision.transcript_oid:
                raise _client(
                    "oid_mismatch",
                    "transcript oid mismatch",
                    status=409,
                    oid=decision.transcript_oid,
                )
        zapis_path = None
        zapis_body = None
        if zapis_md:
            zapis_path, zapis_body, raw_date = _compose_zapis(
                zapis_md,
                archive_rel=archive_rel,
                drive_urls=urls,
                meeting_date=meeting_date,
                slug=slug,
            )
            decision.zapis_path = zapis_path
            decision.zapis_body = zapis_body
            month_in_name = name[5:7] if len(name) >= 7 else ""
            if month_in_name and month_in_name != raw_date[5:7]:
                decision.warnings.append("archive_month_differs")
            marker = f"Zápis: {zapis_path}"
        else:
            lines = [f"skip_reason: {skip_reason}"]
            if str(skip_note or "").strip():
                lines.append(f"skip_note: {skip_note.strip()}")
            marker = "\n".join(lines)
        archive_body = _header(marker, transcript or "")
        decision.archive_body = archive_body

        def _zapis_same() -> bool | None:
            if not zapis_path or not zapis_body:
                return None
            hit = _read(vault, zapis_path)
            if hit is None:
                return None
            decision.zapis_oid = getattr(hit[1], "oid", None)
            return hit[0] == zapis_body

        def _archive_header_ok() -> bool | None:
            hit = _read(vault, archive_rel)
            if hit is None:
                return None
            return _archive_header_matches(hit[0], marker)

        if transcript is None:
            same = _zapis_same()
            arch = _archive_header_ok()
            if zapis_path and same is False:
                raise _client("zapis_exists", "zapis already exists", status=409, oid=decision.zapis_oid)
            if arch is False:
                raise _client("archive_exists", "archive already exists", status=409)
            if (zapis_path and same and arch) or (not zapis_path and arch):
                decision.idempotent = True
                if expect_oid:
                    decision.warnings.append("expect_oid_skipped_archived")
                return decision
            if (zapis_path and same and not arch) or (zapis_path and arch and not same):
                raise _client("inconsistent_state", "zapis and archive are out of step", status=409)
            if not zapis_path and not arch and same is None:
                raise _client("transcript_not_found", "transcript not found", status=404)
            raise _client("transcript_not_found", "transcript not found", status=404)

        siblings = vault.list_dir(parent, pattern="*", recursive=False) if hasattr(vault, "list_dir") else []
        moves: list[tuple[str, str]] = []
        for meta in siblings:
            other = getattr(meta, "name", "")
            if not attachment_belongs(name, other):
                continue
            src = f"{parent}/{other}"
            if hasattr(vault, "is_tracked") and not vault.is_tracked(src):
                raise _client("attachment_untracked", f"untracked attachment {other}")
            dst = str(Path(archive_rel).parent / other)
            if vault.exists(dst):
                raise _client("attachment_exists", f"attachment destination exists {dst}", status=409)
            moves.append((src, dst))
        decision.attachments = moves

        same = _zapis_same()
        if zapis_path and same is False:
            raise _client("zapis_exists", "zapis already exists", status=409, oid=decision.zapis_oid)
        arch = _archive_header_ok()
        if arch is False:
            raise _client("archive_exists", "archive already exists", status=409)
        if arch and (not zapis_path or same):
            decision.idempotent = True
            return decision
        decision.write_zapis = bool(zapis_path and same is None)
        decision.write_archive = True
        decision.delete_inbox = True
        decision.would_write = True
        return decision

    sha_before = None
    with brain_vault(mode=mode, env=env) as vault:
        decision = _run(vault)
        if hasattr(vault, "head_sha"):
            sha_before = vault.head_sha()
        if not dry_run and not decision.idempotent:
            if decision.write_zapis and decision.zapis_path and decision.zapis_body is not None:
                vault.write_text(decision.zapis_path, decision.zapis_body)
            if decision.write_archive:
                parent = str(Path(decision.archive_path).parent)
                if hasattr(vault, "mkdir_p"):
                    vault.mkdir_p(parent)
                vault.write_text(decision.archive_path, decision.archive_body)
            for src, dst in decision.attachments:
                vault.move(src, dst)
            if decision.delete_inbox:
                vault.delete(rel)
            vault.commit_message = f"brain: finalize_meeting {decision.archive_path}"
    sha_after = vault.head_sha() if hasattr(vault, "head_sha") else None
    commit = sha_after if sha_after and sha_after != sha_before else None
    return {
        "zapis_path": decision.zapis_path,
        "archive_path": decision.archive_path,
        "zapis_oid": decision.zapis_oid,
        "commit": commit,
        "warnings": decision.warnings,
        "idempotent": decision.idempotent,
        "dry_run": dry_run,
        "transcript_oid": decision.transcript_oid,
        "attachment_paths": [dst for _src, dst in decision.attachments],
        "would_write": decision.would_write and not decision.idempotent,
    }
