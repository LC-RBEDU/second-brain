"""Heuristika pro detekci „komplexního materiálu" v 01-INBOX/.

Auto-routing v triage:
- ne-komplexní zdroj (slack ping, krátký mail, daily note) → default BATCH.
- komplexní zdroj (Sembly meeting transcript, dlouhý clipping, multi-action
  plán) → DEEP režim skillu `agenda-triage` (item-by-item analýza, víc
  tasků/materiálů z jednoho zdroje).

Heuristika je **OR** — stačí 1 splněné pravidlo a flag je `True`.
Override komentář `<!-- triage:deep -->` / `<!-- triage:simple -->` v těle
souboru má precedenci před vším ostatním.

Pravidla:
1. Override komentář (precedence).
2. Subdir `01-INBOX/sembly/` → vždy DEEP (přepisy meetingů).
3. Subdir `01-INBOX/email/sent/` → nikdy DEEP (sent commitment fast-path
   běží před touto funkcí, ale chováme se defenzivně).
4. word_count > 800 → DEEP.
5. line_count > 100 → DEEP.
6. 3+ H2/H3 headingů v těle → DEEP (strukturovaný materiál).
7. 5+ unchecked checkboxů `- [ ]` v těle → DEEP (multi-action plán).
8. Signální fráze v těle ("Action items", "Akční kroky", "Úkoly",
   "Závěry", "Decision points", "Rozhodnutí") → DEEP.
9. Sekce ``## Přílohy`` s alespoň jednou položkou (Drive link / soubor) → DEEP.

Funkce vrací `(is_complex, reasons)`; `reasons` je lidsky čitelný seznam
pro debug / batch summary, nikdy neobsahuje větší výřez těla.
"""
from __future__ import annotations

import re

# Frontmatter (YAML) — odřízneme před vyhodnocením size/content metrik.
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Override HTML komentáře — hledáme v celém těle (před i za frontmatterem).
_OVERRIDE_DEEP_RE = re.compile(r"<!--\s*triage:\s*deep\s*-->", re.IGNORECASE)
_OVERRIDE_SIMPLE_RE = re.compile(r"<!--\s*triage:\s*simple\s*-->", re.IGNORECASE)

# H2/H3 markdown headingy (počítáme pouze v body, ne v YAML).
_HEADING_RE = re.compile(r"^(?:#{2,3})\s+\S", re.MULTILINE)

# Unchecked checkbox — `- [ ]` nebo `* [ ]` (chceme jen otevřené úkoly,
# proto vynecháváme `- [x]`).
_CHECKBOX_OPEN_RE = re.compile(r"^[ \t]*[-*]\s\[\s\]\s+\S", re.MULTILINE)

# ## Přílohy sekce — SSOT formát z n8n capture workflows.
_ATTACHMENTS_SECTION_RE = re.compile(
    r"^##\s+Přílohy(?:\s*\(\d+\))?\s*$",
    re.MULTILINE | re.IGNORECASE,
)
_ATTACHMENT_ITEM_RE = re.compile(
    r"^-\s+(?:\[[^\]]+\]\([^)]+\)|\S)",
    re.MULTILINE,
)

# Signální fráze — case-insensitive, hledáme jako samostatná slova /
# nadpisy v body.
_SIGNAL_PHRASES = (
    "action items",
    "akční kroky",
    "akcni kroky",
    "úkoly",
    "ukoly",
    "závěry",
    "zavery",
    "decision points",
    "rozhodnutí",
    "rozhodnuti",
    "next steps",
    "další kroky",
    "dalsi kroky",
)

# Prahy
_WORD_COUNT_THRESHOLD = 800
_LINE_COUNT_THRESHOLD = 100
_HEADING_THRESHOLD = 3
_CHECKBOX_THRESHOLD = 5


def _strip_frontmatter(body: str) -> str:
    """Return body without leading YAML frontmatter."""
    m = _FRONTMATTER_RE.match(body or "")
    if not m:
        return body or ""
    return body[m.end():]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def _normalize_path(rel_path: str) -> str:
    return (rel_path or "").replace("\\", "/")


def _is_sembly_source(rel_path: str) -> bool:
    norm = _normalize_path(rel_path)
    return "/sembly/" in norm or norm.endswith("/sembly")


def _is_sent_email_source(rel_path: str) -> bool:
    norm = _normalize_path(rel_path)
    return "/email/sent/" in norm or norm.endswith("/email/sent")


def _has_attachments_section(content: str) -> bool:
    """True when body contains ``## Přílohy`` with at least one list item."""
    m = _ATTACHMENTS_SECTION_RE.search(content)
    if not m:
        return False
    rest = content[m.end() :]
    next_heading = re.search(r"^##\s+\S", rest, re.MULTILINE)
    block = rest[: next_heading.start()] if next_heading else rest
    return bool(_ATTACHMENT_ITEM_RE.search(block))


# 10. Inline odkaz na Google Docs/Sheets/Slides nebo souborový dokument → DEEP.
_DOC_LINK_RE = re.compile(
    r"https?://(?:docs\.google\.com/(?:document|spreadsheets|presentation)|drive\.google\.com/file)[^\s)\]>\"']+",
    re.IGNORECASE,
)
_FILE_EXT_LINK_RE = re.compile(
    r"https?://[^\s)\]>\"']+\.(?:pdf|docx?|xlsx?)(?:\?[^\s)\]>\"']*)?",
    re.IGNORECASE,
)


def _has_inline_document_links(content: str) -> bool:
    if _DOC_LINK_RE.search(content):
        return True
    if _FILE_EXT_LINK_RE.search(content):
        return True
    return False


def has_attachments_markers(body: str) -> bool:
    """Public helper — ``## Přílohy`` section in inbox markdown body."""
    content = _strip_frontmatter(body or "")
    return _has_attachments_section(content)


def is_complex_source(rel_path: str, body: str) -> tuple[bool, list[str]]:
    """Return ``(is_complex, reasons)`` pro auto-routing v triage.

    `reasons` je seznam lidsky čitelných řetězců (např. ``"sembly subdir"``,
    ``"word_count=1234"``, ``"4 H2/H3 headings"``). Použij ho do batch
    summary a debug logu — nikdy se neukládá víc než shrnutí, žádný výřez
    obsahu.
    """
    body = body or ""
    rel_path = rel_path or ""
    reasons: list[str] = []

    # 1. Override — má precedenci před vším.
    if _OVERRIDE_DEEP_RE.search(body):
        return True, ["override: <!-- triage:deep -->"]
    if _OVERRIDE_SIMPLE_RE.search(body):
        return False, ["override: <!-- triage:simple -->"]

    # 2. Sent email fast-path — nikdy DEEP (commitment extraction).
    if _is_sent_email_source(rel_path):
        return False, ["email/sent subdir (never DEEP)"]

    # 3. Sembly transcript — vždy DEEP (subdir-level pravidlo).
    if _is_sembly_source(rel_path):
        reasons.append("sembly subdir")

    content = _strip_frontmatter(body)

    # 4. Word count.
    wc = _word_count(content)
    if wc > _WORD_COUNT_THRESHOLD:
        reasons.append(f"word_count={wc}")

    # 5. Line count (jen ne-prázdné řádky, abychom nepřičetli prázdné
    # mezery z formátování).
    lc = sum(1 for ln in content.splitlines() if ln.strip())
    if lc > _LINE_COUNT_THRESHOLD:
        reasons.append(f"line_count={lc}")

    # 6. Strukturovaný materiál — H2/H3 headingy.
    headings = _HEADING_RE.findall(content)
    if len(headings) >= _HEADING_THRESHOLD:
        reasons.append(f"{len(headings)} H2/H3 headings")

    # 7. Multi-action plán — otevřené checkboxy.
    checkboxes = _CHECKBOX_OPEN_RE.findall(content)
    if len(checkboxes) >= _CHECKBOX_THRESHOLD:
        reasons.append(f"{len(checkboxes)} open checkboxes")

    # 8. Signální fráze.
    low = content.lower()
    matched_phrases: list[str] = []
    for phrase in _SIGNAL_PHRASES:
        if phrase in low:
            matched_phrases.append(phrase)
    if matched_phrases:
        reasons.append("signal phrases: " + ", ".join(sorted(set(matched_phrases))))

    # 9. Přílohy — materiál vyžaduje DEEP triáž (sidecar + materiály).
    if _has_attachments_section(content):
        reasons.append("## Přílohy section")

    # 10. Inline document links.
    if _has_inline_document_links(content):
        reasons.append("inline document link")

    return (len(reasons) > 0), reasons


__all__ = ["has_attachments_markers", "is_complex_source"]
