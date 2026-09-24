"""Evaluate relevance of ``01-INBOX/slack/`` items for triage routing.

Two source kinds land in the same folder:

1. **capture_n8n** — intentional :cowork: / reaction capture from
   ``slack-cowork-inbox-with-attachments.json`` (``## Komentář``,
   ``## Forwardovaný obsah``, ``**Čas:**``).
2. **thread_dump** — full thread export with ``**Vlákno:**`` and quoted
   ``> **Name**`` messages. Hub ``slack_poll`` :gear: dumps use
   ``Důvod zálohy: označeno :gear:`` → route **batch**.

Routes (always evaluated before default ``add_task`` for slack):

- **archive** — Lukáš interaction without actionable commitment → ``archive_only``
- **batch** — clear Lukáš action or intentional capture note → ``add_task``
- **deep** — long / multi-party thread or forward-heavy capture → ``deep_analysis``
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

SlackRoute = Literal["archive", "batch", "deep"]
SlackSourceKind = Literal["capture_n8n", "thread_dump", "unknown"]

# Lukáš commitment language (subset aligned with triage_commitments).
_COMMITMENT_RE = re.compile(
    r"\b("
    r"přislíbím|slíbím|pošlu|zašlu|odešlu|odšlu|dodám|zajistím|domluvím|"
    r"připravím|dám\s+vědět|ozvu\s+se|napíšu|zkontroluju|zkontroluji|"
    r"prověřím|projdu|udělám|doplním|dokončím|předám|"
    r"schválím|reviewnu|pořeším|vyřeším|nastavím|upravím|opravím|"
    r"pošleme|zašleme|zajistíme|domluvíme|připravíme|dodáme|"
    r"musím|potřebuju|potřebuji|měl\s+bych|"
    r"do\s+(?:pondělí|úterý|středy|čtvrtka|pátku|soboty|neděle|"
    r"zítra|dnes|týdne|měsíce|\d{1,2}\.\s*\d{1,2}\.)"
    r")\b",
    re.IGNORECASE,
)

# Passive participation — not a Lukáš-owned task.
_PASSIVE_RE = re.compile(
    r"nech[aá]m\s+na\s+(?:v[aá]s|vás)|"
    r"j[aá]\s+tam\s+(?:vůbec\s+)?nem[aá]m|"
    r"prota[hž]l\s+call|"
    r"\bdelay\b|"
    r"\bpardon\b|"
    r"d[ií]ky\s+moc\s+za\s+dota[zž]|"
    r"m[uů]žete\s+dal[sš][ií]|"
    r"can\s+you\s+cancel|"
    r"@\w+\s+can\s+you",
    re.IGNORECASE,
)

_THREAD_DUMP_FILENAME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}_[^/]+_\d+\.\d+\.md$",
)
_CAPTURE_N8N_FILENAME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}-\d{4}-",
)
# thread dumps: 2026-08-24_dm-x_1787226196.980259_v3.md
# messy duplicate: 2026-08-20_dm-x_1787226196 (1).980259_v1.md
_THREAD_VERSION_FILENAME_RE = re.compile(
    r"_(\d+)(?:\s*\(\d+\))?\.(\d+)_v(\d+)\.md$",
)
_THREAD_TS_BODY_RE = re.compile(r"\*\*Thread TS:\*\*\s*(\d+\.\d+)")

_LUKAS_SPEAKER_RE = re.compile(r"\*\*Lukáš(?:\s+Cypra)?\*\*", re.IGNORECASE)
_QUOTED_MESSAGE_RE = re.compile(r"^>\s*\*\*[^*]+\*\*", re.MULTILINE)
# thread_dump v2: ``**Jméno** 12:53`` (export bez blockquote)
_SPEAKER_LINE_RE = re.compile(
    r"^\*\*[^*]+\*\*\s+\d{1,2}:\d{2}",
    re.MULTILINE,
)
# Incoming work for Lukáš when he did not post in the thread (DM / @mention / capture reason).
_ADDRESSED_TO_LUKAS_HEADER_RE = re.compile(
    r"\*\*Důvod\s+zálohy:\*\*\s*adresováno\s+mně",
    re.IGNORECASE,
)
_EYES_CAPTURE_HEADER_RE = re.compile(
    r"\*\*Důvod\s+zálohy:\*\*\s*označeno\s+:(?:gear|eyes):",
    re.IGNORECASE,
)
_KIND_EYES_FM_RE = re.compile(
    r"^kind:\s*(?:gear|eyes)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_MENTION_LUKAS_RE = re.compile(r"@Lukáš\b|@lukas\b", re.IGNORECASE)
_INBOUND_WORK_RE = re.compile(
    r"\bbackend\s+changes\b|"
    r"tvému\s+Cursorovi|"
    r"\bpro\s+Lukáše\b|"
    r"\bLukáš\s+posílá\b|"
    r"\bLukáš\s+Cypra\b",
    re.IGNORECASE,
)
_ATTACHMENT_SPEC_RE = re.compile(
    r"příloha:\s*.+\.md",
    re.IGNORECASE,
)

_SECTION_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


@dataclass
class SlackRelevanceResult:
    route: SlackRoute
    source_kind: SlackSourceKind
    confidence: float
    reasons: list[str] = field(default_factory=list)
    lukas_text: str = ""


def is_slack_inbox(rel_path: str) -> bool:
    return rel_path.startswith("01-INBOX/slack/") and rel_path.endswith(".md")


def slack_thread_version_key(filename: str, body: str = "") -> tuple[str, int] | None:
    """Return (thread_ts, version) for a versioned thread dump, else None."""
    m = _THREAD_TS_BODY_RE.search(body or "")
    thread_ts = m.group(1) if m else None
    vm = _THREAD_VERSION_FILENAME_RE.search(filename)
    if not vm:
        # Cron Later files have no _vN. They are not a version of the Cowork dump.
        return None
    ts = thread_ts or f"{vm.group(1)}.{vm.group(2)}"
    return ts, int(vm.group(3))


def stale_slack_rel_paths_from_items(
    items: list[tuple[str, str]],
) -> set[str]:
    """Rel paths of thread dumps superseded by a higher ``_vN`` sibling."""
    groups: dict[str, list[tuple[int, str]]] = {}
    for rel, body in items:
        if not is_slack_inbox(rel):
            continue
        name = rel.rsplit("/", 1)[-1]
        key = slack_thread_version_key(name, body[:2000] if body else "")
        if not key:
            continue
        thread_ts, ver = key
        groups.setdefault(thread_ts, []).append((ver, rel))
    stale: set[str] = set()
    for versions in groups.values():
        if len(versions) < 2:
            continue
        max_ver = max(v for v, _ in versions)
        for ver, rel in versions:
            if ver < max_ver:
                stale.add(rel)
    return stale


def stale_slack_rel_paths(slack_dir: Path) -> set[str]:
    """Local-dir wrapper around ``stale_slack_rel_paths_from_items``."""
    if not slack_dir.is_dir():
        return set()
    items: list[tuple[str, str]] = []
    for p in slack_dir.glob("*.md"):
        try:
            body = p.read_text(encoding="utf-8", errors="replace")[:2000]
        except OSError:
            body = ""
        items.append((f"01-INBOX/slack/{p.name}", body))
    return stale_slack_rel_paths_from_items(items)


def classify_slack_source(rel_path: str, body: str) -> SlackSourceKind:
    name = rel_path.rsplit("/", 1)[-1]
    head = body[:1200]
    if "**Vlákno:**" in head or _THREAD_DUMP_FILENAME_RE.match(name):
        return "thread_dump"
    if (
        "**Čas:**" in head
        and ("## Komentář" in body or "**Uživatel (Slack ID):**" in head)
    ) or _CAPTURE_N8N_FILENAME_RE.match(name):
        return "capture_n8n"
    if _QUOTED_MESSAGE_RE.search(body):
        return "thread_dump"
    return "unknown"


def extract_section(body: str, heading: str) -> str:
    """Return markdown body under ``## heading`` until next heading."""
    marker = heading.strip().lower()
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = _SECTION_RE.match(line)
        if m and m.group(2).strip().lower() == marker.removeprefix("## ").strip():
            start = i + 1
            level = len(m.group(1))
            break
    if start is None:
        return ""
    out: list[str] = []
    for line in lines[start:]:
        m = _SECTION_RE.match(line)
        if m and len(m.group(1)) <= level:
            break
        out.append(line)
    return "\n".join(out).strip()


def extract_lukas_messages(body: str) -> str:
    """Collect quoted Slack lines attributed to Lukáš."""
    chunks: list[str] = []
    current: list[str] = []
    for line in body.splitlines():
        if _LUKAS_SPEAKER_RE.search(line):
            if current:
                chunks.append(" ".join(current))
            current = [re.sub(r"^>\s*", "", line).strip()]
            continue
        if current and line.startswith(">"):
            current.append(line.lstrip("> ").strip())
        elif current:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return "\n\n".join(chunks)


def _count_quoted_messages(body: str) -> int:
    return len(_QUOTED_MESSAGE_RE.findall(body)) + len(_SPEAKER_LINE_RE.findall(body))


def detect_inbound_work_for_lukas(body: str, lukas_text: str = "") -> tuple[bool, list[str]]:
    """True when the thread assigns work to Lukáš but he did not speak."""
    if lukas_text.strip():
        return False, []
    reasons: list[str] = []
    if _ADDRESSED_TO_LUKAS_HEADER_RE.search(body):
        reasons.append("Důvod zálohy: adresováno mně")
    if _MENTION_LUKAS_RE.search(body):
        reasons.append("@Lukáš ve vlákně")
    if _INBOUND_WORK_RE.search(body):
        reasons.append("požadavek směřovaný na Lukáše / backend")
    if _ATTACHMENT_SPEC_RE.search(body):
        reasons.append("příloha se specifikací (.md)")
    return bool(reasons), reasons


def evaluate_slack_inbox_relevance(
    rel_path: str,
    body: str,
    *,
    guess_proj: Callable[[str, str], str] | None = None,
    stale_rels: set[str] | frozenset[str] | None = None,
) -> SlackRelevanceResult | None:
    """Return routing decision for slack INBOX item, or None if not slack.

    ``stale_rels`` = superseded thread dumps (lower ``_vN``). Always archive
    those — never extract commitments from an outdated snapshot.
    """
    if not is_slack_inbox(rel_path):
        return None

    if stale_rels and rel_path in stale_rels:
        return SlackRelevanceResult(
            route="archive",
            source_kind=classify_slack_source(rel_path, body),
            confidence=0.99,
            reasons=["zastaralá verze vlákna — existuje vyšší _vN (ignorovat)"],
        )

    kind = classify_slack_source(rel_path, body)
    reasons: list[str] = []

    # Intentional :gear: capture (hub slack_poll) → batch, never silent archive.
    if _EYES_CAPTURE_HEADER_RE.search(body) or _KIND_EYES_FM_RE.search(body):
        reasons.append("záměrný capture :gear:")
        return SlackRelevanceResult(
            route="batch",
            source_kind=kind,
            confidence=0.95,
            reasons=reasons,
        )

    if kind == "capture_n8n":
        komentar = extract_section(body, "Komentář")
        forward = extract_section(body, "Forwardovaný obsah")
        if komentar and _COMMITMENT_RE.search(komentar):
            reasons.append("záměrný capture s Lukášovým závazkem v ## Komentář")
            return SlackRelevanceResult(
                route="batch",
                source_kind=kind,
                confidence=0.85,
                reasons=reasons,
                lukas_text=komentar,
            )
        if komentar and len(komentar.strip()) > 25:
            reasons.append("záměrný capture s poznámkou v ## Komentář")
            return SlackRelevanceResult(
                route="batch",
                source_kind=kind,
                confidence=0.75,
                reasons=reasons,
                lukas_text=komentar,
            )
        if forward and (len(forward) > 1500 or _count_quoted_messages(forward) > 4):
            reasons.append("forwardovaný obsah — potřeba DEEP rozboru")
            return SlackRelevanceResult(
                route="deep",
                source_kind=kind,
                confidence=0.8,
                reasons=reasons,
                lukas_text=komentar,
            )
        if komentar.strip():
            reasons.append("capture s krátkým komentářem")
            return SlackRelevanceResult(
                route="batch",
                source_kind=kind,
                confidence=0.65,
                reasons=reasons,
                lukas_text=komentar,
            )
        reasons.append("capture bez komentáře — jen forward")
        return SlackRelevanceResult(
            route="deep",
            source_kind=kind,
            confidence=0.7,
            reasons=reasons,
        )

    if kind == "thread_dump":
        lukas_text = extract_lukas_messages(body)
        msg_count = _count_quoted_messages(body)
        inbound, inbound_reasons = detect_inbound_work_for_lukas(body, lukas_text)
        if inbound:
            reasons.extend(inbound_reasons)
            reasons.append("inbound požadavek bez Lukášovy odpovědi — DEEP, ne archiv")
            return SlackRelevanceResult(
                route="deep",
                source_kind=kind,
                confidence=0.9,
                reasons=reasons,
                lukas_text=lukas_text,
            )
        if not lukas_text.strip():
            reasons.append("vlákno bez zprávy od Lukáše")
            return SlackRelevanceResult(
                route="archive",
                source_kind=kind,
                confidence=0.9,
                reasons=reasons,
            )
        if _PASSIVE_RE.search(lukas_text) and not _COMMITMENT_RE.search(lukas_text):
            reasons.append("pasivní účast / delegace bez Lukášova závazku")
            return SlackRelevanceResult(
                route="archive",
                source_kind=kind,
                confidence=0.85,
                reasons=reasons,
                lukas_text=lukas_text,
            )
        if _COMMITMENT_RE.search(lukas_text):
            if len(lukas_text) > 450 or msg_count > 8:
                reasons.append("Lukášův závazek v dlouhém vlákně")
                return SlackRelevanceResult(
                    route="deep",
                    source_kind=kind,
                    confidence=0.8,
                    reasons=reasons,
                    lukas_text=lukas_text,
                )
            reasons.append("Lukášův závazek v krátkém vlákně")
            return SlackRelevanceResult(
                route="batch",
                source_kind=kind,
                confidence=0.8,
                reasons=reasons,
                lukas_text=lukas_text,
            )
        if len(body) > 2500 or msg_count > 6:
            reasons.append("dlouhé vlákno bez jasného Lukášova tasku")
            return SlackRelevanceResult(
                route="deep",
                source_kind=kind,
                confidence=0.65,
                reasons=reasons,
                lukas_text=lukas_text,
            )
        reasons.append("interakce bez commitmentu — kontext k archivaci")
        return SlackRelevanceResult(
            route="archive",
            source_kind=kind,
            confidence=0.75,
            reasons=reasons,
            lukas_text=lukas_text,
        )

    # Unknown slack format — conservative: short → archive, long → deep
    if len(body) > 2000:
        return SlackRelevanceResult(
            route="deep",
            source_kind="unknown",
            confidence=0.5,
            reasons=["neznámý formát slack INBOX — dlouhý obsah"],
        )
    return SlackRelevanceResult(
        route="archive",
        source_kind="unknown",
        confidence=0.5,
        reasons=["neznámý formát slack INBOX — bez jasné akce"],
    )


def slack_archive_proposal(rel_path: str, body: str, result: SlackRelevanceResult) -> dict:
    name = rel_path.rsplit("/", 1)[-1]
    channel = ""
    m = re.search(r"\*\*Kanál:\*\*\s*(.+)", body)
    if m:
        channel = m.group(1).strip()[:60]
    title_bits = ["Archivovat Slack"]
    if channel:
        title_bits.append(channel)
    else:
        title_bits.append(name.replace(".md", "")[:60])
    reasons_s = "; ".join(result.reasons) if result.reasons else "bez akce"
    return {
        "action": "archive_only",
        "proposalType": "archive_only",
        "kind": "slack_thread_archive",
        "confidence": result.confidence,
        "title": " — ".join(title_bits)[:120],
        "suggestedProj": "",
        "priority": "",
        "ice": [],
        "notes": f"Slack INBOX ({result.source_kind}) — {reasons_s}. "
        f"Po schválení přesunout do HOTOVO (`{name}`).",
        "subtasks": [],
        "sourceFile": rel_path,
        "archiveAfterApply": True,
        "slack_route": result.route,
        "slack_source_kind": result.source_kind,
        "slack_relevance_reasons": list(result.reasons),
    }


def enrich_proposal_with_slack_meta(proposal: dict, result: SlackRelevanceResult) -> dict:
    out = dict(proposal)
    out["slack_route"] = result.route
    out["slack_source_kind"] = result.source_kind
    out["slack_relevance_reasons"] = list(result.reasons)
    if result.confidence and "confidence" not in out:
        out["confidence"] = result.confidence
    existing = (out.get("notes") or "").strip()
    reasons_s = "; ".join(result.reasons)
    prefix = f"Slack relevance ({result.route}): {reasons_s}"
    out["notes"] = f"{prefix}. {existing}" if existing else prefix
    return out
