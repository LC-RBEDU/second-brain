#!/usr/bin/env python3
"""Extract Lukáš commitments from sent email INBOX markdown (heuristic + optional LLM)."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Callable

# Czech commitment / promise language (first-person or outbound promises).
_COMMITMENT_RE = re.compile(
    r"\b("
    r"přislíbím|slíbím|pošlu|zašlu|odešlu|odšlu|dodám|zajistím|domluvím|"
    r"připravím|dám\s+vědět|ozvu\s+se|napíšu|zkontroluju|zkontroluji|"
    r"prověřím|projdu|udělám|doplním|dokončím|předám|"
    r"schválím|reviewnu|pořeším|vyřeším|nastavím|upravím|opravím|"
    r"pošleme|zašleme|zajistíme|domluvíme|připravíme|dodáme|"
    r"do\s+(?:pondělí|úterý|středy|čtvrtka|pátku|soboty|neděle|"
    r"zítra|dnes|týdne|měsíce|\d{1,2}\.\s*\d{1,2}\.)"
    r")\b",
    re.IGNORECASE,
)

_DEADLINE_HINT_RE = re.compile(
    r"\b(do\s+(?:pondělí|úterý|středy|čtvrtka|pátku|soboty|neděle|"
    r"zítra|dnes|týdne|měsíce|\d{1,2}\.\s*\d{1,2}\.))\b",
    re.IGNORECASE,
)

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

_SUBJECT_PREFIX_RE = re.compile(r"^(Re:|Fwd:|FW:|RE:|FWD:)\s*", re.IGNORECASE)

# Odeslané e-maily matching (to + subject) — neukládat do INBOX (n8n) + smazat z INBOX (cron).
_SENT_INBOX_DROP_RULES: tuple[dict[str, str], ...] = (
    {
        "to": "finance@redbutton.cz",
        "subject": "Fakturace dealu",
        "reason": "rutinní fakturace dealu na finance — mimo Second Brain INBOX",
    },
)

# Back-compat alias (tests / starší volání)
_SENT_TRIAGE_IGNORE_RULES = _SENT_INBOX_DROP_RULES


def _normalize_subject(subject: str) -> str:
    s = (subject or "").strip()
    while True:
        m = _SUBJECT_PREFIX_RE.match(s)
        if not m:
            break
        s = s[m.end() :].strip()
    return s


def _extract_email_address(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    m = re.search(r"<([^>]+)>", raw)
    if m:
        return m.group(1).strip().lower()
    first = raw.split(",")[0].strip()
    return first.lower()


def parse_sent_email_headers(body: str) -> dict[str, str]:
    """Return normalized ``to`` (email) and ``subject`` from sent INBOX markdown."""
    fm = parse_frontmatter(body)
    to_raw = fm.get("to", "")
    subject = fm.get("subject", "")
    if not to_raw:
        m = re.search(r"^\*\*To\*\*:\s*(.+)$", body, re.M)
        if m:
            to_raw = m.group(1).strip()
    if not subject:
        m = re.search(r"^#\s*Email:\s*(.+)$", body, re.M)
        if m:
            subject = m.group(1).strip()
    return {
        "to": _extract_email_address(to_raw),
        "subject": _normalize_subject(subject),
    }


def should_drop_sent_email_from_inbox(rel_path: str, body: str) -> tuple[bool, str]:
    """True when sent capture matches a drop rule (do not keep in INBOX)."""
    if not is_sent_email(rel_path, body):
        return False, ""
    meta = parse_sent_email_headers(body)
    for rule in _SENT_INBOX_DROP_RULES:
        rule_to = rule["to"].strip().lower()
        rule_subj = _normalize_subject(rule["subject"])
        if meta["to"] == rule_to and meta["subject"].lower() == rule_subj.lower():
            reason = rule.get("reason") or f"drop to={rule_to!r} subject={rule_subj!r}"
            return True, reason
    return False, ""


def should_ignore_sent_email_for_triage(rel_path: str, body: str) -> tuple[bool, str]:
    """Alias — drop rules = no triage (file should not be in INBOX)."""
    return should_drop_sent_email_from_inbox(rel_path, body)


def purge_dropped_sent_inbox(vault, items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Delete sent INBOX captures matching drop rules (+ co-located attachments)."""
    kept: list[tuple[str, str]] = []
    for rel, body in items:
        drop, reason = should_drop_sent_email_from_inbox(rel, body)
        if not drop:
            kept.append((rel, body))
            continue
        print("purge sent inbox drop:", rel, reason)
        try:
            vault.delete(rel)
        except Exception:
            print("  already gone:", rel)
            continue
        parent, _, name = rel.rpartition("/")
        stem = name[:-3] if name.endswith(".md") else name
        prefix = f"{stem}__"
        if parent:
            try:
                for meta in vault.list_dir(parent, recursive=False):
                    if meta.name.startswith(prefix):
                        vault.delete(meta.rel_path)
                        print("  purge attachment:", meta.rel_path)
            except Exception:
                pass
    return kept


def is_sent_email(rel_path: str, body: str) -> bool:
    norm = rel_path.replace("\\", "/")
    if "/email/sent/" in norm or norm.endswith("/sent") or "/sent/" in norm:
        return True
    fm = parse_frontmatter(body)
    if fm.get("source", "").lower() == "sent":
        return True
    head = body[:600]
    if re.search(r"^\*\*Source\*\*:\s*sent\s*$", head, re.I | re.M):
        return True
    if "**Source**: sent" in head:
        return True
    return False


def parse_frontmatter(body: str) -> dict[str, str]:
    m = _FRONTMATTER_RE.match(body)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        out[key.strip().lower()] = val.strip()
    return out


def email_body_text(body: str) -> str:
    text = body
    text = _FRONTMATTER_RE.sub("", text, count=1)
    for marker in ("## Tělo", "## Body", "## Obsah"):
        idx = text.find(marker)
        if idx != -1:
            text = text[idx + len(marker) :]
            break
    text = re.sub(r"^# .+\n", "", text, count=1)
    text = re.sub(r"^\*\*[^*]+\*\*:\s*.+\n", "", text, flags=re.M)
    return text.strip()


def _snippet_around(text: str, start: int, end: int, radius: int = 120) -> str:
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    snippet = text[a:b].strip()
    snippet = re.sub(r"\s+", " ", snippet)
    return snippet[:280]


def _split_sentences(text: str) -> list[tuple[str, int, int]]:
    parts: list[tuple[str, int, int]] = []
    for m in re.finditer(r"[^.!?\n]+[.!?]?", text):
        chunk = m.group(0).strip()
        if len(chunk) >= 8:
            parts.append((chunk, m.start(), m.end()))
    if not parts and text.strip():
        parts.append((text.strip(), 0, len(text)))
    return parts


def heuristic_extract(
    rel_path: str,
    body: str,
    *,
    guess_proj: Callable[[str, str], str],
) -> list[dict]:
    text = email_body_text(body)
    if not text:
        return []

    proposals: list[dict] = []
    seen: set[str] = set()
    name = rel_path.rsplit("/", 1)[-1]
    subject = parse_frontmatter(body).get("subject", "")
    if not subject:
        for line in body.splitlines()[:20]:
            if line.startswith("# "):
                subject = line[2:].strip()
                break

    for sentence, start, end in _split_sentences(text):
        if not _COMMITMENT_RE.search(sentence):
            continue
        norm = re.sub(r"\s+", " ", sentence.lower()).strip()
        if norm in seen:
            continue
        seen.add(norm)

        snippet = _snippet_around(text, start, end)
        title = sentence.strip()
        if len(title) > 120:
            title = title[:117] + "…"

        confidence = 0.45
        if _DEADLINE_HINT_RE.search(sentence):
            confidence = 0.55

        notes_parts = [f'Odeslaný e-mail `{name}`']
        if subject:
            notes_parts.append(f"předmět „{subject[:80]}“")
        notes_parts.append(f'citace: "{snippet}"')

        proposals.append(
            normalize_proposal(
                {
                    "action": "add_task",
                    "kind": "commitment",
                    "confidence": confidence,
                    "title": title,
                    "suggestedProj": guess_proj(text + " " + rel_path, rel_path),
                    "priority": "Next",
                    "ice": [7, 6, 5],
                    "notes": " — ".join(notes_parts),
                    "subtasks": [],
                    "sourceFile": rel_path,
                }
            )
        )

    return proposals


def llm_extract(
    rel_path: str,
    body: str,
    *,
    guess_proj: Callable[[str, str], str],
) -> list[dict] | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None

    text = email_body_text(body)
    if not text or len(text) < 20:
        return []

    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
    subject = parse_frontmatter(body).get("subject", "")
    prompt = (
        "Analyzuj odeslaný e-mail od Lukáše (Red Button EDU). "
        "Najdi pouze jeho závazky, sliby a úkoly vůči příjemci "
        "(co slíbil udělat, poslat, domluvit, zajistit, dokončit).\n"
        "Ignoruj citace cizích textů a obecné fráze bez akce.\n"
        "Vrať POUZE JSON pole objektů s klíči:\n"
        "  action (add_task | add_note_to_task | commitment_watch),\n"
        "  title (stručný název úkolu v češtině),\n"
        "  suggestedProj (slug tématu, např. finance, rb-universe-development),\n"
        "  priority (ASAP|Next|Backlog|Waiting),\n"
        "  ice ([I,C,E] 1-10),\n"
        "  notes (1 věta s citací z e-mailu),\n"
        "  confidence (0.0-1.0).\n"
        "Pokud žádný závazek není, vrať [].\n\n"
        f"Předmět: {subject}\n"
        f"Soubor: {rel_path}\n\n"
        f"Tělo:\n{text[:12000]}"
    )
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        print("triage_commitments: LLM skip:", e, file=sys.stderr)
        return None

    content = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            content += block.get("text", "")
    m = re.search(r"\[[\s\S]*\]", content)
    if not m:
        return []
    try:
        raw = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, list):
        return None

    proposals: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        action = str(item.get("action") or "add_task")
        if action not in ("add_task", "add_note_to_task", "commitment_watch"):
            action = "add_task"
        try:
            confidence = float(item.get("confidence", 0.75))
        except (TypeError, ValueError):
            confidence = 0.75
        confidence = max(0.0, min(1.0, confidence))
        ice = item.get("ice")
        if not isinstance(ice, list) or len(ice) != 3:
            ice = [7, 6, 5]
        proposals.append(
            {
                "action": action,
                "kind": "commitment",
                "confidence": confidence,
                "title": title[:120],
                "suggestedProj": str(item.get("suggestedProj") or guess_proj(text, rel_path)),
                "priority": str(item.get("priority") or "Next"),
                "ice": ice,
                "notes": str(item.get("notes") or "")[:500],
                "subtasks": [],
                "sourceFile": rel_path,
            }
        )
    return proposals


# Business closure / contract termination in sent mail (no commitment verb).
_SENT_BUSINESS_ACTION_RE = re.compile(
    r"(?:"
    r"ukonč\w*|zrušit\s+smlouv\w*|vypověd\w*|ukončení\s+služeb|"
    r"nevyužív\w*|zrušení\s+služeb"
    r")",
    re.IGNORECASE,
)


def sent_business_action_proposal(
    rel_path: str,
    body: str,
    *,
    guess_proj: Callable[[str, str], str],
) -> dict | None:
    """Suggest add_task when sent mail implies contract/service closure."""
    if not is_sent_email(rel_path, body):
        return None
    text = email_body_text(body)
    if not text or not _SENT_BUSINESS_ACTION_RE.search(text):
        return None

    fm = parse_frontmatter(body)
    subject = fm.get("subject", "")
    name = rel_path.rsplit("/", 1)[-1]
    low = (text + " " + subject + " " + rel_path).lower()

    if "ninjabot" in low:
        title = "Ukončit Ninjabot smlouvu"
        proj = "pipedrive-a-dalsi-nastroje"
    else:
        title = (subject or "Ukončit službu / smlouvu (odeslaný e-mail)")[:120]
        proj = guess_proj(text + " " + rel_path, rel_path)

    notes_parts = [f"Odeslaný e-mail `{name}` (bez závazkového slovesa)"]
    if subject:
        notes_parts.append(f"předmět „{subject[:80]}“")
    snippet = re.sub(r"\s+", " ", text[:200]).strip()
    if snippet:
        notes_parts.append(f'kontext: "{snippet}"')

    return {
        "action": "add_task",
        "proposalType": "add_task",
        "kind": "sent_closure",
        "confidence": 0.5,
        "title": title,
        "suggestedProj": proj,
        "priority": "Waiting",
        "ice": [7, 8, 6],
        "notes": " — ".join(notes_parts),
        "subtasks": [],
        "sourceFile": rel_path,
        "archiveAfterApply": True,
    }


def sent_archive_only_proposal(rel_path: str, body: str) -> dict:
    """Sent mail with no commitments and no business-action heuristic."""
    name = rel_path.rsplit("/", 1)[-1]
    fm = parse_frontmatter(body)
    subject = fm.get("subject", "") or name
    return {
        "action": "archive_only",
        "proposalType": "archive_only",
        "kind": "sent_info",
        "title": f"Archivovat odeslaný e-mail: {subject[:80]}",
        "suggestedProj": "",
        "priority": "",
        "ice": [],
        "notes": f"Odeslaný e-mail bez závazku — po schválení přesunout do HOTOVO (`{name}`).",
        "subtasks": [],
        "sourceFile": rel_path,
        "archiveAfterApply": True,
    }


def normalize_proposal(pr: dict) -> dict:
    """Ensure proposalType, archiveAfterApply, and action alignment."""
    out = dict(pr)
    action = str(out.get("action") or "add_task")
    if action in ("add_note_to_task", "commitment_watch"):
        out.setdefault("proposalType", "update_task")
    elif action == "archive_only":
        out.setdefault("proposalType", "archive_only")
    else:
        out.setdefault("proposalType", "add_task")
    if "archiveAfterApply" not in out:
        out["archiveAfterApply"] = True
    return out


def extract_commitments(
    rel_path: str,
    body: str,
    *,
    guess_proj: Callable[[str, str], str],
) -> list[dict]:
    """Return commitment proposals for a sent email INBOX item."""
    if not is_sent_email(rel_path, body):
        return []
    llm = llm_extract(rel_path, body, guess_proj=guess_proj)
    if llm is not None:
        return [normalize_proposal(p) for p in llm]
    raw = heuristic_extract(rel_path, body, guess_proj=guess_proj)
    return [normalize_proposal(p) for p in raw]
