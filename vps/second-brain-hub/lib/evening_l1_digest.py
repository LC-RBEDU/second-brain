"""Evening L1 digest — match Brain triage sources to open tasks → digests/ + Saturnin."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from drive_io import DriveConflictError, DriveNotFoundError, FileMeta, cas_from_meta
from hierarchy import is_epic
from reminder_chat_delivery import send_grok_chat
from task_io import iter_active_tasks

TZ = ZoneInfo(os.environ.get("TZ", "Europe/Prague"))
DIGEST_DIR = "00-System/digests"
BODY_CAP_BYTES = 3072
HEAD_CAP_BYTES = 8192
SOFT_GROK_CHARS = int(os.environ.get("EVENING_DIGEST_GROK_CHARS") or "28000")
BRAIN_TIMEOUT = float(os.environ.get("EVENING_DIGEST_BRAIN_TIMEOUT") or "120")

STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "for",
        "is",
        "na",
        "pro",
        "do",
        "ze",
        "za",
        "od",
        "po",
        "se",
        "si",
        "je",
        "jsou",
        "aby",
        "když",
        "který",
        "která",
        "které",
        "this",
        "that",
        "with",
        "from",
    }
)
TOKEN_RE = re.compile(r"[a-zá-ž0-9]+", re.IGNORECASE)

PATH_SOURCES = ("slack_dump", "email_dump", "daily", "sembly")
LIVE_SOURCES = ("live_slack", "gmail")


@dataclass
class MatchTask:
    task_id: str
    title: str
    body_cap: str
    rel_path: str


@dataclass
class Candidate:
    source_key: str
    ref: str
    haystack: str
    preview: str
    link: str = ""


@dataclass
class Hit:
    source_key: str
    preview: str
    link: str
    how: str  # id | title | body


@dataclass
class MatchResult:
    matched: dict[str, list[Hit]] = field(default_factory=dict)  # task_id -> hits
    unmatched: list[Candidate] = field(default_factory=list)
    task_meta: dict[str, MatchTask] = field(default_factory=dict)
    partial_errors: list[str] = field(default_factory=list)
    total_degrade: bool = False
    degrade_reason: str = ""
    pool_source: str = "vault_scan"
    candidate_count: int = 0


def writers_paused(env: Mapping[str, str] | None = None) -> bool:
    env_map = env if env is not None else os.environ
    raw = (env_map.get("VAULT_WRITERS_PAUSED") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def digest_rel_path(day: str) -> str:
    return f"{DIGEST_DIR}/{day}-evening-l1.md"


def fetch_l1_brain(
    *,
    brain_url: str | None = None,
    token: str | None = None,
    env: Mapping[str, str] | None = None,
    timeout_s: float = BRAIN_TIMEOUT,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (payload, total_error). total_error set → total degrade."""
    env_map = env if env is not None else os.environ
    url = (brain_url if brain_url is not None else env_map.get("BRAIN_PUBLIC_URL") or "").rstrip("/")
    tok = (token if token is not None else env_map.get("BRAIN_SERVICE_TOKEN") or "").strip()
    if not url or not tok:
        return None, "brain_env_missing"
    req = urllib.request.Request(
        f"{url}/v1/triage/candidates?include_live_slack=true&include_gmail=true",
        method="GET",
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
            if not isinstance(data, dict):
                return None, "brain_bad_json"
            return data, None
    except urllib.error.HTTPError as exc:
        return None, f"brain_http_{exc.code}"
    except Exception as exc:  # noqa: BLE001
        return None, f"brain_error:{type(exc).__name__}"


def load_match_pool(vault: Any) -> list[MatchTask]:
    out: list[MatchTask] = []
    for task in iter_active_tasks(vault):
        if task.is_terminal:
            continue
        if is_epic(task):
            continue
        tid = (task.task_id or "").strip()
        if not tid:
            continue
        title = str(task.frontmatter.get("title") or tid)
        body = task.body or ""
        body_cap = body.encode("utf-8")[:BODY_CAP_BYTES].decode("utf-8", errors="ignore")
        out.append(
            MatchTask(
                task_id=tid,
                title=title,
                body_cap=body_cap,
                rel_path=task.rel_path,
            )
        )
    return out


def _tokens(text: str, *, min_len: int) -> set[str]:
    found: set[str] = set()
    for m in TOKEN_RE.finditer(text.casefold()):
        t = m.group(0)
        if len(t) >= min_len and t not in STOP:
            found.add(t)
    return found


def _id_pattern(task_id: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![A-Za-z0-9]){re.escape(task_id)}(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


def flatten_candidates(sources: dict[str, Any]) -> list[Candidate]:
    out: list[Candidate] = []
    for item in sources.get("live_slack") or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "")
        link = str(item.get("permalink") or "")
        ref = str(item.get("ts") or link or text[:40])
        out.append(
            Candidate(
                source_key="live_slack",
                ref=ref,
                haystack=text,
                preview=text[:280],
                link=link,
            )
        )
    for item in sources.get("gmail") or []:
        if not isinstance(item, dict):
            continue
        subject = str(item.get("subject") or "")
        ref = str(item.get("id") or subject[:40])
        out.append(
            Candidate(
                source_key="gmail",
                ref=ref,
                haystack=subject,
                preview=subject[:280],
                link="",
            )
        )
    for key in PATH_SOURCES:
        for path in sources.get(key) or []:
            if not isinstance(path, str) or not path.endswith(".md"):
                continue
            out.append(
                Candidate(
                    source_key=key,
                    ref=path,
                    haystack="",  # filled by enrich
                    preview=path.rsplit("/", 1)[-1][:280],
                    link=path,
                )
            )
    return out


def enrich_path_sources(vault: Any, candidates: list[Candidate]) -> list[Candidate]:
    enriched: list[Candidate] = []
    for c in candidates:
        if c.source_key not in PATH_SOURCES:
            enriched.append(c)
            continue
        path = c.ref
        try:
            text, _ = vault.read_text(path)
        except DriveNotFoundError:
            stem = path.rsplit("/", 1)[-1]
            enriched.append(
                Candidate(
                    source_key=c.source_key,
                    ref=path,
                    haystack=stem,
                    preview=stem[:280],
                    link=path,
                )
            )
            continue
        except Exception:
            stem = path.rsplit("/", 1)[-1]
            enriched.append(
                Candidate(
                    source_key=c.source_key,
                    ref=path,
                    haystack=stem,
                    preview=stem[:280],
                    link=path,
                )
            )
            continue
        head = text.encode("utf-8")[:HEAD_CAP_BYTES].decode("utf-8", errors="ignore")
        stem = path.rsplit("/", 1)[-1]
        hay = f"{stem}\n{head}"
        # preview from body without huge FM
        body_preview = head
        if body_preview.startswith("---"):
            parts = body_preview.split("---", 2)
            if len(parts) >= 3:
                body_preview = parts[2]
        enriched.append(
            Candidate(
                source_key=c.source_key,
                ref=path,
                haystack=hay,
                preview=body_preview.strip()[:280] or stem[:280],
                link=path,
            )
        )
    return enriched


def match_candidates(pool: list[MatchTask], candidates: list[Candidate]) -> MatchResult:
    result = MatchResult(
        task_meta={t.task_id: t for t in pool},
        candidate_count=len(candidates),
    )
    id_pats = {t.task_id: _id_pattern(t.task_id) for t in pool}
    title_toks = {t.task_id: _tokens(t.title, min_len=3) for t in pool}
    body_toks = {t.task_id: _tokens(t.body_cap, min_len=4) for t in pool}

    for cand in candidates:
        hay = cand.haystack or ""
        hay_fold = hay.casefold()
        hay_tokens = _tokens(hay, min_len=3)
        hits_for_cand = False
        for t in pool:
            how: str | None = None
            if id_pats[t.task_id].search(hay):
                how = "id"
            elif title_toks[t.task_id] & hay_tokens:
                how = "title"
            elif body_toks[t.task_id] & _tokens(hay, min_len=4):
                how = "body"
            if how:
                hits_for_cand = True
                result.matched.setdefault(t.task_id, []).append(
                    Hit(
                        source_key=cand.source_key,
                        preview=cand.preview[:280],
                        link=cand.link,
                        how=how,
                    )
                )
        if not hits_for_cand:
            result.unmatched.append(cand)
    return result


def parse_deliver(md_text: str) -> str | None:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", md_text, re.DOTALL)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.startswith("deliver:"):
            val = line.split(":", 1)[1].strip().strip("\"'")
            return val or None
    return None


def saturnin_payload(md_body: str, *, soft_chars: int = SOFT_GROK_CHARS) -> str:
    if len(md_body) <= soft_chars:
        return md_body
    return md_body[:soft_chars] + "\n\n… truncated; full digest in vault\n"


def render_digest_md(
    *,
    day: str,
    match: MatchResult,
    generated_at: str,
) -> str:
    fm = [
        "---",
        "type: evening-l1-digest",
        f"date: {day}",
        f"pool_source: {match.pool_source}",
        f"generated_at: {generated_at}",
        f"candidate_count: {match.candidate_count}",
        f"matched_tasks: {len(match.matched)}",
        f"unmatched: {len(match.unmatched)}",
    ]
    if match.partial_errors:
        fm.append(f"partial_errors: {json.dumps(match.partial_errors, ensure_ascii=False)}")
    if match.total_degrade:
        fm.append(f"total_degrade: true")
        fm.append(f"degrade_reason: {match.degrade_reason}")
    fm.append("---")
    lines = fm + [
        "",
        f"# Evening L1 — {day}",
        "",
        "_Snapshot ~18:00 (Europe/Prague), ne kompletní denní aktivita. CTA only — 0 auto-create._",
        "",
        "## Stav zdrojů",
        "",
    ]
    if match.total_degrade:
        lines.append(f"- **Total degrade:** `{match.degrade_reason}`")
    elif match.partial_errors:
        lines.append(f"- **Partial:** {', '.join(match.partial_errors)}")
    else:
        lines.append("- L1 OK")
    lines.append(f"- Pool: `{match.pool_source}` ({len(match.task_meta)} open tasks excl. epic)")
    lines.append(f"- Candidates: {match.candidate_count}")
    lines.append("")

    # matched display
    ranked = sorted(
        match.matched.items(),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )
    shown_tasks = ranked[:40]
    trunc_tasks = max(0, len(ranked) - 40)
    lines.append(f"## Matched ({len(ranked)}, shown≤40)")
    lines.append("")
    if not shown_tasks:
        lines.append("_Žádný match._")
        lines.append("")
    for tid, hits in shown_tasks:
        meta = match.task_meta.get(tid)
        title = meta.title if meta else tid
        lines.append(f"### {tid} — {title}")
        for h in hits[:8]:
            link = f" — {h.link}" if h.link else ""
            lines.append(f"- [{h.source_key}/{h.how}] {h.preview}{link}")
        if len(hits) > 8:
            lines.append(f"- … truncated_hits (+{len(hits) - 8})")
        lines.append("")
    if trunc_tasks:
        lines.append(f"_truncated_tasks (+{trunc_tasks})_")
        lines.append("")

    unmatched = match.unmatched
    shown_u = unmatched[:40]
    trunc_u = max(0, len(unmatched) - 40)
    lines.append(f"## Unmatched — zvaž založit ({len(unmatched)}, shown≤40)")
    lines.append("")
    if not shown_u:
        lines.append("_Nic bez páru._")
        lines.append("")
    else:
        for i, c in enumerate(shown_u, 1):
            link = f" — `{c.link}`" if c.link else ""
            lines.append(f"{i}. [{c.source_key}] {c.preview}{link}")
        lines.append("")
        lines.append("CTA: řekni Saturninovi „založ úkol z večerního digestu #N“.")
        lines.append("")
    if trunc_u:
        lines.append(f"_truncated_unmatched (+{trunc_u})_")
        lines.append("")

    if match.candidate_count == 0:
        lines.append("## Prázdný den")
        lines.append("")
        lines.append("0 L1 kandidátů — cron OK. Projeď live triáž, pokud čekáš na něco mimo L1.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _yaml_scalar(value: str) -> str:
    """Quote FM values that break unquoted YAML (colons, newlines, …)."""
    return json.dumps(value, ensure_ascii=False)


def patch_deliver_frontmatter(
    vault: Any,
    rel: str,
    *,
    status: str,
    detail: str,
    meta: FileMeta | None,
) -> bool:
    """CAS-patch deliver status. Returns False on DriveConflictError (no false OK)."""
    text, cur_meta = vault.read_text(rel)
    use_meta = meta or cur_meta
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)$", text, re.DOTALL)
    now = datetime.now(TZ).isoformat(timespec="seconds")
    detail_q = _yaml_scalar(detail)
    if not m:
        new_text = (
            f"---\ntype: evening-l1-digest\ndeliver: {status}\n"
            f"delivered_at: {now}\ndeliver_detail: {detail_q}\n---\n{text}"
        )
    else:
        fm = m.group(2)
        lines = [
            ln
            for ln in fm.splitlines()
            if not ln.startswith(("deliver:", "delivered_at:", "deliver_detail:"))
        ]
        lines.append(f"deliver: {status}")
        lines.append(f"delivered_at: {now}")
        lines.append(f"deliver_detail: {detail_q}")
        new_text = m.group(1) + "\n".join(lines) + m.group(3) + m.group(4)
    try:
        vault.write_text(rel, new_text, **cas_from_meta(use_meta))
    except DriveConflictError:
        return False
    return True


def build_match_from_brain(
    vault: Any,
    payload: dict[str, Any] | None,
    *,
    total_error: str | None,
) -> MatchResult:
    pool = load_match_pool(vault)
    if total_error:
        result = MatchResult(
            task_meta={t.task_id: t for t in pool},
            total_degrade=True,
            degrade_reason=total_error,
            candidate_count=0,
        )
        return result
    assert payload is not None
    sources = payload.get("sources") or {}
    if not isinstance(sources, dict):
        sources = {}
    cands = flatten_candidates(sources)
    cands = enrich_path_sources(vault, cands)
    result = match_candidates(pool, cands)
    err = payload.get("error_reason")
    if err:
        result.partial_errors.append(str(err))
    return result


def deliver_to_saturnin(md_body: str, *, day: str, dry_run: bool = False) -> tuple[bool, str]:
    if dry_run:
        return True, "dry-run"
    msg = saturnin_payload(md_body)
    res = send_grok_chat(
        {
            "message": msg,
            "id": f"evening-l1-{day}",
            "source": "second-brain-hub",
        }
    )
    return bool(res.ok), res.detail or ("ok" if res.ok else "fail")
