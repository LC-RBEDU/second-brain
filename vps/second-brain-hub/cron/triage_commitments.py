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
        return llm
    return heuristic_extract(rel_path, body, guess_proj=guess_proj)
